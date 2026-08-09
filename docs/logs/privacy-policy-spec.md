# Content spec: Privacy Policy (+ quyền GDPR, + self-host font)

**Ngày soạn:** 2026-08-09 · **Trạng thái:** 🔴 **HOÃN, chưa viết dòng code nào** · **Mở khoá khi:** doanh nghiệp đăng ký xong và có Y-tunnus

Doanh nghiệp chưa đăng ký kinh doanh và chưa vận hành thực tế, nên chưa có pháp nhân để đứng tên bên kiểm soát dữ liệu. Tài liệu này giữ lại toàn bộ phần kiểm kê dữ liệu và thiết kế trang, để khi đăng ký xong thì điền 5 dữ kiện hành chính vào là build được ngay.

**Lưu ý về thứ tự khi launch:** trang này là **điều kiện trước khi nhận khách thật đầu tiên**, không phải việc làm sau khi đã chạy.

---

## 0. Ba trang footer đang là `href="#"`

| Trang | Bị chặn bởi | Tài liệu |
|---|---|---|
| FAQs | tính năng chưa nối dây + 9 dữ kiện kinh doanh | `faq-content-spec.md` |
| Terms of Service | cùng bộ quyết định với FAQ | `faq-content-spec.md` mục 7 |
| **Privacy Policy** | **pháp nhân chưa tồn tại** | tài liệu này |

Privacy Policy sạch hơn hai trang kia: nó không chờ quyết định thiết kế nào, chỉ chờ dữ kiện hành chính.

---

## 1. Bản kiểm kê dữ liệu (rút từ schema thật)

Đây là phần tốn công nhất và **dùng lại được nguyên vẹn**. Mọi dòng dưới đây đọc ra từ `PRAGMA table_info`, không suy đoán.

### 1.1 Dữ liệu cá nhân đang thu

| Dữ liệu | Bảng | Thu ở đâu | Bên thứ ba nhận |
|---|---|---|---|
| email, `password_hash`, `oauth_provider`, `oauth_sub`, lang | `users` | đăng ký, Google login | Google |
| họ tên, email, điện thoại, **ngày sinh**, notes, avatar, `stripe_customer_id` | `customers` | đăng ký, hồ sơ | Stripe |
| ghi chú lịch hẹn | `bookings` | form đặt lịch bước 4 | |
| **địa chỉ IP** | `login_attempts` | mọi lần đăng nhập | |
| hoá đơn, thanh toán | `invoices` | checkout | Stripe |
| lịch sử điểm | `loyalty_points_log` | | |
| ảnh đại diện | filesystem | upload | |

### 1.2 Bên xử lý dữ liệu

| Bên | Dùng làm gì | Ghi chú |
|---|---|---|
| **Google** | OAuth, scope `openid email profile` (`app/__init__.py:51`) | **Cộng thêm Fonts CDN trên mọi trang**, xem mục 2.1 |
| **Stripe** | Thanh toán, lưu `stripe_customer_id` | |
| **Resend** | Email giao dịch, gửi qua HTTPS API vì host chặn cổng SMTP outbound (`config.py:21`) | Công ty Mỹ |

### 1.3 Cookie

Chỉ có **session cookie của Flask**. Không tìm thấy analytics, không pixel, không tracker.

| Thuộc tính | Giá trị | Nguồn |
|---|---|---|
| `SESSION_COOKIE_HTTPONLY` | True | `config.py:37` |
| `SESSION_COOKIE_SAMESITE` | Lax | `config.py:38` |
| `SESSION_COOKIE_SECURE` | theo biến môi trường | `config.py:40` |
| `PERMANENT_SESSION_LIFETIME` | 8 giờ | `config.py:41` |

Đây là tin tốt: nếu xử lý xong mục 2.1 thì cookie duy nhất còn lại phục vụ đăng nhập, tức thuộc nhóm strictly necessary, và nhiều khả năng **không cần banner cookie**.

---

## 2. Năm phát hiện

### 2.1 Google Fonts nạp từ CDN trên mọi trang

`base.html:9,11` và `customer_base.html:9-12` gọi `fonts.googleapis.com` + `fonts.gstatic.com`. IP của mọi khách được gửi sang Google ngay khi mở trang, trước bất kỳ tương tác nào.

**Đây là phát hiện duy nhất KHÔNG bị chặn bởi việc đăng ký kinh doanh.** Xem mục 5, nên làm sớm.

### 2.2 Danh tính bên kiểm soát dữ liệu chưa được khai ở đâu cả

`base.html` dùng `business_id`, `branches`, `current_year` nhưng **không context processor nào cung cấp**. Jinja `Undefined` render thành chuỗi rỗng nên không ai thấy lỗi.

Đã verify bằng render thật:

```
footer Business ID -> 'Y-tunnus:'      (bỏ trống)
số branch render   -> 0
```

Cần wire lại khi có pháp nhân.

### 2.3 Khách không tự xoá tài khoản hay tải dữ liệu về được

Chỉ có `admin_delete_customer` do admin bấm (`routes.py:3249`). Không có route export.

### 2.4 Không có chính sách lưu trữ

Không gì tự xoá booking hay customer cũ. Chỉ `login_attempts` (dọn theo IP sau khi đăng nhập thành công) và `email_verifications` được dọn.

### 2.5 Form booking mời khách nhập thông tin dị ứng

Ô ghi chú bước 4 có placeholder *"Any special requests or allergies..."*, tức site chủ động mời khách nhập thông tin sức khoẻ vào `bookings.notes`. Trùng với `faq-content-spec.md` mục 5.3.

---

## 3. Thiết kế trang (đã chốt, chưa code)

**Design read:** greenfield, tài liệu pháp lý để đọc và tra cứu. Theo bảng dial của skill, nhóm *trust-first / regulated*.

**Dials:** `VARIANCE 3` / `MOTION 2` / `DENSITY 5`. Trang này không được "sáng tạo" theo nghĩa thị giác. Việc của nó là tìm thấy nhanh và hiểu đúng.

**Override có chủ đích:** skill cấm eyebrow đánh số mục (`01 / INDEX`). Văn bản pháp lý thì đánh số mục là quy ước thật vì người ta trích dẫn chéo theo số. **Giữ đánh số.**

### Cấu trúc

```
1  Đầu trang       tiêu đề + ngày cập nhật THẬT + 1 dòng tóm tắt
2  Mục lục         desktop: cột trái dính · mobile: khối gập <details>
3  Các mục đánh số 1..10, mỗi mục có id deep-link
4  Bảng kiểm kê    dữ liệu / mục đích / căn cứ / thời hạn / bên nhận
5  Quyền của bạn   liệt kê + cách thực hiện
6  Liên hệ         pháp nhân + email phụ trách dữ liệu
```

Điểm khác wall-of-text thường gặp: **mục 4 là bảng thật**, không phải văn xuôi. Chính bảng ở mục 1.1 của tài liệu này. Chính xác hơn và dễ tra hơn, và nó đến từ schema chứ không phải template copy về.

### Kỹ thuật

- Prefix `.pp`, token theo thang chung `bd-` / `lp-` / `ms-` / `bk-` / `bkc-`
- `<details>` cho mục lục mobile
- Deep-link mọi mục
- **Print stylesheet** (người ta hay in hoặc lưu PDF trang này)
- `MOTION 2` nên gần như không animation

---

## 4. Quyền GDPR: phải ẩN DANH, không xoá

### 4.1 Vì sao không xoá được

Khách nào từng đặt lịch đều có `bookings`, mà `bookings → customers` là FK **được enforce**. Đã verify:

```
foreign_keys qua get_connection() -> 1        (db.py:18 bật PRAGMA)
DELETE FROM customers WHERE id=1  -> IntegrityError: FOREIGN KEY constraint failed
```

> ⚠️ **Bẫy khi kiểm tra lại sau này:** mở `sqlite3.connect()` thô sẽ thấy `PRAGMA foreign_keys → 0` vì SQLite mặc định tắt. Phải kiểm qua `get_connection()` của app. Tôi đã sập bẫy này một lần trong lúc audit.

Bảy bảng tham chiếu `customers.id`: `bookings`, `reviews`, `customer_memberships`, `loyalty_points_log`, `reward_redemptions`, `referrals` (×2).

Và kể cả bỏ chặn được cũng không nên: `invoices` treo trên `bookings`, mà hoá đơn phải giữ theo luật kế toán.

`delete_customer_admin` hiện tại chạy đúng như comment mô tả: xoá `customer_memberships` + `loyalty_points_log` (bookkeeping 1:1), rồi để FK chặn nếu còn `bookings` / `reviews` / `reward_redemptions` / `referrals`.

### 4.2 Đặc tả ẩn danh

| Bảng | Xử lý |
|---|---|
| `customers` | `full_name` → nhãn tombstone · `email`, `phone`, `date_of_birth`, `notes` → NULL · xoá file avatar khỏi đĩa |
| `users` | `email` → NULL · `password_hash` → NULL · `oauth_sub` → NULL · `is_active` → 0 |
| `bookings` | `notes` → NULL (ô có thể chứa thông tin dị ứng, xem 2.5) |
| `invoices`, `loyalty_points_log`, `bookings` | **giữ nguyên hàng**, chỉ còn ID không gắn với người thật |

Lịch sử doanh thu và báo cáo không vỡ. Dữ liệu định danh biến mất.

Chặn thao tác nếu khách còn **lịch hẹn sắp tới** hoặc **subscription Stripe đang chạy**.

### 4.3 Đặc tả export

`GET /customer/my-data` → JSON toàn bộ dữ liệu của khách, 8 bảng: `users`, `customers`, `bookings`, `invoices`, `loyalty_points_log`, `reward_redemptions`, `customer_memberships`, `reviews`.

JSON là đúng định dạng cho quyền chuyển dữ liệu (yêu cầu "structured, commonly used, machine-readable").

---

## 5. Ba mảng công việc, theo thứ tự

### Mảng A · Self-host font. KHÔNG bị chặn, làm được ngay

```
A1. Tải Plus Jakarta Sans + Material Symbols Outlined về app/static/fonts/
    → verify: file tồn tại, đúng woff2
A2. @font-face + font-display: swap trong base.css
    → verify: 0 request tới fonts.googleapis.com / gstatic
A3. Gỡ 6 thẻ <link> Google ở base.html + customer_base.html
    → verify: grep googleapis = 0 trong templates
A4. Kiểm glyph tiếng Việt (dấu) và tiếng Phần (ä ö) còn đủ
    → verify: render 3 ngôn ngữ, so mắt thường
```

Lợi ích độc lập với pháp lý: bớt 2 domain phải phân giải DNS và bắt tay TLS trước khi render chữ; font tự chủ, Google đổi gì cũng không ảnh hưởng.

### Mảng B · Quyền GDPR. Nửa chặn

Bản thân chức năng không cần pháp nhân, nhưng 2 trong 4 quyết định ở mục 7 lại cần. Để cùng mảng C.

```
B1. GET /customer/my-data → JSON 8 bảng
B2. POST /customer/delete-account → ẩn danh theo 4.2
B3. UI trong trang hồ sơ: 2 nút + modal xác nhận gõ lại email
```

### Mảng C · Trang Privacy Policy. Chặn tới khi có pháp nhân

```
C1. Wire business_id / branches / current_year qua context processor
C2. Route GET /privacy + nối link footer
C3. privacy.html + privacy.css (prefix .pp)
C4. Dịch
```

---

## 6. Năm dữ kiện hành chính cần có

Không có thì không viết được mục 6 của trang, và đó là mục bắt buộc:

1. **Tên pháp nhân đầy đủ** và **Y-tunnus**
2. **Địa chỉ đăng ký** (Kyyhkysmäki 9, 02650 Espoo là địa chỉ tiệm hay địa chỉ pháp nhân?)
3. **Email phụ trách dữ liệu** (có thể trùng email liên hệ chung)
4. **Thời hạn lưu** từng nhóm dữ liệu. Hoá đơn theo luật kế toán Phần Lan có yêu cầu tối thiểu, cần xác nhận con số
5. Có **chi nhánh** nào khác ngoài Espoo không (`branches` đang rỗng)

---

## 7. Bốn quyết định sản phẩm cần chốt

1. **Nhãn tombstone** cho tài khoản đã ẩn danh: `Deleted account`, hay giữ chữ cái đầu kiểu `D. H. D.`? Nhãn này hiện trong lịch sử booking phía admin và staff.
2. **`stripe_customer_id`**: giữ lại để đối soát hoá đơn, hay gọi API xoá luôn khách bên Stripe? Xoá bên Stripe không hoàn tác được.
3. **Reviews**: khách viết đánh giá công khai rồi xoá tài khoản. Giữ nội dung và ẩn tên, hay xoá luôn đánh giá?
4. **Thời hạn lưu** (trùng mục 6.4).

---

## 8. Ranh giới

**Làm được, và làm tốt:** trang, bố cục, mục lục, deep-link, print style, và **bảng kiểm kê dữ liệu chính xác** rút từ schema. Phần kiểm kê là phần khó nhất và đã có dữ liệu thật, nằm ở mục 1.

**Không làm:** soạn văn bản pháp lý ràng buộc rồi bảo dùng được luôn. Dựng được khung mục và bản nháp mô tả **sự thật kỹ thuật**, nhưng câu chữ cuối, căn cứ pháp lý cho từng loại dữ liệu, và thời hạn lưu trữ phải do người có chuyên môn quyết. Một bản trông chuẩn mà không ai duyệt thì nguy hiểm hơn là chưa có.

---

## 9. Việc cần làm khi mở khoá

```
1. Có Y-tunnus và pháp nhân → điền 5 dữ kiện mục 6
2. Chốt 4 quyết định mục 7
3. Rà lại mục 1: schema có đổi gì từ 2026-08-09 không
4. Làm mảng A (làm sớm được, không cần đợi 1 và 2)
5. Làm mảng C, rồi mảng B
6. Người có chuyên môn duyệt câu chữ TRƯỚC khi nhận khách thật đầu tiên
```
