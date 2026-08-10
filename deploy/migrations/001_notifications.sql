-- =============================================================================
-- 001_notifications.sql  ·  Feature "Notification from admin"
-- =============================================================================
-- schema.sql CHỈ dùng khi khởi tạo DB mới (nó mở đầu bằng DROP TABLE). DB
-- production đã có dữ liệu thật nên không bao giờ đọc lại file đó, phải chạy
-- migration này bằng tay trước khi restart app. Xem docs/DEPLOYMENT_PLAN.md.
--
--   sqlite3 /var/www/nail-app/app/database/database.db < deploy/migrations/001_notifications.sql
--
-- An toàn khi chạy lại nhiều lần: mọi lệnh đều IF NOT EXISTS. Riêng ALTER TABLE
-- không có IF NOT EXISTS trong SQLite, nên hai cột email_* nằm ở cuối file và
-- sẽ báo "duplicate column name" nếu chạy lần hai. Lỗi đó vô hại, bỏ qua được.
-- =============================================================================

-- Dòng thông báo chạy ngang ở public pages.
CREATE TABLE IF NOT EXISTS public_notices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message TEXT NOT NULL,
    message_fi TEXT,
    message_vi TEXT,
    is_active INTEGER NOT NULL DEFAULT 1,
    sort_order INTEGER NOT NULL DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Tin gửi vào hòm thư customer. 1 broadcast = 1 dòng, KHÔNG fan-out.
CREATE TABLE IF NOT EXISTS customer_notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    target TEXT NOT NULL DEFAULT 'all',
    customer_id INTEGER,
    title TEXT NOT NULL,
    title_fi TEXT,
    title_vi TEXT,
    body TEXT NOT NULL,
    body_fi TEXT,
    body_vi TEXT,
    emailed INTEGER NOT NULL DEFAULT 0,
    email_sent INTEGER DEFAULT NULL,
    email_total INTEGER DEFAULT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (customer_id) REFERENCES customers(id)
);

-- Ai đã đọc tin nào. Vắng dòng = chưa đọc.
CREATE TABLE IF NOT EXISTS notification_reads (
    notification_id INTEGER NOT NULL,
    customer_id INTEGER NOT NULL,
    read_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (notification_id, customer_id),
    FOREIGN KEY (notification_id) REFERENCES customer_notifications(id) ON DELETE CASCADE,
    FOREIGN KEY (customer_id) REFERENCES customers(id)
);

CREATE INDEX IF NOT EXISTS idx_public_notices_active ON public_notices(is_active, sort_order);
CREATE INDEX IF NOT EXISTS idx_cust_notif_target ON customer_notifications(target, customer_id);

-- ---------------------------------------------------------------------------
-- Chỉ chạy hai dòng dưới nếu customer_notifications đã tồn tại TỪ TRƯỚC bản
-- này (tức DB đã chạy bản migration đầu, chưa có hai cột email_*). DB mới tạo
-- bởi chính file này đã có sẵn hai cột, chạy lại sẽ báo duplicate column.
-- ---------------------------------------------------------------------------
-- ALTER TABLE customer_notifications ADD COLUMN email_sent INTEGER DEFAULT NULL;
-- ALTER TABLE customer_notifications ADD COLUMN email_total INTEGER DEFAULT NULL;
