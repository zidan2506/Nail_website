DROP TABLE IF EXISTS carousel_slides;
DROP TABLE IF EXISTS reward_redemptions;
DROP TABLE IF EXISTS referrals;
DROP TABLE IF EXISTS loyalty_points_log;
DROP TABLE IF EXISTS loyalty_config;
DROP TABLE IF EXISTS rewards;
DROP TABLE IF EXISTS customer_memberships;
DROP TABLE IF EXISTS membership_tiers;
DROP TABLE IF EXISTS reviews;
DROP TABLE IF EXISTS invoices;
DROP TABLE IF EXISTS bookings;
DROP TABLE IF EXISTS customers;
DROP TABLE IF EXISTS services;
DROP TABLE IF EXISTS service_categories;
DROP TABLE IF EXISTS staff;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS email_verifications;
DROP TABLE IF EXISTS gallery_images;

CREATE TABLE service_categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    name_fi TEXT,
    name_vi TEXT,
    slug TEXT NOT NULL UNIQUE,
    is_active INTEGER NOT NULL DEFAULT 1,
    sort_order INTEGER NOT NULL DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE services (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    name_fi TEXT,
    name_vi TEXT,
    description TEXT,
    description_fi TEXT,
    description_vi TEXT,
    duration_minutes INTEGER NOT NULL,
    price REAL NOT NULL,
    points INTEGER NOT NULL DEFAULT 0,
    is_active INTEGER NOT NULL DEFAULT 1,
    image TEXT DEFAULT NULL,
    badge TEXT DEFAULT NULL,
    icon TEXT NOT NULL DEFAULT 'spa',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (category_id) REFERENCES service_categories(id)
);

CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    password_hash TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    role TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 0,
    oauth_provider TEXT DEFAULT NULL,
    oauth_sub TEXT DEFAULT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE staff (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    full_name TEXT NOT NULL,
    email TEXT NOT NULL,
    phone TEXT NOT NULL,
    hourly_rate REAL DEFAULT 0,
    commission_rate REAL DEFAULT 0,
    role TEXT DEFAULT NULL,
    photo TEXT DEFAULT NULL,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE customers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NULL,
    full_name TEXT NOT NULL,
    email TEXT NOT NULL,
    phone TEXT,
    notes TEXT,
    date_of_birth DATE,
    is_verified INTEGER NOT NULL DEFAULT 0,
    stripe_customer_id TEXT DEFAULT NULL,
    avatar TEXT DEFAULT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE bookings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL,
    staff_id INTEGER NOT NULL,
    service_id INTEGER NOT NULL,
    booking_date DATE NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    status TEXT NOT NULL DEFAULT 'unverified',
    notes TEXT,
    payment_method TEXT DEFAULT 'cash',
    cancellation_reason TEXT,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    staff_commission REAL DEFAULT 0,
    staff_hourly_earning REAL DEFAULT 0,
    staff_total_earning REAL DEFAULT 0,

    FOREIGN KEY (customer_id) REFERENCES customers(id),
    FOREIGN KEY (staff_id) REFERENCES staff(id),
    FOREIGN KEY (service_id) REFERENCES services(id)
);

CREATE TABLE email_verifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    verification_code TEXT NOT NULL,
    verification_type TEXT NOT NULL,
    reference_id INTEGER,
    expired_at DATETIME NOT NULL,
    last_sent_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    verified_at DATETIME,
    is_used INTEGER NOT NULL DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE invoices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    booking_id INTEGER NOT NULL UNIQUE,
    invoice_number TEXT NOT NULL UNIQUE,
    amount REAL NOT NULL,
    payment_method TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'paid',
    issued_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (booking_id) REFERENCES bookings(id)
);

CREATE TABLE reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    booking_id INTEGER NOT NULL UNIQUE,
    customer_id INTEGER NOT NULL,
    rating INTEGER NOT NULL CHECK(rating BETWEEN 1 AND 5),
    comment TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (booking_id) REFERENCES bookings(id),
    FOREIGN KEY (customer_id) REFERENCES customers(id)
);

CREATE TABLE membership_tiers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    price REAL NOT NULL,
    point_multiplier REAL NOT NULL DEFAULT 1.0,
    duration_days INTEGER NOT NULL,
    description TEXT,
    is_active INTEGER NOT NULL DEFAULT 1,
    stripe_price_id TEXT DEFAULT NULL,     -- Stripe recurring Price (monthly); NULL cho tier miễn phí (Silver)
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE customer_memberships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL,
    tier_id INTEGER NOT NULL,
    started_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at DATETIME NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1,
    stripe_subscription_id TEXT DEFAULT NULL,      -- NULL = cấp tay (admin/free); có giá trị = subscription Stripe
    subscription_status TEXT DEFAULT NULL,         -- 'active' | 'past_due' | 'canceled' | NULL (cấp tay); dùng để cảnh báo khi past_due
    cancel_at_period_end INTEGER NOT NULL DEFAULT 0,

    FOREIGN KEY (customer_id) REFERENCES customers(id),
    FOREIGN KEY (tier_id) REFERENCES membership_tiers(id)
);

CREATE TABLE rewards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    name_fi TEXT,
    name_vi TEXT,
    cost INTEGER NOT NULL,
    description TEXT,
    description_fi TEXT,
    description_vi TEXT,
    banner_image TEXT DEFAULT NULL,
    is_active INTEGER NOT NULL DEFAULT 1,
    max_redeems_per_customer INTEGER DEFAULT NULL,
    cooldown_days INTEGER DEFAULT NULL,
    stock INTEGER DEFAULT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE loyalty_points_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL,
    points INTEGER NOT NULL,
    source TEXT NOT NULL,
    reference_id INTEGER,
    note TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (customer_id) REFERENCES customers(id)
);

CREATE TABLE reward_redemptions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL,
    reward_id INTEGER NOT NULL,
    points_spent INTEGER NOT NULL,
    voucher_code TEXT NOT NULL UNIQUE,
    is_used INTEGER NOT NULL DEFAULT 0,
    redeemed_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (customer_id) REFERENCES customers(id),
    FOREIGN KEY (reward_id) REFERENCES rewards(id)
);

CREATE TABLE referrals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    referrer_customer_id INTEGER NOT NULL,
    referred_customer_id INTEGER NOT NULL,
    points_awarded INTEGER NOT NULL DEFAULT 0,
    is_completed INTEGER NOT NULL DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (referrer_customer_id) REFERENCES customers(id),
    FOREIGN KEY (referred_customer_id) REFERENCES customers(id)
);

CREATE TABLE loyalty_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT NOT NULL UNIQUE,
    value TEXT NOT NULL,
    description TEXT,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE carousel_slides (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    carousel_key TEXT NOT NULL,          -- 'homepage' | 'dashboard_offers' | 'loyalty_missions'
    slot_key TEXT,                       -- loyalty_missions only: 'first_booking' | 'review' | 'referral' (fixed set)
    reward_id INTEGER,                   -- dashboard_offers only
    title TEXT,                          -- homepage
    title_fi TEXT,
    title_vi TEXT,
    subtitle TEXT,                       -- homepage
    subtitle_fi TEXT,
    subtitle_vi TEXT,
    badge TEXT,                          -- homepage
    badge_fi TEXT,
    badge_vi TEXT,
    icon TEXT,                           -- loyalty_missions
    pts_label TEXT,                      -- loyalty_missions
    image TEXT,                          -- homepage + loyalty_missions (uploaded filename)
    cta_label TEXT,
    cta_label_fi TEXT,
    cta_label_vi TEXT,
    cta_url TEXT,
    cta_style TEXT DEFAULT 'primary',
    cta2_label TEXT,                     -- homepage secondary button
    cta2_label_fi TEXT,
    cta2_label_vi TEXT,
    cta2_url TEXT,
    cta2_style TEXT DEFAULT 'outline',
    sort_order INTEGER NOT NULL DEFAULT 0,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (reward_id) REFERENCES rewards(id)
);

CREATE TABLE gallery_images (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    image_url TEXT NOT NULL,
    alt_text TEXT,
    alt_text_fi TEXT,
    alt_text_vi TEXT,
    sort_order INTEGER NOT NULL DEFAULT 0,
    is_active INTEGER NOT NULL DEFAULT 1,
    uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_reviews_booking_id ON reviews(booking_id);
CREATE INDEX idx_reviews_customer_id ON reviews(customer_id);
CREATE INDEX idx_invoices_booking_id ON invoices(booking_id);
CREATE INDEX idx_customers_user_id ON customers(user_id);
CREATE INDEX idx_bookings_customer_id ON bookings(customer_id);
CREATE INDEX idx_bookings_staff_date ON bookings(staff_id, booking_date);
CREATE INDEX idx_bookings_status ON bookings(status);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_customers_email ON customers(email);
CREATE INDEX idx_loyalty_log_customer_id ON loyalty_points_log(customer_id);
CREATE INDEX idx_customer_memberships_customer_id ON customer_memberships(customer_id);
-- Mỗi Stripe subscription chỉ 1 dòng (NULL vẫn cho nhiều dòng cấp tay). Chống race fallback+webhook.
CREATE UNIQUE INDEX idx_cm_stripe_sub ON customer_memberships(stripe_subscription_id);
CREATE INDEX idx_carousel_slides_key ON carousel_slides(carousel_key);