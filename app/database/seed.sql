INSERT INTO service_categories (name, slug, is_active, sort_order)
VALUES
('Manicure', 'manicure', 1, 1),
('Pedicure', 'pedicure', 1, 2),
('Nail Art', 'nail_art', 1, 3);

INSERT INTO services (category_id, name, description, duration_minutes, price)
VALUES
(1, 'Classic Manicure', 'Basic nail care and polish', 45, 25),
(1, 'Gel Manicure', 'Long-lasting gel polish', 60, 35),
(2, 'Spa Pedicure', 'Relaxing foot care treatment', 75, 45);

INSERT INTO staff (full_name, email, phone, hourly_rate, commission_rate, user_id)
VALUES
('Anna Nguyen', 'anna@example.com', '0401234567', 18, 10, NULL),
('Linh Tran', 'linh@example.com', '0402345678', 19, 12, NULL),
('Mon', 'mon@staff.com', '0399222999', 999, 999, 2);

INSERT INTO customers (user_id, full_name, email, phone, notes)
VALUES
(3, 'Mon', 'mon@customer.com', '0409998888', 'Test customer');

INSERT INTO users (password_hash, email, role)
VALUES
("scrypt:32768:8:1$WjbfcQVhEJ2iH7Cu$ac3742bf7abcdf8fca4cb76fdbd2d4d6bb5e16e603750d0f57602c503cca37ba1c6e4cf0b9b8250925f94156936c3f36c593ee77467ae461e684d0218e6d8d04","mon@admin.com", "admin" ),
("scrypt:32768:8:1$WjbfcQVhEJ2iH7Cu$ac3742bf7abcdf8fca4cb76fdbd2d4d6bb5e16e603750d0f57602c503cca37ba1c6e4cf0b9b8250925f94156936c3f36c593ee77467ae461e684d0218e6d8d04","mon@staff.com", "staff" ),
("scrypt:32768:8:1$eyrwAm1eM5x8ogfP$ecf8bf2a308643a63aee46c6eb3af307d3b93dd046cf8fd9623daa4266ca8f4490ab107a5311bb1a63ada539bae8d98daa4e9ccc32a95968f60b441a16581ac9","mon@customer.com", "customer" );


-- ============================================
-- 30 BOOKINGS for customer_id = 1
-- Insert order: 22 completed FIRST (id 1-22) → 4 cancelled (23-26) → 2 pending (27-28) → 2 confirmed (29-30)
-- ============================================
INSERT INTO bookings (customer_id, staff_id, service_id, booking_date, start_time, end_time, status, notes)
VALUES
-- ===== id 1-22: completed (sẽ có invoice) =====
-- Dates rải từ 2024-03 đến 2026-05 để test date filter

-- Old dates (>1 year ago, để filter "Last year" loại)
(1, 1, 1, "2024-03-15", "10:00", "10:45", "completed", "Visa paid"),
(1, 2, 2, "2024-05-20", "14:00", "15:00", "completed", "Mastercard paid"),
(1, 3, 3, "2024-07-08", "09:00", "10:15", "completed", "Mobile pay paid"),
(1, 1, 2, "2024-09-12", "11:00", "12:00", "completed", "Apple pay paid"),

-- Within last year, > 3 months ago
(1, 2, 1, "2024-11-25", "13:30", "14:15", "completed", "Google pay refunded"),
(1, 3, 3, "2025-01-18", "15:00", "16:15", "completed", "Cash paid"),
(1, 1, 1, "2025-02-14", "10:00", "10:45", "completed", "Bank transfer paid"),
(1, 2, 2, "2025-03-22", "14:30", "15:30", "completed", "Visa pending"),

-- Within last 3 months, > 30 days ago (giả sử current ~ May 2026)
(1, 3, 3, "2025-04-10", "09:00", "10:15", "completed", "Mastercard paid"),
(1, 1, 2, "2025-05-19", "11:00", "12:00", "completed", "Mobile pay refunded"),
(1, 2, 1, "2025-07-08", "13:00", "13:45", "completed", "Apple pay paid"),
(1, 3, 3, "2025-08-15", "15:00", "16:15", "completed", "Google pay paid"),
(1, 1, 1, "2025-09-20", "10:00", "10:45", "completed", "Cash paid"),
(1, 2, 2, "2025-10-12", "14:00", "15:00", "completed", "Bank transfer refunded"),
(1, 3, 3, "2025-11-25", "09:30", "10:45", "completed", "Visa paid"),
(1, 1, 2, "2025-12-18", "11:00", "12:00", "completed", "Mastercard paid"),

-- Within last 3 months (Feb-May 2026)
(1, 2, 1, "2026-02-22", "13:30", "14:15", "completed", "Mobile pay paid"),
(1, 3, 3, "2026-03-15", "15:00", "16:15", "completed", "Apple pay paid"),
(1, 1, 1, "2026-04-05", "10:00", "10:45", "completed", "Google pay pending"),
(1, 2, 2, "2026-04-20", "14:00", "15:00", "completed", "Cash paid"),

-- Within last 30 days
(1, 3, 2, "2026-05-08", "11:00", "12:00", "completed", "Visa paid"),
(1, 1, 3, "2026-05-22", "09:00", "10:15", "completed", "Mastercard pending"),


-- ===== id 23-26: cancelled =====
(1, 1, 1, "2024-08-15", "10:00", "10:45", "cancelled", "Customer cancelled - old"),
(1, 2, 2, "2025-06-20", "14:00", "15:00", "cancelled", "Staff unavailable"),
(1, 3, 3, "2026-01-12", "09:00", "10:15", "cancelled", "Customer cancelled"),
(1, 1, 2, "2026-05-15", "11:00", "12:00", "cancelled", "Cancelled last minute"),


-- ===== id 27-28: pending (chưa diễn ra) =====
(1, 2, 1, "2026-06-20", "13:00", "13:45", "pending", "Awaiting confirmation"),
(1, 3, 2, "2026-07-10", "10:00", "11:00", "pending", "New booking"),


-- ===== id 29-30: confirmed (chưa diễn ra) =====
(1, 1, 3, "2026-06-25", "14:00", "15:15", "confirmed", "Upcoming visit"),
(1, 2, 1, "2026-07-05", "11:00", "11:45", "confirmed", "Birthday treat");


-- ============================================
-- INVOICES for 22 completed bookings (id 1-22)
-- Phân bổ:
--   visa: 4, mastercard: 4, mobile_pay: 3, apple_pay: 3, google_pay: 3, cash: 3, bank_transfer: 2
--   paid: 14, refunded: 5, pending: 3
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
-- REVIEWS: ~12 đã review, 10 chưa review
-- Reviewed bookings: 1, 2, 4, 6, 9, 11, 13, 15, 16, 17, 20, 21
-- Not reviewed: 3, 5, 7, 8, 10, 12, 14, 18, 19, 22
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