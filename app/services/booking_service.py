from app.utils.helpers import parse_time, now_helsinki, today_helsinki
from datetime import timedelta
from datetime import datetime
from app.services.email_system import generate_verification_code, send_verification_email
from app.database.db import get_staff_by_id, get_available_staff_for_slot , get_customer_by_email , create_customer, create_verification, create_booking, get_customer_id, get_booking_by_id, get_service_by_id, get_connection, create_invoice
from app.services.loyalty import get_active_multiplier, get_config_value, already_awarded, award_points, check_streak
import random

def is_overlap(candidate_start, candidate_end, existing_start, existing_end):
    return candidate_start < existing_end and candidate_end > existing_start

def get_available_slots(duration_min, existing_bookings, open_time="09:00", close_time="18:00", step_minutes=30):
    available_slots = []
    
    current = parse_time(open_time)
    close_dt = parse_time(close_time)
    service_duration = timedelta(minutes=duration_min)

    while current + service_duration <= close_dt:
        candidate_start = current
        candidate_end = current + service_duration

        conflict = False

        for booking in existing_bookings:
            existing_start = parse_time(booking["start_time"])
            existing_end = parse_time(booking["end_time"])

            if is_overlap(candidate_start, candidate_end, existing_start, existing_end):
                conflict = True
                break
        
        if not conflict:
            available_slots.append(candidate_start.strftime("%H:%M"))

        current += timedelta(minutes=step_minutes)

    return available_slots

def get_following_days(n_days):
    date_list = []
    today = today_helsinki()

    for i in range(n_days):
        current_date = today + timedelta(days=i)
        date_list.append({
            "value": current_date.strftime("%Y-%m-%d"),
            "label": current_date.strftime("%d %b")
        })
    return date_list


#Error handling
class GuestInfoMissingError(Exception):
    pass

class BookingValidatorError(Exception):
    pass

class GuestService:
    @staticmethod
    def resolve_customer_info(form):
        name = form.get("full_name", "").strip()
        phone = form.get("phone", "").strip()
        email = form.get("email", "").strip()


        if not name or not phone or not email:
            raise GuestInfoMissingError("Please fill in guest information")

        customer = get_customer_by_email(email)
        if customer is None:
            create_customer(name, email, phone)
            customer = get_customer_by_email(email)
        return customer
        
    
# Map lựa chọn payment_method trên form -> công cụ thanh toán lưu ở booking/invoice.
# Hiện chỉ có "pay_at_salon" (trả tiền mặt tại tiệm); online payment đang "coming soon".
_PAYMENT_METHOD_MAP = {"pay_at_salon": "cash"}

class BookingService:
    @staticmethod
    def parse_form(form):
        return {
            "note": form.get("note", "").strip(),
            "service_id": int(form.get("service_id", "").strip()),
            "staff_id": int(form.get("staff_id", "").strip()),
            "booking_date": form.get("booking_date", "").strip(),
            "slot": form.get("start_time", "").strip(),
            "payment_method": _PAYMENT_METHOD_MAP.get(
                form.get("payment_method", "pay_at_salon").strip(), "cash"),
        }
    
    def parse_slot(booking_date, slot, duration_minutes):
        date_obj = datetime.strptime(booking_date, "%Y-%m-%d").date()
        time_obj = datetime.strptime(slot, "%H:%M").time()
        start_at = datetime.combine(date_obj, time_obj)
        end_at = start_at + timedelta(minutes=duration_minutes)
        return start_at.strftime("%H:%M"), end_at.strftime("%H:%M")
    
    def pick_staff(staff_id, service_id, booking_date, start_time, end_time):
        
        staff_id = int(staff_id)
        service_id = int(service_id)

        if staff_id != 0:
            staff = get_staff_by_id(staff_id)
            return staff 

        availalble = get_available_staff_for_slot(
            booking_date,
            start_time,
            end_time
        )
        
        if not availalble:
            raise BookingValidatorError("No staff availalble for this slot")
        
        picked = random.choice(availalble)
        return picked
    
    def create(customer_id, staff_id, service_id, booking_date, start_time, end_time, note, email, payment_method):
        booking_id = create_booking(customer_id, staff_id, service_id, booking_date, start_time, end_time, "unverified", note, payment_method)
        verification_id = VerificationService.create_booking_verification(email)
        return booking_id, verification_id
    
class VerificationService:
    @staticmethod
    def create_booking_verification(email):
        code = generate_verification_code()
        send_verification_email(email, code, "booking")
        expires_at = (now_helsinki() + timedelta(minutes=10)).strftime("%Y-%m-%d %H:%M:%S")
        verification_id = create_verification(code, "booking", expires_at)
        return verification_id


def complete_booking_txn(booking_id):
    """Nguồn chân lý DUY NHẤT để hoàn tất 1 booking sang 'done': snapshot thu
    nhập staff + tạo invoice (pending) + trao điểm loyalty (base/double/first/
    streak), tất cả trong 1 transaction, và bump updated_at. Idempotent nhờ
    guard already_awarded + kiểm tra invoice đã tồn tại (chạy lại không double).
    Dùng chung cho staff portal, admin đổi status, và dev_tools. Trả True nếu OK."""
    booking = get_booking_by_id(booking_id)
    service = get_service_by_id(booking["service_id"]) if booking else None
    staff = get_staff_by_id(booking["staff_id"]) if booking else None
    if not booking or not service or not staff:
        return False

    customer_id = booking["customer_id"]
    booking_date = booking["booking_date"]
    multiplier = get_active_multiplier(customer_id)
    base_points = int((service["points"] or 0) * multiplier)
    double_points_day = get_config_value("double_points_day")
    booking_day = datetime.strptime(booking_date, "%Y-%m-%d").isoweekday()
    streak_ref = int(datetime.strptime(booking_date, "%Y-%m-%d").strftime("%Y%m"))

    # Snapshot thu nhập tại thời điểm hoàn thành, không tính live theo rate hiện tại.
    hourly_earning = (staff["hourly_rate"] or 0) * (service["duration_minutes"] or 0) / 60
    commission = (service["price"] or 0) * (staff["commission_rate"] or 0) / 100
    total_earning = hourly_earning + commission
    updated_at = now_helsinki().strftime("%Y-%m-%d %H:%M:%S")

    conn = get_connection()
    try:
        conn.execute(
            """UPDATE bookings
               SET status = 'done', staff_hourly_earning = ?, staff_commission = ?,
                   staff_total_earning = ?, updated_at = ?
               WHERE id = ?""",
            (hourly_earning, commission, total_earning, updated_at, booking_id)
        )

        # Tạo invoice khi hoàn thành (nếu chưa có). Cash -> 'pending' đến khi staff
        # xác nhận đã thu tiền thì mới tính vào doanh thu.
        existing_invoice = conn.execute(
            "SELECT 1 FROM invoices WHERE booking_id = ?", (booking_id,)
        ).fetchone()
        if not existing_invoice:
            create_invoice(conn, booking_id, service["price"] or 0,
                           booking["payment_method"], "pending")

        # 1. Base points
        if base_points > 0 and not already_awarded(customer_id, "booking", booking_id):
            award_points(customer_id, base_points, "booking", booking_id,
                         f"{service['name']} × {multiplier}", conn=conn)

        # 2. Double points day bonus
        if double_points_day and booking_day == double_points_day:
            if not already_awarded(customer_id, "double_points", booking_id):
                award_points(customer_id, base_points, "double_points", booking_id,
                             "Double points day bonus", conn=conn)

        # 3. First booking bonus — đếm SAU update (cùng conn thấy write chưa commit)
        row = conn.execute(
            "SELECT COUNT(*) FROM bookings WHERE customer_id = ? AND status = 'done'",
            (customer_id,)
        ).fetchone()
        if row[0] == 1:
            first_bonus = get_config_value("first_booking_bonus")
            if first_bonus and not already_awarded(customer_id, "first_booking", booking_id):
                award_points(customer_id, first_bonus, "first_booking", booking_id,
                             "First booking bonus", conn=conn)

        # 4. Streak bonus — truyền conn để check thấy UPDATE chưa commit
        if check_streak(customer_id, booking_date, conn=conn):
            streak_bonus = get_config_value("streak_bonus")
            if streak_bonus and not already_awarded(customer_id, "streak", streak_ref):
                award_points(customer_id, streak_bonus, "streak", streak_ref,
                             "3-month streak bonus", conn=conn)

        conn.commit()
        return True
    except Exception:
        conn.rollback()
        return False
    finally:
        conn.close()


def revert_booking_txn(booking_id):
    """Đối xứng với complete_booking_txn: thu hồi side-effect khi 1 booking RỜI
    trạng thái 'done' — xoá invoice, hoàn (xoá) điểm loyalty gắn trực tiếp với
    booking này (base/double/first_booking, reference_id = booking_id), và reset
    staff earnings về 0. KHÔNG tự đổi status (caller đặt status mới, và chính lệnh
    đó mới bump updated_at).

    Giới hạn có chủ đích: điểm 'streak' (theo THÁNG, reference_id = YYYYMM, không
    gắn booking_id) KHÔNG tự thu hồi — vì streak có thể vẫn đúng nhờ booking khác
    trong tháng; thu hồi mù sẽ sai. Nếu cần chỉnh, dùng dev_tools points subtract.
    Trả True nếu OK."""
    conn = get_connection()
    try:
        conn.execute(
            """UPDATE bookings
               SET staff_hourly_earning = 0, staff_commission = 0, staff_total_earning = 0
               WHERE id = ?""", (booking_id,)
        )
        conn.execute("DELETE FROM invoices WHERE booking_id = ?", (booking_id,))
        conn.execute(
            """DELETE FROM loyalty_points_log
               WHERE reference_id = ? AND source IN ('booking', 'double_points', 'first_booking')""",
            (booking_id,)
        )
        conn.commit()
        return True
    except Exception:
        conn.rollback()
        return False
    finally:
        conn.close()

