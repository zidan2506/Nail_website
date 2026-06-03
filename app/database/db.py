import sqlite3
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

# Thêm vào app/database/db.py

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
