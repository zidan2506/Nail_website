# Pre-Production Checklist — Nail Booking Web App

**Cập nhật:** 2026-07-17 · **Stack:** Flask + SQLite · gunicorn + nginx (VPS Linux)

Danh sách kiểm tra trước khi deploy production. Ưu tiên các điểm **chưa được cover** trong `DEPLOYMENT_PLAN.md`.

---

## 🔴 Ưu tiên cao (dễ gây sự cố thật khi có tải)

### 1. SQLite concurrency — rủi ro "database is locked" — ✅ ĐÃ XỬ LÝ (2026-07-17)
`app/database/db.py` — `get_connection()` giờ set `timeout=5` + các PRAGMA. Verified: journal_mode=wal, busy_timeout=5000, synchronous=NORMAL.

- [x] Bật `PRAGMA journal_mode=WAL`
- [x] `PRAGMA busy_timeout=5000` + `sqlite3.connect(..., timeout=5)`
- [x] `PRAGMA synchronous=NORMAL`
- [x] ✅ **gitignore:** đã thêm `*.db-wal` `*.db-shm` (WAL tạo 2 file runtime này).

### 2. Stripe chuyển sang LIVE mode
- [ ] Đổi `sk_test_`/`pk_test_` → `sk_live_`/`pk_live_` trong `.env` server
- [ ] Tạo webhook endpoint trên Stripe Dashboard → `https://domain/payment/webhook`
- [ ] Lấy `STRIPE_WEBHOOK_SECRET` **live** (khác test)
- [ ] Chạy `python -m app.database.setup_stripe_prices` trên môi trường live (price ID test ≠ live)
- [ ] Test 1 giao dịch thật + xác nhận webhook `checkout.session.completed` về đúng

### 3. Google OAuth redirect URI
- [ ] Thêm `https://domain/...callback` (domain thật, HTTPS) vào Authorized redirect URIs trong Google Cloud Console — nếu quên, login fail hoàn toàn

---

## 🟡 Ưu tiên trung bình

### 4. Biến môi trường production
- [ ] `SECRET_KEY` = chuỗi random mạnh (không dùng lại giá trị dev)
- [ ] `SESSION_COOKIE_SECURE=true` (**chỉ sau khi** đã có HTTPS)
- [ ] `FLASK_DEBUG=false`, `LOG_LEVEL=INFO`
- [ ] `MAIL_PASSWORD` = Gmail **App Password** (không phải mật khẩu thường)

### 5. Hai TODO trong luồng booking — ✅ ĐÃ XỬ LÝ (2026-07-17)
Kết luận: 2 TODO là comment **stale** — logic đã implement ngay bên dưới. Luồng reschedule **có** check slot trống (chặn đặt trùng giờ) và **có** gọi `update_booking_schedule`. Đã xoá 2 comment thừa.

- [x] Xác nhận không thiếu logic check slot (reschedule an toàn, không double-booking)
- [x] Xoá 2 comment stale ở `routes.py`

**Nợ kỹ thuật:**
- [x] ✅ Giờ làm việc `09:00`–`18:00` + bước slot 30' → gom về **1 nguồn duy nhất**: hằng `BUSINESS_OPEN`/`BUSINESS_CLOSE`/`SLOT_STEP_MINUTES` trong `booking_service.py`, dùng làm default của `get_available_slots`; đã bỏ 3 tham số thừa ở 4 lời gọi trong `routes.py`. Verified: kết quả slot không đổi.
- [ ] ⏭️ Race condition TOCTOU giữa check slot và update — **quyết định KHÔNG fix**: xác suất ~0 với tiệm nhỏ, fix thật cần lock/guard tầng DB → thêm phức tạp/rủi ro cho thứ chưa từng xảy ra. Có sẵn `check_booking_conflict` nếu sau này lưu lượng tăng cần siết.

### 6. Auto-expire booking chạy lazy — ✅ QUYẾT ĐỊNH: GIỮ NGUYÊN (2026-07-17)
`auto_expire_bookings` flip booking quá hạn → `no-show` bằng 1 UPDATE quét toàn bộ. Gọi lazy ở 3 trang staff/admin (`routes.py:1785, 2142, 2242`).

- [x] Đã đánh giá: **self-healing** — mỗi lần admin/staff mở dashboard, mọi booking quá hạn được flip ngay. Tiệm mở dashboard thường xuyên → expire diễn ra gần liên tục. Không phải bug, không chặn go-live.
- Khe hở nhỏ (cosmetic): trang phía khách **không** gọi hàm này → nếu lâu không ai mở dashboard, khách có thể thấy booking quá hạn tạm hiện `confirmed`. Tự đúng lại khi staff mở dashboard. Không ảnh hưởng tiền/booking.
- ⏭️ **Không thêm scheduler lúc này** (systemd timer) — giải pháp thừa cho vấn đề gần như vô hại ở quy mô tiệm nhỏ. Cân nhắc lại nếu sau này lưu lượng tăng.

### 7. Backup DB
- [ ] `deploy/backup-db.sh` đã có → cài **cron** thật trên server
- [ ] Test restore thử 1 lần

---

## 🟢 Kiểm tra nhanh

- [ ] `deploy/nginx-nail-app.conf`: sửa `your-domain.com` → domain thật
- [ ] Chạy `certbot --nginx` để có block :443 (HTTPS)
- [ ] `client_max_body_size 10M` (nginx) khớp giới hạn upload ảnh trong app
- [ ] Translations `.mo` đã compile (`pybabel compile`) — nếu quên, FI/EN/VI hiện text gốc
- [ ] `.env` **không** bị commit (đã confirm: chỉ `.env.example` được track ✅)
- [ ] Không deploy `__pycache__/` / file `.pyc` cũ lên server

---

## Tham chiếu
- Kế hoạch tổng thể: `docs/DEPLOYMENT_PLAN.md`
- Runbook triển khai: `docs/DEPLOYMENT_RUNBOOK.md`
- Artifacts hạ tầng: `deploy/nail-app.service`, `deploy/nginx-nail-app.conf`, `deploy/backup-db.sh`
