# 🔒 Báo cáo Audit Bảo mật Backend

> **Ngày audit:** 2026-07-17
> **Phạm vi:** `app/routes.py`, `app/database/db.py`, `app/services/payment_service.py`, `app/services/email_system.py`, `app/config.py`, `app/__init__.py`, `app/utils/helpers.py`
> **Tiêu chí:** Auth, phân quyền, IDOR, SQLi, CSRF, luồng thanh toán, quản lý secret

---

## Tổng quan kết quả

| Mức độ | Số lượng | Tình trạng |
|---|---|---|
| 🔴 Nghiêm trọng | 1 | ✅ Đã sửa (2026-07-17) |
| 🟠 Trung bình | 2 | Nên sửa |
| 🟡 Thấp | 3 | Cân nhắc |
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

## 🟠 TRUNG BÌNH #1 — Login khách không có rate-limit

**Vị trí:** `routes.py:4065` (`login`)

Staff login (`routes.py:1602`) có cơ chế `_failed_logins` chặn brute-force, nhưng **login khách hàng thì không** — cho phép dò mật khẩu / credential stuffing không giới hạn trên tài khoản khách.

**Đề xuất sửa:** áp cùng cơ chế `_failed_logins` như `staff_login`.

---

## 🟠 TRUNG BÌNH #2 — Rate-limit chỉ lưu trong RAM, theo từng worker

**Vị trí:** `routes.py:46` (`_failed_logins = {}`)

Chạy 3 gunicorn workers → hiệu lực chặn bị nhân 3 (mỗi worker đếm riêng), và **reset mỗi lần restart/deploy**. Nên cân nhắc lưu vào DB/Redis. (Keying theo `remote_addr` OK vì đã có `ProxyFix x_for=1`.)

---

## 🟡 THẤP

### #1 — `/staff/complete-booking/<id>` thiếu kiểm tra chủ sở hữu

**Vị trí:** `routes.py:2113`

Khác với `mark_done` (`routes.py:2075`), route này **không** check `booking["staff_id"] == current_staff["id"]`. Bất kỳ nhân viên nào cũng hoàn thành booking của nhân viên khác (kích hoạt tính điểm/hoa hồng). Có vẻ là route trùng/cũ của `mark_done` — nên xác nhận có còn dùng không.

### #2 — TOCTOU khi đổi thưởng

**Vị trí:** `routes.py:1296` + `db.py:918`

`get_loyalty_balance` kiểm tra ngoài transaction; hai request đồng thời có thể cùng vượt qua và trừ điểm 2 lần (âm điểm). Nên kiểm tra lại balance bên trong transaction của `redeem_reward`.

### #3 — Chính sách mật khẩu yếu

**Vị trí:** `routes.py:4243`

Chỉ yêu cầu ≥ 6 ký tự, không kiểm tra độ phức tạp.

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

Nền tảng backend **khá vững**: SQLi / CSRF / IDOR / payment đều ổn, phân quyền nhất quán, quản lý secret sạch. Lỗ hổng 🔴 nghiêm trọng (brute-force OTP → chiếm tài khoản admin) **đã được xử lý**. Còn lại 2 lỗi 🟠 trung bình về rate-limit nên xử lý tiếp khi có thời gian.
