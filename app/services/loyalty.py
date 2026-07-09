from app.database.db import get_connection, get_customer_current_tier
from app.utils.helpers import now_helsinki
from datetime import datetime


def get_active_multiplier(customer_id: int) -> float:
    # Hệ số điểm theo TIER HIỆN TẠI (gói đang gia hạn), thống nhất với hiển thị.
    tier = get_customer_current_tier(customer_id)
    return float(tier["point_multiplier"]) if tier else 1.0


def get_config_value(key: str) -> int:
    conn = get_connection()
    row = conn.execute(
        "SELECT value FROM loyalty_config WHERE key = ?", (key,)
    ).fetchone()
    conn.close()
    return int(row["value"]) if row else 0


def already_awarded(customer_id: int, source: str, reference_id: int) -> bool:
    conn = get_connection()
    row = conn.execute("""
        SELECT 1 FROM loyalty_points_log
        WHERE customer_id = ? AND source = ? AND reference_id = ?
    """, (customer_id, source, reference_id)).fetchone()
    conn.close()
    return row is not None


def award_points(customer_id: int, points: int, source: str,
                 reference_id=None, note=None, conn=None):
    """
    Insert một row vào loyalty_points_log.
    Nếu conn được truyền vào thì dùng chung transaction (không commit/close).
    Nếu không thì tự mở conn, commit, close.
    """
    own_conn = conn is None
    if own_conn:
        conn = get_connection()
    conn.execute("""
        INSERT INTO loyalty_points_log (customer_id, points, source, reference_id, note)
        VALUES (?, ?, ?, ?, ?)
    """, (customer_id, points, source, reference_id, note))
    if own_conn:
        conn.commit()
        conn.close()


def check_streak(customer_id: int, booking_date, conn=None) -> bool:
    """
    Trả về True nếu customer có ít nhất 1 completed booking
    trong mỗi tháng của 3 tháng liên tiếp tính đến tháng booking_date.

    Nhận conn tuỳ chọn để đọc các uncommitted write từ cùng transaction.
    """
    if isinstance(booking_date, str):
        booking_date = datetime.strptime(booking_date, "%Y-%m-%d").date()

    year, month = booking_date.year, booking_date.month

    months_to_check = []
    for offset in range(2, -1, -1):
        m = month - offset
        y = year
        while m <= 0:
            m += 12
            y -= 1
        months_to_check.append((y, m))

    own_conn = conn is None
    if own_conn:
        conn = get_connection()

    for y, m in months_to_check:
        row = conn.execute("""
            SELECT 1 FROM bookings
            WHERE customer_id = ?
              AND status = 'done'
              AND strftime('%Y', booking_date) = ?
              AND strftime('%m', booking_date) = ?
            LIMIT 1
        """, (customer_id, str(y), f"{m:02d}")).fetchone()
        if not row:
            if own_conn:
                conn.close()
            return False

    if own_conn:
        conn.close()
    return True
