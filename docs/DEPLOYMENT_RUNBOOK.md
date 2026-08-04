# Deployment Runbook — VPS Ubuntu 24.04

Hướng dẫn deploy từ đầu lên VPS Linux. Chạy các lệnh theo đúng thứ tự.
**Giả định:** Ubuntu 24.04 LTS · path `/var/www/nail-app` · chạy dưới user riêng `nailapp` · gunicorn `127.0.0.1:8000` sau nginx.

> Ký hiệu: `# [local]` chạy ở máy bạn · còn lại chạy trên VPS (SSH vào). Thay `your-domain.com` bằng domain thật.

---

## 0. Chuẩn bị trước

**Nhà cung cấp VPS (gợi ý cho tiệm ở Phần Lan — gần + đúng GDPR):**
- **Hetzner** — có datacenter Helsinki, rẻ (~€4/tháng gói CX22, 2vCPU/4GB). Khuyến nghị.
- **UpCloud** — công ty Phần Lan, datacenter Helsinki.
- DigitalOcean / Vultr — không có Helsinki nhưng có Frankfurt/Amsterdam.

Gói nhỏ nhất (1–2 vCPU, 2–4GB RAM) là quá đủ cho site salon + SQLite.

**DNS:** trỏ `your-domain.com` (và `www`) về IP của VPS bằng record **A** (và AAAA nếu có IPv6). Chờ propagate trước khi chạy certbot (bước 9).

**✅ ProxyFix — đã có sẵn trong code, KHÔNG cần làm gì:** app dùng `url_for(..., _external=True)` cho Google OAuth callback + Stripe redirect. Sau nginx, Flask phải biết request là HTTPS, nếu không login Google sẽ vỡ (redirect_uri mismatch). Việc này do **ProxyFix** lo, và nó **đã nằm trong `app/__init__.py`** (dòng 4 và 37, xác nhận 2026-08-05). Chi tiết ở *Phụ lục A*. **Đừng thêm lần nữa** — bọc ProxyFix hai lần sẽ làm sai cách đọc `X-Forwarded-*`.


---

## 1. SSH vào VPS + cập nhật hệ thống

```bash
ssh root@YOUR_VPS_IP
apt update && apt upgrade -y
```

## 2. Cài package cần thiết

```bash
apt install -y python3-venv python3-pip nginx sqlite3 git certbot python3-certbot-nginx ffmpeg
```

> **`ffmpeg` là gói hệ điều hành, KHÔNG phải package Python.** Không có và không thể có trong `requirements.txt` (trên PyPI `ffmpeg-python` chỉ là lớp bọc và vẫn cần binary này; `ffmpeg` là package chết). App gọi nó qua `subprocess`.
>
> Dùng để transcode video minh hoạ dịch vụ mà admin upload: hạ về 720p kèm cờ `-movflags +faststart`. **Thiếu ffmpeg thì mọi upload video đều fail.**
>
> Vì sao bắt buộc: file test đo được 16 giây / 53MB / bitrate 26.6 Mbps; sau transcode 720p còn 3.2MB, nhẹ hơn 16 lần. Cờ `+faststart` dời box `moov` lên đầu file, thiếu nó thì trình duyệt phải tải hết file mới phát được.
>
> Xác nhận: `ffmpeg -version`

## 3. Tạo user riêng + firewall

```bash
# user hệ thống chạy app (không login, không quyền root)
adduser --system --group --home /var/www/nail-app nailapp

# firewall: chỉ mở SSH + web
apt install -y ufw
ufw allow OpenSSH
ufw allow 'Nginx Full'
ufw --force enable
```

## 4. Lấy code + tạo venv + cài dependencies

```bash
cd /var/www
git clone https://github.com/zidan2506/Nail_website.git nail-app

chmod o+x /var/www/nail-app
chmod o+x /var/www/nail-app/app
chmod o+x /var/www/nail-app/app/static
chmod -R o+r /var/www/nail-app/app/static

cd nail-app

python3 -m venv venv
./venv/bin/pip install --upgrade pip
./venv/bin/pip install -r requirements.txt
```

## 5. Tạo file `.env` production

`.env` KHÔNG nằm trong git — tạo tay trên server:

```bash
# sinh SECRET_KEY mới, mạnh (đừng dùng lại key ở local)
./venv/bin/python -c "import secrets; print(secrets.token_hex(32))"

nano /var/www/nail-app/.env
```

Nội dung `.env` production:
```
SECRET_KEY=your-strong-secret-key-here

GOOGLE_CLIENT_ID=your-google-client-id

GOOGLE_CLIENT_SECRET=your-google-client-secret

STRIPE_SECRET_KEY=sk_test_...

STRIPE_PUBLISHABLE_KEY=pk_test_...

STRIPE_WEBHOOK_SECRET=whsec_...

# Email gửi qua Resend API (https://resend.com) — cổng HTTPS, không bị host chặn như SMTP

RESEND_API_KEY=re_your_api_key

# 'from' phải thuộc domain đã verify trên Resend

MAIL_DEFAULT_SENDER=Misa Nails <noreply@your-domain.com>

# Để FALSE ở bước này. Lúc này chưa có HTTPS (certbot chạy ở bước 9), đặt true
# sớm sẽ khiến trình duyệt không gửi cookie qua http -> không đăng nhập được.
# Bước 9 sẽ quay lại đổi thành true.

SESSION_COOKIE_SECURE=false

# true ở local để auto-reload/debugger; KHÔNG set (hoặc false) ở production

FLASK_DEBUG=false

# Mức log: INFO (mặc định) cho production; DEBUG để bật log chi tiết tầng db

LOG_LEVEL=INFO
```

#### 5.1 Cách lấy GOOGLE_CLIENT_ID & GOOGLE_CLIENT_SECRET

1. Truy cập vào [Google Cloud Console](https://console.cloud.google.com/welcome?authuser=2&hl=en&project=dahacare-oauth)
2. Vào mục API & Service -> OAuth consent screen -> Clients -> Create Client
3. Select Web application (Mục Application Type)
4. Đặt tên (Mục Name)
5. Add URI (Mục Authorized redirect URIs) -> Paste Domain vào (Buộc phải có domain)
6. Ấn create xong thì sẽ popup modal thông tin -> Copy Client ID với Client Secret

#### 5.2 Cách lấy Stripe_keys

1. Truy cập vào [Stripe Dashboard](https://dashboard.stripe.com/)
2. Chỉnh sang chế độ sandbox nếu đang test/ Hoặc ấn vào Switch to live account nếu deploy
3. Ngay chỗ home sẽ có một khu vực API Keys -> Copy các keys vào

#### 5.3 Cách lấy RESEND_API_KEY & MAIL_DEFAULT_SENDER

> App gửi mail qua **Resend API** (HTTPS), **không** dùng SMTP/Gmail app password nữa. Xem `docs/EMAIL_RESEND_MIGRATION.md`.
> `app/config.py` **raise `RuntimeError` khi thiếu `RESEND_API_KEY` hoặc `MAIL_DEFAULT_SENDER`**, nên đặt sai hai biến này thì app không khởi động nổi.

1. Đăng ký [resend.com](https://resend.com) → **API Keys** → tạo key mới, dạng `re_...` → điền vào `RESEND_API_KEY`.
2. **Domains → Add Domain** → thêm domain thật → Resend đưa vài bản ghi DNS (SPF/DKIM) → thêm vào DNS → chờ verify.
3. `MAIL_DEFAULT_SENDER` phải là địa chỉ **thuộc domain đã verify**, đúng dạng `Name <email@domain>`:
   ```
   MAIL_DEFAULT_SENDER=Misa Nails <noreply@your-domain.com>
   ```

> **Test nhanh khi chưa kịp verify domain:** đặt tạm `MAIL_DEFAULT_SENDER=onboarding@resend.dev`, nhưng chỉ gửi được tới email của chính chủ tài khoản Resend.

Lỗi thường gặp: `401` sai/thiếu API key · `403` domain chưa verify · `422` sai định dạng `from`/`to`.

## 6. Khởi tạo database

Init bằng 1 lệnh duy nhất (`app/init_db.py`):

```bash
cd /var/www/nail-app
# tạo schema (bảng rỗng)
./venv/bin/python -m app.init_db
```

**Quyết định về dữ liệu ban đầu** (`seed.sql` chứa CẢ data tham chiếu lẫn data demo giả):

- **Cách A — sạch (khuyến nghị khi launch thật):** chỉ chạy `init_db` ở trên, rồi tự thêm services / categories / staff / membership tiers / rewards qua trang admin. DB không dính booking/khách giả.
- **Cách B — nhanh:** nạp thêm seed để có sẵn mọi thứ, rồi XOÁ data giao dịch giả trước khi mở cho khách:
  ```bash
  ./venv/bin/python -m app.init_db --seed   # schema + seed.sql
  # xoá data demo, GIỮ lại data tham chiếu (services/staff/tiers/rewards...)
  sqlite3 app/database/database.db "DELETE FROM bookings; DELETE FROM invoices; DELETE FROM reviews; DELETE FROM reward_redemptions; DELETE FROM loyalty_points_log; DELETE FROM customer_memberships; DELETE FROM customers; DELETE FROM users WHERE role='customer';"
  ```
  > Kiểm tra lại danh sách bảng cần xoá cho khớp nhu cầu trước khi chạy.

Phân quyền file cho user app:
```bash
chown -R nailapp:nailapp /var/www/nail-app
```

## 7. systemd service (gunicorn tự chạy + tự restart)

```bash
cp /var/www/nail-app/deploy/nail-app.service /etc/systemd/system/nail-app.service
systemctl daemon-reload
systemctl enable --now nail-app
systemctl status nail-app        # kiểm tra active (running)
```
Nếu lỗi: `journalctl -u nail-app -n 50 --no-pager`.
Ấn q để thoát chế độ preview

## 8. nginx reverse proxy

```bash
cp /var/www/nail-app/deploy/nginx-nail-app.conf /etc/nginx/sites-available/nail-app
# SỬA server_name trong file thành domain thật:
# SỬA LUÔN client_max_body_size: 10M -> 300M (xem ghi chú bên dưới)
nano /etc/nginx/sites-available/nail-app

ln -s /etc/nginx/sites-available/nail-app /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default   # bỏ trang mặc định
nginx -t && systemctl reload nginx
```
Giờ vào `http://your-domain.com` phải thấy site (chưa HTTPS).

> **`client_max_body_size` phải là `300M`.** File `deploy/nginx-nail-app.conf` để mặc định `10M` (chỉ đủ cho ảnh). Video thô 1080p60 từ điện thoại khoảng 150MB, giữ nguyên `10M` thì nginx chặn ngay từ đầu và admin nhận lỗi `413 Request Entity Too Large`.
>
> Không cần đụng `gunicorn.conf.py`: nginx mặc định buffer toàn bộ request body rồi mới đẩy sang gunicorn, nên upload chậm **không** bị `timeout = 60` giết.

## 9. HTTPS bằng Let's Encrypt

```bash
certbot --nginx -d your-domain.com -d www.your-domain.com
```
Certbot tự sửa nginx thêm HTTPS + redirect 80→443, và tự gia hạn (cron sẵn).

**Giờ mới đổi `SESSION_COOKIE_SECURE`** (ở bước 5 nó đang là `false` vì chưa có HTTPS):
```bash
nano /var/www/nail-app/.env      # SESSION_COOKIE_SECURE=false -> true
systemctl restart nail-app
```
Vào `https://your-domain.com` kiểm tra khoá xanh.

## 10. Stripe (live)

1. Dashboard Stripe → bật **live mode** → lấy `pk_live_...` / `sk_live_...` → cập nhật `.env`.
2. Developers → Webhooks → **Add endpoint**: `https://your-domain.com/<đường-dẫn-webhook>` (kiểm tra route webhook trong `routes.py`). Chọn events cần (checkout/subscription). Lấy **Signing secret** `whsec_...` → điền `STRIPE_WEBHOOK_SECRET` trong `.env`.
3. Tạo price live:
   ```bash
   cd /var/www/nail-app
   ./venv/bin/python -m app.database.setup_stripe_prices
   ```
4. `systemctl restart nail-app`.

## 11. Google OAuth (production)

Google Cloud Console → OAuth client → **Authorized redirect URIs** → thêm:
```
https://your-domain.com/auth/google/callback
```
(đường dẫn = route `main.google_callback` trong `routes.py`). Không cần đổi client id/secret nếu dùng lại client cũ.

## 12. Cron backup DB

```bash
chmod +x /var/www/nail-app/deploy/backup-db.sh
crontab -e
# thêm dòng: chạy 3h sáng mỗi ngày
0 3 * * * /var/www/nail-app/deploy/backup-db.sh >> /var/log/nail-backup.log 2>&1
```
> Backup nằm cùng VPS. Để an toàn hơn nên copy định kỳ ra nơi khác (S3/rsync) — tùy chọn.

---

## Deploy bản cập nhật sau này

```bash
cd /var/www/nail-app
sudo -u nailapp git pull
sudo -u nailapp ./venv/bin/pip install -r requirements.txt   # nếu deps đổi
sudo -u nailapp sqlite3 app/database/database.db "<ALTER TABLE nếu có cột mới>"   # xem bên dưới
systemctl restart nail-app
```

### ⚠️ Migration: `git pull` KHÔNG tự thêm cột

DB không bị đụng khi deploy (đã untrack khỏi git từ Phase 1). Đó là điều tốt cho dữ liệu, nhưng kéo theo hệ quả: **`schema.sql` chỉ áp dụng khi khởi tạo DB mới**, DB production đã có dữ liệu thật nên không bao giờ đọc lại file đó.

Nghĩa là mỗi khi code mới thêm cột, phải ALTER tay trên server **trước khi** `systemctl restart`. Bỏ qua thì app sập với `sqlite3.OperationalError: no such column: ...`.

Cột đã thêm cần chạy trên server (tính đến 2026-08-05) — **cả 3 cột, thiếu cột nào cũng sập**:

```bash
cd /var/www/nail-app
sqlite3 app/database/database.db "
ALTER TABLE services ADD COLUMN video_url    TEXT DEFAULT NULL;
ALTER TABLE services ADD COLUMN video_status TEXT DEFAULT NULL;
ALTER TABLE services ADD COLUMN video_error  TEXT DEFAULT NULL;
"
```

| Cột | Dùng làm gì |
|---|---|
| `video_url` | Tên file trong `uploads/videos/` hoặc URL CDN. Chỉ được ghi khi transcode xong |
| `video_status` | `NULL` / `processing` / `ready` / `failed` |
| `video_error` | Thông báo lỗi hiện cho admin khi `failed` |

Kiểm tra trước khi chạy để khỏi ALTER trùng (chạy lại sẽ báo `duplicate column name`, không phá dữ liệu nhưng script sẽ dừng giữa chừng):
```bash
sqlite3 app/database/database.db "PRAGMA table_info(services);" | grep video
```
Kỳ vọng thấy đủ 3 dòng `video_url`, `video_status`, `video_error`. Nếu đã có sẵn một phần thì chỉ chạy `ALTER` cho những cột còn thiếu.

> **Sau khi restart, kiểm tra ngay:** mở `/admin/services` và `/services`. Thiếu cột thì cả hai trang sập với `sqlite3.OperationalError: no such column`.

---

## Phụ lục A — ProxyFix (✅ đã áp dụng, chỉ để tham khảo)

Trong `app/__init__.py`:
```python
from werkzeug.middleware.proxy_fix import ProxyFix
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)
```
Để Flask tin `X-Forwarded-Proto` từ nginx → `url_for(_external=True)` sinh URL `https://` đúng cho Google OAuth + Stripe.

**Đã có trong code** (`app/__init__.py:4` và `:37`, xác nhận 2026-08-05). Mục này chỉ để giải thích cơ chế, **không phải việc cần làm**. Thêm lần thứ hai sẽ bọc ProxyFix chồng lên nhau và làm sai số hop khi đọc `X-Forwarded-For`.

## Phụ lục B — Checklist nhanh

- [ ] DNS A record trỏ về VPS
- [x] ~~ProxyFix~~ đã có sẵn trong code, không cần làm (Phụ lục A)
- [ ] `.env` production: SECRET_KEY mới, Stripe **live**, `RESEND_API_KEY` + `MAIL_DEFAULT_SENDER` (mục 5.3)
- [ ] `SESSION_COOKIE_SECURE=true` — **chỉ đổi sau khi có HTTPS ở bước 9**, không phải ở bước 5
- [ ] systemd `nail-app` active + enable
- [ ] nginx `nginx -t` pass, HTTPS ok
- [ ] Stripe webhook + `setup_stripe_prices` chạy trên live
- [ ] Google OAuth redirect URI production
- [ ] Cron backup chạy
- [ ] `ffmpeg -version` chạy được (bước 2) — thiếu thì upload video fail
- [ ] nginx `client_max_body_size 300M` (bước 8) — thiếu thì upload video lỗi 413
- [ ] ALTER TABLE đủ **3** cột video (`video_url`, `video_status`, `video_error`) trước khi restart (xem mục Migration)
