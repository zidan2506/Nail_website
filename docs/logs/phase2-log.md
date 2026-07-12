# Phase 2 — Work Log

**Ngày:** 2026-07-12 · **Phase:** 2 (Production entry) · **Trạng thái:** ✅ Hoàn tất (chưa commit)

Log lại những gì Claude Code đã làm trong Phase 2 để tiện theo dõi.

---

## 1. Sửa `run.py` — bỏ hardcode `debug=True`

**Vấn đề:** `run.py` cũ dùng `app.run(debug=True)` — Flask dev server + debug mode, không được lên production (RCE qua Werkzeug debugger).

**Điểm cần nhớ:** gunicorn import `run:app` ở cấp module, **không chạy block `if __name__ == "__main__"`** → debug này thực ra đã không ảnh hưởng khi chạy qua gunicorn. Rủi ro thật chỉ là ai đó lỡ chạy `python run.py` thẳng trên server.

**Đã làm (secure-by-default):**
```python
import os
from app import create_app

app = create_app()

if __name__ == "__main__":
    debug = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    app.run(debug=debug)
```
- Mặc định `FLASK_DEBUG` không set → debug **tắt**.
- Local muốn auto-reload/debugger thì set `FLASK_DEBUG=true` trong `.env`.

## 2. Thêm `gunicorn.conf.py` (production entry)

Chọn `gunicorn.conf.py` thay vì Procfile/runtime.txt — đúng với stack VPS + systemd, ít file thừa hơn. systemd (Phase 3) sẽ gọi `gunicorn -c gunicorn.conf.py run:app`.

```python
import os

bind = os.environ.get("GUNICORN_BIND", "127.0.0.1:8000")  # nginx proxy vào đây
workers = int(os.environ.get("GUNICORN_WORKERS", "3"))     # SQLite: giữ vừa phải
timeout = 60
accesslog = "-"   # stdout -> journald (systemd) bắt log
errorlog = "-"
```

**Quyết định đáng nhớ:**
- `bind` = `127.0.0.1:8000` — chỉ nghe localhost, nginx reverse-proxy vào (không expose thẳng ra ngoài).
- `workers = 3` — SQLite ghi tuần tự, để số worker vừa phải tránh lỗi "database is locked". Có thể chỉnh qua env `GUNICORN_WORKERS`.
- `accesslog/errorlog = "-"` — log ra stdout/stderr để journald của systemd bắt, không cần quản file log riêng.

## 3. Cập nhật `.env` + `.env.example`

- `.env` (local): thêm `FLASK_DEBUG=true` → giữ auto-reload khi dev.
- `.env.example`: thêm `FLASK_DEBUG=false` + chú thích "KHÔNG set ở production".

## 4. Bỏ Procfile / runtime.txt so với plan gốc

Plan ban đầu ghi "Procfile + runtime.txt" (quy ước Heroku/PaaS). Trên VPS + systemd không dùng tới → bỏ để tránh file cargo-cult. Bản Python target sẽ ghi vào `DEPLOYMENT_PLAN.md`.

## 5. Verification

gunicorn là Unix-only → **không chạy thử được trên Windows**, sẽ chạy thật ở VPS (Phase 3). Ở local verify được phần quan trọng:
- `run:app` import OK → `<Flask 'app'>`, callable = True (gunicorn dùng đúng cái này).
- `gunicorn.conf.py` parse OK → bind/workers/timeout đúng.
- Logic `FLASK_DEBUG`: unset → False · true → True · false → False.

---

## Kết quả git (Phase 1 + 2 đang staged, chưa commit)

**Files Phase 2:**
```
M  run.py
?? gunicorn.conf.py
(.env — gitignored, không hiện trong git status)
M  .env.example
```

**Bước tiếp theo:** commit Phase 1+2 → Phase 3 (hạ tầng VPS: nginx + HTTPS + systemd, phần này chạy trên server).
