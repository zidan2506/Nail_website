import logging
import sqlite3
import secrets
import string
from pathlib import Path
from werkzeug.security import generate_password_hash
from app.utils.helpers import now_helsinki

logger = logging.getLogger(__name__)

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

def get_active_staff():
    conn = get_connection()
    staff = conn.execute(
        "SELECT * FROM staff WHERE is_active = 1 ORDER BY id ASC"
    ).fetchall()
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
        AND status IN ('pending', 'confirmed', 'in-progress')

""", (staff_id, booking_date, end_at, start_at)).fetchone()
    conn.close()
    return conflict is not None

def create_booking(customer_id, staff_id, service_id, booking_date, start_time, end_time, status, notes, payment_method):
    conn = get_connection()
    updated_at = now_helsinki().strftime("%Y-%m-%d %H:%M:%S")
    cur = conn.execute("""
    INSERT INTO bookings (
        customer_id,
        staff_id,
        service_id,
        booking_date,
        start_time,
        end_time,
        status,
        notes,
        payment_method,
        updated_at

    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (customer_id, staff_id, service_id, booking_date, start_time, end_time, status, notes, payment_method, updated_at))
    booking_id = cur.lastrowid
    conn.commit()
    conn.close()
    logger.debug("Create new booking done! Status: %s", status)
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
    logger.debug("Create new customer done!")
    return customer_id


def update_status(id, status):
    conn = get_connection()
    updated_at = now_helsinki().strftime("%Y-%m-%d %H:%M:%S")
    conn.execute(
        """
    UPDATE bookings
    SET
        status = ?,
        updated_at = ?
    WHERE id = ?
""", (status, updated_at, id)
    )
    conn.commit()
    conn.close()
    logger.debug("Updating status: %s success!", status)

def cancel_booking_with_reason(booking_id, reason):
    conn = get_connection()
    updated_at = now_helsinki().strftime("%Y-%m-%d %H:%M:%S")
    conn.execute(
        "UPDATE bookings SET status = 'cancelled', cancellation_reason = ?, updated_at = ? WHERE id = ?",
        (reason or None, updated_at, booking_id)
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
    
    logger.debug("Verify customer with id = %s successfully!", id)
    return True

def update_new_code(id, code, expires_at):
    conn = get_connection()
    last_sent_at = now_helsinki().strftime("%Y-%m-%d %H:%M:%S")
    conn.execute(
        """
    UPDATE email_verifications
    SET
        verification_code = ?,
        expired_at = ?,
        last_sent_at = ?
    WHERE id = ?
        AND is_used = 0;
""", (code, expires_at, last_sent_at, id)
    )
    conn.commit()
    conn.close()

    logger.debug("Udating new code success! New code: %s Expires at: %s", code, expires_at)
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

    logger.debug("Deleted expired booking!")
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
    
    logger.debug("Updated unverified_bookings status = expired!")
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
    logger.debug("Create new user successfully! User id: %s", user_id)
    return user_id

def create_oauth_user(email, oauth_provider, oauth_sub, role="customer"):
    """Tạo user đăng nhập bằng OAuth (Google...). User loại này không có mật khẩu
    thật — lưu 1 hash ngẫu nhiên vô dụng để thỏa ràng buộc NOT NULL của cột
    password_hash và để không ai đăng nhập được bằng mật khẩu."""
    conn = get_connection()
    random_password = secrets.token_urlsafe(32)
    password_hash = generate_password_hash(random_password)
    user = conn.execute(
        """
    INSERT INTO users (password_hash, email, role, oauth_provider, oauth_sub)
    VALUES (?, ?, ?, ?, ?)
""", (password_hash, email, role, oauth_provider, oauth_sub)
    )
    conn.commit()
    user_id = user.lastrowid
    conn.close()
    logger.debug("Create OAuth user successfully! User id: %s", user_id)
    return user_id

def set_user_oauth(user_id, oauth_provider, oauth_sub):
    """Gắn thông tin OAuth vào 1 user đã tồn tại (link tài khoản email/password
    cũ với đăng nhập Google khi email trùng)."""
    conn = get_connection()
    conn.execute(
        "UPDATE users SET oauth_provider = ?, oauth_sub = ? WHERE id = ?",
        (oauth_provider, oauth_sub, user_id)
    )
    conn.commit()
    conn.close()
    logger.debug("Set OAuth for user id=%s successfully!", user_id)
    return True

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
    logger.debug("Link customer with id=%s to user with id=%s successfully!", customer_id, user_id)
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

    logger.debug("Create verification id=%s successfully!", verification_id)    
    return verification_id

def get_verification_by_id(verification_id):
    conn = get_connection()
    now_str = now_helsinki().strftime("%Y-%m-%d %H:%M:%S")
    verification = conn.execute(
        """
    SELECT *
    FROM email_verifications
    WHERE id = ?
    AND is_used = 0
    AND expired_at > ?
""", (verification_id, now_str)
    ).fetchone()
    conn.close()

    logger.debug("Get verification with id= %s successfully!", verification_id)
    return verification

def update_verification(verification_id,reference_id, is_used):
    conn = get_connection()
    verified_at = now_helsinki().strftime("%Y-%m-%d %H:%M:%S")
    curr = conn.execute(
        """
    UPDATE email_verifications
    SET
        reference_id = ?,
        verified_at = ?,
        is_used = ?
    WHERE id = ?
""", (reference_id, verified_at, is_used, verification_id)
    )
    conn.commit()
    conn.close()
    logger.debug("Update verification with id=%s successfully", verification_id)
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
    logger.debug("Get customer by user_id = %s successfully", user_id)
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
    logger.debug("Get staff by user_id = %s  successfully", user_id)
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
    updated_at = now_helsinki().strftime("%Y-%m-%d %H:%M:%S")
    conn.execute(
        """
    UPDATE bookings
    SET booking_date = ?,
        start_time = ?,
        end_time = ?,
        updated_at = ?
    WHERE id = ?
""", (booking_date, start_time, end_time, updated_at, booking_id)
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
            c.name_fi AS category_name_fi,
            c.name_vi AS category_name_vi,
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


def get_all_categories():
    conn = get_connection()
    categories = conn.execute(
        "SELECT * FROM service_categories ORDER BY sort_order ASC, name ASC"
    ).fetchall()
    conn.close()
    return categories


def get_service_categories_with_services(q='', category_id=None, active=None):
    conn = get_connection()

    cat_where = "WHERE 1=1"
    cat_params = []
    if category_id:
        cat_where += " AND id = ?"
        cat_params.append(category_id)

    categories = conn.execute(
        f"SELECT * FROM service_categories {cat_where} ORDER BY sort_order ASC, name ASC",
        cat_params
    ).fetchall()

    result = []
    for cat in categories:
        c = dict(cat)

        svc_where = "WHERE category_id = ?"
        svc_params = [c["id"]]
        if q:
            svc_where += " AND name LIKE ?"
            svc_params.append(f"%{q}%")
        if active is not None:
            svc_where += " AND is_active = ?"
            svc_params.append(active)

        # services has no sort_order column (unlike service_categories), so order by name
        services = conn.execute(
            f"SELECT * FROM services {svc_where} ORDER BY name ASC",
            svc_params
        ).fetchall()
        c["services"] = [dict(s) for s in services]
        result.append(c)

    conn.close()
    return result


def get_service_stats():
    conn = get_connection()
    total_categories = conn.execute("SELECT COUNT(*) FROM service_categories").fetchone()[0]
    total_services = conn.execute("SELECT COUNT(*) FROM services").fetchone()[0]
    active_services = conn.execute("SELECT COUNT(*) FROM services WHERE is_active = 1").fetchone()[0]
    avg_price = conn.execute("SELECT COALESCE(AVG(price), 0) FROM services").fetchone()[0]
    conn.close()
    return {
        "total_categories": total_categories,
        "total_services": total_services,
        "active_services": active_services,
        "avg_price": avg_price,
    }


def create_service(category_id, name, description, duration_minutes, price, points, is_active, image, badge, icon,
                   name_fi=None, name_vi=None, description_fi=None, description_vi=None):
    conn = get_connection()
    cur = conn.execute("""
        INSERT INTO services (category_id, name, description, duration_minutes, price, points, is_active, image, badge, icon,
                              name_fi, name_vi, description_fi, description_vi)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (category_id, name, description, duration_minutes, price, points, is_active, image, badge, icon,
          name_fi, name_vi, description_fi, description_vi))
    conn.commit()
    service_id = cur.lastrowid
    conn.close()
    return service_id


def update_service(service_id, category_id, name, description, duration_minutes, price, points, is_active, image, badge, icon,
                   name_fi=None, name_vi=None, description_fi=None, description_vi=None):
    conn = get_connection()
    conn.execute("""
        UPDATE services
        SET category_id=?, name=?, description=?, duration_minutes=?, price=?, points=?,
            is_active=?, image=?, badge=?, icon=?,
            name_fi=?, name_vi=?, description_fi=?, description_vi=?, updated_at=CURRENT_TIMESTAMP
        WHERE id=?
    """, (category_id, name, description, duration_minutes, price, points, is_active, image, badge, icon,
          name_fi, name_vi, description_fi, description_vi, service_id))
    conn.commit()
    conn.close()


def delete_service(service_id):
    conn = get_connection()
    conn.execute("DELETE FROM services WHERE id = ?", (service_id,))
    conn.commit()
    conn.close()


def toggle_service_active(service_id):
    conn = get_connection()
    conn.execute("UPDATE services SET is_active = 1 - is_active WHERE id = ?", (service_id,))
    conn.commit()
    conn.close()


def create_category(name, slug, is_active, name_fi=None, name_vi=None):
    conn = get_connection()
    max_sort = conn.execute("SELECT COALESCE(MAX(sort_order), -1) FROM service_categories").fetchone()[0]
    cur = conn.execute("""
        INSERT INTO service_categories (name, slug, is_active, sort_order, name_fi, name_vi)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (name, slug, is_active, max_sort + 1, name_fi, name_vi))
    conn.commit()
    category_id = cur.lastrowid
    conn.close()
    return category_id


def update_category(category_id, name, slug, is_active, name_fi=None, name_vi=None):
    conn = get_connection()
    conn.execute("""
        UPDATE service_categories
        SET name=?, slug=?, is_active=?, name_fi=?, name_vi=?, updated_at=CURRENT_TIMESTAMP
        WHERE id=?
    """, (name, slug, is_active, name_fi, name_vi, category_id))
    conn.commit()
    conn.close()


def delete_category(category_id):
    conn = get_connection()
    conn.execute("DELETE FROM service_categories WHERE id = ?", (category_id,))
    conn.commit()
    conn.close()


def get_gallery_images():
    conn = get_connection()
    images = conn.execute(
        "SELECT * FROM gallery_images WHERE is_active = 1 ORDER BY sort_order ASC, id ASC"
    ).fetchall()
    conn.close()
    return images


def get_gallery_images_admin():
    conn = get_connection()
    images = conn.execute(
        "SELECT * FROM gallery_images ORDER BY sort_order ASC, id ASC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in images]


def get_gallery_image_by_id(image_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM gallery_images WHERE id = ?", (image_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_gallery_stats():
    conn = get_connection()
    total = conn.execute("SELECT COUNT(*) FROM gallery_images").fetchone()[0]
    active = conn.execute("SELECT COUNT(*) FROM gallery_images WHERE is_active = 1").fetchone()[0]
    conn.close()
    return {"total": total, "active": active, "hidden": total - active}


def create_gallery_images(rows):
    """rows: list of (image_url, alt_text, sort_order) tuples."""
    conn = get_connection()
    conn.executemany(
        "INSERT INTO gallery_images (image_url, alt_text, sort_order, is_active) VALUES (?, ?, ?, 1)",
        rows
    )
    conn.commit()
    conn.close()


def update_gallery_image(image_id, alt_text, sort_order, is_active, image_url=None,
                         alt_text_fi=None, alt_text_vi=None):
    conn = get_connection()
    if image_url is not None:
        conn.execute(
            "UPDATE gallery_images SET alt_text=?, alt_text_fi=?, alt_text_vi=?, sort_order=?, is_active=?, image_url=? WHERE id=?",
            (alt_text, alt_text_fi, alt_text_vi, sort_order, is_active, image_url, image_id)
        )
    else:
        conn.execute(
            "UPDATE gallery_images SET alt_text=?, alt_text_fi=?, alt_text_vi=?, sort_order=?, is_active=? WHERE id=?",
            (alt_text, alt_text_fi, alt_text_vi, sort_order, is_active, image_id)
        )
    conn.commit()
    conn.close()


def delete_gallery_image(image_id):
    conn = get_connection()
    conn.execute("DELETE FROM gallery_images WHERE id = ?", (image_id,))
    conn.commit()
    conn.close()


def bulk_delete_gallery_images(image_ids):
    conn = get_connection()
    conn.executemany("DELETE FROM gallery_images WHERE id = ?", [(i,) for i in image_ids])
    conn.commit()
    conn.close()


def reorder_gallery_images(order):
    """order: list of (sort_order, id) tuples."""
    conn = get_connection()
    conn.executemany("UPDATE gallery_images SET sort_order = ? WHERE id = ?", order)
    conn.commit()
    conn.close()

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
                AND b.status IN ('pending', 'confirmed')
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
          AND b.status IN ('done', 'cancelled')
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
        WHERE customer_id = ? AND status = 'done'
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
    from datetime import timedelta
    conn = get_connection()
    try:
        now = now_helsinki()
        started_at = now.strftime("%Y-%m-%d %H:%M:%S")
        expires_at = (now + timedelta(days=duration_days)).strftime("%Y-%m-%d %H:%M:%S")
        # Cấp tay/free -> chỉ đụng row thủ công (stripe_subscription_id IS NULL),
        # tuyệt đối không clobber row subscription của Stripe.
        existing = conn.execute(
            "SELECT id FROM customer_memberships WHERE customer_id = ? AND stripe_subscription_id IS NULL",
            (customer_id,)
        ).fetchone()
        if existing:
            conn.execute(
                "UPDATE customer_memberships SET tier_id = ?, started_at = ?, expires_at = ?, is_active = 1 WHERE id = ?",
                (tier_id, started_at, expires_at, existing["id"])
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
    redeemed_at = now_helsinki().strftime("%Y-%m-%d %H:%M:%S")
    try:
        conn.execute(
            "INSERT INTO reward_redemptions (customer_id, reward_id, points_spent, voucher_code, redeemed_at) VALUES (?, ?, ?, ?, ?)",
            (customer_id, reward_id, cost, voucher_code, redeemed_at)
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


def get_staff_bookings_range(staff_id, date_from=None, date_to=None):
    """Bookings của 1 staff cho trang 'Lịch của tôi'. LEFT JOIN invoices để lấy
    trạng thái thanh toán (bookings không có cột payment_method/is_paid — model thật
    nằm ở bảng invoices). date_from/date_to = None → không lọc ngày (preset 'all')."""
    conn = get_connection()
    sql = """
        SELECT b.id, b.booking_date, b.start_time, b.end_time, b.status,
               c.full_name AS customer_name, c.phone AS customer_phone,
               sv.name AS service_name, sv.price AS total_price,
               iv.payment_method AS invoice_method, iv.status AS invoice_status
        FROM bookings b
        JOIN customers c ON c.id = b.customer_id
        JOIN services sv ON sv.id = b.service_id
        LEFT JOIN invoices iv ON iv.booking_id = b.id
        WHERE b.staff_id = ?
          AND b.status != 'unverified'
    """
    params = [staff_id]
    if date_from and date_to:
        sql += " AND b.booking_date BETWEEN ? AND ?"
        params.extend([date_from, date_to])
    sql += " ORDER BY b.booking_date ASC, b.start_time ASC"
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_staff_history_months(staff_id):
    """Danh sách 'YYYY-MM' có booking done/cancelled của staff, mới nhất trước."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT DISTINCT strftime('%Y-%m', booking_date) AS ym
        FROM bookings
        WHERE staff_id = ? AND status IN ('done', 'cancelled')
        ORDER BY ym DESC
    """, (staff_id,)).fetchall()
    conn.close()
    return [r["ym"] for r in rows]


def get_staff_profile_stats(staff_id):
    """Stats tháng này cho trang Hồ sơ — bookings hoàn thành + thu nhập (lương + hoa hồng)."""
    conn = get_connection()
    bookings_this_month = conn.execute("""
        SELECT COUNT(*) FROM bookings
        WHERE staff_id = ? AND status = 'done'
          AND strftime('%Y-%m', booking_date) = strftime('%Y-%m', 'now')
    """, (staff_id,)).fetchone()[0]
    income_this_month = conn.execute("""
        SELECT COALESCE(SUM(staff_total_earning), 0) FROM bookings
        WHERE staff_id = ? AND status = 'done'
          AND strftime('%Y-%m', booking_date) = strftime('%Y-%m', 'now')
    """, (staff_id,)).fetchone()[0]
    conn.close()
    return {"bookings_this_month": bookings_this_month, "income_this_month": income_this_month}


def get_staff_history_stats(staff_id, today_str):
    """Stats trang Lịch sử — luôn tính trên toàn bộ record, không theo filter đang chọn.
    incomplete = cancelled sau khi đã qua ngày hẹn (khác cancelled trước ngày hẹn)."""
    conn = get_connection()
    total = conn.execute(
        "SELECT COUNT(*) FROM bookings WHERE staff_id = ? AND status IN ('done', 'cancelled')",
        (staff_id,)
    ).fetchone()[0]
    done = conn.execute(
        "SELECT COUNT(*) FROM bookings WHERE staff_id = ? AND status = 'done'",
        (staff_id,)
    ).fetchone()[0]
    cancelled = conn.execute(
        "SELECT COUNT(*) FROM bookings WHERE staff_id = ? AND status = 'cancelled'",
        (staff_id,)
    ).fetchone()[0]
    incomplete = conn.execute(
        "SELECT COUNT(*) FROM bookings WHERE staff_id = ? AND status = 'cancelled' AND booking_date < ?",
        (staff_id, today_str)
    ).fetchone()[0]
    conn.close()
    return {"total": total, "done": done, "cancelled": cancelled, "incomplete": incomplete}


def get_staff_history(staff_id, month='', search='', status='all', today_str=None):
    """Bookings done/cancelled của 1 staff cho trang 'Lịch sử'. LEFT JOIN invoices
    giống get_staff_bookings_range (payment model thật nằm ở invoices, không ở bookings)."""
    conn = get_connection()
    where = "WHERE b.staff_id = ? AND b.status IN ('done', 'cancelled')"
    params = [staff_id]
    if month:
        where += " AND strftime('%Y-%m', b.booking_date) = ?"
        params.append(month)
    if search:
        where += " AND c.full_name LIKE ?"
        params.append(f'%{search}%')
    if status == 'done':
        where += " AND b.status = 'done'"
    elif status == 'cancelled':
        where += " AND b.status = 'cancelled'"
    elif status == 'incomplete':
        where += " AND b.status = 'cancelled' AND b.booking_date < ?"
        params.append(today_str)

    rows = conn.execute(f"""
        SELECT b.id, b.booking_date, b.start_time, b.end_time, b.status,
               b.staff_commission, b.staff_hourly_earning, b.staff_total_earning,
               c.full_name AS customer_name, c.phone AS customer_phone,
               sv.name AS service_name, sv.price AS total_price,
               iv.payment_method AS invoice_method, iv.status AS invoice_status
        FROM bookings b
        JOIN customers c ON c.id = b.customer_id
        JOIN services sv ON sv.id = b.service_id
        LEFT JOIN invoices iv ON iv.booking_id = b.id
        {where}
        ORDER BY b.booking_date DESC, b.start_time DESC
    """, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_invoice_by_booking(booking_id):
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM invoices WHERE booking_id = ?", (booking_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def create_invoice(conn, booking_id, amount, payment_method, status="pending"):
    """Tạo invoice cho 1 booking. Dùng chung conn của caller để atomic
    với lúc set booking = 'done'. invoice_number = INV-{year}-{booking_id}."""
    year = now_helsinki().strftime("%Y")
    invoice_number = f"INV-{year}-{booking_id:04d}"
    conn.execute(
        """INSERT INTO invoices (booking_id, invoice_number, amount, payment_method, status)
           VALUES (?, ?, ?, ?, ?)""",
        (booking_id, invoice_number, amount, payment_method, status)
    )


def mark_invoice_paid(booking_id):
    conn = get_connection()
    conn.execute(
        "UPDATE invoices SET status = 'paid' WHERE booking_id = ?", (booking_id,)
    )
    conn.commit()
    conn.close()


def update_customer_profile(customer_id, full_name, email, phone, date_of_birth):
    conn = get_connection()
    conn.execute(
        "UPDATE customers SET full_name=?, email=?, phone=?, date_of_birth=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
        (full_name, email, phone, date_of_birth, customer_id)
    )
    conn.commit()
    conn.close()


def update_customer_avatar(customer_id, avatar):
    conn = get_connection()
    conn.execute(
        "UPDATE customers SET avatar=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
        (avatar, customer_id)
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


def update_user_lang(user_id, lang):
    conn = get_connection()
    conn.execute("UPDATE users SET lang=? WHERE id=?", (lang, user_id))
    conn.commit()
    conn.close()

def get_admin_kpis(date_str):
    conn = get_connection()
    revenue = conn.execute(
        """SELECT COALESCE(SUM(i.amount), 0)
           FROM invoices i JOIN bookings b ON b.id = i.booking_id
           WHERE b.booking_date = ? AND i.status = 'paid'""",
        (date_str,)
    ).fetchone()[0]
    bookings = conn.execute(
        "SELECT COUNT(*) FROM bookings WHERE booking_date = ? AND status NOT IN ('unverified', 'cancelled')",
        (date_str,)
    ).fetchone()[0]
    new_customers = conn.execute(
        "SELECT COUNT(*) FROM customers WHERE DATE(created_at) = ?",
        (date_str,)
    ).fetchone()[0]
    pending = conn.execute(
        "SELECT COUNT(*) FROM bookings WHERE status = 'pending'"
    ).fetchone()[0]
    conn.close()
    return {
        "revenue": f"{revenue:,.0f}",
        "bookings": bookings,
        "new_customers": new_customers,
        "pending": pending,
    }

def get_admin_today_appointments(date_str):
    conn = get_connection()
    rows = conn.execute("""
        SELECT b.start_time, b.status,
               c.full_name AS customer_name,
               s.name AS service_name, s.duration_minutes,
               st.full_name AS staff_name
        FROM bookings b
        JOIN customers c ON c.id = b.customer_id
        JOIN services s ON s.id = b.service_id
        JOIN staff st ON st.id = b.staff_id
        WHERE b.booking_date = ?
          AND b.status != 'unverified'
        ORDER BY b.start_time ASC
    """, (date_str,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def auto_expire_bookings():
    """Flips 'confirmed'/'pending' bookings to 'no-show' once the current
    Helsinki wall-clock time has passed their end_time today (or their
    booking_date is in the past). Starting a booking ('in-progress') is now
    a manual staff action (see mark_in_progress) — this function only handles
    the no-show cutoff. Called on admin/staff page loads (see staff_dashboard/
    admin_bookings/admin_dashboard) — there's no scheduler in this project,
    so this is evaluated lazily on read."""
    conn = get_connection()
    now = now_helsinki()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M")
    conn.execute("""
        UPDATE bookings
        SET status = 'no-show',
            updated_at = ?
        WHERE status IN ('confirmed', 'pending')
          AND (booking_date < ?
               OR (booking_date = ? AND end_time <= ?))
    """, (now.strftime("%Y-%m-%d %H:%M:%S"), date_str, date_str, time_str))
    conn.commit()
    conn.close()

def get_admin_revenue_chart(date_str):
    from datetime import datetime as _dt, timedelta as _td
    today = _dt.strptime(date_str, "%Y-%m-%d").date()
    conn = get_connection()

    # Week: last 7 days, one point per day
    week_start = (today - _td(days=6)).strftime("%Y-%m-%d")
    week_rows = conn.execute("""
        SELECT b.booking_date AS day, COALESCE(SUM(i.amount), 0) AS revenue
        FROM invoices i JOIN bookings b ON b.id = i.booking_id
        WHERE b.booking_date >= ? AND b.booking_date <= ? AND i.status = 'paid'
        GROUP BY b.booking_date ORDER BY b.booking_date ASC
    """, (week_start, date_str)).fetchall()
    week_map = {r["day"]: r["revenue"] for r in week_rows}
    week_data = []
    for i in range(7):
        d = today - _td(days=6 - i)
        week_data.append({"label": d.strftime("%a"), "value": week_map.get(d.strftime("%Y-%m-%d"), 0)})

    # Month: last 4 weeks grouped by week
    month_start = (today - _td(days=27)).strftime("%Y-%m-%d")
    month_rows = conn.execute("""
        SELECT strftime('%Y-W%W', b.booking_date) AS wk, COALESCE(SUM(i.amount), 0) AS revenue
        FROM invoices i JOIN bookings b ON b.id = i.booking_id
        WHERE b.booking_date >= ? AND b.booking_date <= ? AND i.status = 'paid'
        GROUP BY wk ORDER BY wk ASC
    """, (month_start, date_str)).fetchall()
    month_map = {r["wk"]: r["revenue"] for r in month_rows}
    month_data = []
    for i in range(4):
        d = today - _td(weeks=3 - i)
        month_data.append({"label": f"Week {i + 1}", "value": month_map.get(d.strftime("%Y-W%W"), 0)})

    conn.close()
    return {"week": week_data, "month": month_data}

def get_admin_recent_activity(limit=5):
    conn = get_connection()
    rows = conn.execute("""
        SELECT b.id, b.status, b.updated_at,
               c.full_name AS customer_name,
               s.name AS service_name
        FROM bookings b
        JOIN customers c ON c.id = b.customer_id
        JOIN services s ON s.id = b.service_id
        WHERE b.status != 'unverified'
        ORDER BY b.updated_at DESC
        LIMIT ?
    """, (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_admin_top_services(date_from, date_to, limit=3):
    """Ranked by booking count (not revenue) — unlike get_report_top_services,
    this counts confirmed/done bookings (LEFT JOIN invoices), not just paid
    ones, so it still shows data for a month with no paid invoices yet."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT sv.name AS name,
               COUNT(b.id) AS booking_count,
               COALESCE(SUM(i.amount), 0) AS revenue
        FROM bookings b
        JOIN services sv ON sv.id = b.service_id
        LEFT JOIN invoices i ON i.booking_id = b.id AND i.status = 'paid'
        WHERE b.booking_date BETWEEN ? AND ?
          AND b.status IN ('confirmed', 'done')
        GROUP BY sv.id
        ORDER BY booking_count DESC
        LIMIT ?
    """, (date_from, date_to, limit)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_popular_services(limit=4):
    """Active services ranked by booking count for the public homepage.
    Same ranking convention as get_admin_top_services (COUNT of bookings with
    status confirmed/done), but LEFT JOIN so services with 0 bookings still show,
    and returns full card fields (id, price, image, category slug)."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT s.id, s.name, s.name_fi, s.name_vi,
               s.description, s.description_fi, s.description_vi,
               s.price, s.image,
               c.slug AS category_slug,
               COUNT(CASE WHEN b.status IN ('confirmed', 'done') THEN b.id END) AS booking_count
        FROM services s
        JOIN service_categories c ON s.category_id = c.id
        LEFT JOIN bookings b ON b.service_id = s.id
        WHERE s.is_active = 1
          AND c.is_active = 1
        GROUP BY s.id
        ORDER BY booking_count DESC, s.name ASC
        LIMIT ?
    """, (limit,)).fetchall()
    conn.close()
    return rows

def get_admin_top_loyalty(limit=5):
    conn = get_connection()
    rows = conn.execute("""
        SELECT c.full_name,
               COALESCE(mt.name, 'Silver') AS tier_name,
               SUM(lpl.points) AS total_points
        FROM loyalty_points_log lpl
        JOIN customers c ON c.id = lpl.customer_id
        LEFT JOIN customer_memberships cm ON cm.id = (
            SELECT cm2.id FROM customer_memberships cm2
            WHERE cm2.customer_id = c.id AND cm2.is_active = 1
            ORDER BY (cm2.stripe_subscription_id IS NOT NULL) DESC, cm2.id DESC
            LIMIT 1
        )
        LEFT JOIN membership_tiers mt ON mt.id = cm.tier_id
        GROUP BY lpl.customer_id
        HAVING total_points > 0
        ORDER BY total_points DESC
        LIMIT ?
    """, (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_admin_new_members(month_str, limit=8):
    conn = get_connection()
    rows = conn.execute("""
        SELECT full_name, email, created_at
        FROM customers
        WHERE strftime('%Y-%m', created_at) = ?
        ORDER BY created_at DESC
        LIMIT ?
    """, (month_str, limit)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_all_customers():
    conn = get_connection()
    rows = conn.execute(
        "SELECT id, full_name, phone FROM customers ORDER BY full_name ASC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_admin_bookings(q='', status='', staff_id='', service_id='', date='', page=1, per_page=15):
    conn = get_connection()

    joins = """
        FROM bookings b
        JOIN customers c ON c.id = b.customer_id
        JOIN staff st ON st.id = b.staff_id
        JOIN services sv ON sv.id = b.service_id
        WHERE 1=1
    """
    params = []
    if q:
        search = q.lstrip('#')
        joins += " AND (CAST(b.id AS TEXT) LIKE ? OR c.full_name LIKE ?)"
        params.extend([f'%{search}%', f'%{search}%'])
    if status:
        joins += " AND b.status = ?"
        params.append(status)
    if staff_id:
        joins += " AND b.staff_id = ?"
        params.append(staff_id)
    if service_id:
        joins += " AND b.service_id = ?"
        params.append(service_id)
    if date:
        joins += " AND b.booking_date = ?"
        params.append(date)

    total = conn.execute("SELECT COUNT(*) " + joins, params).fetchone()[0]

    select = (
        "SELECT b.id, b.booking_date, b.start_time, b.end_time, b.status, "
        "b.notes, b.cancellation_reason, "
        "c.id AS customer_id, c.full_name AS customer_name, c.phone AS customer_phone, "
        "st.id AS staff_id, st.full_name AS staff_name, "
        "sv.id AS service_id, sv.name AS service_name, sv.duration_minutes "
    )
    rows = conn.execute(
        select + joins + " ORDER BY b.booking_date DESC, b.start_time DESC LIMIT ? OFFSET ?",
        params + [per_page, (page - 1) * per_page]
    ).fetchall()

    conn.close()
    return [dict(r) for r in rows], total


def get_booking_status_counts(q='', staff_id='', service_id='', date=''):
    conn = get_connection()

    joins = """
        FROM bookings b
        JOIN customers c ON c.id = b.customer_id
        WHERE 1=1
    """
    params = []
    if q:
        search = q.lstrip('#')
        joins += " AND (CAST(b.id AS TEXT) LIKE ? OR c.full_name LIKE ?)"
        params.extend([f'%{search}%', f'%{search}%'])
    if staff_id:
        joins += " AND b.staff_id = ?"
        params.append(staff_id)
    if service_id:
        joins += " AND b.service_id = ?"
        params.append(service_id)
    if date:
        joins += " AND b.booking_date = ?"
        params.append(date)

    rows = conn.execute(
        "SELECT b.status, COUNT(*) AS cnt " + joins + " GROUP BY b.status",
        params
    ).fetchall()
    conn.close()

    counts = {r['status']: r['cnt'] for r in rows}
    return {
        'all':         sum(counts.values()),
        'pending':     counts.get('pending', 0),
        'confirmed':   counts.get('confirmed', 0),
        'in_progress': counts.get('in-progress', 0),
        'done':        counts.get('done', 0),
        'cancelled':   counts.get('cancelled', 0),
        'no_show':     counts.get('no-show', 0),
    }


def update_booking_details(booking_id, staff_id, booking_date, start_time, end_time, notes):
    conn = get_connection()
    updated_at = now_helsinki().strftime("%Y-%m-%d %H:%M:%S")
    conn.execute(
        "UPDATE bookings SET staff_id=?, booking_date=?, start_time=?, end_time=?, notes=?, updated_at=? WHERE id=?",
        (staff_id, booking_date, start_time, end_time, notes, updated_at, booking_id)
    )
    conn.commit()
    conn.close()


def get_staff_stats(month_start_str):
    conn = get_connection()
    total_staff = conn.execute("SELECT COUNT(*) FROM staff").fetchone()[0]
    active_staff = conn.execute("SELECT COUNT(*) FROM staff WHERE is_active = 1").fetchone()[0]
    bookings_this_month = conn.execute(
        "SELECT COUNT(*) FROM bookings WHERE booking_date >= ? AND status NOT IN ('unverified', 'cancelled')",
        (month_start_str,)
    ).fetchone()[0]
    avg_hourly_rate = conn.execute("SELECT COALESCE(AVG(hourly_rate), 0) FROM staff").fetchone()[0]
    conn.close()
    return {
        "total_staff": total_staff,
        "active_staff": active_staff,
        "bookings_this_month": bookings_this_month,
        "avg_hourly_rate": avg_hourly_rate,
    }


def get_staff_role_list():
    conn = get_connection()
    rows = conn.execute(
        "SELECT DISTINCT role FROM staff WHERE role IS NOT NULL AND role != '' ORDER BY role ASC"
    ).fetchall()
    conn.close()
    return [r["role"] for r in rows]


def get_staff_list(today_str, month_start_str, q='', role='', active=None):
    conn = get_connection()

    where = "WHERE 1=1"
    params = []
    if q:
        where += " AND (s.full_name LIKE ? OR s.email LIKE ?)"
        params.extend([f'%{q}%', f'%{q}%'])
    if role:
        where += " AND s.role = ?"
        params.append(role)
    if active is not None:
        where += " AND s.is_active = ?"
        params.append(active)

    rows = conn.execute(f"SELECT s.* FROM staff s {where} ORDER BY s.full_name ASC", params).fetchall()

    staff_list = []
    for row in rows:
        s = dict(row)
        s["bookings_this_month"] = conn.execute(
            "SELECT COUNT(*) FROM bookings WHERE staff_id = ? AND booking_date >= ? AND status NOT IN ('unverified', 'cancelled')",
            (s["id"], month_start_str)
        ).fetchone()[0]
        s["total_today"] = conn.execute(
            "SELECT COUNT(*) FROM bookings WHERE staff_id = ? AND booking_date = ? AND status NOT IN ('unverified', 'cancelled')",
            (s["id"], today_str)
        ).fetchone()[0]
        s["done_today"] = conn.execute(
            "SELECT COUNT(*) FROM bookings WHERE staff_id = ? AND booking_date = ? AND status = 'done'",
            (s["id"], today_str)
        ).fetchone()[0]
        staff_list.append(s)

    conn.close()
    return staff_list


def create_staff(full_name, email, phone, role, hourly_rate, commission_rate, is_active, user_id):
    conn = get_connection()
    cur = conn.execute("""
        INSERT INTO staff (full_name, email, phone, role, hourly_rate, commission_rate, is_active, user_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (full_name, email, phone, role, hourly_rate, commission_rate, is_active, user_id))
    conn.commit()
    staff_id = cur.lastrowid
    conn.close()
    return staff_id


def update_staff(staff_id, full_name, email, phone, role, hourly_rate, commission_rate, is_active):
    conn = get_connection()
    conn.execute("""
        UPDATE staff
        SET full_name = ?, email = ?, phone = ?, role = ?, hourly_rate = ?, commission_rate = ?, is_active = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (full_name, email, phone, role, hourly_rate, commission_rate, is_active, staff_id))
    conn.commit()
    conn.close()


def update_staff_photo(staff_id, photo_filename):
    conn = get_connection()
    conn.execute(
        "UPDATE staff SET photo = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (photo_filename, staff_id)
    )
    conn.commit()
    conn.close()


def delete_staff(staff_id):
    conn = get_connection()
    conn.execute("DELETE FROM staff WHERE id = ?", (staff_id,))
    conn.commit()
    conn.close()


def toggle_staff_active(staff_id):
    conn = get_connection()
    conn.execute(
        "UPDATE staff SET is_active = 1 - is_active, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (staff_id,)
    )
    conn.commit()
    conn.close()


def get_admin_customer_stats(month_start_str):
    conn = get_connection()
    total = conn.execute("SELECT COUNT(*) FROM customers").fetchone()[0]
    has_account = conn.execute("SELECT COUNT(*) FROM customers WHERE user_id IS NOT NULL").fetchone()[0]
    new_this_month = conn.execute(
        "SELECT COUNT(*) FROM customers WHERE created_at >= ?", (month_start_str,)
    ).fetchone()[0]
    # Đếm mỗi khách MỘT lần theo tier hiện tại (sub mới nhất thắng), tránh nhân
    # bản khi khách có nhiều row membership active (Silver cấp tay + sub, hoặc chồng lấn).
    tier_rows = conn.execute("""
        SELECT LOWER(mt.name) AS tier, COUNT(*) AS cnt
        FROM customers c
        JOIN membership_tiers mt ON mt.id = (
            SELECT cm.tier_id FROM customer_memberships cm
            WHERE cm.customer_id = c.id AND cm.is_active = 1
            ORDER BY (cm.stripe_subscription_id IS NOT NULL) DESC, cm.id DESC LIMIT 1
        )
        GROUP BY LOWER(mt.name)
    """).fetchall()
    conn.close()

    tier_counts = {r["tier"]: r["cnt"] for r in tier_rows}
    return {
        "total": total,
        "has_account": has_account,
        "new_this_month": new_this_month,
        "silver_count": tier_counts.get("silver", 0),
        "gold_count": tier_counts.get("gold", 0),
        "diamond_count": tier_counts.get("diamond", 0),
    }


def get_admin_customers(q='', sort='newest', tier='', page=1, per_page=15):
    conn = get_connection()

    joins = """
        FROM customers c
        LEFT JOIN customer_memberships cm ON cm.id = (
            SELECT cm2.id FROM customer_memberships cm2
            WHERE cm2.customer_id = c.id AND cm2.is_active = 1
            ORDER BY (cm2.stripe_subscription_id IS NOT NULL) DESC, cm2.id DESC
            LIMIT 1
        )
        LEFT JOIN membership_tiers mt ON mt.id = cm.tier_id
        LEFT JOIN (
            SELECT customer_id, SUM(points) AS total_points
            FROM loyalty_points_log GROUP BY customer_id
        ) pts ON pts.customer_id = c.id
        LEFT JOIN (
            SELECT customer_id, COUNT(*) AS total_bookings, MAX(booking_date) AS last_visit
            FROM bookings GROUP BY customer_id
        ) bk ON bk.customer_id = c.id
        LEFT JOIN (
            SELECT b.customer_id, SUM(i.amount) AS total_spend
            FROM invoices i JOIN bookings b ON i.booking_id = b.id
            WHERE i.status = 'paid' GROUP BY b.customer_id
        ) sp ON sp.customer_id = c.id
        LEFT JOIN (
            SELECT customer_id, COUNT(*) AS voucher_count
            FROM reward_redemptions WHERE is_used = 0 GROUP BY customer_id
        ) vc ON vc.customer_id = c.id
        WHERE 1=1
    """
    params = []
    if q:
        joins += " AND (c.full_name LIKE ? OR c.email LIKE ? OR c.phone LIKE ?)"
        params.extend([f'%{q}%', f'%{q}%', f'%{q}%'])
    if tier:
        joins += " AND LOWER(mt.name) = ?"
        params.append(tier.lower())

    total = conn.execute("SELECT COUNT(*) " + joins, params).fetchone()[0]

    sort_map = {
        "points":   "COALESCE(pts.total_points, 0) DESC",
        "bookings": "COALESCE(bk.total_bookings, 0) DESC",
        "newest":   "c.created_at DESC",
    }
    order_by = sort_map.get(sort, sort_map["newest"])

    select = """
        SELECT c.id, c.full_name, c.email, c.phone, c.date_of_birth, c.notes,
               c.user_id, c.created_at,
               LOWER(COALESCE(mt.name, 'silver')) AS tier_name,
               COALESCE(pts.total_points, 0) AS total_points,
               COALESCE(bk.total_bookings, 0) AS total_bookings,
               bk.last_visit,
               COALESCE(sp.total_spend, 0) AS total_spend,
               COALESCE(vc.voucher_count, 0) AS voucher_count
    """
    rows = conn.execute(
        select + joins + f" ORDER BY {order_by} LIMIT ? OFFSET ?",
        params + [per_page, (page - 1) * per_page]
    ).fetchall()

    customers = []
    for row in rows:
        c = dict(row)
        recent = conn.execute("""
            SELECT s.name AS service_name, b.booking_date, st.full_name AS staff_name, b.status
            FROM bookings b
            JOIN services s ON s.id = b.service_id
            JOIN staff st ON st.id = b.staff_id
            WHERE b.customer_id = ?
            ORDER BY b.booking_date DESC, b.start_time DESC
            LIMIT 3
        """, (c["id"],)).fetchall()
        c["recent_bookings"] = [dict(r) for r in recent]
        customers.append(c)

    conn.close()
    return customers, total


def create_customer_admin(full_name, email, phone, date_of_birth, notes):
    conn = get_connection()
    cur = conn.execute(
        """
        INSERT INTO customers (full_name, email, phone, date_of_birth, notes)
        VALUES (?, ?, ?, ?, ?)
        """, (full_name, email or '', phone or None, date_of_birth, notes or None)
    )
    conn.commit()
    customer_id = cur.lastrowid
    conn.close()
    return customer_id


def delete_customer_admin(customer_id):
    # Every customer always has a customer_memberships row (auto-assigned Silver on
    # registration) and may have loyalty_points_log rows — both are bookkeeping tied
    # 1:1 to the customer, not standalone business records, so they cascade with the
    # delete. bookings/reviews/reward_redemptions/referrals are real history and are
    # left to raise IntegrityError, blocking deletion as intended.
    conn = get_connection()
    try:
        row = conn.execute("SELECT user_id FROM customers WHERE id = ?", (customer_id,)).fetchone()
        user_id = row["user_id"] if row else None

        conn.execute("DELETE FROM customer_memberships WHERE customer_id = ?", (customer_id,))
        conn.execute("DELETE FROM loyalty_points_log WHERE customer_id = ?", (customer_id,))
        conn.execute("DELETE FROM customers WHERE id = ?", (customer_id,))
        if user_id:
            conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def update_customer_admin(customer_id, full_name, email, phone, date_of_birth, notes):
    conn = get_connection()
    conn.execute(
        """
        UPDATE customers
        SET full_name = ?, email = ?, phone = ?, date_of_birth = ?, notes = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """, (full_name, email or '', phone, date_of_birth, notes, customer_id)
    )
    conn.commit()
    conn.close()


# ─────────────────────────────────────────────────────────────
#  ADMIN LOYALTY MANAGEMENT
#  "Missions" are edits to the 5 real loyalty_config rows that
#  already drive award_points() in the booking flow (see
#  app/services/loyalty.py). Not a free-form CRUD namespace —
#  the key set is fixed because these keys are hardcoded at the
#  call sites in routes.py.
# ─────────────────────────────────────────────────────────────

MISSION_KEYS = [
    "first_booking_bonus",
    "streak_bonus",
    "review_bonus",
    "birthday_bonus",
    "referral_bonus",
]

def get_admin_loyalty_customers():
    conn = get_connection()
    rows = conn.execute("""
        SELECT c.id, c.full_name, c.email,
               LOWER(COALESCE(mt.name, 'silver')) AS tier_name,
               COALESCE(pts.total_points, 0) AS total_points,
               COALESCE(vc.voucher_count, 0) AS voucher_count,
               cm.expires_at AS membership_expires_at,
               cm.tier_id AS membership_tier_id
        FROM customers c
        LEFT JOIN customer_memberships cm ON cm.id = (
            SELECT cm2.id FROM customer_memberships cm2
            WHERE cm2.customer_id = c.id AND cm2.is_active = 1
            ORDER BY (cm2.stripe_subscription_id IS NOT NULL) DESC, cm2.id DESC
            LIMIT 1
        )
        LEFT JOIN membership_tiers mt ON mt.id = cm.tier_id
        LEFT JOIN (
            SELECT customer_id, SUM(points) AS total_points
            FROM loyalty_points_log GROUP BY customer_id
        ) pts ON pts.customer_id = c.id
        LEFT JOIN (
            SELECT customer_id, COUNT(*) AS voucher_count
            FROM reward_redemptions WHERE is_used = 0 GROUP BY customer_id
        ) vc ON vc.customer_id = c.id
        WHERE c.user_id IS NOT NULL
        ORDER BY c.full_name ASC
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_admin_loyalty_stats():
    conn = get_connection()
    total_customers_with_account = conn.execute(
        "SELECT COUNT(*) FROM customers WHERE user_id IS NOT NULL"
    ).fetchone()[0]
    total_points_circulating = conn.execute(
        "SELECT COALESCE(SUM(points), 0) FROM loyalty_points_log"
    ).fetchone()[0]
    active_vouchers = conn.execute(
        "SELECT COUNT(*) FROM rewards WHERE is_active = 1"
    ).fetchone()[0]
    placeholders = ",".join("?" * len(MISSION_KEYS))
    active_missions = conn.execute(
        f"SELECT COUNT(*) FROM loyalty_config WHERE key IN ({placeholders}) AND CAST(value AS INTEGER) > 0",
        MISSION_KEYS
    ).fetchone()[0]
    conn.close()
    return {
        "total_customers_with_account": total_customers_with_account,
        "total_points_circulating": total_points_circulating,
        "active_vouchers": active_vouchers,
        "active_missions": active_missions,
    }


def get_rewards_admin():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM rewards ORDER BY created_at DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_missions():
    conn = get_connection()
    placeholders = ",".join("?" * len(MISSION_KEYS))
    rows = conn.execute(
        f"SELECT key, value, description FROM loyalty_config WHERE key IN ({placeholders})",
        MISSION_KEYS
    ).fetchall()
    conn.close()
    by_key = {r["key"]: dict(r) for r in rows}
    return [by_key[k] for k in MISSION_KEYS if k in by_key]


def create_reward(name, description, cost, stock, max_redeems_per_customer, cooldown_days, banner_image=None,
                  name_fi=None, name_vi=None, description_fi=None, description_vi=None):
    conn = get_connection()
    cur = conn.execute("""
        INSERT INTO rewards (name, description, cost, stock, max_redeems_per_customer, cooldown_days, banner_image, is_active,
                             name_fi, name_vi, description_fi, description_vi)
        VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, ?, ?, ?)
    """, (name, description, cost, stock, max_redeems_per_customer, cooldown_days, banner_image,
          name_fi, name_vi, description_fi, description_vi))
    conn.commit()
    reward_id = cur.lastrowid
    conn.close()
    return reward_id


def update_reward(reward_id, name, description, cost, stock, max_redeems_per_customer, cooldown_days, is_active, banner_image,
                  name_fi=None, name_vi=None, description_fi=None, description_vi=None):
    conn = get_connection()
    conn.execute("""
        UPDATE rewards
        SET name = ?, description = ?, cost = ?, stock = ?,
            max_redeems_per_customer = ?, cooldown_days = ?, is_active = ?, banner_image = ?,
            name_fi = ?, name_vi = ?, description_fi = ?, description_vi = ?
        WHERE id = ?
    """, (name, description, cost, stock, max_redeems_per_customer, cooldown_days, is_active, banner_image,
          name_fi, name_vi, description_fi, description_vi, reward_id))
    conn.commit()
    conn.close()


def get_reward_by_id(reward_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM rewards WHERE id = ?", (reward_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_reward_redemption_count(reward_id):
    conn = get_connection()
    count = conn.execute(
        "SELECT COUNT(*) FROM reward_redemptions WHERE reward_id = ?", (reward_id,)
    ).fetchone()[0]
    conn.close()
    return count


def delete_reward(reward_id):
    conn = get_connection()
    conn.execute("DELETE FROM rewards WHERE id = ?", (reward_id,))
    conn.commit()
    conn.close()


def deactivate_reward(reward_id):
    conn = get_connection()
    conn.execute("UPDATE rewards SET is_active = 0 WHERE id = ?", (reward_id,))
    conn.commit()
    conn.close()


def update_mission_config(key, description, points):
    conn = get_connection()
    conn.execute(
        "UPDATE loyalty_config SET value = ?, description = ?, updated_at = CURRENT_TIMESTAMP WHERE key = ?",
        (str(points), description, key)
    )
    conn.commit()
    conn.close()


def toggle_mission_config(key, default_points):
    conn = get_connection()
    row = conn.execute("SELECT value FROM loyalty_config WHERE key = ?", (key,)).fetchone()
    current = int(row["value"]) if row else 0
    new_value = 0 if current > 0 else default_points
    conn.execute(
        "UPDATE loyalty_config SET value = ?, updated_at = CURRENT_TIMESTAMP WHERE key = ?",
        (str(new_value), key)
    )
    conn.commit()
    conn.close()
    return new_value


def get_active_membership_tiers():
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM membership_tiers WHERE is_active = 1 ORDER BY point_multiplier ASC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def adjust_membership_admin(customer_id, tier_id, started_at, expires_at):
    conn = get_connection()
    try:
        # Admin cấp tay -> chỉ deactivate row thủ công cũ, không đụng row subscription.
        conn.execute(
            "UPDATE customer_memberships SET is_active = 0 WHERE customer_id = ? AND is_active = 1 AND stripe_subscription_id IS NULL",
            (customer_id,)
        )
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


# ─────────────────────────────────────────────────────────────
#  STRIPE MEMBERSHIP SUBSCRIPTION
#  Nhiều dòng/khách: row subscription (stripe_subscription_id NOT NULL) do webhook
#  quản; row cấp tay (NULL) do admin/free quản. get_customer_current_tier chọn tier
#  hiện tại: sub active MỚI NHẤT thắng, không có sub -> grant cấp tay.
# ─────────────────────────────────────────────────────────────

def set_customer_stripe_id(customer_id, stripe_customer_id):
    conn = get_connection()
    conn.execute("UPDATE customers SET stripe_customer_id = ? WHERE id = ?",
                 (stripe_customer_id, customer_id))
    conn.commit()
    conn.close()


def get_customer_by_stripe_customer(stripe_customer_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM customers WHERE stripe_customer_id = ?",
                       (stripe_customer_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_tier_by_id(tier_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM membership_tiers WHERE id = ?", (tier_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_tier_by_stripe_price(price_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM membership_tiers WHERE stripe_price_id = ?",
                       (price_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_customer_subscription_row(customer_id):
    """Row subscription đang active MỚI NHẤT của khách (để cancel / hiển thị banner).
    Lúc đổi tier có thể có nhiều row active chồng lấn -> lấy cái mới nhất (đang gia hạn)."""
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM customer_memberships WHERE customer_id = ? "
        "AND stripe_subscription_id IS NOT NULL AND is_active = 1 "
        "ORDER BY id DESC LIMIT 1",
        (customer_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_active_subscription_rows(customer_id):
    """Mọi row subscription đang active của khách (kể cả đã hẹn hủy). Dùng để hủy
    các gói cũ khi mua gói mới, và guard 'đã đăng ký tier này'."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM customer_memberships WHERE customer_id = ? "
        "AND stripe_subscription_id IS NOT NULL AND is_active = 1",
        (customer_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_customer_current_tier(customer_id):
    """Tier HIỆN TẠI của khách — nguồn chân lý DUY NHẤT cho cả hiển thị lẫn hệ số
    điểm. Định nghĩa: gói SUBSCRIPTION active MỚI NHẤT (gói vừa chọn / đang gia hạn;
    kể cả đã hẹn hủy thì vẫn giữ tới hết kỳ). Không có sub -> grant cấp tay active
    cao nhất. Không có gì -> None (Silver). Không dùng 'tier cao nhất thắng' nữa:
    đổi tier = tier mới thay thế ngay (gói cũ đã hủy không còn tính quyền lợi)."""
    conn = get_connection()
    now_str = now_helsinki().strftime("%Y-%m-%d %H:%M:%S")
    row = conn.execute("""
        SELECT mt.name, mt.point_multiplier, cm.expires_at
        FROM customer_memberships cm
        JOIN membership_tiers mt ON cm.tier_id = mt.id
        WHERE cm.customer_id = ? AND cm.is_active = 1 AND cm.expires_at > ?
          AND cm.stripe_subscription_id IS NOT NULL
        ORDER BY cm.id DESC LIMIT 1
    """, (customer_id, now_str)).fetchone()
    if not row:
        row = conn.execute("""
            SELECT mt.name, mt.point_multiplier, cm.expires_at
            FROM customer_memberships cm
            JOIN membership_tiers mt ON cm.tier_id = mt.id
            WHERE cm.customer_id = ? AND cm.is_active = 1 AND cm.expires_at > ?
              AND cm.stripe_subscription_id IS NULL
            ORDER BY mt.point_multiplier DESC LIMIT 1
        """, (customer_id, now_str)).fetchone()
    conn.close()
    return dict(row) if row else None


def upsert_subscription_membership(customer_id, tier_id, subscription_id, expires_at,
                                   status, cancel_at_period_end):
    """Upsert row subscription theo stripe_subscription_id. Dùng chung cho
    checkout hoàn tất + gia hạn + đổi tier + đồng bộ trạng thái. is_active suy ra
    từ status Stripe (past_due vẫn giữ tier, expiry gate sẽ chặn nếu quá hạn).
    subscription_status lưu trạng thái Stripe gốc (để phân biệt active vs past_due)."""
    is_active = 1 if status in ("active", "trialing", "past_due") else 0
    started_at = now_helsinki().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_connection()
    try:
        # ON CONFLICT theo UNIQUE(stripe_subscription_id): nguyên tử trong 1 câu,
        # chống race fallback+webhook tạo dòng trùng. started_at giữ nguyên khi update.
        conn.execute(
            "INSERT INTO customer_memberships (customer_id, tier_id, started_at, "
            "expires_at, is_active, stripe_subscription_id, subscription_status, "
            "cancel_at_period_end) VALUES (?, ?, ?, ?, ?, ?, ?, ?) "
            "ON CONFLICT(stripe_subscription_id) DO UPDATE SET "
            "tier_id=excluded.tier_id, expires_at=excluded.expires_at, "
            "subscription_status=excluded.subscription_status, "
            "cancel_at_period_end=excluded.cancel_at_period_end, is_active=excluded.is_active",
            (customer_id, tier_id, started_at, expires_at, is_active,
             subscription_id, status, cancel_at_period_end))
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def deactivate_subscription(subscription_id):
    conn = get_connection()
    conn.execute(
        "UPDATE customer_memberships SET is_active = 0, subscription_status = 'canceled' "
        "WHERE stripe_subscription_id = ?", (subscription_id,))
    conn.commit()
    conn.close()


# ─────────────────────────────────────────────────────────────
#  ADMIN REPORTS & STATISTICS
#  All revenue is attributed to bookings.booking_date (date of
#  service), joined to paid invoices. All date filters are
#  inclusive [date_from, date_to] on 'YYYY-MM-DD' strings.
# ─────────────────────────────────────────────────────────────

def get_report_totals(date_from, date_to):
    """4 KPI scalars for a date range. Reused for the previous period too."""
    conn = get_connection()
    revenue = conn.execute(
        """
        SELECT COALESCE(SUM(i.amount), 0)
        FROM invoices i
        JOIN bookings b ON b.id = i.booking_id
        WHERE i.status = 'paid' AND b.booking_date BETWEEN ? AND ?
        """, (date_from, date_to)
    ).fetchone()[0]
    bookings = conn.execute(
        """
        SELECT COUNT(*) FROM bookings
        WHERE booking_date BETWEEN ? AND ? AND status NOT IN ('unverified', 'cancelled')
        """, (date_from, date_to)
    ).fetchone()[0]
    new_customers = conn.execute(
        "SELECT COUNT(*) FROM customers WHERE DATE(created_at) BETWEEN ? AND ?",
        (date_from, date_to)
    ).fetchone()[0]
    points_issued = conn.execute(
        "SELECT COALESCE(SUM(points), 0) FROM loyalty_points_log WHERE points > 0 AND DATE(created_at) BETWEEN ? AND ?",
        (date_from, date_to)
    ).fetchone()[0]
    conn.close()
    return {
        "revenue": revenue,
        "bookings": bookings,
        "new_customers": new_customers,
        "points_issued": int(points_issued),
    }


def get_report_revenue_by_day(date_from, date_to):
    """Paid revenue per service day. Only days with revenue are returned."""
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT b.booking_date AS day, COALESCE(SUM(i.amount), 0) AS amount
        FROM invoices i
        JOIN bookings b ON b.id = i.booking_id
        WHERE i.status = 'paid' AND b.booking_date BETWEEN ? AND ?
        GROUP BY b.booking_date
        ORDER BY b.booking_date ASC
        """, (date_from, date_to)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_report_revenue_by_hour(date_str):
    """Paid revenue per hour-of-day (0-23) for a single date."""
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT CAST(substr(b.start_time, 1, 2) AS INTEGER) AS hour,
               COALESCE(SUM(i.amount), 0) AS amount
        FROM invoices i
        JOIN bookings b ON b.id = i.booking_id
        WHERE i.status = 'paid' AND b.booking_date = ?
        GROUP BY hour
        """, (date_str,)
    ).fetchall()
    conn.close()
    return {int(r["hour"]): r["amount"] for r in rows}


def get_report_booking_status(date_from, date_to):
    """{status: count} for bookings in range (excluding unverified)."""
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT status, COUNT(*) AS cnt FROM bookings
        WHERE booking_date BETWEEN ? AND ? AND status != 'unverified'
        GROUP BY status
        """, (date_from, date_to)
    ).fetchall()
    conn.close()
    return {r["status"]: r["cnt"] for r in rows}


def get_report_top_services(date_from, date_to, limit=5):
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT sv.name AS name,
               COUNT(DISTINCT b.id) AS booking_count,
               COALESCE(SUM(i.amount), 0) AS revenue
        FROM bookings b
        JOIN services sv ON sv.id = b.service_id
        JOIN invoices i ON i.booking_id = b.id AND i.status = 'paid'
        WHERE b.booking_date BETWEEN ? AND ?
        GROUP BY sv.id
        ORDER BY revenue DESC
        LIMIT ?
        """, (date_from, date_to, limit)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_report_staff_performance(date_from, date_to):
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT st.id AS staff_id, st.full_name AS full_name,
               COUNT(DISTINCT b.id) AS booking_count,
               COALESCE(SUM(i.amount), 0) AS revenue
        FROM bookings b
        JOIN staff st ON st.id = b.staff_id
        JOIN invoices i ON i.booking_id = b.id AND i.status = 'paid'
        WHERE b.booking_date BETWEEN ? AND ?
        GROUP BY st.id
        ORDER BY revenue DESC
        """, (date_from, date_to)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_report_loyalty(date_from, date_to):
    """Points issued (log, points>0) + redeemed (reward_redemptions)."""
    conn = get_connection()
    total_issued = conn.execute(
        "SELECT COALESCE(SUM(points), 0) FROM loyalty_points_log WHERE points > 0 AND DATE(created_at) BETWEEN ? AND ?",
        (date_from, date_to)
    ).fetchone()[0]
    red = conn.execute(
        "SELECT COUNT(*) AS cnt, COALESCE(SUM(points_spent), 0) AS spent FROM reward_redemptions WHERE DATE(redeemed_at) BETWEEN ? AND ?",
        (date_from, date_to)
    ).fetchone()
    sources = conn.execute(
        """
        SELECT source, SUM(points) AS points
        FROM loyalty_points_log
        WHERE points > 0 AND DATE(created_at) BETWEEN ? AND ?
        GROUP BY source
        ORDER BY points DESC
        """, (date_from, date_to)
    ).fetchall()
    conn.close()
    return {
        "total_issued": int(total_issued),
        "total_redeemed": int(red["spent"]),
        "redemption_count": red["cnt"],
        "sources": [dict(s) for s in sources],
    }


def get_report_customer_growth(since_str):
    """{ 'YYYY-MM': count } of new customers since since_str. Route fills the 6-month window."""
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT strftime('%Y-%m', created_at) AS ym, COUNT(*) AS cnt
        FROM customers
        WHERE DATE(created_at) >= ?
        GROUP BY ym
        """, (since_str,)
    ).fetchall()
    conn.close()
    return {r["ym"]: r["cnt"] for r in rows}


# ─────────────────────────────────────────────────────────────
#  ADMIN CAROUSEL MANAGEMENT
#  carousel_slides holds 3 unrelated content types, told apart by
#  carousel_key: 'homepage' (full CRUD), 'dashboard_offers' (full
#  CRUD, each slide just points at a reward_id), 'loyalty_missions'
#  (fixed 3 rows keyed by slot_key, update-only — see MISSION_KEYS
#  and admin_loyalty_update_mission for the analogous fixed-slot
#  pattern already used for loyalty_config).
# ─────────────────────────────────────────────────────────────

MISSION_SLOT_KEYS = ["first_booking", "review", "referral"]

def get_carousel_slides(carousel_key, active_only=False):
    conn = get_connection()
    query = "SELECT * FROM carousel_slides WHERE carousel_key = ?"
    params = [carousel_key]
    if active_only:
        query += " AND is_active = 1"
    query += " ORDER BY sort_order ASC, id ASC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_carousel_slide_by_id(slide_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM carousel_slides WHERE id = ?", (slide_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_next_carousel_sort_order(carousel_key):
    conn = get_connection()
    row = conn.execute(
        "SELECT COALESCE(MAX(sort_order), 0) FROM carousel_slides WHERE carousel_key = ?",
        (carousel_key,)
    ).fetchone()
    conn.close()
    return row[0] + 1


def create_homepage_slide(title, subtitle, badge, image, cta_label, cta_url, cta_style, cta2_label, cta2_url, cta2_style, sort_order,
                          title_fi=None, title_vi=None, subtitle_fi=None, subtitle_vi=None, badge_fi=None, badge_vi=None,
                          cta_label_fi=None, cta_label_vi=None, cta2_label_fi=None, cta2_label_vi=None):
    conn = get_connection()
    cur = conn.execute("""
        INSERT INTO carousel_slides
            (carousel_key, title, subtitle, badge, image, cta_label, cta_url, cta_style, cta2_label, cta2_url, cta2_style, sort_order, is_active,
             title_fi, title_vi, subtitle_fi, subtitle_vi, badge_fi, badge_vi, cta_label_fi, cta_label_vi, cta2_label_fi, cta2_label_vi)
        VALUES ('homepage', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (title, subtitle, badge, image, cta_label, cta_url, cta_style, cta2_label, cta2_url, cta2_style, sort_order,
          title_fi, title_vi, subtitle_fi, subtitle_vi, badge_fi, badge_vi, cta_label_fi, cta_label_vi, cta2_label_fi, cta2_label_vi))
    conn.commit()
    slide_id = cur.lastrowid
    conn.close()
    return slide_id


def update_homepage_slide(slide_id, title, subtitle, badge, image, cta_label, cta_url, cta_style, cta2_label, cta2_url, cta2_style, is_active,
                          title_fi=None, title_vi=None, subtitle_fi=None, subtitle_vi=None, badge_fi=None, badge_vi=None,
                          cta_label_fi=None, cta_label_vi=None, cta2_label_fi=None, cta2_label_vi=None):
    conn = get_connection()
    conn.execute("""
        UPDATE carousel_slides
        SET title = ?, subtitle = ?, badge = ?, image = ?, cta_label = ?, cta_url = ?, cta_style = ?,
            cta2_label = ?, cta2_url = ?, cta2_style = ?, is_active = ?,
            title_fi = ?, title_vi = ?, subtitle_fi = ?, subtitle_vi = ?, badge_fi = ?, badge_vi = ?,
            cta_label_fi = ?, cta_label_vi = ?, cta2_label_fi = ?, cta2_label_vi = ?
        WHERE id = ?
    """, (title, subtitle, badge, image, cta_label, cta_url, cta_style, cta2_label, cta2_url, cta2_style, is_active,
          title_fi, title_vi, subtitle_fi, subtitle_vi, badge_fi, badge_vi, cta_label_fi, cta_label_vi, cta2_label_fi, cta2_label_vi,
          slide_id))
    conn.commit()
    conn.close()


def create_offer_slide(title, subtitle, badge, image, cta_label, cta_url, cta_style, sort_order,
                       title_fi=None, title_vi=None, subtitle_fi=None, subtitle_vi=None,
                       badge_fi=None, badge_vi=None, cta_label_fi=None, cta_label_vi=None):
    conn = get_connection()
    cur = conn.execute("""
        INSERT INTO carousel_slides
            (carousel_key, title, subtitle, badge, image, cta_label, cta_url, cta_style, sort_order, is_active,
             title_fi, title_vi, subtitle_fi, subtitle_vi, badge_fi, badge_vi, cta_label_fi, cta_label_vi)
        VALUES ('dashboard_offers', ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (title, subtitle, badge, image, cta_label, cta_url, cta_style, sort_order,
          title_fi, title_vi, subtitle_fi, subtitle_vi, badge_fi, badge_vi, cta_label_fi, cta_label_vi))
    conn.commit()
    slide_id = cur.lastrowid
    conn.close()
    return slide_id


def update_offer_slide(slide_id, title, subtitle, badge, image, cta_label, cta_url, cta_style, is_active,
                       title_fi=None, title_vi=None, subtitle_fi=None, subtitle_vi=None,
                       badge_fi=None, badge_vi=None, cta_label_fi=None, cta_label_vi=None):
    conn = get_connection()
    conn.execute("""
        UPDATE carousel_slides
        SET title = ?, subtitle = ?, badge = ?, image = ?, cta_label = ?, cta_url = ?, cta_style = ?, is_active = ?,
            title_fi = ?, title_vi = ?, subtitle_fi = ?, subtitle_vi = ?, badge_fi = ?, badge_vi = ?, cta_label_fi = ?, cta_label_vi = ?
        WHERE id = ?
    """, (title, subtitle, badge, image, cta_label, cta_url, cta_style, is_active,
          title_fi, title_vi, subtitle_fi, subtitle_vi, badge_fi, badge_vi, cta_label_fi, cta_label_vi, slide_id))
    conn.commit()
    conn.close()


def delete_carousel_slide(slide_id):
    conn = get_connection()
    conn.execute("DELETE FROM carousel_slides WHERE id = ?", (slide_id,))
    conn.commit()
    conn.close()


def get_mission_slides():
    conn = get_connection()
    placeholders = ",".join("?" * len(MISSION_SLOT_KEYS))
    rows = conn.execute(
        f"""SELECT * FROM carousel_slides
            WHERE carousel_key = 'loyalty_missions' AND slot_key IN ({placeholders})
            ORDER BY sort_order ASC""",
        MISSION_SLOT_KEYS
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_mission_slide(slot_key, icon, title, pts_label, image, title_fi=None, title_vi=None):
    conn = get_connection()
    conn.execute("""
        UPDATE carousel_slides
        SET icon = ?, title = ?, pts_label = ?, image = ?, title_fi = ?, title_vi = ?
        WHERE carousel_key = 'loyalty_missions' AND slot_key = ?
    """, (icon, title, pts_label, image, title_fi, title_vi, slot_key))
    conn.commit()
    conn.close()


def reorder_carousel_slides(order):
    """order: list of (sort_order, id) tuples."""
    conn = get_connection()
    conn.executemany("UPDATE carousel_slides SET sort_order = ? WHERE id = ?", order)
    conn.commit()
    conn.close()
