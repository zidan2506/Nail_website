-- ============================================
-- SERVICE CATEGORIES
-- ============================================
INSERT INTO service_categories (name, slug, is_active, sort_order)
VALUES
('Manicure', 'manicure', 1, 1),
('Pedicure', 'pedicure', 1, 2),
('Nail Art', 'nail_art', 1, 3);

-- ============================================
-- SERVICES (có thêm points)
-- Classic Manicure → 50 pts
-- Gel Manicure     → 80 pts
-- Spa Pedicure     → 120 pts
-- ============================================
INSERT INTO services (category_id, name, description, duration_minutes, price, points, image, badge, icon)
VALUES
(1, 'Classic Manicure', 'Basic nail care and polish',   45, 25,  50, 'Classic Manicure.png', NULL,      'spa'),
(1, 'Gel Manicure',     'Long-lasting gel polish',      60, 35,  80, 'Classic Manicure.png', 'Popular', 'auto_awesome'),
(2, 'Spa Pedicure',     'Relaxing foot care treatment', 75, 45, 120, 'Classic Manicure.png', NULL,      'spa');

-- ============================================
-- USERS
-- id=1 admin | id=2 staff | id=3 customer
-- ============================================
INSERT INTO users (password_hash, email, role)
VALUES
("scrypt:32768:8:1$E79PFmE43XkwUaoJ$bb50aad268e09a79c72b68f2fec4e1d84cd02810fefff942c1b31da4bb1d883bc91848a80c528efce3ad8e75e8dbde0ab5a1a376196866d5bcd7b014536b2b5b", "mon@admin.com",    "admin"),
("scrypt:32768:8:1$E79PFmE43XkwUaoJ$bb50aad268e09a79c72b68f2fec4e1d84cd02810fefff942c1b31da4bb1d883bc91848a80c528efce3ad8e75e8dbde0ab5a1a376196866d5bcd7b014536b2b5b", "mon@staff.com",    "staff"),
("scrypt:32768:8:1$E79PFmE43XkwUaoJ$bb50aad268e09a79c72b68f2fec4e1d84cd02810fefff942c1b31da4bb1d883bc91848a80c528efce3ad8e75e8dbde0ab5a1a376196866d5bcd7b014536b2b5b", "mon@customer.com", "customer");

-- ============================================
-- STAFF
-- ============================================
INSERT INTO staff (full_name, email, phone, hourly_rate, commission_rate, role, photo, user_id)
VALUES
('Anna Nguyen', 'anna@example.com', '0401234567', 18,  10,  'Senior Technician',      'https://lh3.googleusercontent.com/aida-public/AB6AXuC_aUwdcEjZaXxhz9CKBX_Akg0aZKCkOIqBYabE-RmqLJgvE53yNsextuAXNWEIdkwzVR9g-X-56Yc1iAONr8oWR92LPY6EcE9EFNcUs8S3-Ba4umXv_35t9rldlcsB911C8CcDfBFqNkiz6bxqonqaAf3GMasT7hxxmQeqjUpW87lI7KhC4Qm3zqA8uYNBNC9q1LvbtwVez1pwcXLWTk-_6awd2M1MLX_dcD9BLKsIBO99IdLwC4IkCXhJt6s0W5iidVxfsRgnRlDa', NULL),
('Linh Tran',   'linh@example.com', '0402345678', 19,  12,  'Nail Art Specialist',    'https://lh3.googleusercontent.com/aida-public/AB6AXuA6kDWLDB5ofX-pgm-4hToDyFGEz7PYg30SPjO5dlAZlISo1Jt4wXRbo_mUF7Giumm9Dc_Q_3IQ0y76FS23Fj_TrjrddUpKfsZZG78YEkzu7u4pzuGWqvcTyQMseBp6FpgjWgNzRiYMZZJ_N1xX5mBuNR1fTZI5iV2p9PU30YZdGhPeZ9KRfFYjWTHv6NwTa37d2aqwZLsxQdEvWmgtLquJK97klBkKdY9hKJswVS8MIMRIE35NGVaHB6z8rCXppGsCA9605nFt_Hmr', NULL),
('Mon',         'mon@staff.com',    '0399222999', 999, 999, 'Founder & Lead Artist', 'https://lh3.googleusercontent.com/aida-public/AB6AXuCLw5WTYptIBZdjI5TCk8iwKUBvmaDy6rQmqxHl4K9fqijP8-nkzmlZCbpIF8MwTPse9wWLu6aMVc4Zg6FvlSUyt0gtkDwqptdYoHzlq6h7TSB1HX-rfFI_8yVkzu09Y1CfS9czTFQlcB7zj9ja4CeIlzdCN4gy88HuNbokPnojWu48_kM7OVG9J52dJ0hDcPQ32ibxGFFFkIei8kM2tYDv-IIsFwAFYlAcWqbXeR5raq2JmTmNCKpUocLx8TXPq931ZM_3Tu0CnYtQ', 2);

-- ============================================
-- CUSTOMERS (có thêm date_of_birth)
-- ============================================
INSERT INTO customers (user_id, full_name, email, phone, notes, date_of_birth)
VALUES
(3, 'Mon', 'mon@customer.com', '0409998888', 'Test customer', '1998-06-15');

-- ============================================
-- MEMBERSHIP TIERS
-- id=1 Silver | id=2 Gold | id=3 VIP
-- ============================================
INSERT INTO membership_tiers (name, price, point_multiplier, duration_days, description, is_active)
VALUES
('Silver',  0.00,  1.0, 365, 'Basic membership - standard points earning',       1),
('Gold',   49.99,  1.5, 365, 'Gold membership - 1.5x points on all bookings',    1),
('Diamond', 99.99,  2.0, 365, 'Diamond membership - 2x points + exclusive perks', 1);

-- ============================================
-- CUSTOMER MEMBERSHIPS
-- Mon đang là Gold (tier_id=2)
-- ============================================
INSERT INTO customer_memberships (customer_id, tier_id, started_at, expires_at, is_active)
VALUES
(1, 2, '2026-01-01 00:00:00', '2026-12-31 23:59:59', 1);

-- ============================================
-- REWARDS (sorted by cost asc)
-- ============================================
-- max_redeems_per_customer | cooldown_days | stock
INSERT INTO rewards (name, cost, description, is_active, max_redeems_per_customer, cooldown_days, stock)
VALUES
('Free Nail Art (2 nails)',  300,  'Complimentary nail art on 2 nails of your choice', 1, 5,    7,   NULL),
('Free Classic Manicure',   600,  'One free Classic Manicure session',                 1, 3,    7,   5),
('Free Gel Manicure',       1000, 'One free Gel Manicure session',                     1, 4,    7,   6),
('Free Spa Pedicure',       1500, 'One free Spa Pedicure session',                     1, NULL, 7, 10),
('Free Luxury Treatment',   2500, 'One free premium treatment of your choice',         1, 1,    7, 3),
('VIP Day Package',         4000, 'Full day of premium nail treatments',               1, 1,    7, 2);

-- ============================================
-- CAROUSEL SLIDES
-- homepage: migrated from the old hardcoded _CAROUSEL_SLIDES list in routes.py
-- dashboard_offers: independent slides (same shape as homepage, minus cta2),
--   seeded here with content copied from the 3 cheapest rewards to replicate
--   the old "top 3 active rewards" default — NOT linked to the rewards table
-- loyalty_missions: fixed 3 slots (slot_key), cosmetic-only, matched to the
--   award_points() call sites in the booking flow — see MISSION_KEYS in db.py
-- ============================================
INSERT INTO carousel_slides (carousel_key, slot_key, reward_id, title, subtitle, badge, icon, pts_label, image, cta_label, cta_url, cta_style, cta2_label, cta2_url, cta2_style, sort_order, is_active)
VALUES
('homepage', NULL, NULL, 'Your nails, perfectly cared.', 'Premium nail care & art services crafted just for you. Experience the intersection of precision and relaxation.', 'New season collection', NULL, NULL,
 'https://lh3.googleusercontent.com/aida-public/AB6AXuBdLs7y_erczKwTFAkkULT1a042tLNhFZGl9Ah7tK1zkNUMr0o9u-X8GVtruUJ8m-Kajy88JyX1pSLbZlovykcDs0Rxw67LR_aip4hxOtv-IGtso02wXGW7UX54KpBWBoe2H-wZStp_ArLDpO8BzT-8iTORkuh4yO39_AKE-kN4J9NFmdwpo1vkJiAbAJb_5wQy0bJv5B_gUha00oYboCESO-c5MCJ0gc7fZnXL1YkzurU2-V5iWdq_K_X3i_nrZXwOKzVhewpDx6Ti',
 'Book Now', '/public/booking', 'primary', 'Explore Services', '/services', 'outline', 1, 1),
('homepage', NULL, NULL, 'Your nails, perfectly cared.', 'Premium nail care & art services crafted just for you. Experience the intersection of precision and relaxation.', 'New season collection', NULL, NULL,
 '/static/images/Homepage_Carousel_Slides/slide_2.jpg',
 'Book Now', '/public/booking', 'primary', 'Explore Services', '/services', 'outline', 2, 1),
('homepage', NULL, NULL, 'Your nails, perfectly cared.', 'Premium nail care & art services crafted just for you. Experience the intersection of precision and relaxation.', 'New season collection', NULL, NULL,
 '/static/images/Homepage_Carousel_Slides/slide_3.jpg',
 'Book Now', '/public/booking', 'primary', 'Explore Services', '/services', 'outline', 3, 1),

('dashboard_offers', NULL, NULL, 'Free Nail Art (2 nails)', 'Complimentary nail art on 2 nails of your choice', '✦ Loyalty Reward', NULL, NULL, NULL,
 'Redeem for 300 pts', '/customer/loyalty-points', 'primary', NULL, NULL, 'outline', 1, 1),
('dashboard_offers', NULL, NULL, 'Free Classic Manicure', 'One free Classic Manicure session', '✦ Loyalty Reward', NULL, NULL, NULL,
 'Redeem for 600 pts', '/customer/loyalty-points', 'primary', NULL, NULL, 'outline', 2, 1),
('dashboard_offers', NULL, NULL, 'Free Gel Manicure', 'One free Gel Manicure session', '✦ Loyalty Reward', NULL, NULL, NULL,
 'Redeem for 1000 pts', '/customer/loyalty-points', 'primary', NULL, NULL, 'outline', 3, 1),

('loyalty_missions', 'review',        NULL, 'Write a Review',              NULL, NULL, '⭐', '+50 pts',  '/static/images/customer/Loyalty Points/leave_review.png',   NULL, NULL, 'primary', NULL, NULL, 'outline', 1, 1),
('loyalty_missions', 'referral',      NULL, 'Refer a Friend',              NULL, NULL, '👥', '+200 pts', '/static/images/customer/Loyalty Points/invite_friends.png', NULL, NULL, 'primary', NULL, NULL, 'outline', 2, 1),
('loyalty_missions', 'first_booking', NULL, 'Book Your First Appointment', NULL, NULL, '📅', '+100 pts', '/static/images/customer/Loyalty Points/first_visit.png',    NULL, NULL, 'primary', NULL, NULL, 'outline', 3, 1);

-- ============================================
-- LOYALTY CONFIG
-- ============================================
INSERT INTO loyalty_config (key, value, description)
VALUES
('review_bonus',        '50',  'Points awarded for writing a review'),
('birthday_bonus',      '100', 'Points awarded during birthday month'),
('first_booking_bonus', '99', 'Points awarded on first completed booking'),
('streak_bonus',        '100', 'Points awarded for booking 3 months in a row'),
('referral_bonus',      '200', 'Points awarded when referred friend completes first booking'),
('double_points_day',   '2',   'Day of week for double points: 1=Mon 2=Tue 3=Wed 4=Thu 5=Fri 6=Sat 7=Sun');

-- ============================================
-- BOOKINGS
-- 22 done | 4 cancelled | 2 pending | 2 confirmed | 2 in-progress
-- ============================================
INSERT INTO bookings (customer_id, staff_id, service_id, booking_date, start_time, end_time, status, notes, payment_method)
VALUES
-- id 1-22: done (payment_method khớp với invoice tương ứng bên dưới)
(1, 1, 1, '2024-03-15', '10:00', '10:45', 'done', 'Visa paid', 'visa'),
(1, 2, 2, '2024-05-20', '14:00', '15:00', 'done', 'Mastercard paid', 'mastercard'),
(1, 3, 3, '2024-07-08', '09:00', '10:15', 'done', 'Mobile pay paid', 'mobile_pay'),
(1, 1, 2, '2024-09-12', '11:00', '12:00', 'done', 'Apple pay paid', 'apple_pay'),
(1, 2, 1, '2024-11-25', '13:30', '14:15', 'done', 'Google pay refunded', 'google_pay'),
(1, 3, 3, '2025-01-18', '15:00', '16:15', 'done', 'Cash paid', 'cash'),
(1, 1, 1, '2025-02-14', '10:00', '10:45', 'done', 'Bank transfer paid', 'bank_transfer'),
(1, 2, 2, '2025-03-22', '14:30', '15:30', 'done', 'Visa pending', 'visa'),
(1, 3, 3, '2025-04-10', '09:00', '10:15', 'done', 'Mastercard paid', 'mastercard'),
(1, 1, 2, '2025-05-19', '11:00', '12:00', 'done', 'Mobile pay refunded', 'mobile_pay'),
(1, 2, 1, '2025-07-08', '13:00', '13:45', 'done', 'Apple pay paid', 'apple_pay'),
(1, 3, 3, '2025-08-15', '15:00', '16:15', 'done', 'Google pay paid', 'google_pay'),
(1, 1, 1, '2025-09-20', '10:00', '10:45', 'done', 'Cash paid', 'cash'),
(1, 2, 2, '2025-10-12', '14:00', '15:00', 'done', 'Bank transfer refunded', 'bank_transfer'),
(1, 3, 3, '2025-11-25', '09:30', '10:45', 'done', 'Visa paid', 'visa'),
(1, 1, 2, '2025-12-18', '11:00', '12:00', 'done', 'Mastercard paid', 'mastercard'),
(1, 2, 1, '2026-02-22', '13:30', '14:15', 'done', 'Mobile pay paid', 'mobile_pay'),
(1, 3, 3, '2026-03-15', '15:00', '16:15', 'done', 'Apple pay paid', 'apple_pay'),
(1, 1, 1, '2026-04-05', '10:00', '10:45', 'done', 'Google pay pending', 'google_pay'),
(1, 2, 2, '2026-04-20', '14:00', '15:00', 'done', 'Cash paid', 'cash'),
(1, 3, 2, '2026-05-08', '11:00', '12:00', 'done', 'Visa paid', 'visa'),
(1, 1, 3, '2026-05-22', '09:00', '10:15', 'done', 'Mastercard pending', 'mastercard'),

-- id 23-26: cancelled
(1, 1, 1, '2024-08-15', '10:00', '10:45', 'cancelled', 'Customer cancelled - old', 'cash'),
(1, 2, 2, '2025-06-20', '14:00', '15:00', 'cancelled', 'Staff unavailable', 'cash'),
(1, 3, 3, '2026-01-12', '09:00', '10:15', 'cancelled', 'Customer cancelled', 'cash'),
(1, 1, 2, '2026-05-15', '11:00', '12:00', 'cancelled', 'Cancelled last minute', 'cash'),

-- id 27-28: pending
(1, 2, 1, '2026-06-20', '13:00', '13:45', 'pending', 'Awaiting confirmation', 'cash'),
(1, 3, 2, '2026-07-10', '10:00', '11:00', 'pending',  'New booking', 'cash'),

-- id 29-30: confirmed
(1, 1, 3, '2026-06-25', '14:00', '15:15', 'confirmed', 'Upcoming visit', 'cash'),
(1, 2, 1, '2026-07-05', '11:00', '11:45', 'confirmed', 'Birthday treat', 'cash'),

-- id 31-32: in-progress (today 2026-07-01, no conflicts with existing staff slots)
(1, 1, 1, '2026-07-01', '09:00', '09:45', 'in-progress', 'Currently in session', 'cash'),
(1, 2, 3, '2026-07-01', '10:00', '11:15', 'in-progress', 'Session ongoing', 'cash');

-- ============================================
-- INVOICES (giữ nguyên)
-- ============================================
INSERT INTO invoices (booking_id, invoice_number, amount, payment_method, status)
VALUES
(1,  'INV-2024-0001', 25.00, 'visa',          'paid'),
(2,  'INV-2024-0002', 35.00, 'mastercard',    'paid'),
(3,  'INV-2024-0003', 45.00, 'mobile_pay',    'paid'),
(4,  'INV-2024-0004', 35.00, 'apple_pay',     'paid'),
(5,  'INV-2024-0005', 25.00, 'google_pay',    'refunded'),
(6,  'INV-2025-0006', 45.00, 'cash',          'paid'),
(7,  'INV-2025-0007', 25.00, 'bank_transfer', 'paid'),
(8,  'INV-2025-0008', 35.00, 'visa',          'pending'),
(9,  'INV-2025-0009', 45.00, 'mastercard',    'paid'),
(10, 'INV-2025-0010', 35.00, 'mobile_pay',    'refunded'),
(11, 'INV-2025-0011', 25.00, 'apple_pay',     'paid'),
(12, 'INV-2025-0012', 45.00, 'google_pay',    'paid'),
(13, 'INV-2025-0013', 25.00, 'cash',          'paid'),
(14, 'INV-2025-0014', 35.00, 'bank_transfer', 'refunded'),
(15, 'INV-2025-0015', 45.00, 'visa',          'paid'),
(16, 'INV-2025-0016', 35.00, 'mastercard',    'paid'),
(17, 'INV-2026-0017', 25.00, 'mobile_pay',    'paid'),
(18, 'INV-2026-0018', 45.00, 'apple_pay',     'refunded'),
(19, 'INV-2026-0019', 25.00, 'google_pay',    'pending'),
(20, 'INV-2026-0020', 35.00, 'cash',          'paid'),
(21, 'INV-2026-0021', 35.00, 'visa',          'paid'),
(22, 'INV-2026-0022', 35.00, 'mastercard',    'pending');

-- ============================================
-- REVIEWS (giữ nguyên)
-- ============================================
INSERT INTO reviews (booking_id, customer_id, rating, comment)
VALUES
(1,  1, 5, 'Amazing service! Will come back.'),
(2,  1, 4, 'Very good experience overall.'),
(4,  1, 5, 'Best manicure I have ever had.'),
(6,  1, 5, 'Loved the staff, super friendly.'),
(9,  1, 3, 'Decent but a bit rushed.'),
(11, 1, 5, 'Apple pay was so convenient!'),
(13, 1, 4, 'Cash payment hassle-free.'),
(15, 1, 5, 'Perfect nails for the holiday.'),
(16, 1, 4, 'Great gel manicure, lasted weeks.'),
(17, 1, 5, 'Mobile pay + great service = win.'),
(20, 1, 4, 'Solid pedicure, relaxing atmosphere.'),
(21, 1, 5, 'Quick, clean, and professional.');

-- ============================================
-- LOYALTY POINTS LOG
--
-- Gold tier multiplier = 1.5
-- service points:
--   service_id=1 (Classic) → 50 × 1.5 = 75
--   service_id=2 (Gel)     → 80 × 1.5 = 120
--   service_id=3 (Spa)     → 120 × 1.5 = 180
--
-- Booking map (service_id → points):
--   1→75, 2→120, 3→180, 4→120, 5→75,
--   6→180, 7→75, 8→120, 9→180, 10→120,
--   11→75, 12→180, 13→75, 14→120, 15→180,
--   16→120, 17→75, 18→180, 19→75, 20→120,
--   21→120, 22→180
--
-- Subtotal bookings : 2,670
-- first_booking     :  +200
-- reviews (×12)     :  +600
-- birthday (×2)     :  +200
-- streak (×1)       :  +100
-- redeem            :  -600
-- TOTAL             : 3,170
-- Next reward       : Free Gel Manicure (1,000 pts) → already passed
--                     Free Spa Pedicure (1,500 pts) → already passed
--                     Free Luxury Treatment (2,500 pts) → already passed
--                     VIP Day Package (4,000 pts) → next! 3,170/4,000 = 79%
-- ============================================
INSERT INTO loyalty_points_log (customer_id, points, source, reference_id, note, created_at)
VALUES
-- first booking bonus
(1, 200, 'first_booking', 1,    'First booking bonus',              '2024-03-15 10:45:00'),

-- completed bookings
(1,  75, 'booking', 1,  'Classic Manicure × Gold (×1.5)',           '2024-03-15 10:45:00'),
(1, 120, 'booking', 2,  'Gel Manicure × Gold (×1.5)',               '2024-05-20 15:00:00'),
(1, 180, 'booking', 3,  'Spa Pedicure × Gold (×1.5)',               '2024-07-08 10:15:00'),
(1, 120, 'booking', 4,  'Gel Manicure × Gold (×1.5)',               '2024-09-12 12:00:00'),
(1,  75, 'booking', 5,  'Classic Manicure × Gold (×1.5)',           '2024-11-25 14:15:00'),
(1, 180, 'booking', 6,  'Spa Pedicure × Gold (×1.5)',               '2025-01-18 16:15:00'),
(1,  75, 'booking', 7,  'Classic Manicure × Gold (×1.5)',           '2025-02-14 10:45:00'),
(1, 120, 'booking', 8,  'Gel Manicure × Gold (×1.5)',               '2025-03-22 15:30:00'),
(1, 180, 'booking', 9,  'Spa Pedicure × Gold (×1.5)',               '2025-04-10 10:15:00'),
(1, 120, 'booking', 10, 'Gel Manicure × Gold (×1.5)',               '2025-05-19 12:00:00'),
(1,  75, 'booking', 11, 'Classic Manicure × Gold (×1.5)',           '2025-07-08 13:45:00'),
(1, 180, 'booking', 12, 'Spa Pedicure × Gold (×1.5)',               '2025-08-15 16:15:00'),
(1,  75, 'booking', 13, 'Classic Manicure × Gold (×1.5)',           '2025-09-20 10:45:00'),
(1, 120, 'booking', 14, 'Gel Manicure × Gold (×1.5)',               '2025-10-12 15:00:00'),
(1, 180, 'booking', 15, 'Spa Pedicure × Gold (×1.5)',               '2025-11-25 10:45:00'),
(1, 120, 'booking', 16, 'Gel Manicure × Gold (×1.5)',               '2025-12-18 12:00:00'),
(1,  75, 'booking', 17, 'Classic Manicure × Gold (×1.5)',           '2026-02-22 14:15:00'),
(1, 180, 'booking', 18, 'Spa Pedicure × Gold (×1.5)',               '2026-03-15 16:15:00'),
(1,  75, 'booking', 19, 'Classic Manicure × Gold (×1.5)',           '2026-04-05 10:45:00'),
(1, 120, 'booking', 20, 'Gel Manicure × Gold (×1.5)',               '2026-04-20 15:00:00'),
(1, 120, 'booking', 21, 'Gel Manicure × Gold (×1.5)',               '2026-05-08 12:00:00'),
(1, 180, 'booking', 22, 'Spa Pedicure × Gold (×1.5)',               '2026-05-22 10:15:00'),

-- review bonuses (12 reviews)
(1, 50, 'review', 1,  'Review bonus - booking #1',                  '2024-03-16 09:00:00'),
(1, 50, 'review', 2,  'Review bonus - booking #2',                  '2024-05-21 10:00:00'),
(1, 50, 'review', 4,  'Review bonus - booking #4',                  '2024-09-13 10:00:00'),
(1, 50, 'review', 6,  'Review bonus - booking #6',                  '2025-01-19 10:00:00'),
(1, 50, 'review', 9,  'Review bonus - booking #9',                  '2025-04-11 10:00:00'),
(1, 50, 'review', 11, 'Review bonus - booking #11',                 '2025-07-09 10:00:00'),
(1, 50, 'review', 13, 'Review bonus - booking #13',                 '2025-09-21 10:00:00'),
(1, 50, 'review', 15, 'Review bonus - booking #15',                 '2025-11-26 10:00:00'),
(1, 50, 'review', 16, 'Review bonus - booking #16',                 '2025-12-19 10:00:00'),
(1, 50, 'review', 17, 'Review bonus - booking #17',                 '2026-02-23 10:00:00'),
(1, 50, 'review', 20, 'Review bonus - booking #20',                 '2026-04-21 10:00:00'),
(1, 50, 'review', 21, 'Review bonus - booking #21',                 '2026-05-09 10:00:00'),

-- Admin Debug --
(1, 9999, 'admin', NULL, 'Admin debug',                 '2026-05-09 10:00:00'),

-- birthday bonus (tháng 6 = tháng sinh nhật Mon)
(1, 100, 'birthday', NULL, 'Birthday bonus - June 2024',            '2024-06-15 00:00:00'),
(1, 100, 'birthday', NULL, 'Birthday bonus - June 2025',            '2025-06-15 00:00:00'),

-- streak bonus (Jan → Feb → Mar 2025 liên tiếp)
(1, 100, 'streak', NULL, 'Streak bonus - 3 months Jan-Mar 2025',    '2025-03-22 15:30:00'),

-- redeem: đổi Free Gel Manicure (reward_id=3, cost=1000)
(1, -600, 'redeem', 3, 'Redeemed: Free Gel Manicure',               '2026-04-01 12:00:00');

-- ============================================
-- REWARD REDEMPTIONS
-- ============================================
INSERT INTO reward_redemptions (customer_id, reward_id, points_spent, voucher_code, is_used, redeemed_at)
VALUES
(1, 3, 600, 'DAHA-K7MN-2QXP', 0, '2026-04-01 12:00:00');

-- ============================================
-- GALLERY IMAGES
-- ============================================
INSERT INTO gallery_images (image_url, alt_text, sort_order)
VALUES
('https://lh3.googleusercontent.com/aida/AP1WRLsl-oCjb8RhXAeIEuB_eNHK2tFeQvd3wmgVOQpY88UPDJ37BFw-U3t-mLkh0Z6HgtiFqLplPaZL5YZP6gW0ABINPIeNUwBPyIEPzsdxG2gyd6EeYOpRa-EJa-NVjOHk4bySuqwuvFahqWVjOFQzF6ViuS4LSvleJGW8_bQESJ2hgMhW5ZYEyeg0nzEmSYC2uUQqYeu-z6CeQt7-NLWM5nKxvhYK9oF4HZpII1db0XmelxVmjNgi0vOAAzo', 'Close-up of polished gel manicure', 1),
('https://lh3.googleusercontent.com/aida/AP1WRLsNy0yLgd0coTdlPmjRkPHASeHleXdtaC2yTbdKqkilh96b47yjFXCqpFaovNiMkSZdhGuTYBAhSEM0jAuDSdLfNl5xcjDQ2IIgOIdOibCoUkv3Y8iPfJv5yEI02YDEUaT4Q3I1DDW7z--shWyt9ywUzsyFlfAmLqrdqWHMat7yluvED17sDc7BG_dTSUSrweZbYsLUFu-87RLMb74FKNPx726wS5jOq7k-Ur8VP_0oqlSenwpShBEC7LOH', 'Nail art studio session', 2),
('https://lh3.googleusercontent.com/aida/AP1WRLv8V_3DNk87h2pPBhNPKrg95sbPxyEAec70Je_D8nmPrO_Ld8mMgG4wFYK_USNMwbJuR_98yv3PHsYaJy49pxFZ8qzadr0rNCC1z-cY62PB30XKapHUdVCyju6oIJCq69j9v5KijLythFgb-mm29Uqs58_Un3J7ckI0L2MIkDWyaO961bvLW6POGFk0zh0yXQeGGys6qDbZDeo8Aj1ELAbg-XpKmP1jPQ7uPw91sYXIezIuaZAYk4rvz10', 'Macro shot of nail design detail', 3),
('https://lh3.googleusercontent.com/aida/AP1WRLsASQhDr3ZdZOalE4xeRT2BoAWEb8Bf0g1o2GX2v71FHpZI9XbxduTfw338P0tWuSirVqzWHTkd3NLLy0aJgOg7HAnRLVT1e9de92IHeoWmw7b-iej2tGlGrd306WQkUhq-jWffD4-lqG6JppMusfs_xoCYII1ngF8oOfcuPIIMKPaLUV-tp5wliQpT3m-jdXgODZgg507ZoM_w_eV1N1cAbowwPC-tKA425iqI-X6gvRHc8UoiXtzY2MSn', 'Salon interior detail shot', 4),
('https://lh3.googleusercontent.com/aida-public/AB6AXuC2c4ySum3S7Y99dttSJGXpx9PXsq7zEeBi-6yKJIjY2axoj0IX_CFFeD4E7CRmllmBDpSPYDnRQCW4EAsNiadiNp4iDNUJoZclmTdQWJVq1EspTFt-8Eo9oM_TuYHvMLfgAD0l1Qt2Pg2xpLTodak5J1sLNyr73eB3QgRHMjbE5O0BWXA3A9Y1joVtugkxiyC-tZSDjJpKUYD5Js6QKKMjkntd_85r-fZI-ytufLX06f5yOiNMc7Sn5sNlCFENXmv4a3xp4TTnxsuC', 'Almond-shaped nails with gold foil accents on blossom-pink silk', 5),
('https://lh3.googleusercontent.com/aida-public/AB6AXuA1_1ah9v8CXFtO9Gb2poXx5FSa4BywICbfdjZDi8MPn-YJhQhjWJ88sIyTDDma4WsdUPQt0wFoxOBRAp8FZkTz73C-KeZzPeQBhSKXdoQb5twG8BzkrtMVVYWfAW4ewll-CT-UQA7UUwOuqvq2D0-5AncUvi4yWNd50DudpdQx8vUJNQluYsDdij36hTs4pAs5Ygl9jazicjXQu2CDngpK2xFXKdPg99_ChQxd05IaWcgVqbueM4hfJrpSad3zmwu1HgsmeVZBXdc3', '3D sculpted rose nail art on deep plum base', 6),
('https://lh3.googleusercontent.com/aida-public/AB6AXuAgvQd7mN2M_f3eVNCTbmWWI_MR6_edcNzEFDNtp_h0o-KU68pF8fwHDPuEmaGb9qBREYuQdVpG-W81Loqcy043OzEYnvpRcL1kBsb1mlfR3NDV_JoNIBXL4WY2MsrOk5WV0vpnJeWNsKXzajcRQlscKSDx7ttiI9LW36AX2UQCMXwGKFFEWsaJ5Xc93XfzJBcH_NagAXOLOFUarQ07bvS1HITke-3avbm_ygh9GV8madO660hXkKZDa-1Ssymi1hKqxwLAGVdM_-Fp', 'Modern French tip manicure with blush pink base', 7),
('https://lh3.googleusercontent.com/aida-public/AB6AXuB3MaFKpVRnfTPWQuHJmvlwbtFXlCT0CETgsM9KTjw6imV7ggoqSxX6BR5VFlJrFXluOjAeKjVTJY24mHwX1MfhnE5IKFCj1OpsdbYrA2I9X1kJilUF-mtIuIHPzOKNF815sm86GMJcZ9Vi6QeyQEXU-KmDbwGxkfvjf3LvkQYoQH6HXcRqzAqAnDk6bCp-sh0Z5cQi3toMx_6VlcpAUGDh5yHc3vw1gOFxRZuq4lsqRYQlrarGgAcg9svtl-jOfR7Qgf3Yj7VvmTIW', 'Minimalist sheer nude manicure with single crystal accent', 8),
('https://lh3.googleusercontent.com/aida-public/AB6AXuDttvQceukXIqghQTa9U5wE6lAZ7lEa1DGZm_yJfB4zgxBsDnFA_y_7ppZAxetMpLS_PuFWW16qDRognQCjfR4tcG0G2fCK3Y1Ja0PjARHdh7gBH8PZEREJo_UyWG8R2DxlgrunnsE1O7BdDxEgbNBBTINUQPjfjN1Mr9Mu4zrAi92jKs3UgYdlxXDv6fDDEobNO2u7zb8npnPb11203oeFtCyj1SBu6dm7pgx-lgZwPAV28LG0-JKXqZAwARL7m2YN1oN40KY8sXhM', 'Glossy deep burgundy nails with cherry blossom branch', 9);