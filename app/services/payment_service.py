"""Stripe payment — Booking (thanh toán một lần).

Flow: khách chọn "online" -> tạo Checkout session (mode=payment) -> Stripe thu tiền
-> webhook `checkout.session.completed` -> booking chuyển 'confirmed' (bỏ qua OTP)
+ invoice 'paid'. Fulfill idempotent (webhook có thể retry nhiều lần)."""

from datetime import datetime, UTC

import stripe
from flask import current_app

from app.database.db import (
    get_connection, get_booking_by_id, get_service_by_id, create_invoice,
    set_customer_stripe_id, get_customer_by_stripe_customer, get_tier_by_stripe_price,
    upsert_subscription_membership, deactivate_subscription, get_active_subscription_rows,
)
from app.utils.helpers import now_helsinki, HELSINKI_TZ

# VAT khớp với con số Total hiển thị ở form booking
# (customer_booking.html / public_booking.html: price * (1 + VAT_RATE)).
VAT_RATE = 0.255


def _init_stripe():
    stripe.api_key = current_app.config["STRIPE_SECRET_KEY"]


def create_booking_checkout_session(booking, service, success_url, cancel_url):
    """Tạo Stripe Checkout session cho 1 booking. Thu Total gồm VAT
    (price * (1 + VAT_RATE)); invoice vẫn lưu price gốc (giống flow tiền mặt).
    Trả về URL để redirect khách sang Stripe."""
    _init_stripe()
    total = (service["price"] or 0) * (1 + VAT_RATE)
    # Gắn session_id vào success_url để fallback trên success page có thể tra
    # cứu & fulfill (Stripe thay {CHECKOUT_SESSION_ID} bằng id thật khi redirect).
    sep = "&" if "?" in success_url else "?"
    success_url = f"{success_url}{sep}session_id={{CHECKOUT_SESSION_ID}}"
    session = stripe.checkout.Session.create(
        mode="payment",
        line_items=[{
            "price_data": {
                "currency": "eur",
                "product_data": {"name": service["name"]},
                "unit_amount": int(round(total * 100)),  # Stripe tính bằng cent
            },
            "quantity": 1,
        }],
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={"type": "booking", "booking_id": str(booking["id"])},
    )
    return session.url


def create_subscription_checkout_session(customer, tier, success_url, cancel_url):
    """Tạo Checkout session gói tự động gia hạn (mode=subscription) cho 1 tier trả
    phí. Reuse stripe_customer_id nếu khách đã có. Gắn metadata lên cả session và
    subscription để các event sau (invoice.paid, subscription.*) đọc được."""
    _init_stripe()
    sep = "&" if "?" in success_url else "?"
    success_url = f"{success_url}{sep}session_id={{CHECKOUT_SESSION_ID}}"
    meta = {"type": "membership", "customer_id": str(customer["id"]), "tier_id": str(tier["id"])}
    params = dict(
        mode="subscription",
        line_items=[{"price": tier["stripe_price_id"], "quantity": 1}],
        success_url=success_url,
        cancel_url=cancel_url,
        metadata=meta,
        subscription_data={"metadata": meta},
    )
    if customer["stripe_customer_id"]:  # cột luôn tồn tại; None nếu chưa có Stripe customer
        params["customer"] = customer["stripe_customer_id"]
    session = stripe.checkout.Session.create(**params)
    return session.url


def create_billing_portal_session(stripe_customer_id, return_url):
    """Mở Stripe Customer Portal (trang hosted) để khách tự cập nhật thẻ — dùng khi
    subscription past_due (gia hạn thất bại). Trả URL để redirect."""
    _init_stripe()
    session = stripe.billing_portal.Session.create(
        customer=stripe_customer_id, return_url=return_url)
    return session.url


def cancel_subscription(subscription_id):
    """Hủy gia hạn: giữ quyền lợi tới hết kỳ đã trả rồi dừng (không hoàn tiền).
    Sync ngay vào DB từ object trả về (không đợi webhook); webhook sau re-sync."""
    _init_stripe()
    sub = stripe.Subscription.modify(subscription_id, cancel_at_period_end=True)
    _sync_subscription(sub)


def _cancel_other_subscriptions(customer_id, keep_sub_id):
    """Sau khi mua gói mới thành công: hủy gia hạn MỌI gói cũ khác của khách
    (giữ tới hết kỳ, không refund). keep_sub_id = gói vừa mua, không đụng."""
    for row in get_active_subscription_rows(customer_id):
        sid = row["stripe_subscription_id"]
        if sid and sid != keep_sub_id and not row["cancel_at_period_end"]:
            try:
                cancel_subscription(sid)
            except Exception as e:
                print(f"[payment] cancel old sub {sid} failed: {e}")


def construct_event(payload, sig_header):
    """Verify chữ ký webhook, trả về Stripe event (raise nếu payload/chữ ký sai)."""
    return stripe.Webhook.construct_event(
        payload, sig_header, current_app.config["STRIPE_WEBHOOK_SECRET"]
    )


def handle_event(event):
    """Định tuyến webhook event -> fulfill. Idempotent."""
    _init_stripe()
    etype = event["type"]
    obj = event["data"]["object"]
    if etype == "checkout.session.completed":
        _fulfill_session(obj)
    elif etype in ("customer.subscription.updated", "customer.subscription.created"):
        _sync_subscription(obj)
    elif etype == "customer.subscription.deleted":
        deactivate_subscription(obj["id"])
    elif etype in ("invoice.paid", "invoice.payment_failed"):
        sub_id = _invoice_subscription_id(obj)
        if sub_id:
            _sync_subscription(stripe.Subscription.retrieve(sub_id))


def _invoice_subscription_id(invoice):
    """Lấy subscription id từ invoice. API mới: invoice.parent.subscription_details
    .subscription; API cũ: invoice.subscription."""
    if "subscription" in invoice and invoice["subscription"]:
        return invoice["subscription"]
    parent = invoice["parent"] if "parent" in invoice else None
    if parent and parent["subscription_details"]:
        return parent["subscription_details"]["subscription"]
    return None


def fulfill_from_session(session_id):
    """Fallback (dùng trên success page): chủ động hỏi Stripe session đã trả tiền
    chưa; nếu rồi thì fulfill ngay (idempotent, chung với webhook). Bù cho ca
    webhook trễ/thiếu, và cho phép test local không cần Stripe CLI."""
    _init_stripe()
    try:
        session = stripe.checkout.Session.retrieve(session_id)
    except Exception as e:
        print(f"[payment] retrieve session failed: {e}")
        return None
    if session["payment_status"] in ("paid", "no_payment_required"):
        _fulfill_session(session)
    meta = session["metadata"].to_dict() if session["metadata"] else {}
    return meta.get("type")  # 'booking' | 'membership' | None (để success page điều hướng)


def _fulfill_session(session):
    """Fulfill 1 checkout session đã trả tiền (dùng chung webhook + fallback).
    Stripe object không hỗ trợ .get() -> chuyển metadata sang dict thường."""
    meta = session["metadata"].to_dict() if session["metadata"] else {}
    mtype = meta.get("type")
    if mtype == "booking":
        fulfill_booking_payment(int(meta["booking_id"]))
    elif mtype == "membership":
        _activate_membership_from_session(session)


def _activate_membership_from_session(session):
    """Checkout subscription hoàn tất: lưu stripe_customer_id + kích hoạt gói mới,
    rồi hủy gia hạn các gói cũ (đổi tier = mua mới + hủy cũ, không refund)."""
    meta = session["metadata"].to_dict() if session["metadata"] else {}
    customer_id = meta.get("customer_id")
    sc_id = session["customer"]
    if customer_id and sc_id:
        set_customer_stripe_id(int(customer_id), sc_id)
    sub_id = session["subscription"]
    if sub_id:
        _sync_subscription(stripe.Subscription.retrieve(sub_id))
        if customer_id:
            _cancel_other_subscriptions(int(customer_id), sub_id)


def _ts_to_helsinki(ts):
    """Unix timestamp (UTC) -> chuỗi naive giờ Helsinki khớp expires_at trong DB."""
    return (datetime.fromtimestamp(ts, tz=UTC).astimezone(HELSINKI_TZ)
            .replace(tzinfo=None).strftime("%Y-%m-%d %H:%M:%S"))


def _sync_subscription(sub):
    """Đồng bộ 1 Stripe Subscription vào DB (dùng cho mọi event subscription).
    customer_id lấy từ metadata (fallback: map qua stripe_customer_id); tier lấy
    từ price id trên item (luôn đúng kể cả sau khi đổi tier)."""
    meta = sub["metadata"].to_dict() if sub["metadata"] else {}
    customer_id = meta.get("customer_id")
    if not customer_id:
        c = get_customer_by_stripe_customer(sub["customer"])
        customer_id = c["id"] if c else None
    if not customer_id:
        print(f"[payment] subscription {sub['id']}: khong xac dinh duoc customer")
        return
    item = sub["items"]["data"][0]
    price_id = item["price"]["id"]
    tier = get_tier_by_stripe_price(price_id)
    if not tier:
        print(f"[payment] subscription {sub['id']}: price {price_id} khong map duoc tier")
        return
    cancel = 1 if sub["cancel_at_period_end"] else 0
    # current_period_end: API mới nằm ở subscription item, API cũ ở subscription.
    period_end = item["current_period_end"] if "current_period_end" in item else sub["current_period_end"]
    expires_at = _ts_to_helsinki(period_end)
    upsert_subscription_membership(int(customer_id), tier["id"], sub["id"],
                                   expires_at, sub["status"], cancel)


def fulfill_booking_payment(booking_id):
    """Thanh toán online thành công -> booking 'confirmed' (bỏ qua OTP) + invoice
    'paid'. Idempotent: chỉ confirm khi còn 'unverified' và slot chưa bị người khác
    chiếm; không tạo invoice trùng."""
    booking = get_booking_by_id(booking_id)
    if not booking:
        return
    service = get_service_by_id(booking["service_id"])
    updated_at = now_helsinki().strftime("%Y-%m-%d %H:%M:%S")

    conn = get_connection()
    try:
        # Re-check conflict như flow OTP: tránh 2 khách cùng trả tiền 1 slot -> double-book.
        conflict = conn.execute(
            """SELECT 1 FROM bookings
               WHERE staff_id = ? AND booking_date = ?
                 AND start_time < ? AND end_time > ?
                 AND status IN ('pending', 'confirmed', 'in-progress')
                 AND id != ?""",
            (booking["staff_id"], booking["booking_date"],
             booking["end_time"], booking["start_time"], booking_id),
        ).fetchone()

        if conflict:
            # Hiếm: slot đã bị người khác xác nhận trong lúc khách đang trả tiền.
            # Không confirm (tránh double-book). Ghi log để admin xử lý refund/đổi giờ.
            print(f"[payment] WARN booking {booking_id} paid but slot taken -> cần xử lý thủ công")
        else:
            conn.execute(
                "UPDATE bookings SET status='confirmed', updated_at=? "
                "WHERE id=? AND status='unverified'",
                (updated_at, booking_id),
            )

        # Ghi nhận invoice 'paid' (tiền đã thu). Idempotent theo booking_id.
        existing = conn.execute(
            "SELECT 1 FROM invoices WHERE booking_id=?", (booking_id,)
        ).fetchone()
        if not existing and service:
            create_invoice(conn, booking_id, service["price"] or 0, "online", "paid")

        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
