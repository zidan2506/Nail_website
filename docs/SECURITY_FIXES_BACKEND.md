# 🛡️ Tổng hợp Khắc phục Bảo mật Backend

> **Ngày:** 2026-07-17
> **Nguồn:** [SECURITY_AUDIT_BACKEND.md](SECURITY_AUDIT_BACKEND.md)
> **Trạng thái:** ✅ Đã xử lý toàn bộ 6 phát hiện (1 🔴 · 2 🟠 · 3 🟡)

File này ghi lại **những gì đã sửa** và **cần làm gì khi deploy**. Chi tiết phân tích từng lỗ hổng xem file audit gốc.

---

## ⚠️ BẮT BUỘC khi deploy — 2 migration DB

Chạy trên DB production (`app/database/database.db`) **trước khi** chạy code mới:

```sql
-- Fix 🔴 (OTP brute-force): bộ đếm số lần nhập sai mã
ALTER TABLE email_verifications ADD COLUMN attempts INTEGER NOT NULL DEFAULT 0;

-- Fix 🟠 (rate-limit): bảng khoá đăng nhập bền theo IP
CREATE TABLE login_attempts (
    ip TEXT PRIMARY KEY,
    count INTEGER NOT NULL DEFAULT 0,
    blocked_until REAL NOT NULL DEFAULT 0,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

> Đã áp trên DB local. `schema.sql` cũng đã cập nhật (bản dựng mới tự có 2 thay đổi này).
> Nhóm 🟡 **không cần** migration.

---

## 🔴 NGHIÊM TRỌNG — Brute-force mã OTP → chiếm tài khoản admin

**Vấn đề:** Mã xác thực 6 chữ số (10⁶ tổ hợp) nhưng `/verify-email` không giới hạn số lần thử → kẻ tấn công dùng `/staff/forgot-password` nhắm email admin rồi vét cạn mã → đổi mật khẩu admin.

**Cách sửa:** Sau **5 lần nhập sai**, mã bị vô hiệu (`is_used = 1`) → buộc xin mã mới (cooldown 60s). Không gian brute-force sập từ 10⁶/10 phút → 5 lần/60s.

| File | Thay đổi |
|---|---|
| `schema.sql` | Thêm cột `email_verifications.attempts` |
| `db.py` | `MAX_VERIFY_ATTEMPTS = 5`; `register_failed_verification()`; `update_new_code` reset `attempts = 0` khi cấp mã mới |
| `routes.py` | Helper `_wrong_code_response()` trong `verify_email` (dùng chung 3 nhánh register/booking/forgot_password); áp cùng guard cho `change_password`, `update_email_address`, `staff_change_password` |

---

## 🟠 TRUNG BÌNH ×2 — Rate-limit đăng nhập

**Vấn đề:**
- #1: Login khách (`login`) hoàn toàn không có rate-limit.
- #2: Rate-limit lưu dict RAM (`_failed_logins`) → per gunicorn worker (3 workers = 3× số lần), reset mỗi lần restart.

**Cách sửa:** Thay dict RAM bằng bảng `login_attempts` (SQLite) — bền, dùng chung mọi worker, sống qua restart. Áp cho **cả** staff và khách. Ngưỡng giữ nguyên: 5 lần sai → khoá 15 phút.

| File | Thay đổi |
|---|---|
| `schema.sql` | Thêm bảng `login_attempts` |
| `db.py` | `import time`; `get_login_block_remaining()`, `record_login_failure()`, `clear_login_attempts()` |
| `routes.py` | Xoá dict `_failed_logins`; `staff_login` + `login` dùng chung 3 hàm trên |

---

## 🟡 THẤP ×3

### #1 — Route chết `complete_booking` thiếu check chủ sở hữu
Route `/staff/complete-booking` không kiểm tra `staff_id` → nhân viên bất kỳ hoàn thành booking người khác.
**Sửa:** Xoá hẳn route (dead code — đã bị `mark_done` có check chủ sở hữu thay thế). — `routes.py`

### #2 — TOCTOU double-spend điểm khi đổi thưởng
Balance kiểm tra ngoài transaction → 2 request đồng thời cùng trừ điểm.
**Sửa:** `redeem_reward` dùng `BEGIN IMMEDIATE` + đọc lại balance trong transaction; thiếu điểm → `ROLLBACK` + trả `False`; route báo "Not enough points". — `db.py`, `routes.py`

### #3 — Chính sách mật khẩu không nhất quán
`register` không check độ dài, có chỗ `< 6`, có chỗ `< 8`.
**Sửa:** Đồng bộ **tối thiểu 8 ký tự** cho `register`, `set_new_password`, `change_password` (staff sẵn 8). Theo NIST — ưu tiên độ dài, không ép ký tự đặc biệt. — `routes.py`

---

## 📁 File thay đổi (tổng)

| File | Vai trò |
|---|---|
| `app/routes.py` | Guard OTP, rate-limit login, xoá route chết, xử lý redeem `False`, min-8 password |
| `app/database/db.py` | Hàm đếm OTP sai, hàm throttle login, redeem atomic |
| `app/database/schema.sql` | Cột `attempts` + bảng `login_attempts` |
| `app/database/database.db` | Đã migrate local (production cần chạy 2 lệnh SQL ở trên) |
| `docs/SECURITY_AUDIT_BACKEND.md` | Báo cáo audit (đã cập nhật trạng thái ✅) |

---

## ✅ Kiểm chứng

- `py_compile` sạch cho `routes.py` + `db.py`.
- OTP: test 5 lần sai → khoá mã, lần 6 lookup trả `None`.
- Rate-limit: test 5 lần sai → khoá 900s, đăng nhập thành công clear reset.
- Redeem: test thiếu điểm → `False` không insert; đủ điểm → trừ về 0; đổi tiếp → `False`.
- Không còn tham chiếu `_failed_logins`; không còn check `< 6`; route `complete_booking` đã biến mất.

---

## 🔭 Ngoài phạm vi (ghi nhận, chưa xử lý)

- Rate-limit theo IP có thể bị chia sẻ sau NAT (nhiều user chung 1 IP). Đủ dùng cho quy mô hiện tại.
- Chưa có scheduler dọn bảng `login_attempts` / `email_verifications` cũ (row hết hạn tích tụ chậm — không ảnh hưởng bảo mật, chỉ là dọn dẹp).
