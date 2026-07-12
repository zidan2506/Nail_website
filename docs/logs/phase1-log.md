# Phase 1 — Work Log

**Ngày:** 2026-07-12 · **Phase:** 1 (Dependency & DB) · **Trạng thái:** ✅ Hoàn tất (chưa commit)

Log lại những gì Claude Code đã làm trong Phase 1 để tiện theo dõi.

---

## 1. Viết lại `requirements.txt`

**Vấn đề ban đầu:** `app/requirements.txt` là bản `pip freeze` toàn máy — encode UTF-16, ~180 package rác (jupyter, pyside6, pygame, chromadb, openai, matplotlib, kubernetes, mysql-connector...). App thật chỉ dùng vài package.

**Đã làm:**
- Scan toàn bộ `import` trong project → xác định deps thật (7 third-party: flask, flask_wtf, flask_babel, authlib, stripe, dotenv, werkzeug; còn lại stdlib).
- Kiểm tra version đang cài để pin chính xác.
- Tạo file mới `requirements.txt` ở **repo root** (UTF-8, 9 package), xoá bản cũ `app/requirements.txt` (`git rm`).

**Nội dung `requirements.txt` cuối:**
```
Flask==3.1.2
Flask-WTF==1.2.2
Flask-Babel==4.0.0
Authlib==1.7.2
requests==2.32.5
stripe==15.3.0
python-dotenv==1.2.1
tzdata==2025.2
gunicorn==23.0.0
```

**Quyết định đáng nhớ:**
- `Werkzeug` không pin riêng — là dep bắt buộc của Flask, tránh pin thừa gây khó nâng cấp.
- `requests` pin explicit — Authlib cần fetch OpenID metadata của Google (không phải hard-dep của Authlib), stripe cũng dùng.
- `gunicorn` thêm mới cho production.
- **`tzdata` thêm nhờ verification** (xem mục 3).

## 2. Untrack `database.db`

**Vấn đề:** `app/database/database.db` bị commit vào git → deploy mang theo data test, mỗi lần deploy đè lên DB thật.

**Đã làm:**
- `git rm --cached app/database/database.db` — untrack nhưng **giữ file local** (184KB vẫn còn trên đĩa).
- `.gitignore` đã có sẵn `*.db` → `git check-ignore` xác nhận file giờ bị ignore, không lo commit nhầm lần sau.
- Deploy sẽ init DB sạch từ `schema.sql` + `seed.sql` (bước init để Phase 2/3).

## 3. Verification (venv sạch)

Theo plan, tạo venv sạch để chắc requirements.txt đủ và đúng:
- `python -m venv` + `pip install -r requirements.txt` → OK.
- Import app: `create_app()` → OK, **111 routes**.

**Phát hiện quan trọng:** lần verify đầu crash tại `ZoneInfo("Europe/Helsinki")` (`app/utils/helpers.py`) — venv sạch không có tz database. Máy dev chạy được nhờ `tzdata` nằm trong đống freeze cũ.
→ **Fix:** thêm `tzdata==2025.2` vào requirements để portable mọi môi trường (Docker slim, Linux tối giản). Verify lại → pass.

> Ghi chú kỹ thuật: lần install đầu ở scratchpad fail do đường dẫn quá sâu chạm giới hạn MAX_PATH của Windows (tên file dài của `stripe`). Chạy lại ở đường dẫn ngắn (`C:\vv`) thì OK. Venv tạm đã xoá sau khi verify.

---

## Kết quả git (đang staged, chưa commit)

```
D  app/database/database.db      (untrack, file vẫn còn trên đĩa)
D  app/requirements.txt          (đã xoá)
?? requirements.txt              (file mới ở root)
?? docs/                         (DEPLOYMENT_PLAN.md + log này)
```

**Bước tiếp theo:** commit Phase 1 (message đề xuất: `Clean up dependencies and untrack database.db for deployment`) hoặc gộp với Phase 2 rồi commit chung. → Phase 2: tách `debug=True` + thêm entry production gunicorn.
