# Phase 3 — Work Log

**Ngày:** 2026-07-12 · **Phase:** 3 (Hạ tầng VPS) · **Trạng thái:** ✅ Artifacts + code xong (chờ chạy trên VPS)

Phase 3 là hạ tầng chạy TRÊN VPS. Vai trò của Claude: tạo config template + runbook + 1 thay đổi code bắt buộc (ProxyFix). Việc chạy lệnh trên server do bạn thực hiện.

**Bối cảnh:** bạn chưa có VPS. Target chốt: Ubuntu 24.04 LTS · path `/var/www/nail-app` · user riêng `nailapp` · gunicorn `127.0.0.1:8000` sau nginx.

---

## 1. Config artifacts (thư mục `deploy/`)

- **`deploy/nail-app.service`** — systemd unit. `Type=notify`, chạy dưới user `nailapp`, `Restart=always`, gọi `gunicorn -c gunicorn.conf.py run:app`. Không cần EnvironmentFile vì app tự nạp `.env` qua `load_dotenv()`.
- **`deploy/nginx-nail-app.conf`** — reverse proxy vào `127.0.0.1:8000`, serve `/static/` trực tiếp, `client_max_body_size 10M` (upload ảnh), truyền `X-Forwarded-Proto`. Chỉ có block `:80`; certbot tự thêm `:443`.
- **`deploy/backup-db.sh`** — backup SQLite bằng online `.backup` API (an toàn khi app chạy), giữ 14 bản. Cú pháp verify OK (`bash -n`).

## 2. Runbook (`docs/DEPLOYMENT_RUNBOOK.md`)

12 bước theo thứ tự: chọn VPS → DNS → user+firewall → cài package → clone+venv → `.env` production → init DB → systemd → nginx → HTTPS (certbot) → Stripe live + webhook + `setup_stripe_prices` → Google OAuth redirect → cron backup. Kèm phần "deploy bản cập nhật sau" + checklist.

**Khuyến nghị nhà cung cấp:** Hetzner hoặc UpCloud — đều có datacenter Helsinki (gần tiệm + GDPR), rẻ. Gói 1–2 vCPU/2–4GB dư cho SQLite.

## 3. Thay đổi code bắt buộc: ProxyFix

**Vấn đề:** app dùng `url_for(_external=True)` cho Google OAuth callback (`routes.py:4219`) + Stripe success/cancel URLs. Sau nginx, Flask tưởng request là `http` → sinh `redirect_uri` `http://` → Google báo mismatch, login vỡ.

**Đã làm** — thêm vào `app/__init__.py` ngay sau `app = Flask(__name__)`:
```python
from werkzeug.middleware.proxy_fix import ProxyFix
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)
```
`x_proto=1` = tin `X-Forwarded-Proto` từ 1 proxy (nginx). An toàn ở local (không proxy thì header không tồn tại).

**Verify:** `create_app()` OK, 111 routes, `isinstance(app.wsgi_app, ProxyFix) == True`.

## 4. Phát hiện trong lúc khảo sát (đã ghi vào runbook)

- **`app/init_db.py` hỏng** — import `init_db` từ `db.py` nhưng hàm này không tồn tại. Init DB thật dùng `reset_db.py` (chạy `schema.sql`) + `test_data.py` (chạy `seed.sql`).
- **`seed.sql` lẫn data** — chứa cả data tham chiếu (services/categories/staff/tiers/rewards) LẪN data demo giả (bookings/customers/reviews/invoices). Runbook nêu 2 cách: A) chỉ schema rồi thêm tay qua admin (sạch, khuyến nghị launch thật); B) seed rồi xoá data giao dịch giả.

---

## Kết quả git (Phase 3 chờ commit)

```
M  app/__init__.py                  ← ProxyFix
?? deploy/                          ← 3 file config
?? docs/DEPLOYMENT_RUNBOOK.md
?? docs/logs/phase3-log.md
```

**Còn lại (chạy trên VPS, không phải code):** toàn bộ 12 bước runbook — mua VPS, DNS, cài đặt, HTTPS, Stripe/OAuth live, cron. Làm khi bạn có server.
