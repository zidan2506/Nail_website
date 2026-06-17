import sqlite3
import secrets
import string
from pathlib import Path
from werkzeug.security import generate_password_hash

base_dir = Path(__file__).resolve().parent
db_path = base_dir / "database.db"
def get_connection():
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def get_all_services():
    conn = get_connection()
    services = conn.execute("SELECT * FROM services").fetchall()
    conn.close()
    return services

def get_all_staff():
    conn = get_connection()
    staff = conn.execute("SELECT * FROM staff").fetchall()
    conn.close()
    return staff

def get_service_by_id(service_id):
    conn = get_connection()
    service = conn.execute("SELECT * FROM services WHERE id = ?", (service_id,)).fetchone()
    conn.close()
    return service

def get_staff_by_id(staff_id):
    conn = get_connection()
    staff = conn.execute("SELECT * FROM staff where id = ?", (staff_id,)).fetchone()
    conn.close()
    return staff

def get_customer_id(email):
    conn = get_connection()
    customer = conn.execute("SELECT id FROM customers WHERE email = ?", (email,)).fetchone()
    conn.close()
    return customer

def check_booking_conflict(staff_id, booking_date, start_at, end_at):
    conn = get_connection()
    conflict = conn.execute("""
    SELECT * FROM bookings
    WHERE staff_id = ?
        AND booking_date = ?
        AND start_time < ?
        AND end_time > ?
        AND status IN ('pending', 'confirmed')

""", (staff_id, booking_date, end_at, start_at)).fetchone()
    conn.close()
    return conflict is not None

def create_booking(customer_id, staff_id, service_id, booking_date, start_time, end_time, status, notes):
    conn = get_connection()
    cur = conn.execute("""
    INSERT INTO bookings (
        customer_id,
        staff_id,
        service_id,
        booking_date,
        start_time,
        end_time,
        status,
        notes

    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (customer_id, staff_id, service_id, booking_date, start_time, end_time, status, notes))
    booking_id = cur.lastrowid
    conn.commit()
    conn.close()
    print(f"Create new booking done! Status: {status} ")
    return booking_id

def create_customer(full_name,email,phone):
    conn = get_connection()
    curr = conn.execute(
    """
    INSERT INTO customers (full_name,email,phone)
    VALUES (?, ?, ?)
    """, (full_name,email,phone))
    conn.commit()
    customer_id = curr.lastrowid
    conn.close()
    print("Create new customer done! ")
    return customer_id


def update_status(id, status):
    conn = get_connection()
    conn.execute(
        """
    UPDATE bookings
    SET
        status = ?
    WHERE id = ?
""", (status, id)
    )
    conn.commit()
    conn.close()
    return print(f"Updating status: {status} success!")

def cancel_booking_with_reason(booking_id, reason):
    conn = get_connection()
    conn.execute(
        "UPDATE bookings SET status = 'cancelled', cancellation_reason = ? WHERE id = ?",
        (reason or None, booking_id)
    )
    conn.commit()
    conn.close()

def verify_customer(customer_id):
    conn = get_connection()
    conn.execute(
        """
    UPDATE customers
    SET is_verified = 1
    WHERE id = ?
        AND is_verified = 0;
""", (customer_id,)
    )
    conn.commit()
    conn.close()
    
    print(f"Verify customer with id = {id} successfully!")
    return True

def update_new_code(id, code, expires_at):
    conn = get_connection()
    conn.execute(
        """
    UPDATE email_verifications
    SET 
        verification_code = ?,
        expired_at = ?,
        last_sent_at = CURRENT_TIMESTAMP
    WHERE id = ?
        AND is_used = 0;
""", (code, expires_at, id)
    )
    conn.commit()
    conn.close()

    print(f"Udating new code success!\nNew code: {code}\nExpires at: {expires_at}")
    return True

def get_booking_by_id(id):
    conn = get_connection()
    booking = conn.execute(
        """
    SELECT *
    FROM bookings
    WHERE id = ?
""", (id,)
    ).fetchone()
    conn.close()
    return booking

def delete_expired_verifications():
    conn = get_connection()
    conn.execute(
        """
    DELETE FROM email_verifications
    WHERE expired_at > CURRENT TIMESTAMP
    """
    )
    conn.commit()
    conn.close()

    print("Deleted expired booking!")
    return True

def get_booking_by_staff_and_date(staff_id, booking_date):
    conn = get_connection()
    rows = conn.execute(
        """
    SELECT *
    FROM bookings
    WHERE staff_id = ?
        AND booking_date = ?
        AND status IN ("pending", "confirmed")
""", (staff_id, booking_date)
    ).fetchall()
    conn.close()
    return rows

def expire_unverified_booknigs():
    conn = get_connection()
    conn.execute(
        """
    
    UPDATE bookings
    SET status = 'expired'
    WHERE status ='unverified'
        AND verification_expires_at < CURRENT_TIMESTAMP
"""
    )
    conn.commit()
    conn.close()
    
    print("Updated unverified_bookings status = expired!")
    return True

def get_user_by_email(email):
    conn = get_connection()
    user = conn.execute(
        """
    SELECT *
    FROM users
    WHERE email = ?
""", (email,)
    ).fetchone()
    conn.close()

    return user

def get_customer_by_email(email):
    conn = get_connection()
    customer = conn.execute(
        """
    SELECT *
    FROM customers
    WHERE email = ?
""", (email, )
    ).fetchone()
    conn.close()

    return customer

def create_user(email, password, role="customer"):
    conn = get_connection()
    password_hash = generate_password_hash(password)
    user = conn.execute(
        """
    INSERT INTO users (
        password_hash,
        email,
        role
    )
    VALUES (?, ?, ?)
""", (password_hash, email, role)
    )
    conn.commit()
    user_id =  user.lastrowid
    conn.close()
    print(f"Create new user successfully! User id: {user_id}")
    return user_id

def link_customer_to_user(customer_id, user_id):
    conn = get_connection()
    conn.execute(
        """
    UPDATE customers
    SET user_id = ?
    WHERE id = ?
""", (user_id, customer_id)
    )
    conn.commit()
    conn.close()
    print(f"Link customer with id={customer_id} to user with id={user_id} successfully!")
    return True

def create_verification(verification_code, verification_type, expired_at):
    conn = get_connection()
    curr = conn.execute(
        """
    INSERT INTO email_verifications (
    verification_code,
    verification_type,
    expired_at
    ) VALUES (?, ?, ?)
""", (verification_code, verification_type, expired_at)
    )
    conn.commit()
    verification_id = curr.lastrowid
    conn.close()

    print(f"Create verification id={verification_id} successfully!")    
    return verification_id

def get_verification_by_id(verification_id):
    conn = get_connection()
    verification = conn.execute(
        """
    SELECT *
    FROM email_verifications
    WHERE id = ?
    AND is_used = 0
    AND expired_at > CURRENT_TIMESTAMP
""", (verification_id, )
    ).fetchone()
    conn.close()

    print(f"Get verification with id= {verification_id} successfully!")
    return verification

def update_verification(verification_id,reference_id, is_used):
    conn = get_connection()
    curr = conn.execute(
        """
    UPDATE email_verifications
    SET
        reference_id = ?,
        verified_at = CURRENT_TIMESTAMP,
        is_used = ?
    WHERE id = ?
""", (reference_id, is_used, verification_id)
    )
    conn.commit()
    conn.close()
    print(f"Update verification with id={verification_id} successfully")
    return True

def get_customer_by_user_id(user_id):
    conn = get_connection()
    customer = conn.execute(
        """
    SELECT * 
    FROM customers
    WHERE user_id = ?
""", (user_id, )
    ).fetchone()
    conn.close()
    print(f"Get customer by user_id = {user_id} successfully")
    return customer

def get_staff_by_user_id(user_id):
    conn = get_connection()
    staff = conn.execute(
        """
    SELECT *
    FROM staff
    WHERE user_id = ?
""", (user_id, )
    ).fetchone()
    conn.close()
    print(f"Get staff by user_id = {user_id}  successfully")
    return staff

def get_customer_bookings(customer_id):
    conn = get_connection()
    bookings = conn.execute(
        """
    SELECT
        b.*,
        s.name AS service_name,
        s.duration_minutes AS service_duration,
        s.price AS service_price,
        s.description AS service_description,
        s.image AS service_image,

        st.full_name AS staff_name,
        st.email AS staff_email,

        c.full_name AS customer_name,
        c.email AS customer_email,
        c.phone AS customer_phone


    FROM bookings b
    JOIN services s ON b.service_id = s.id
    JOIN staff st ON b.staff_id = st.id
    JOIN customers c ON b.customer_id = c.id

    WHERE b.customer_id = ?
    ORDER BY b.booking_date ASC, b.start_time ASC
""", (customer_id, )
    ).fetchall()
    conn.close()
    return bookings

def get_customer_by_customer_id(customer_id):
    conn = get_connection()
    customer = conn.execute(
        """
    SELECT *
    FROM customers
    WHERE id = ?
""", (customer_id, )
    ).fetchone()
    conn.close()
    return customer

def update_booking_schedule(booking_id, booking_date, start_time, end_time):
    conn = get_connection()
    conn.execute(
        """
    UPDATE bookings
    SET booking_date = ?,
        start_time = ?,
        end_time = ?
    WHERE id = ?
""", (booking_date, start_time, end_time, booking_id)
    )
    conn.commit()
    conn.close()

def get_active_service_categories():
    conn = get_connection()
    categories = conn.execute(
        """
        SELECT *
        FROM service_categories
        WHERE is_active = 1
        ORDER BY sort_order ASC, name ASC
        """
    ).fetchall()
    conn.close()
    return categories

def get_active_services_with_category():
    conn = get_connection()
    services = conn.execute(
        """
        SELECT
            s.*,
            c.id AS category_id,
            c.name AS category_name,
            c.slug AS category_slug
        FROM services s
        JOIN service_categories c ON s.category_id = c.id
        WHERE s.is_active = 1
            AND c.is_active = 1
        ORDER BY c.sort_order ASC, s.name ASC
        """
    ).fetchall()
    conn.close()
    return services

def get_available_staff_for_slot(booking_date, start_time, end_time):
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT s.*
        FROM staff s
        WHERE s.is_active = 1
          AND NOT EXISTS (
              SELECT 1 FROM bookings b
              WHERE b.staff_id = s.id
                AND b.booking_date = ?
                AND b.start_time < ?
                AND b.end_time > ?
                AND b.status IN ('pending', 'confirmed', 'unverified')
          )
        """,
        (booking_date, end_time, start_time)
    ).fetchall()
    conn.close()
    return rows

def get_customer_appointment_history(customer_id):
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT
            b.id              AS booking_id,
            b.booking_date,
            b.start_time,
            b.end_time,
            b.status,
            b.notes,
            s.id              AS service_id,
            s.name            AS service_name,
            s.price           AS service_price,
            st.id             AS staff_id,
            st.full_name      AS stylist_name,
            r.id              AS review_id,
            r.rating          AS review_rating
        FROM bookings b
        JOIN services s     ON b.service_id = s.id
        JOIN staff st       ON b.staff_id = st.id
        LEFT JOIN reviews r ON b.id = r.booking_id
        WHERE b.customer_id = ?
          AND b.status IN ('completed', 'cancelled')
        ORDER BY b.booking_date DESC, b.start_time DESC
    """, (customer_id,))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]

def get_customer_invoices(customer_id):
    """
    Lấy tất cả invoices của 1 customer, kèm thông tin booking + service.
    
    Returns: list of dict, sắp xếp mới nhất trước
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT
            i.id              AS invoice_id,
            i.invoice_number,
            i.amount,
            i.payment_method,
            i.status          AS invoice_status,
            i.issued_at,
            b.id              AS booking_id,
            b.booking_date,
            b.start_time,
            s.name            AS service_name,
            st.full_name      AS stylist_name
        FROM invoices i
        JOIN bookings b   ON i.booking_id = b.id
        JOIN services s   ON b.service_id = s.id
        JOIN staff st     ON b.staff_id = st.id
        WHERE b.customer_id = ?
        ORDER BY i.issued_at DESC
    """, (customer_id,))
    
    rows = cursor.fetchall()
    conn.close()
    #convert sang dict cho dễ xử lý 
    return [dict(row) for row in rows]

def has_pending_review(customer_id):
    conn = get_connection()
    row = conn.execute("""
        SELECT COUNT(*) FROM bookings
        WHERE customer_id = ? AND status = 'completed'
        AND id NOT IN (SELECT booking_id FROM reviews)
    """, (customer_id,)).fetchone()
    conn.close()
    return row[0] > 0

def has_source_award(customer_id, source):
    conn = get_connection()
    row = conn.execute(
        "SELECT 1 FROM loyalty_points_log WHERE customer_id = ? AND source = ?",
        (customer_id, source)
    ).fetchone()
    conn.close()
    return row is not None

def get_tier_by_name(name):
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM membership_tiers WHERE name = ? AND is_active = 1",
        (name,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None

def upgrade_membership(customer_id, tier_id, duration_days):
    from datetime import datetime, timedelta
    conn = get_connection()
    try:
        now = datetime.now()
        started_at = now.strftime("%Y-%m-%d %H:%M:%S")
        expires_at = (now + timedelta(days=duration_days)).strftime("%Y-%m-%d %H:%M:%S")
        existing = conn.execute(
            "SELECT id FROM customer_memberships WHERE customer_id = ?",
            (customer_id,)
        ).fetchone()
        if existing:
            conn.execute(
                "UPDATE customer_memberships SET tier_id = ?, started_at = ?, expires_at = ?, is_active = 1 WHERE customer_id = ?",
                (tier_id, started_at, expires_at, customer_id)
            )
        else:
            conn.execute(
                "INSERT INTO customer_memberships (customer_id, tier_id, started_at, expires_at, is_active) VALUES (?, ?, ?, ?, 1)",
                (customer_id, tier_id, started_at, expires_at)
            )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

# Thêm vào app/database/db.py

def get_customer_active_tier(customer_id):
    conn = get_connection()
    row = conn.execute("""
        SELECT mt.name, mt.point_multiplier, cm.expires_at
        FROM customer_memberships cm
        JOIN membership_tiers mt ON cm.tier_id = mt.id
        WHERE cm.customer_id = ?
          AND cm.is_active = 1
          AND cm.expires_at > datetime('now')
        ORDER BY mt.point_multiplier DESC
        LIMIT 1
    """, (customer_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_loyalty_balance(customer_id):
    conn = get_connection()
    balance = conn.execute(
        "SELECT COALESCE(SUM(points), 0) FROM loyalty_points_log WHERE customer_id = ?",
        (customer_id,)
    ).fetchone()[0]
    conn.close()
    return int(balance)


def get_active_rewards():
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM rewards WHERE is_active = 1 ORDER BY cost ASC"
    ).fetchall()
    conn.close()
    return rows

def get_customer_vouchers(customer_id):
    conn = get_connection()
    rows = conn.execute("""
        SELECT rr.id, rr.voucher_code, rr.points_spent, rr.redeemed_at,
               r.name, r.description
        FROM reward_redemptions rr
        JOIN rewards r ON rr.reward_id = r.id
        WHERE rr.customer_id = ?
        ORDER BY rr.redeemed_at DESC
    """, (customer_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_customer_reward_status(customer_id, reward_id):
    conn = get_connection()
    row = conn.execute("""
        SELECT COUNT(*) as redeem_count, MAX(redeemed_at) as last_redeemed_at
        FROM reward_redemptions
        WHERE customer_id = ? AND reward_id = ?
    """, (customer_id, reward_id)).fetchone()
    conn.close()
    return dict(row) if row else {"redeem_count": 0, "last_redeemed_at": None}

def _generate_voucher_code():
    alphabet = string.ascii_uppercase + string.digits
    while True:
        code = "DAHA-" + "".join(secrets.choice(alphabet) for _ in range(4)) + "-" + "".join(secrets.choice(alphabet) for _ in range(4))
        conn = get_connection()
        exists = conn.execute("SELECT 1 FROM reward_redemptions WHERE voucher_code = ?", (code,)).fetchone()
        conn.close()
        if not exists:
            return code

def redeem_reward(customer_id, reward_id, cost, reward_name=""):
    voucher_code = _generate_voucher_code()
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO reward_redemptions (customer_id, reward_id, points_spent, voucher_code) VALUES (?, ?, ?, ?)",
            (customer_id, reward_id, cost, voucher_code)
        )
        conn.execute(
            "UPDATE rewards SET stock = stock - 1 WHERE id = ? AND stock IS NOT NULL",
            (reward_id,)
        )
        conn.execute(
            "INSERT INTO loyalty_points_log (customer_id, points, source, reference_id, note) VALUES (?, ?, ?, ?, ?)",
            (customer_id, -cost, "reward_redemption", reward_id, f"Redeemed: {reward_name}" if reward_name else "Reward redemption")
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_loyalty_history(customer_id, limit=20):
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT points, note, created_at, source
        FROM loyalty_points_log
        WHERE customer_id = ?
        ORDER BY created_at DESC
        LIMIT ?
        """,
        (customer_id, limit)
    ).fetchall()
    conn.close()
    return rows


def get_invoice_detail_by_id(invoice_id):
    """Lấy full invoice detail bằng cách join invoices -> bookings -> customers, staff, services"""
    db = get_connection()
    row = db.execute("""
        SELECT
            i.id,
            i.invoice_number,
            i.amount,
            i.payment_method,
            i.status,
            i.issued_at,

            b.booking_date,
            b.start_time,
            b.end_time,

            c.id        AS customer_id,
            c.full_name AS customer_name,
            c.email     AS customer_email,
            c.phone     AS customer_phone,

            st.full_name AS staff_name,

            sv.name             AS service_name,
            sv.duration_minutes AS service_duration,
            sv.price            AS service_price,

            sc.name AS category_name

        FROM invoices i
        JOIN bookings b  ON b.id  = i.booking_id
        JOIN customers c ON c.id  = b.customer_id
        JOIN staff st    ON st.id = b.staff_id
        JOIN services sv ON sv.id = b.service_id
        JOIN service_categories sc ON sc.id = sv.category_id
        WHERE i.id = ?
    """, (invoice_id,)).fetchone()

    return dict(row) if row else None


def update_customer_profile(customer_id, full_name, email, phone, date_of_birth):
    conn = get_connection()
    conn.execute(
        "UPDATE customers SET full_name=?, email=?, phone=?, date_of_birth=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
        (full_name, email, phone, date_of_birth, customer_id)
    )
    conn.commit()
    conn.close()


def update_user_email(user_id, email):
    conn = get_connection()
    conn.execute("UPDATE users SET email=? WHERE id=?", (email, user_id))
    conn.commit()
    conn.close()


def update_user_password(user_id, password_hash):
    conn = get_connection()
    conn.execute("UPDATE users SET password_hash=? WHERE id=?", (password_hash, user_id))
    conn.commit()
    conn.close()
