# 🔒 Báo cáo Audit Bảo mật Backend

> **Ngày audit:** 2026-07-17
> **Phạm vi:** `app/routes.py`, `app/database/db.py`, `app/services/payment_service.py`, `app/services/email_system.py`, `app/config.py`, `app/__init__.py`, `app/utils/helpers.py`
> **Tiêu chí:** Auth, phân quyền, IDOR, SQLi, CSRF, luồng thanh toán, quản lý secret

---

## Tổng quan kết quả

| Mức độ | Số lượng | Tình trạng |
|---|---|---|
| 🔴 Nghiêm trọng | 1 | ✅ Đã sửa (2026-07-17) |
| 🟠 Trung bình | 2 | ✅ Đã sửa (2026-07-17) |
| 🟡 Thấp | 3 | ✅ Đã sửa (2026-07-17) |
| 🟢 Đạt chuẩn | nhiều | Không có vấn đề |

---

## 🔴 NGHIÊM TRỌNG — Brute-force mã xác thực → chiếm tài khoản (kể cả admin)  ✅ ĐÃ SỬA

**Vị trí:** `routes.py:4428` (`verify_email`) + `routes.py:4169` (`forgot_password`) + `routes.py:4196` (`staff_forgot_password`)

Mã xác thực là **6 chữ số** (`email_system.py:28` → `secrets.randbelow(1000000)`), nhưng route kiểm tra mã `/verify-email` **không có bất kỳ giới hạn số lần thử nào** — so sánh trực tiếp `if user_code == verification_code`, sai thì cho thử lại vô hạn.

### Chuỗi khai thác (account takeover)

1. Kẻ tấn công vào `/staff/forgot-password`, nhập **email của admin**. Route chấp nhận role `admin`/`staff`, sinh mã, lưu vào **session của kẻ tấn công**: `verify_context = {user_id: <admin_id>, ...}`.
2. Mã gửi tới hòm mail admin, nhưng **việc kiểm tra mã diễn ra trong session kẻ tấn công**.
3. Kẻ tấn công spam `/verify-email` đoán 6 chữ số. Không lockout, mã sống 10 phút, xin mã mới lặp lại → sớm muộn trúng.
4. Trúng → `reset_user_id = admin_id` → `/set-new-password` đổi mật khẩu admin → **chiếm toàn quyền admin**.

### ✅ Cách đã sửa

Thêm cột `attempts` vào bảng `email_verifications` (migrate cả `database.db` production bằng `ALTER TABLE`) và hàm `register_failed_verification()` (`db.py`): mỗi lần nhập sai `attempts += 1`; khi `attempts >= MAX_VERIFY_ATTEMPTS (=5)` thì đánh dấu `is_used = 1` → mã bị vô hiệu, lần lookup sau trả `None` (buộc xin mã mới, có cooldown 60s).

- `db.py`: `MAX_VERIFY_ATTEMPTS`, `register_failed_verification()`; `update_new_code` reset `attempts = 0` khi cấp mã mới.
- `routes.py` (`verify_email`): helper `_wrong_code_response()` đếm + khoá, dùng chung cho cả 3 nhánh (register / booking / forgot_password).
- Áp cùng guard cho các endpoint OTP nhạy cảm khác (đã đăng nhập): `change_password`, `update_email_address`, `staff_change_password`.

Kết quả: không gian brute-force sập từ 10⁶/10 phút xuống còn 5 lần thử/60s → bất khả thi.

---

## 🟠 TRUNG BÌNH #1 — Login khách không có rate-limit  ✅ ĐÃ SỬA

**Vị trí:** `routes.py` (`login`)

Trước đây staff login có cơ chế chặn brute-force nhưng **login khách hàng thì không**.

### ✅ Cách đã sửa

Áp cùng cơ chế throttle vào route `login()`: kiểm tra `get_login_block_remaining(ip)` đầu request, `record_login_failure()` khi sai, `clear_login_attempts()` khi thành công. Sửa chung một lần với #2 (dùng store DB).

---

## 🟠 TRUNG BÌNH #2 — Rate-limit chỉ lưu trong RAM, theo từng worker  ✅ ĐÃ SỬA

**Vị trí:** `routes.py` (trước đây: `_failed_logins = {}`)

Chạy 3 gunicorn workers → hiệu lực chặn bị nhân 3 (mỗi worker đếm riêng), và **reset mỗi lần restart/deploy**.

### ✅ Cách đã sửa

Thay dict RAM bằng bảng `login_attempts` (SQLite) — lưu bền theo IP, **dùng chung mọi worker và sống qua restart**. Ngưỡng giữ nguyên: 5 lần sai → khoá 15 phút.

- `schema.sql`: thêm bảng `login_attempts (ip, count, blocked_until, updated_at)` + migrate `database.db` production (`CREATE TABLE`).
- `db.py`: `get_login_block_remaining()`, `record_login_failure()`, `clear_login_attempts()`.
- `routes.py`: `staff_login` và `login` (khách) đều dùng chung 3 hàm trên; xoá dict `_failed_logins`.

(Keying theo `remote_addr` OK vì đã có `ProxyFix x_for=1`.)

---

## 🟡 THẤP

### #1 — `/staff/complete-booking/<id>` thiếu kiểm tra chủ sở hữu  ✅ ĐÃ SỬA

Route `complete_booking` không check `booking["staff_id"] == current_staff["id"]` → bất kỳ nhân viên nào cũng hoàn thành booking của người khác.

**✅ Cách đã sửa:** Xoá hẳn route (dead code — không nơi nào gọi, đã bị `mark_done` có check chủ sở hữu thay thế). Vừa hết lỗ hổng vừa sạch code trùng.

### #2 — TOCTOU khi đổi thưởng  ✅ ĐÃ SỬA

`get_loyalty_balance` kiểm tra ngoài transaction → hai request đồng thời có thể cùng qua và trừ điểm 2 lần (âm điểm / double-spend).

**✅ Cách đã sửa:** `redeem_reward` (`db.py`) dùng `BEGIN IMMEDIATE` khoá ghi ngay rồi **đọc lại balance trong transaction**; số dư không đủ → `ROLLBACK` + trả `False`. Request thứ 2 buộc phải chờ request thứ 1 commit nên thấy số dư đã trừ. Route `redeem_reward_route` xử lý `False` → báo "Not enough points".

### #3 — Chính sách mật khẩu yếu  ✅ ĐÃ SỬA

Không nhất quán: `register` không check độ dài, có chỗ `< 6`, có chỗ `< 8`.

**✅ Cách đã sửa:** Đồng bộ **tối thiểu 8 ký tự** cho `register`, `set_new_password`, `change_password` (staff đã 8 sẵn). Theo khuyến nghị NIST — ưu tiên độ dài, không ép ký tự đặc biệt.

---

## 🟢 ĐẠT CHUẨN (làm tốt)

| Hạng mục | Kết quả |
|---|---|
| SQL Injection | ✅ Parameterized 100%, kể cả WHERE động (`get_admin_bookings`, `get_staff_history`) đều bind param |
| CSRF | ✅ Global + webhook exempt đúng chỗ, có verify chữ ký Stripe (`payment_service.py:109`) |
| Thanh toán | ✅ Giá tính server-side từ `service["price"]`, fulfill idempotent, re-check double-book |
| IDOR | ✅ Có check chủ sở hữu ở invoice/booking/cancel/reschedule (`routes.py:503`, `1041`, `383`...) |
| Phân quyền admin/staff | ✅ `@admin_required` / `@staff_required` nhất quán (chỉ `/admin/logout` không cần) |
| Session | ✅ `session.clear()` khi login (chống fixation), cookie HTTPOnly/SameSite/Secure, admin idle-timeout 30' |
| Upload file | ✅ Whitelist đuôi, giới hạn size, tên file UUID, `secure_filename` |
| OAuth Google | ✅ Check `email_verified`, tách role rõ ràng |
| Secrets | ✅ Lấy từ env, `.env` đã gitignore, không `debug=True` |
| Password | ✅ Hash bằng `werkzeug.generate_password_hash` |
| Chống user enumeration | ✅ `forgot_password` trả về giống nhau dù email tồn tại hay không |

---

## Kết luận

Nền tảng backend **khá vững**: SQLi / CSRF / IDOR / payment đều ổn, phân quyền nhất quán, quản lý secret sạch. **Toàn bộ phát hiện đã được xử lý**: 🔴 nghiêm trọng (brute-force OTP → chiếm tài khoản admin), 🟠 ×2 (rate-limit login), 🟡 ×3 (ownership check, TOCTOU redeem, password policy).
