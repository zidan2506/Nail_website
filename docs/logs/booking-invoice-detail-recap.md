# Redesign UI khách hàng: Booking details + Invoice detail

**Ngày:** 2026-08-08 · **Phạm vi:** `/customer/my-booking/booking_id=<id>` và `/customer/history/invoice/<id>` (viết lại cả hai trang) · **Trạng thái:** ⚠️ code xong, `@media print` chưa xem preview thật, chưa chạy với DB thật qua trình duyệt, chưa deploy

Mảnh cuối của bộ portal khách hàng. Nối tiếp `docs/CUSTOMER_UI_REDESIGN.md` (My bookings + Dashboard) và `docs/logs/customer-history-mobile-recap.md` (History). Hai trang này là hai trang duy nhất còn giữ ngôn ngữ thị giác cũ.

---

## 1. Quyết định mở đầu: giữ page, không đổi sang modal

Câu hỏi ban đầu của user không phải "redesign thế nào" mà **"có nên xoá hẳn hai page này và thay bằng modal popup"**. Đáng ghi lại vì nó quyết định toàn bộ phần còn lại.

Kết luận: **giữ page riêng.** Không phải vì "page tốt hơn modal" nói chung, mà vì nội dung cụ thể của hai trang này không phù hợp làm modal:

| Lý do | Bằng chứng trong repo |
|---|---|
| **Invoice là chứng từ, cần URL** | `invoice_detail.html` có `window.print()`. Hoá đơn phải bookmark / gửi mail / in được. Modal không có URL, refresh là mất |
| **Print từ trong modal là địa ngục CSS** | Phải ẩn cả page phía sau, bỏ scroll-lock, ép modal về `position: static`. Với page riêng thì print gần như free |
| **Nội dung quá lớn** | `view_booking_details.html` có 6 khối gồm ảnh map 220px. Nhồi vào modal ở mobile là scroll lồng trong scroll, iOS Safari hay bị scroll xuyên ra body |
| **Modal không loại bỏ được navigation** | Nút Reschedule vẫn dẫn sang page `customer_reschedule`. Trả giá cho modal mà không thu được lợi ích "không rời trang" |
| **Ở mobile, modal full-screen CHÍNH LÀ một page** | Nhưng mất back gesture, deep link, refresh, và phải tự viết focus trap + History API |
| **Rủi ro riêng của codebase** | Không có reset `box-sizing: border-box` toàn cục. Modal là chỗ dễ vỡ nhất vì `width: 100%` + `padding` là tràn ngang ở 360px |

Chỗ modal **thực sự** đáng dùng: hành động ngắn (xác nhận huỷ). Tiền lệ đúng đã có sẵn: `redeem_confirm_modal.html` và modal cancel của My bookings. Trang Booking details nay dùng lại đúng modal đó (xem mục 3).

---

## 2. Audit trạng thái cũ

### `view_booking_details.html`

| Vấn đề | Chi tiết |
|---|---|
| Mobile được vá, không được thiết kế | `booking-details-layout` là grid `1.85fr 0.9fr`, ≤1100px sập 1 cột thành 6 card xếp dọc. Ảnh map + contact card nằm cuối, dưới ~1200px scroll |
| Không kế thừa gì từ bộ mới | Không plum surface, không khối ngày `[14]/[AUG]`, không ledger row. Là trang duy nhất còn `.btn-outline-pink` |
| **Fake data cho mọi lịch hẹn** | `:73` `Senior Artist • ★ 4.9` hardcode cho **mọi** staff. `:101` một đoạn notes tiếng Anh generic hardcode cho **mọi** booking |
| Contact là text tĩnh | Số điện thoại và email in ra `<span>`, ở mobile không bấm được |
| Cancel không có xác nhận | `:80` submit POST trực tiếp. My bookings đã có modal confirm cho **đúng hành động này**. Cùng một việc, hai cách xử lý |
| Status in ra thô | `{{ status }}` từ DB, luôn tiếng Anh kể cả UI là FI/VI |

### `invoice_detail.html`

| Vấn đề | Chi tiết |
|---|---|
| **Sai đơn vị tiền** | 4 chỗ hardcode `${{ "%.2f"\|format(...) }}` (`:39, :82, :121, :127`). Salon ở Espoo, app có filter `format_currency`, và `view_booking_details` dùng đúng filter đó. Trang này in ra dollar |
| 4 stat-card lặp lại chính nó | Invoice Date / Total / Payment Method / Status ở `:27-58`, rồi **cả bốn xuất hiện lại** ở `details-grid` + `payment-summary`. Đúng lỗi "4 stat-card ăn hết màn hình đầu" đã sửa ở History |
| **Nút Download PDF in ra cả sidebar** | `:143` gọi `window.print()`, mà grep toàn repo: **không có một dòng `@media print` nào**. Bản in gồm hamburger, sidebar, nav |
| Status không dịch | `:54` `invoice.status \| upper` in thẳng chuỗi DB |
| Số không thẳng hàng | Không có `tabular-nums`. Đây là trang duy nhất mà cột tiền thẳng hàng là bắt buộc |
| Em-dash trong `<title>` | `:3`, ký tự U+2014 nằm giữa số hoá đơn và nhãn |

### Xác nhận trước khi thiết kế

Mobile **không có bottom nav**: `customer_base.css:562-639` chỉ có topbar sticky (`z-index: 120`, cao 56px), drawer (`200`), scrim (`150`). Nên đáy màn hình là chỗ trống, dùng được cho action bar dính đáy ở `z-index: 100`.

---

## 3. Booking details: cấu trúc mới

Prefix CSS: `bd-`. Token lấy **đúng giá trị** của `bk-` (không import chéo được: hai trang nạp hai file CSS rời).

### Nét riêng của trang

Trang này có hai thứ ba trang kia không có, nên chúng thành hai điểm nhấn thay vì bị nhét vào sidebar card:

1. **Địa điểm** (`.bd-place`) - ảnh bản đồ là điểm nhìn thứ hai
2. **Hành động phá huỷ** (`.bd-actionbar`) - dính đáy ở mobile

### Information architecture

| Trước | Sau |
|---|---|
| `booking-summary-card` trắng, badge rời | `.bd-focus` nền plum, badge cạnh tên dịch vụ |
| Ngày dạng `Aug 14` / `Thu` chữ thường | Khối ngày `[14]/[AUG]`, motif của `.bk-row` |
| 6 card xếp dọc ở mobile | `.bd-rail`: hàng phẳng ngăn bằng hairline |
| Notes generic hardcode | Bỏ |
| `Senior Artist • ★ 4.9` | Bỏ. Artist còn avatar + tên thật |
| (không có) | **Video minh hoạ** (`Demo video`), dưới Service Description |
| Contact là `<span>` | `tel:` + `mailto:` bấm được |
| Nút trôi giữa trang | Action bar dính đáy ở mobile, hàng nút tĩnh ở desktop |
| Cancel submit thẳng | Modal xác nhận dùng chung với My bookings |

### Vì sao badge hiện ở MỌI trạng thái ở đây

My bookings và History cố tình không dán badge mọi dòng. Quy ước đó chống **lặp trong danh sách**. Trang này chỉ có một object, không có gì để lặp, và trạng thái là lý do chính khách mở trang. Nên nó được nói thẳng bằng chữ.

### Plum chỉ dành cho lịch còn hiệu lực

`confirmed` / `pending` được bề mặt plum. `cancelled` / `completed` chuyển sang nền sáng (`.bd-focus--past`), và `cancelled` thì tên dịch vụ bị gạch. Lý do giống `.bk-focus--empty`: một khối tối to tướng cho việc đã xong là sai trọng lượng.

### Badge: một công thức cho bốn trạng thái

Bản đầu tiên bị user bắt lỗi, và đúng: `confirmed` được nền pearl 16% **không viền** (mờ tới mức chỉ còn thấy chữ trắng), còn `pending` được pill hổ phách **đục**. Hai cách vẽ cho cùng một loại vật.

Sửa thành một công thức duy nhất:

```
nền  = hue @ 10-14%
viền = hue @ 30-40%   <- thứ giữ hình dạng pill nhìn thấy được ở mọi hue
chữ  = cùng hue, đủ tương phản trên bề mặt của nó
```

| Trạng thái | Nằm trên | Chữ | Ratio |
|---|---|---|---|
| `confirmed` | plum | `#FBF4F8` pearl | ~11:1 |
| `pending` | plum | `#F4DFA8` hổ phách **sáng** | ~8:1 |
| `completed` | nền sáng | `#ab2261` accent | |
| `cancelled` | nền sáng | `#B03A4A` danger | |

`pending` phải đổi từ hổ phách đậm `#7A5A11` (giá trị của `.bk-flag`) sang bản sáng: màu đậm đó dùng được ở My bookings vì badge nằm trên nền **trắng**, còn ở đây nó nằm trên plum và sẽ không đọc được.

### Badge nằm cạnh tên dịch vụ, và cái bẫy kèm theo

User thích badge inline hơn là đứng riêng một dòng phía trên. Đúng motif `.bk-focus__service`. Nhưng phải bọc tên trong `.bd-focus__name` riêng: trạng thái `cancelled` gạch ngang tên, mà để chữ trần trong `<h2>` thì **gạch ăn luôn cả badge** bên cạnh. `.bk-focus__service` bên My bookings không gặp vì nó không có state `cancelled`.

### Video minh hoạ: dùng lại hệ sẵn có, không dựng gì mới

Hệ video đã có từ `docs/SERVICE_VIDEO_MODAL.md`: cột `services.video_url`, filter `video_src`, pattern `<video controls preload="none" playsinline>` với `poster` là ảnh service.

Trang này chỉ cần:
- `routes.py` truyền thêm `service_video=service["video_url"]` và `service_image=service["image"]` (`get_service_by_id` là `SELECT *` nên đã có sẵn, **không đụng `db.py`**)
- Template `{% set video = service_video | video_src %}{% if video %}`

**Không đọc `video_status`**, theo đúng quy ước đã lập: `video_url` chỉ được ghi khi transcode xong, nên trang không bao giờ thấy video dở.

Khung `aspect-ratio: 16/9` nền tối `#1E0C16` + `object-fit: contain`: video dọc 9:16 letterbox trông có chủ ý thay vì bị crop mất tay. Cùng quy ước với `.svc-detail__video`.

### Modal cancel: dùng chung JS, và cái giá phải trả

Trang này nạp lại `js/my_booking.js` để dùng đúng luồng xác nhận huỷ. JS bind theo `.bk-cancel-form` và các id `cancel-modal-*`, nên markup modal giữ **nguyên tên class `bk-` và nguyên các id đó**, dù trang dùng prefix `bd-`. Đổi tên là phải fork JS.

`my_booking.js` chạy được trên trang này không cần sửa một dòng: `querySelector(".bk-tabs")` trả `null` nhưng biến đó chỉ dùng trong `if (tabList)`, và `querySelectorAll(".bk-tab")` rỗng nên `forEach` không chạy. Nó tự dừng ở `if (!cancelModal) return`.

**Cái giá:** ~250 dòng CSS modal bị copy từ `my_bookings.css` sang `booking_details.css`. Sửa modal thì phải sửa hai chỗ. Cách hết trùng là tách modal ra một file CSS riêng nạp ở cả hai trang, nhưng làm vậy phải đụng `my_bookings.css` đã ship. Đã nêu cho user, user chưa yêu cầu tách.

Script chỉ nạp khi `status in ('confirmed', 'pending')`, vì chỉ hai trạng thái đó có form huỷ.

### Lỗi tự gây ra và đã sửa: rail không có lề ngang

Đặt `.bd-rail { padding: 4px 2px }` với suy nghĩ "rail là hàng phẳng, không phải card". Nhưng lại cho nó `background: #ffffff`, mà nền trang là `#f8f4f6` (`customer_base.css:19`) nên bề mặt trắng đó **nhìn thấy được**, và chữ dán vào mép khối. Hai quyết định chống nhau. User bắt được.

Sửa: `padding: 4px 22px` (mobile 18px), thêm `border: 1px solid` và bo góc 20px để cùng họ với `.bd-place` / `.bd-contact`. `.bd-rail__item` thành `padding: 20px 0` nên hairline chạy hết vùng nội dung mà không chạm viền khối.

> **Bài học:** "không phải card" là một ý định, không phải một thuộc tính CSS. Nếu khối có nền khác nền trang thì nó **là** một bề mặt, và phải có lề như mọi bề mặt. Muốn thật sự không-card thì bỏ `background` đi.

### Không dùng full-bleed

Có cân nhắc cho plum panel và ảnh map bleed ra sát mép ở mobile. **Bỏ.** `.bd` nằm trong `.dashboard-main` vốn cũng có `padding: 20px 16px`, nên negative margin chỉ bù được padding của `.bd` và bleed ra được một nửa, trông như lỗi layout. Bù cả hai lớp thì vỡ ngay khi padding của `.dashboard-main` đổi. Điểm nhấn lấy từ tỉ lệ ảnh, không từ việc phá lề.

### Motion

Ba chuyển động, mỗi cái trả lời một câu hỏi:

| Chuyển động | Trả lời |
|---|---|
| Panel + rail + side dâng lên so le (`--bd-i` × 60ms) | "trang vừa mở" |
| Action bar trượt lên từ đáy | "đây là hành động, luôn trong tầm tay" |
| `scale(0.98)` khi ấn | phản hồi chạm |

Có block `prefers-reduced-motion: reduce`. Cũng có `prefers-reduced-transparency: reduce` cho action bar: nền `rgba(255,255,255,0.92)` + `backdrop-filter` mà bị tắt trong suốt thì chữ dưới nó lộ qua, nên phải đục hẳn.

---

## 4. Invoice detail: trang giấy

Prefix CSS: `inv-`.

### Quyết định lớn: trang này KHÔNG có băng plum

User chốt phương án "trang giấy sáng" sau khi được đưa cả hai lựa chọn. Hai lý do:

1. **Nhịp.** Bốn trang liên tiếp mở đầu bằng một băng plum tối thì thành template.
2. **Chức năng.** Nền tối in ra là tốn mực, và phần lớn trình duyệt bỏ nền khi in nên chữ pearl trên plum thành pearl trên trắng, tức là vô hình.

Nên nó là một tờ giấy: bề mặt trắng duy nhất, khổ **760px** (ba trang kia 1180px), mã hoá đơn dùng mono, số căn phải bằng `tabular-nums`. Palette không đổi một token nào.

### Information architecture

| Trước | Sau |
|---|---|
| 4 stat-card (Invoice Date / Total / Payment / Status) | Bỏ. Số tiền + trạng thái lên `.inv-head`, hai cái còn lại vào `<dl>` |
| `details-grid` 2 card (Service + Appointment) | Bỏ. Tên + hạng mục + thời lượng lên `.inv-service` |
| `payment-summary` với line item + total | `.inv-sum`, một dòng, gạch đôi `3px double` |
| Nút Download trong `payment-footer` | `.inv-foot` **ngoài** tờ giấy: nút không phải nội dung của chứng từ |

Còn lại **5 hàng** trong `<dl>`, không hàng nào lặp thứ đã nói ở trên: Date · Time Window · Assigned Stylist · Invoice Date · Payment Method.

Đã cân nhắc thêm hàng `Base Price` cho tổng có nguồn gốc, rồi bỏ: DB không có field giảm giá nào nên `service_price` luôn bằng `amount`, tức là một dòng trùng lặp.

### Cột giá trị thẳng hàng: thứ trang này làm được mà History không

`<dl>` là **một grid duy nhất** (`grid-template-columns: auto minmax(0, 1fr)`), nên mọi hàng dùng chung track và cột giá trị neo vào một mép. History ghi "cột giá không thẳng hàng" vào tồn đọng vì ở đó **mỗi `.ch-row` là một grid riêng**, track `auto` co theo nội dung từng hàng. Ở đây làm được vì trang chỉ có một danh sách và không có nút trong hàng.

Ở mobile hàng **giữ hai cột**, không đổ thành hai dòng: nhãn và giá trị nằm cùng tầm mắt mới đọc được, đó là toàn bộ lý do dùng `<dl>`.

### `@media print`

Nút `window.print()` có từ trước nhưng repo không có một dòng print CSS nào. Khối print làm:

- Ẩn `.customer-topbar` / `.customer-navbg` / `.dashboard-sidebar`
- `.customer-dashboard` về `display: block`, nền trắng; `.dashboard-main` về `padding: 0`
- Ẩn `.inv-back` và `.inv-foot`
- Tờ giấy bỏ bo góc, viền, đổ bóng, animation
- `@page { margin: 16mm }`
- Badge chuyển sang **viền đen không nền**: khi trình duyệt bỏ màu nền thì viền là thứ duy nhất còn giữ được nghĩa
- Ẩn `.inv-who__avatar`: avatar không mang thông tin trên bản in, tên đã ngay cạnh

Các selector `.dashboard-*` / `.customer-*` thuộc `customer_base.css`. Chỉ đụng chúng **trong `@media print`**, và chỉ file này nạp khối đó, nên không rò sang trang khác. Dùng `!important` vì `customer_base.css` cũng khai `.customer-topbar` trong một media query, và lỗi print rất khó phát hiện.

`booking_details.css` cũng có một khối print nhỏ hơn (khách có thể in lịch hẹn ra để cầm đi), nhưng **không** ẩn sidebar vì trang đó không có nút in.

---

## 5. i18n: 1 msgid mới

Đã audit `.po` trước khi viết chữ. Toàn bộ chuỗi của Invoice detail và gần hết của Booking details đã có sẵn **và đã dịch cả fi/vi**: `Booking Details`, `Back to Appointments`, `Add to Calendar`, `mins`, `Service Description`, `Artist`, `Reschedule`, `Cancel`, `Address`, `Get Directions`, `Salon Contact`, `Confirmed`, `Pending`, `Cancelled`, `Completed`, `Paid`, `Refunded`, `Date`, `Time Window`, `Assigned Stylist`, `Invoice Date`, `Payment Method`, `Total Paid Amount`, `Download PDF Invoice`, `Back to Invoices`, `Invoice Detail`, `min`, và toàn bộ chuỗi của modal cancel.

Một msgid **phải** thêm:

| msgid | en | fi | vi |
|---|---|---|---|
| `Demo video` | (rỗng, fallback msgid) | Esittelyvideo | Video minh họa |

Nút gọi salon **không** cần msgid `Call` (chưa có trong catalog): nó hiện chính số điện thoại, tức là dữ liệu chứ không phải chuỗi dịch.

Cách thêm: **append tay** vào cuối 3 file `.po` + `messages.pot` rồi `python -m babel.messages.frontend compile -d app/translations`. Không chạy `extract`/`update` để tránh viết lại toàn bộ file.

> ⚠️ Vẫn đúng cái bẫy của recap trước: phải compile `.mo` **trước** khi render, không thì chuỗi mới lọt ra dạng tiếng Anh. Đã kiểm mtime của `.mo` mới hơn `.po` trước khi test.

Trạng thái từ DB nay được dịch qua bảng map trong template (`status_labels`), giống cách History đã làm. Cả hai trang trước đó in thẳng chuỗi DB.

---

## 6. Bug đã sửa

| Bug | Trước | Sau |
|---|---|---|
| **Hoá đơn in ra dollar** | 4 chỗ `${{ "%.2f"\|format(...) }}` | `\| format_currency` → `45,00 €` |
| **Print ra cả sidebar** | Không có `@media print` ở đâu trong repo | Khối print đầy đủ |
| Status không dịch | `{{ status }}` / `invoice.status \| upper` | Map qua `_()`, 3 locale |
| Contact không bấm được ở mobile | `<span>+358 465 978 425</span>` | `tel:` + `mailto:` |
| Cancel không xác nhận | POST thẳng | Modal dùng chung với My bookings |
| Fake data | `Senior Artist • ★ 4.9` + notes generic hardcode | Bỏ |
| Em-dash trong `<title>` | `INV-xxx` + U+2014 + `Invoice Detail` | `INV-xxx - Invoice Detail` |

---

## 7. Files

| File | Trước | Sau | Nội dung |
|---|---|---|---|
| `app/templates/customer/view_booking_details.html` | 152 | 247 | Viết lại |
| `app/static/css/customer/booking_details.css` | 676 | 924 | Viết lại, prefix `bd-`. **~250 dòng là modal copy** |
| `app/templates/customer/invoice_detail.html` | 150 | **93** | Viết lại, ngắn hơn 38% mà không mất thông tin |
| `app/static/css/customer/invoice_detail.css` | 305 | 464 | Viết lại, prefix `inv-`. Có `@media print` |
| `app/routes.py` | | | Bỏ `booking_date1`, thêm `service_image` + `service_video` |
| `app/translations/{en,fi,vi}/LC_MESSAGES/messages.po` + `.mo` | | | +1 msgid |
| `messages.pot` | | | +1 msgid |

**Không đụng:** `app/database/db.py`, `app/template_filters.py`, `customer_base.html`, `my_booking.js`, `my_bookings.css`, `my_bookings.html`, các trang khác, URL slug, nav label.

`invoice_detail.html` ngắn đi 57 dòng vì bỏ 4 stat-card và `details-grid` vốn lặp lại chính nó. `booking_details.css` dài ra chủ yếu vì modal copy và hai khối print / reduced-transparency.

Diff `routes.py` có 2 dòng chỉ đổi trailing whitespace trên dòng trống, phát sinh khi viết lại khối `render_template`. Không liên quan tới yêu cầu, để nguyên vì thêm lại trailing space là kỳ quái hơn.

---

## 8. Đã verify / chưa verify

### Đã verify

Toàn bộ bằng render qua **Jinja env thật của app** (`create_app()`, filter và loader thật), **không dùng browser** (xem mục 10).

**Booking details**, 4 trạng thái:

| Trạng thái | Action bar | Reschedule | Cancel + modal | JS nạp | Add to Calendar | Nền | Badge (vi) |
|---|---|---|---|---|---|---|---|
| `confirmed` | có | có | có | có | có | plum | Đã xác nhận |
| `pending` | có | **không** | có | có | có | plum | Chờ duyệt |
| `cancelled` | không | không | không | không | không | sáng, tên gạch | Đã hủy |
| `completed` | không | không | không | không | không | sáng | Hoàn thành |

- Badge inline trong `<h2>` ở cả 4 trạng thái, tên bọc trong `.bd-focus__name` riêng
- `tel:+358465978425` và `mailto:dahacaree@gmail.com` có mặt
- Khối Service Description tự biến mất khi `service_description` rỗng (3 rail item → 2)
- Video: `service_video=None` → khối biến mất (2 item); `='test-service.mp4'` → 3 item, `src=/static/uploads/videos/test-service.mp4`, `poster=/static/images/services/classic-manicure.webp`
- Nhãn video dịch đúng 3 locale: `Esittelyvideo` / `Video minh họa` / `Demo video`
- Grep toàn `app/`: không còn tham chiếu `date1` / `booking_date1`
- `create_app()` load sạch, 110 route

**Invoice detail**, 3 trạng thái × 3 locale (mỗi lần một `test_request_context` riêng, vì Flask-Babel cache locale trong một request):

- Badge: `Maksettu`/`Hyvitetty` · `Đã thanh toán`/`Đã hoàn tiền` · `Paid`/`Refunded`
- Nhãn hàng: `Päivä, Aikaikkuna, Osoitettu stylisti, Laskun päivä, Maksutapa` · `Ngày, Khung giờ, Thợ được phân công, Ngày hóa đơn, Phương thức thanh toán` · bản en
- Tiền render `45,00 €` (nbsp giữa số và ký hiệu). **0 ký tự `$`** trong template
- 5 `<dt>` / 5 `<dd>`. `stat-card` và `details-grid` không còn trong output
- `window.print()` còn nguyên

**Cả hai trang:** 0 em-dash và 0 en-dash trong cả 4 file · CSS braces cân bằng (`booking_details` 161/161, `invoice_detail` 73/73) · `format_currency` dùng `float(value)` nên `invoice.amount` (REAL) không có vấn đề kiểu dữ liệu

### Chưa verify

| Việc | Ghi chú |
|---|---|
| **`@media print`** | Không kiểm được bằng render. Cần mở print preview thật. Nếu sidebar vẫn lọt vào bản in thì có một rule nào đó `!important` chưa thắng |
| Chạy app với DB thật qua trình duyệt | Toàn bộ test dùng stub context |
| Video play thật | Chỉ verify `src` / `poster` render đúng. Chưa bấm play, chưa xem letterbox với video dọc |
| Action bar trên Safari iOS thật | `position: fixed` + `env(safe-area-inset-bottom)`. Chrome thì đúng |
| Sheet modal trên Safari iOS thật | Cùng rủi ro đã ghi ở recap History |
| Bản dịch VI trên trình duyệt | Mới thấy qua render |
| `prefers-reduced-motion` và `prefers-reduced-transparency` | Có block CSS nhưng chưa bật thử |
| Ảnh map thật ở tỉ lệ mới | `.bd-place__map` cao 190/210/180px tuỳ breakpoint, ảnh `nail_studio.jpg` `object-fit: cover` |

---

## 9. Còn tồn đọng

| Việc | Ghi chú |
|---|---|
| **Địa chỉ salon lệch nhau giữa hai chỗ** | Template hiển thị `Kyykysmäki 9 A`, còn `routes.py:793` dùng `Kyyhkysmäki 9` để dựng link Google Maps. Khác nhau ở chữ `h` và ở ` A`. Giữ nguyên chuỗi hiển thị của bản cũ vì không tự ý sửa địa chỉ thật của salon. **Đã nêu cho user, chưa được chốt** |
| **`video_url` trỏ vào bản chưa nén** | DB có `video_url = 'test-service.mp4'` (**53 MB** bản gốc) chứ không phải `test-service-720p.mp4` (3.3 MB) nằm cùng thư mục. Trang `/services` cũng dùng đúng giá trị đó nên **không phải regression**. `preload="none"` nên chỉ tốn khi khách bấm play. Sửa 1 dòng trong DB là xong |
| **`description` không được dịch** | Template dùng `service_description` = `service["description"]` thô, trong khi bảng `services` có `description_fi` / `description_vi` và repo có helper `tr()`. Lỗi có sẵn từ trước, nằm ngay dòng đang chạm nhưng không thuộc yêu cầu nên không tự sửa |
| **250 dòng CSS modal trùng lặp** | Xem mục 3. Cách gỡ: tách ra file CSS riêng nạp ở cả hai trang |
| Ngày tháng in ra tiếng Anh | `format_date` là `strftime` thuần, không qua locale. `date2` (`%a`) và `[AUG]` đều tiếng Anh. Cả app đang thế nên không phải regression. Cách gỡ như recap History đã ghi: thêm jinja global bọc `flask_babel.format_date` |
| Context thừa của invoice | `get_invoice_detail_by_id` vẫn SELECT `customer_name`, `customer_email`, `customer_phone`, `service_price` mà template mới không dùng. Là field của một join dùng chung, không phải context var riêng, nên để nguyên |
| Không có dark mode | Cả app không có dark mode ở đâu |

---

## 10. Ghi chú cho lần sau

- **Không tự động verify bằng Claude-in-Chrome.** User chốt rule này giữa task: browser automation tốn rất nhiều quota và token, chỉ được dùng khi user cho phép rõ ràng trong lượt đó. Verify bằng render / grep / test thì bình thường. Đã lưu vào memory
- **Render nhiều locale phải mỗi lần một `test_request_context` riêng.** Flask-Babel resolve locale một lần rồi cache cho request đó, nên set `session['lang']` trong vòng lặp bên trong **một** context sẽ ra cùng một ngôn ngữ cho mọi vòng. Mất một vòng debug vì tưởng bản dịch fi bị sai
- **`grep -c` trả exit code 1 khi đếm được 0.** Nối bằng `&&` là các lệnh sau không chạy. Dùng `;` khi kiểm "phải bằng 0"
- **stdout của Python trên Windows là cp1252.** `print` chuỗi tiếng Việt là `UnicodeEncodeError`, dù việc **ghi file** với `encoding="utf-8"` đã thành công. Bọc `sys.stdout` bằng `TextIOWrapper(..., encoding='utf-8')`. Đừng nhìn traceback rồi kết luận file chưa được ghi
- **Nền trang là `#f8f4f6`, không phải trắng.** Bất kỳ khối `background: #ffffff` nào cũng là một bề mặt nhìn thấy được và phải có lề ngang. Xem mục 3
- **Muốn dùng chung JS thì phải dùng chung tên class và id**, kể cả khi trang có prefix riêng. Đổi tên là fork JS
- **Kiểm `!important` có thật sự cần trước khi dùng.** `{% block extra_css %}` ở `customer_base.html:13` nạp **sau** `customer_base.css`, nên CSS của trang thắng ở cùng specificity. Chỗ duy nhất dùng `!important` là khối print, vì ở đó `@media (max-width: 860px)` của base cũng apply khi in
- Icon dùng **Material Symbols** (cả app đang dùng), không đổi sang Phosphor/Tabler dù skill design ưu tiên
- Trước khi thêm chữ mới, audit `app/translations/*/LC_MESSAGES/messages.po`. Hai trang này chỉ cần **1 msgid mới** nhờ vậy
- Codebase không có reset `box-sizing: border-box` toàn cục. CSS mới tự khai trong phạm vi prefix
