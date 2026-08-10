# Thông báo từ Admin

**Ngày:** 2026-08-10 · **Phạm vi:** `/admin/notifications` · public pages · portal khách hàng · **Trạng thái:** ✅ code xong, chưa deploy

Hai kênh thông báo do admin phát:

1. **Public notice** - dòng chữ chạy ngang trên mọi trang công khai, dính dưới navbar. Dùng cho thông báo toàn hệ thống (nghỉ lễ, bảo trì, khuyến mãi).
2. **Customer notification** - tin vào hòm thư riêng của khách trên portal. Gửi được cho toàn bộ khách hoặc một khách cụ thể, tuỳ chọn gửi kèm email thật.

---

## 1. Vì sao làm

Trước đó admin không có cách nào phát thông báo. Chuông ở topbar admin (`admin_base.html`) là một chấm đỏ hard-code, **luôn sáng, không nối vào dữ liệu nào** - di sản của bản dựng UI ban đầu.

Nhu cầu thực tế: tiệm cần báo nghỉ lễ cho khách đã đặt lịch, và cần dán một dòng thông báo lên trang công khai mà không phải sửa code.

---

## 2. Các quyết định kiến trúc

Phần quan trọng nhất của tài liệu này. Đọc lại sau vài tháng sẽ hiểu vì sao không làm cách khác.

### 2.1 Read-log thay vì fan-out

Broadcast cho N khách = **1 dòng** trong `customer_notifications`, không phải N dòng. Trạng thái đọc nằm ở bảng riêng `notification_reads` (`notification_id`, `customer_id`).

Lý do:
- Sửa hoặc xoá một broadcast chỉ đụng 1 dòng, không phải N.
- Khách **đăng ký sau** vẫn thấy thông báo cũ. Fan-out thì không, vì lúc gửi chưa có họ trong bảng.

Đánh đổi: query hòm thư phải `LEFT JOIN` mỗi lần. Với quy mô một tiệm nail thì không đáng lo.

### 2.2 Tách 3 bảng, không gộp 1 bảng có cột `channel`

`carousel_slides` đang gộp 3 loại carousel vào một bảng bằng cột `carousel_key`, hệ quả là hơn nửa số cột luôn NULL. Không lặp lại lỗi đó.

Public notice và customer notification là hai thực thể khác nhau thật: public không có người nhận và không có trạng thái đọc; customer không có `sort_order` lẫn `is_active`. Gộp lại là để lại một đống cột chết.

### 2.3 Modal thay vì trang chi tiết cho từng thông báo

Nội dung một thông báo là 1 tiêu đề + vài câu, không có hành động con nào. Dựng cả một route cho từng đó nội dung là nặng hơn chính nội dung. Modal còn giữ được ngữ cảnh: đọc xong đóng, đọc tiếp cái kế, không phải bấm back mỗi lần.

**Nhược điểm của modal là không dán link được. Đã khử:** modal cũng là một URL thật.

- Row là `<a href="?n=<id>">`.
- Có JS: chặn điều hướng, mở modal tại chỗ, `pushState` cho URL khớp.
- Không JS: tải trang, server render sẵn modal đang mở.
- **Cả hai đường đều đánh dấu tin đó đã đọc.**

Nút Back đóng modal thay vì rời trang (`popstate`).

### 2.4 Dropdown chuông render sẵn ở server, không gọi AJAX

Context processor `inject_customer_notifications()` cấp luôn 5 tin gần nhất cho mọi trang customer. Bấm chuông là hiện ngay, không cần endpoint riêng, không cần trạng thái đang tải, không có khoảng trắng nhấp nháy.

Giá phải trả: thêm một query `LIMIT 5` mỗi request customer. Cùng bậc chi phí với `inject_customer_sidebar()` vốn đã chạy sẵn.

### 2.5 Email gửi ở thread nền, kết quả ghi vào DB

`send_email()` là blocking, timeout 10s mỗi địa chỉ. Broadcast đồng bộ sẽ treo request của admin hàng phút. Dùng lại đúng mẫu daemon-thread của `_start_video_transcode()`.

Hai điểm đáng ghi nhớ:

- **Chọn ngôn ngữ bằng cách đọc thẳng cột `title_fi` / `title_vi`**, không dùng `gettext()`. Thread nền không có request context nên locale selector không chạy được.
- **Kết quả ghi vào `email_sent` / `email_total` trong khối `finally`.** Không có hai cột này thì admin chỉ biết mình đã bấm gửi, muốn biết có tới nơi hay không phải mở log server. `finally` đảm bảo thread chết giữa chừng vẫn không kẹt vĩnh viễn ở trạng thái "đang gửi".

Một địa chỉ lỗi không chặn phần còn lại (`try/except EmailSendError: continue`).

### 2.6 Đánh dấu đã đọc theo TỪNG tin

Bản đầu đánh dấu đọc hết khi mở hòm thư. Cách đó gãy ngay khi có dropdown chuông: bấm "Xem tất cả" là badge về 0 dù chưa đọc chữ nào, và cột trạng thái mất sạch ý nghĩa.

Giờ chỉ tin nào được mở mới đánh dấu. Có nút "Đánh dấu đã đọc tất cả" riêng, và nút đó **chỉ hiện khi còn tin chưa đọc**.

### 2.7 Ép locale `vi` cho mọi path `/admin`

Toàn bộ template admin viết cứng tiếng Việt, nhưng flash message đi qua `gettext()` nên chạy theo bộ chọn ngôn ngữ của khách. Hệ quả: admin thấy thông báo **tiếng Phần Lan** xen giữa giao diện tiếng Việt (locale mặc định của site là `fi`).

Sửa 3 dòng trong `select_locale()`: `request.path.startswith("/admin")` thì luôn trả `"vi"`. Trang public và staff không bị ảnh hưởng. Phương án còn lại là dịch ~60 chuỗi flash sang FI/EN, nhưng UI admin vẫn toàn tiếng Việt nên sẽ lệch.

### 2.8 Chuông admin không có badge

Hệ thống này **một chiều admin → customer**. Admin không có hòm thư nên không tồn tại khái niệm "chưa đọc" cho họ. Gắn con số vào đó là bịa. Chấm đỏ cũ đã bỏ, chuông giờ chỉ là lối tắt tới `/admin/notifications`.

### 2.9 Public notice: bề mặt plum, không phải hồng

Hồng `--color-primary` là màu của mọi CTA trên site. Một dải hồng đặc chạy suốt ngay dưới nút "Book Now" là hai thứ tranh nhau. Dùng `--color-deep-plum` + chữ pearl: vẫn là cặp màu sẵn có của brand (portal đã dùng đúng cặp này), tương phản khoảng 13:1.

Dải **sticky ở `top: var(--nav-height)`**, tức dính ngay dưới navbar. Muốn hai lớp sticky xếp đúng tầng thì thứ tự DOM phải là header trước, dải sau.

---

## 3. Các bẫy đã gặp

Hai lỗi dưới đây chỉ lộ ra khi mở trình duyệt xem, đọc code không thấy.

### 3.1 `mask-image` khoét thủng cả nền của thanh

Ý định ban đầu: làm mờ chữ ở hai mép dải chạy bằng `mask-image: linear-gradient(90deg, transparent, #000 7%, ...)`.

Mask áp lên toàn bộ element, **kể cả background**. Kết quả là hai đầu dải trong suốt, lộ nguyên trang phía sau, trông như lỗi render.

Cách đúng: hai lớp phủ `::before` / `::after` gradient **màu plum** đè lên, `pointer-events: none`.

### 3.2 `display: grid` trên `<summary>` làm hỏng `<details>`

Bản đầu của hòm thư dùng `<details>` accordion, với `display: grid` đặt thẳng lên `<summary>` để dàn cột.

Chrome khi đó **thôi coi `<summary>` là nút đóng/mở**. Hệ quả: nội dung luôn hiện dù `<details>` đang đóng, và selector `[open]` không bao giờ khớp.

Cách đúng: giữ `<summary>` ở `display` mặc định (`list-item`), đưa grid xuống một `<span>` con.

> Bản hiện tại đã bỏ accordion, chuyển sang row + modal (mục 2.3). Ghi lại vì bẫy này sẽ gặp lại ở bất kỳ chỗ nào dùng `<details>`.

---

## 4. Schema

```
public_notices
  id · message / message_fi / message_vi · is_active · sort_order · created_at

customer_notifications
  id · target ('all' | 'customer') · customer_id
  title / title_fi / title_vi · body / body_fi / body_vi
  emailed · email_sent · email_total · created_at

notification_reads
  notification_id · customer_id · read_at        PK (notification_id, customer_id)
  FK notification_id -> customer_notifications ON DELETE CASCADE
```

Index: `idx_public_notices_active(is_active, sort_order)` · `idx_cust_notif_target(target, customer_id)`

Ý nghĩa 3 cột email:

| `emailed` | `email_sent` | Hiển thị ở admin |
|---|---|---|
| 0 | - | không hiện gì |
| 1 | NULL | Đang gửi email |
| 1 | = `email_total` | Đã gửi email X/Y |
| 1 | < `email_total` | Email lỗi Z/Y |

---

## 5. Routes

| Method | Path | Việc |
|---|---|---|
| GET | `/admin/notifications` | trang quản lý, 2 tab |
| POST | `/admin/notifications/public/create` | tạo dải chạy |
| POST | `/admin/notifications/public/<id>/update` | sửa |
| POST | `/admin/notifications/public/<id>/toggle` | bật/tắt |
| POST | `/admin/notifications/public/<id>/delete` | xoá |
| POST | `/admin/notifications/customer/send` | gửi tin (+ spawn thread email) |
| POST | `/admin/notifications/customer/<id>/delete` | xoá tin đã gửi |
| GET | `/customer/notifications` | hòm thư. `?n=<id>` mở modal, `?page=` phân trang |
| POST | `/customer/notifications/<id>/read` | đánh dấu 1 tin (đường JS) |
| POST | `/customer/notifications/read-all` | đánh dấu tất cả |

**Phân quyền:** cả `get_notification_for_customer()` lẫn `mark_notification_read()` đều lọc lại `target='all' OR customer_id=?` trong câu WHERE. Sửa tay `?n=` sang id của khách khác thì không mở được và cũng không ghi được dấu đọc.

---

## 6. File đã đụng

**Mới**
```
app/templates/admin/admin_notifications.html
app/templates/customer/customer_notifications.html
app/static/css/customer/customer_notifications.css
deploy/migrations/001_notifications.sql
```

**Sửa**
```
app/__init__.py                      select_locale() ép 'vi' cho /admin
app/database/schema.sql              3 bảng + 2 index
app/database/db.py                   CRUD 2 kênh, query hòm thư, read-log
app/routes.py                        7 route admin + 3 route customer,
                                     2 context processor, thread gửi email
app/templates/admin/admin_base.html  nav item + chuông topbar
app/templates/base.html              dải chạy ngang (đặt sau <header>)
app/templates/customer_base.html     chuông + dropdown ở topbar
app/static/css/base.css              .notice-bar + token --color-pearl
app/static/css/customer_base.css     topbar hiện mọi kích thước, chuông, dropdown
```

Prefix CSS: `nt-` (admin) · `nf-` (hòm thư) · `.notice-bar` (public) · `.bell-*` (dropdown).

---

## 7. i18n

Nội dung do admin nhập có cột `_fi` / `_vi`, render bằng `tr(obj, 'field')`, để trống thì fallback về bản EN. Đúng pattern của `services` / `rewards` / `carousel_slides`.

Chuỗi giao diện đã dịch đủ VI/FI và compile. **Template admin không dịch** (viết cứng tiếng Việt), đúng như 10 trang admin còn lại.

---

## 8. Deploy

`schema.sql` mở đầu bằng `DROP TABLE` nên **chỉ dùng khi khởi tạo DB mới**. DB production đã có dữ liệu thật nên không bao giờ đọc lại file đó.

```bash
sqlite3 /var/www/nail-app/app/database/database.db < deploy/migrations/001_notifications.sql
```

Chạy **trước** khi restart app. Bỏ qua bước này thì app crash ngay khi có khách vào portal. File chạy lại nhiều lần được (`IF NOT EXISTS`).

---

## 9. Giới hạn đã biết

Những thứ **cố ý không có**, không phải quên:

- **Public notice không hẹn lịch.** Chỉ bật/tắt tay. Thêm `start_at` / `end_at` sẽ phải lọc theo thời gian ở mọi request.
- **Không có trang chi tiết riêng cho từng thông báo.** Xem mục 2.3. Nếu sau này nội dung dài ra hoặc cần SEO thì phải làm trang thật, modal không thay thế được.
- **Mẫu số lượt đọc tính theo số khách hiện tại.** Broadcast cũ có mẫu số thay đổi khi có khách mới đăng ký. Muốn cố định thì phải chụp lại số lượng lúc gửi.
- **Không có retry cho email lỗi.** Admin thấy được số lỗi nhưng phải gửi lại tay.
- **Hòm thư phân trang 15 tin/trang, không có tìm kiếm hay lọc.**
