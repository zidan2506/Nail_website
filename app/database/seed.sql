-- ============================================
-- SEED — dữ liệu tối thiểu để chạy server + default.
-- Cột gốc (name/description/alt_text) = English; _fi = Suomi; _vi = Tiếng Việt.
-- KHÔNG chứa data giao dịch demo (bookings/invoices/reviews/loyalty/customers).
-- ============================================

-- ============================================================
-- SEED: service_categories
-- DahaCare Nail Salon
-- Prices incl. 25.5% VAT | Points: 1 EUR = 1 point
-- ============================================================

-- ------------------------------------------------------------
-- service_categories
-- ------------------------------------------------------------
INSERT INTO service_categories (name, name_vi, name_fi, slug, sort_order, is_active) VALUES
    ('Manicure',  'Làm móng tay',  'Manikyyri',   'manicure',  1, 1),
    ('Pedicure',  'Làm móng chân', 'Pedikyyrі',   'pedicure',  2, 1),
    ('Nail Art',  'Nghệ thuật móng','Kynsikoristelu', 'nail-art', 3, 1);

-- services: xem seed_services.sql (chạy bằng --seed-services)

-- ============================================
-- USERS — admin (id=1) + staff (id=2) để đăng nhập.
-- ⚠️ Production: đổi email + mật khẩu trước khi mở cho khách.
-- ============================================
INSERT INTO users (password_hash, email, role)
VALUES
("scrypt:32768:8:1$E79PFmE43XkwUaoJ$bb50aad268e09a79c72b68f2fec4e1d84cd02810fefff942c1b31da4bb1d883bc91848a80c528efce3ad8e75e8dbde0ab5a1a376196866d5bcd7b014536b2b5b", "mon@admin.com", "admin"),
("scrypt:32768:8:1$E79PFmE43XkwUaoJ$bb50aad268e09a79c72b68f2fec4e1d84cd02810fefff942c1b31da4bb1d883bc91848a80c528efce3ad8e75e8dbde0ab5a1a376196866d5bcd7b014536b2b5b", "mon@staff.com", "staff");

-- ============================================
-- STAFF — chỉ Mon, gắn với tài khoản staff (user_id=2)
-- ============================================
INSERT INTO staff (full_name, email, phone, hourly_rate, commission_rate, role, photo, user_id)
VALUES
('Mon', 'mon@staff.com', '0399222999', 20, 10, 'Founder & Lead Artist', NULL, 2);

-- ============================================
-- MEMBERSHIP TIERS — id=1 Silver | id=2 Gold | id=3 Diamond
-- (Silver = tier mặc định của khách mới trong code)
-- ============================================
INSERT INTO membership_tiers (name, price, point_multiplier, duration_days, description, is_active)
VALUES
('Silver',  0.00, 1.0, 365, 'Basic membership - standard points earning',       1),
('Gold',   49.99, 1.5, 365, 'Gold membership - 1.5x points on all bookings',    1),
('Diamond', 99.99, 2.0, 365, 'Diamond membership - 2x points + exclusive perks', 1);

-- ============================================
-- REWARDS — 1 reward test (các cột không phải name để default, tự chỉnh sau)
-- max_redeems_per_customer | cooldown_days | stock
-- ============================================
INSERT INTO rewards (name, cost, description, is_active, max_redeems_per_customer, cooldown_days, stock)
VALUES
('Test', 100, 'Test reward', 1, NULL, 7, NULL);

-- ============================================
-- CAROUSEL SLIDES
-- homepage: slide mặc định trang chủ
-- dashboard_offers: offer mặc định (nội dung theo 3 reward rẻ nhất)
-- loyalty_missions: 3 slot cố định (slot_key) — khớp MISSION_KEYS trong db.py, BẮT BUỘC giữ
-- ============================================
INSERT INTO carousel_slides (
    carousel_key, slot_key, reward_id,
    title, title_fi, title_vi,
    subtitle, subtitle_fi, subtitle_vi,
    badge, badge_fi, badge_vi,
    icon, pts_label, image,
    cta_label, cta_label_fi, cta_label_vi, cta_url, cta_style,
    cta2_label, cta2_label_fi, cta2_label_vi, cta2_url, cta2_style,
    sort_order, is_active)
VALUES
-- homepage (3 slide, mỗi slide 1 ảnh + nội dung riêng)
('homepage', NULL, NULL,
 'Every detail, done right.', 'Jokainen yksityiskohta kohdallaan.', 'Chỉn chu trong từng chi tiết.',
 'Salon-grade gel, freshly sterilised tools and a technician who takes the time your nails deserve.',
 'Ammattilaatuinen geeli, tuoreesti steriloidut työvälineet ja teknikko, jolla on aikaa juuri sinun kynsillesi.',
 'Gel chuẩn salon, dụng cụ tiệt trùng trước mỗi lượt và kỹ thuật viên dành trọn thời gian cho bộ móng của bạn.',
 'Sterilised tools, every guest', 'Steriloidut työvälineet, joka kerta', 'Dụng cụ tiệt trùng cho từng khách',
 NULL, NULL, '/static/images/Default/Homepage_Carousel_Slides/homepage-slide-1.webp',
 'Book Now', 'Varaa nyt', 'Đặt lịch ngay', '/public/booking', 'primary',
 'Explore Services', 'Tutustu palveluihin', 'Khám phá dịch vụ', '/services', 'outline',
 1, 1),
('homepage', NULL, NULL,
 'A calm space, made for you.', 'Rauhallinen tila, tehty sinua varten.', 'Không gian thư thái, dành riêng cho bạn.',
 'Step in, settle into the chair and let the day slow down. Your slot is reserved — no queue, no rush.',
 'Astu sisään, asetu tuoliin ja anna päivän hidastua. Aikasi on varattu — ei jonoa, ei kiirettä.',
 'Bước vào, ngả lưng vào ghế và để nhịp ngày chậm lại. Giờ hẹn đã được giữ sẵn — không xếp hàng, không vội vã.',
 'Welcome to MisaNails', 'Tervetuloa MisaNails', 'Chào mừng đến MisaNails',
 NULL, NULL, '/static/images/Default/Homepage_Carousel_Slides/homepage-slide-2.webp',
 'Book your visit', 'Varaa käyntisi', 'Đặt lịch hẹn', '/public/booking', 'primary',
 'About the salon', 'Tietoa salongista', 'Về salon', '/about', 'outline',
 2, 1),
('homepage', NULL, NULL,
 'From classic care to bold nail art.', 'Klassisesta hoidosta rohkeaan kynsitaiteeseen.', 'Từ chăm sóc cơ bản đến nail art ấn tượng.',
 'Nine services across manicure, pedicure and nail art. Pick the look — we take care of the rest.',
 'Yhdeksän palvelua manikyyristä ja pedikyyristä kynsitaiteeseen. Valitse tyyli — me hoidamme loput.',
 'Chín dịch vụ trải từ manicure, pedicure đến nail art. Bạn chọn phong cách — phần còn lại để chúng tôi lo.',
 'Manicure · Pedicure · Nail art', 'Manikyyri · Pedikyyri · Kynsitaide', 'Manicure · Pedicure · Vẽ móng',
 NULL, NULL, '/static/images/Default/Homepage_Carousel_Slides/homepage-slide-3.webp',
 'See services & prices', 'Katso palvelut ja hinnat', 'Xem dịch vụ & bảng giá', '/services', 'primary',
 'View our work', 'Katso töitämme', 'Xem tác phẩm', '/gallery', 'outline',
 3, 1),

-- dashboard_offers (badge chung, nội dung theo 3 reward)
('dashboard_offers', NULL, NULL,
 'Free Nail Art (2 nails)', 'Ilmainen kynsitaide (2 kynttä)', 'Vẽ móng nghệ thuật miễn phí (2 móng)',
 'Complimentary nail art on 2 nails of your choice', 'Ilmainen kynsitaide kahteen valitsemaasi kynteen', 'Vẽ nghệ thuật miễn phí trên 2 móng bạn chọn',
 '✦ Loyalty Reward', '✦ Kanta-asiakaspalkinto', '✦ Phần thưởng thành viên',
 NULL, NULL, NULL,
 'Redeem for 300 pts', 'Lunasta 300 pisteellä', 'Đổi bằng 300 điểm', '/customer/loyalty-points', 'primary',
 NULL, NULL, NULL, NULL, 'outline',
 1, 1),
('dashboard_offers', NULL, NULL,
 'Free Classic Manicure', 'Ilmainen klassinen manikyyri', 'Manicure cổ điển miễn phí',
 'One free Classic Manicure session', 'Yksi ilmainen klassinen manikyyri', 'Một buổi Manicure cổ điển miễn phí',
 '✦ Loyalty Reward', '✦ Kanta-asiakaspalkinto', '✦ Phần thưởng thành viên',
 NULL, NULL, NULL,
 'Redeem for 600 pts', 'Lunasta 600 pisteellä', 'Đổi bằng 600 điểm', '/customer/loyalty-points', 'primary',
 NULL, NULL, NULL, NULL, 'outline',
 2, 1),
('dashboard_offers', NULL, NULL,
 'Free Gel Manicure', 'Ilmainen geelimanikyyri', 'Manicure gel miễn phí',
 'One free Gel Manicure session', 'Yksi ilmainen geelimanikyyri', 'Một buổi Manicure gel miễn phí',
 '✦ Loyalty Reward', '✦ Kanta-asiakaspalkinto', '✦ Phần thưởng thành viên',
 NULL, NULL, NULL,
 'Redeem for 1000 pts', 'Lunasta 1000 pisteellä', 'Đổi bằng 1000 điểm', '/customer/loyalty-points', 'primary',
 NULL, NULL, NULL, NULL, 'outline',
 3, 1),

-- loyalty_missions (chỉ title dịch; slot cố định, BẮT BUỘC giữ)
('loyalty_missions', 'review', NULL,
 'Write a Review', 'Kirjoita arvostelu', 'Viết đánh giá',
 NULL, NULL, NULL,
 NULL, NULL, NULL,
 '⭐', '+50 pts', '/static/images/customer/Loyalty Points/leave_review.png',
 NULL, NULL, NULL, NULL, 'primary',
 NULL, NULL, NULL, NULL, 'outline',
 1, 1),
('loyalty_missions', 'referral', NULL,
 'Refer a Friend', 'Suosittele ystävälle', 'Giới thiệu bạn bè',
 NULL, NULL, NULL,
 NULL, NULL, NULL,
 '👥', '+200 pts', '/static/images/customer/Loyalty Points/invite_friends.png',
 NULL, NULL, NULL, NULL, 'primary',
 NULL, NULL, NULL, NULL, 'outline',
 2, 1),
('loyalty_missions', 'first_booking', NULL,
 'Book Your First Appointment', 'Varaa ensimmäinen aikasi', 'Đặt lịch hẹn đầu tiên',
 NULL, NULL, NULL,
 NULL, NULL, NULL,
 '📅', '+100 pts', '/static/images/customer/Loyalty Points/first_visit.png',
 NULL, NULL, NULL, NULL, 'primary',
 NULL, NULL, NULL, NULL, 'outline',
 3, 1);

-- ============================================
-- LOYALTY CONFIG
-- ============================================
INSERT INTO loyalty_config (key, value, description)
VALUES
('review_bonus',        '50',  'Points awarded for writing a review'),
('birthday_bonus',      '100', 'Points awarded during birthday month'),
('first_booking_bonus', '99',  'Points awarded on first completed booking'),
('streak_bonus',        '100', 'Points awarded for booking 3 months in a row'),
('referral_bonus',      '200', 'Points awarded when referred friend completes first booking'),
('double_points_day',   '2',   'Day of week for double points: 1=Mon 2=Tue 3=Wed 4=Thu 5=Fri 6=Sat 7=Sun');

-- ============================================
-- GALLERY IMAGES — 5 ảnh default (trong static/uploads/gallery/, tên file trần)
-- ============================================
INSERT INTO gallery_images (image_url, alt_text, alt_text_fi, alt_text_vi, sort_order)
VALUES
('68deb1dcc79944f8ba590860234fb197.jpg', 'Nail art showcase 1', 'Kynsitaidenäyte 1', 'Ảnh nghệ thuật móng 1', 1),
('7fb1420550b64d2488836e1ed3ec5bab.jpg', 'Nail art showcase 2', 'Kynsitaidenäyte 2', 'Ảnh nghệ thuật móng 2', 2),
('8813eb56408c4b85871cb1f9b9d9dcd9.jpg', 'Nail art showcase 3', 'Kynsitaidenäyte 3', 'Ảnh nghệ thuật móng 3', 3),
('910bbeb3f5ab463b8a923e714a581ae2.jpg', 'Nail art showcase 4', 'Kynsitaidenäyte 4', 'Ảnh nghệ thuật móng 4', 4),
('9c972f000433436bb56db8ff506f99ba.jpg', 'Nail art showcase 5', 'Kynsitaidenäyte 5', 'Ảnh nghệ thuật móng 5', 5);
