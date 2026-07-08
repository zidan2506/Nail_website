"""Stripe payment — Booking (thanh toán một lần).

Flow: khách chọn "online" -> tạo Checkout session (mode=payment) -> Stripe thu tiền
-> webhook `checkout.session.completed` -> booking chuyển 'confirmed' (bỏ qua OTP)
+ invoice 'paid'. Fulfill idempotent (webhook có thể retry nhiều lần)."""

import stripe
from flask import current_app

from app.database.db import (
    get_connection, get_booking_by_id, get_service_by_id, create_invoice,
)
from app.utils.helpers import now_helsinki

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


def construct_event(payload, sig_header):
    """Verify chữ ký webhook, trả về Stripe event (raise nếu payload/chữ ký sai)."""
    return stripe.Webhook.construct_event(
        payload, sig_header, current_app.config["STRIPE_WEBHOOK_SECRET"]
    )


def handle_event(event):
    """Định tuyến webhook event -> fulfill. Idempotent."""
    if event["type"] == "checkout.session.completed":
        _fulfill_session(event["data"]["object"])


def fulfill_from_session(session_id):
    """Fallback (dùng trên success page): chủ động hỏi Stripe session đã 'paid'
    chưa; nếu rồi thì fulfill ngay (idempotent, chung với webhook). Bù cho ca
    webhook trễ/thiếu, và cho phép test local không cần Stripe CLI."""
    _init_stripe()
    try:
        session = stripe.checkout.Session.retrieve(session_id)
    except Exception as e:
        print(f"[payment] retrieve session failed: {e}")
        return
    if session["payment_status"] == "paid":
        _fulfill_session(session)


def _fulfill_session(session):
    """Fulfill 1 checkout session đã trả tiền (dùng chung webhook + fallback).
    Stripe object không hỗ trợ .get() -> chuyển metadata sang dict thường."""
    meta = session["metadata"].to_dict() if session["metadata"] else {}
    if meta.get("type") == "booking":
        fulfill_booking_payment(int(meta["booking_id"]))


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
