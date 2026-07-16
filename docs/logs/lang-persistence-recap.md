# Lang Persistence — Recap

**Ngày:** 2026-07-16
**Yêu cầu:** Feature set lang trong `customer_setting` không nhớ lựa chọn. Logout → tắt page → login lại vẫn về default `fi` dù đã set lang khác. Cần lưu lang thành **dữ liệu của tài khoản** (không chỉ session). Chỉ áp dụng cho user đã đăng ký account.

---

## Nguyên nhân gốc

`lang` chỉ sống trong `session`:
- `routes.py` `/set-language` set `session["lang"]`
- `app/__init__.py:24` `select_locale()` đọc `session["lang"]`, fallback `"fi"`

Logout gọi `session.clear()` → mất sạch → login lại rơi về `"fi"`. Bảng `users` không có cột lang nên không có gì để nhớ.

---

## Quyết định thiết kế (đã chốt với user)

| Câu hỏi | Lựa chọn |
|---|---|
| Lưu ở bảng nào | `users.lang` — khớp "chỉ user đã đăng ký"; route `/set-language` dùng chung nên chỉ cần 1 nhánh `if session.get("user_id")`, cover cả customer lẫn staff |
| Migration | Chỉ sửa `schema.sql` (user tự chạy lại init_db) |
| Xung đột login | DB thắng; nếu `users.lang` NULL (account cũ chưa từng set) thì giữ lang guest đang xem |

---

## Thay đổi (28 thêm / 2 sửa)

| File | Thay đổi |
|---|---|
| `app/database/schema.sql:62` | `users` += `lang TEXT DEFAULT NULL` |
| `app/database/db.py:1176` | Hàm mới `update_user_lang(user_id, lang)` |
| `app/routes.py:17` | Import `update_user_lang` |
| `app/routes.py:144` | `/set-language` ghi DB khi có `user_id` |
| `app/routes.py:155` | Helper `_apply_login_lang(user_lang, guest_lang)` — DB thắng, NULL thì giữ guest |
| `app/routes.py` (staff login ~1643) | Giữ `guest_lang` qua `session.clear()`, gọi `_apply_login_lang` |
| `app/routes.py` (customer login ~4088) | Tương tự |
| `app/routes.py` (OAuth callback ~4149) | Tương tự — account mới (`user is None`) truyền `None` |

Guest vẫn chỉ dùng session, không ghi DB.

---

## Verify

Script test dùng DB tạm (không đụng `database.db` thật) — **7/7 pass**:

1. User login đổi lang → ghi `users.lang` ✅
2. **Logout → login lại → giữ `vi` (không về `fi`)** ← đúng bug đã báo ✅
3. Account lang NULL + guest xem `en` → giữ `en` ✅
4. Guest set-language không ghi DB ✅
5. DB lang thắng guest lang ✅
6. Lang không hợp lệ → DB không đổi ✅

---

## Việc user cần làm (BẮT BUỘC)

Cột `lang` chưa có trong `database.db` hiện tại → code sẽ lỗi `no such column: lang` cho tới khi migrate.

**Phương án đã chọn (xoá sạch dữ liệu):**
```
python -m app.init_db --seed
```

**Nếu muốn giữ dữ liệu hiện có:**
```
sqlite3 app/database/database.db "ALTER TABLE users ADD COLUMN lang TEXT DEFAULT NULL;"
```

---

## Điểm cần user xác nhận

Ở luồng Google OAuth, user đăng ký mới hoàn toàn (`user is None`) được truyền `None` → giữ ngôn ngữ khách đang xem lúc bấm đăng nhập. Nếu muốn account mới luôn về `fi` thì cần đổi.
