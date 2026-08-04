# Deployment Plan — Nail Booking Web App

**Target:** VPS Linux (gunicorn + nginx) · **Stack:** Flask + SQLite · **Cập nhật:** 2026-07-12

Kế hoạch chuẩn bị trước khi deploy, theo hướng tối ưu và dễ maintain.

---

## Thực trạng — vấn đề đang chặn deploy

| # | Vấn đề | Mức độ |
|---|--------|--------|
| 1 | ~~`requirements.txt` là bản `pip freeze` toàn máy — encode UTF-16, ~180 package rác.~~ | ✅ Đã xử lý (Phase 1) |
| 2 | ~~`app/database/database.db` bị commit vào git.~~ | ✅ Đã xử lý (Phase 1) |
| 3 | ~~`run.py` dùng `app.run(debug=True)`.~~ | ✅ Đã xử lý (Phase 2) |
| 4 | ~~Không có entry production.~~ | ✅ Đã xử lý (Phase 2) |
| 5 | `print()` rải khắp `routes.py` / `db.py` thay vì logging. | 🟡 Nên sửa |
| 6 | Không có scheduler — `auto_expire_bookings` chạy lazy lúc load trang. | 🟢 Ghi chú |

**Điểm tốt sẵn có:** `.env` đã gitignore · `SESSION_COOKIE_SECURE` đọc từ env · CSRF bật · translations `.mo` đã compile · có `schema.sql` + `seed.sql` để init DB sạch.

---

## Plan

### Phase 1 — Dependency & DB *(code)* — ✅ HOÀN TẤT (2026-07-12)
1. ✅ Viết lại `requirements.txt` (chuyển ra **repo root**, xoá bản `app/requirements.txt` cũ).
   - Từ ~180 package rác (UTF-16, pip freeze toàn máy) → **9 package thật**, UTF-8, pin version.
   - Deps: Flask 3.1.2 · Flask-WTF 1.2.2 · Flask-Babel 4.0.0 · Authlib 1.7.2 · requests 2.32.5 · stripe 15.3.0 · python-dotenv 1.2.1 · tzdata 2025.2 · gunicorn 23.0.0.
   - **`tzdata` được thêm nhờ verification** — venv sạch crash ở `ZoneInfo("Europe/Helsinki")` vì không có tz db của OS; thêm `tzdata` để portable mọi môi trường (Docker slim, Linux tối giản).
   - **Verify:** venv sạch → `pip install -r requirements.txt` OK → `create_app()` OK, **111 routes**.
2. ✅ `git rm --cached app/database/database.db` — untrack DB, giữ file local (184KB), `git check-ignore` xác nhận đã ignore (`.gitignore` có sẵn `*.db`). Deploy sẽ init sạch từ `schema.sql` + `seed.sql` (bước init làm ở Phase 2/3).

> **Trạng thái git:** các thay đổi Phase 1 đang staged, **chưa commit**.

### Phase 2 — Production entry *(code)* — ✅ HOÀN TẤT (2026-07-12)
3. ✅ `run.py` — bỏ hardcode `debug=True`, đọc từ `FLASK_DEBUG` (mặc định tắt; local set `true` trong `.env`). Production chạy qua `gunicorn run:app` (không đụng block `__main__`).
4. ✅ Thêm `gunicorn.conf.py` (bind `127.0.0.1:8000`, workers 3, log ra stdout→journald). systemd sẽ gọi `gunicorn -c gunicorn.conf.py run:app`.
   - Bỏ `Procfile`/`runtime.txt` (quy ước Heroku/PaaS, VPS+systemd không cần). **Python target: 3.13.**
   - **Verify:** `run:app` import OK · config parse OK · logic `FLASK_DEBUG` đúng. (gunicorn Unix-only → chạy thật ở Phase 3.)

### Phase 3 — Hạ tầng VPS *(bạn làm trên server)* — 🟡 Artifacts + code xong, chờ chạy trên VPS
Artifacts đã tạo sẵn trong repo: `deploy/nail-app.service`, `deploy/nginx-nail-app.conf`, `deploy/backup-db.sh`, và runbook 12 bước → **`docs/DEPLOYMENT_RUNBOOK.md`**.
Code: ✅ thêm **ProxyFix** vào `app/__init__.py` (để `url_for(_external=True)` sinh URL https đúng cho OAuth/Stripe sau nginx).

Các bước chạy trên server (chi tiết trong runbook):
5. nginx reverse proxy + HTTPS (Let's Encrypt / certbot). Có HTTPS rồi mới set `SESSION_COOKIE_SECURE=true`.
6. systemd service chạy gunicorn (auto-restart).
7. Set env vars thật: `SECRET_KEY` mạnh · Stripe **live** key + `STRIPE_WEBHOOK_SECRET` · Google OAuth redirect URI domain thật.
8. Chạy `python -m app.database.setup_stripe_prices` trên môi trường live.
9. Cron backup file SQLite định kỳ.

> Khuyến nghị VPS: **Hetzner / UpCloud** (datacenter Helsinki, gần tiệm + GDPR).

#### Bổ sung cho tính năng video dịch vụ *(2026-08-05)*

Ba việc dưới đây chạy **một lần duy nhất** trên server, không lặp lại mỗi lần deploy.

**a. Cài ffmpeg.** Đây là gói hệ điều hành, **KHÔNG phải package Python** — không có và không thể có trong `requirements.txt`. Trên PyPI có vài tên gây nhầm (`ffmpeg-python` chỉ là lớp bọc và vẫn cần binary; `ffmpeg` là package chết). App gọi ffmpeg qua `subprocess` nên không cần wrapper nào.

```bash
sudo apt update && sudo apt install -y ffmpeg
ffmpeg -version   # xác nhận
```

Server dùng ffmpeg để transcode video admin upload về 720p kèm `-movflags +faststart`. Thiếu ffmpeg thì mọi upload video đều fail.

> Vì sao bắt buộc transcode: file test thực tế đo được 16 giây / 53MB / bitrate 26.6 Mbps. Sau khi transcode 720p còn **3.2MB**, nhẹ hơn 16 lần. Không transcode thì user phải tải hàng chục MB cho một video minh hoạ.

> Vì sao bắt buộc `+faststart`: cờ này dời box `moov` (chứa metadata) lên đầu file. Thiếu nó thì trình duyệt phải tải **hết** file mới bắt đầu phát được.

**b. Nâng giới hạn upload của nginx.** `deploy/nginx-nail-app.conf` đang để `client_max_body_size 10M` (chỉ đủ cho ảnh). Video thô 1080p60 từ điện thoại khoảng 150MB.

```nginx
client_max_body_size 300M;
```
```bash
sudo systemctl reload nginx
```

nginx mặc định buffer toàn bộ request body rồi mới đẩy sang gunicorn, nên upload chậm **không** bị `timeout = 60` của gunicorn giết. Không cần sửa `gunicorn.conf.py`.

**c. Chạy migration DB.** `git pull` **không** tự thêm cột. `schema.sql` chỉ áp dụng khi khởi tạo DB mới, còn DB production đã có dữ liệu thật nên không bao giờ đọc lại file đó.

```bash
sqlite3 /var/www/nail-app/app/database/database.db \
  "ALTER TABLE services ADD COLUMN video_url TEXT DEFAULT NULL;"
```

Thiếu bước này thì sau khi deploy, trang `/services` sập với `sqlite3.OperationalError: no such column: video_url`. Giai đoạn 2 sẽ thêm tiếp `video_status` và `video_error`, cùng vấn đề.

### Phase 4 — Nên có *(tùy chọn)* — ✅ HOÀN TẤT (2026-07-12)
10. ✅ `print()` → `logging`. Cấu hình 1 lần trong `create_app` (`LOG_LEVEL` env, mặc định INFO, ra stderr→journald). `[payment]` error/warning ở routes.py + payment_service.py → `logger.exception`/`logger.warning`; 16 debug noise ở db.py → `logger.debug`. CLI scripts (reset_db/test_data/setup_stripe_prices) giữ nguyên `print()`.

---

## Checklist bên ngoài code (nhắc lại gọn)

- [ ] `SECRET_KEY` production mạnh, khác local
- [ ] `SESSION_COOKIE_SECURE=true` (sau khi có HTTPS)
- [ ] Stripe: đổi `sk_test` → `sk_live`, đăng ký webhook endpoint domain production, set `STRIPE_WEBHOOK_SECRET`
- [ ] Google OAuth: thêm redirect URI domain production vào Google Console
- [ ] Backup SQLite định kỳ
- [ ] `apt install ffmpeg` trên server (không nằm trong `requirements.txt`)
- [ ] nginx `client_max_body_size` 10M → 300M cho upload video
- [ ] Chạy migration ALTER TABLE trước khi restart app (xem Phase 3, mục bổ sung)

---

## Lưu ý SQLite trên VPS

SQLite phù hợp salon nhỏ (ít ghi đồng thời). Trên VPS Linux, file DB nằm bền trên đĩa → chỉ cần backup định kỳ. Không dùng PaaS filesystem ephemeral (sẽ mất DB khi restart). Nếu sau này lưu lượng ghi tăng mạnh mới cân nhắc chuyển Postgres.
