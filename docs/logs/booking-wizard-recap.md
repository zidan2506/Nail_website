# Redesign UI: Booking Wizard (Public + Customer)

**Ngày:** 2026-08-09 · **Phạm vi:** `/public/booking` + `/customer/booking` (viết lại toàn bộ CSS, tách JS dùng chung) + 6 chuỗi dịch mới · **Trạng thái:** ⚠️ code xong, đã render-test bằng test client với DB thật, **chưa xem trên trình duyệt**, chưa commit, chưa deploy

Nối tiếp `docs/logs/loyalty-points-recap.md` và `docs/logs/booking-invoice-detail-recap.md`. Đây là đợt đầu tiên chạm vào luồng đặt lịch, và là đợt duy nhất tới giờ mà **một file CSS phục vụ hai trang thuộc hai layout chủ khác nhau** (`base.html` và `customer_base.html`).

---

## 1. Phát hiện lúc audit: hai trang là bản sao của nhau

`public_booking.html` (650 dòng) và `customer_booking.html` (589 dòng) dùng chung `css/public/public_booking.css`, và markup gần như trùng khít. Khác nhau đúng hai chỗ:

| | public | customer |
|---|---|---|
| Số bước | 5 (có `Your Details`) | 4 |
| Loyalty points | không | có `data-points` + `#summary-points` + `multiplier` |

Nhưng **JS thì bị chép hai bản**, mỗi bản ~250 dòng, lệch nhau đúng hai đoạn trên. Mọi sửa lỗi từ trước tới nay đều phải làm hai lần.

Đã tách thành `app/static/js/booking_wizard.js`. Hai điểm khác biệt **không** xử lý bằng cờ cấu hình mà bằng feature-detect từ DOM:

```js
// Guest info: chỉ chạy khi trang có #full_name
var hasGuestStep = ['full_name','phone','email'].every(id => document.getElementById(id));

// Loyalty points: chỉ chạy khi trang có #summary-points
if (document.getElementById('summary-points')) { ... }
```

Lý do không dùng cờ: cờ phải được cả hai template khai đúng, và khai sai thì im lặng hỏng. Feature-detect thì nguồn sự thật là chính DOM đang có.

> **Bài học:** trước khi redesign hai trang "na ná nhau", diff chúng trước. Ở đây diff cho ra đúng 2 điểm, nghĩa là chi phí tách JS gần bằng 0 mà xoá được 250 dòng trùng.

---

## 2. Audit trạng thái cũ

### A. Lệch khỏi hệ thống portal

| Vấn đề | Chi tiết |
|---|---|
| **Màu xanh navy ngoài palette** | `--bk-navy: #0F172A` dùng cho **mọi** heading của cả hai trang. Portal đã chuẩn hoá ink `#2A1520` sau ba đợt trước |
| **Token khai trên `:root`** | File tự đặt 20 biến `--bk-*` lên `:root` toàn cục. `my_bookings.css` cũng có `--bk-surface` (giá trị khác: `#ffffff` vs `#fff8f8`) |
| Xám hồng rời rạc | `#efdee4` rải 9 chỗ, không phải token nào của hệ |
| `max-width: 896px` | `lp-` / `ms-` đều là 1180px |
| Title `clamp(28px, 5vw, 48px)` | 48px cho tiêu đề một bước wizard, căn giữa, trong khi cả portal đã chuyển sang căn trái |

### B. Prefix `bk-` bị bốn trang khác dùng lại

Đây là rủi ro thật khi sửa, nên đã đo trước:

| File | Số class `bk-` | Nghĩa |
|---|---|---|
| `my_bookings.css` | 257 | `bk-btn`, `bk-accent`, `bk-surface` |
| `admin_bookings.html` | 249 | `bk-action-btn`, `bk-avatar`, `bk-booking-id` |
| `booking_details.css` | 41 | `bk-modal`, `bk-row`, `bk-cancel-form` |
| `my_booking.js` | 8 | `bk-tab`, `bk-panel` |

Giao nhau với wizard: **đúng 1 tên** là `--bk-surface`, và hai file không bao giờ nạp cùng trang. Không có bug thực tế, nhưng đã chuyển toàn bộ token từ `:root` xuống `.bk-wrap` để không còn phải dựa vào điều đó nữa.

### C. Bug thật: thanh bước dính sai chỗ trên trang customer

```css
.bk-indicator-bar { position: sticky; top: 73px; }   /* 73px = header của base.html */
```

Nhưng `customer_base.html` **không nạp `base.css`** và không có header đó:

| | Desktop | ≤860px |
|---|---|---|
| public | header 72px | header 72px |
| customer | sidebar, **không header** | topbar 56px |

Nghĩa là trên `/customer/booking` thanh bước bị đẩy xuống 73px vô cớ ở desktop, và lệch 17px ở mobile. Đã thay bằng biến, neo qua `.booking-wrapper` (class chỉ customer mới có):

```css
.bk-wrap { --bk-top: 72px; }
.booking-wrapper .bk-wrap { --bk-top: 0px; }
@media (max-width: 860px) { .booking-wrapper .bk-wrap { --bk-top: 56px; } }
```

### D. Các vấn đề UX người dùng nêu

| Bước | Vấn đề |
|---|---|
| 1 Service | `flex-direction: column`, 9 card × ~250px = **~2.250px cuộn** để xem hết |
| 1 Service | Nút `Continue` nằm sau toàn bộ danh sách, phải cuộn hết mới thấy |
| 2 Stylist | 4 lựa chọn xếp dọc chiếm cả màn hình |
| 3 Date & Time | `.bk-time-grid` là `flex-wrap`, pill rộng khác nhau (`9:00 AM` vs `11:30 AM`) làm hàng cuối lệch, nhìn bừa bộn |
| 3 Date & Time | Ô ngày 36px, dưới ngưỡng chạm 44px |

---

## 3. Các thay đổi

### Bước 1 - Dịch vụ

Lưới thay danh sách: 3 cột desktop / 2 cột mobile. 9 service từ ~2.250px còn ~900px.

Card đổi từ row-card (thumb 96px trái, text phải, vòng tròn check) sang **tile ảnh trên**: ảnh 4:3, thân card gồm tên (clamp 2 dòng) và hàng `duration / giá`. Bỏ description vì khách đã đọc ở trang Services, ở đây họ chọn nhanh.

Vòng chọn vẽ bằng `::after` chứ không đổi `border-width`:

```css
.bk-svc-card::after { border: 2px solid transparent; }
.bk-svc-card--selected::after { border-color: var(--bk-accent); }
```

Border 1px → 2px sẽ dịch toàn bộ nội dung 1px mỗi lần chọn. Cùng kỹ thuật áp cho staff card và payment card.

Chip lọc thêm số đếm, và **ẩn category rỗng** (`test` có 0 service, bấm vào chỉ dẫn tới lưới trống).

### Bước 2 - Chuyên viên

Bố cục đổi theo breakpoint vì `No Preference` khác loại với ba người thật:

- **Desktop:** `No Preference` là một hàng ngang full-width (`grid-column: 1 / -1`), ba staff xếp 3 cột bên dưới
- **Mobile:** `No Preference` trở về làm ô thường để lưới khép đúng **2×2**

### Bước 3 - Ngày và giờ

- Khung giờ: `flex-wrap` → `grid-template-columns: repeat(auto-fill, minmax(92px, 1fr))`, cột đều tăm tắp
- **Gom theo buổi** Morning / Afternoon / Evening, chia ở client từ `slot.value`, backend không đổi. Kiểm chứng với dữ liệu thật: 17 slot → 6 / 10 / 1
- Ô ngày: hình tròn 36px → vuông bo góc 12px, khớp hình dạng với `slot-pill` bên cạnh
- Loading: chữ `Loading...` → **skeleton pill** đúng hình dạng kết quả, không nhảy bố cục khi dữ liệu về
- Empty: có icon + câu gợi ý
- Slot đã kín: bỏ `line-through` (10 pill gạch ngang làm nhiễu cả lưới), đổi thành nền wash mờ

### Thanh hành động dính đáy (mobile)

Giải bài "nút Continue ở tận dưới". Không dùng scroll listener. Một `IntersectionObserver` trên chính `.bk-nav` của bước đang mở:

```
thanh hiện  ⟺  .bk-nav thật đang ở ngoài màn hình
```

Thanh không có logic riêng, nút của nó **bấm hộ nút thật** (`confirm.click()` hoặc `goNext()`), nên mọi ràng buộc disabled/submit chỉ tồn tại một chỗ. Nội dung thanh đọc lại thứ vừa chọn ở bước đang đứng (`Gel Manicure · €45`), nên nó vừa là nút vừa là xác nhận.

### Đồng bộ hệ thống

Token gộp về đúng thang `bd-` / `lp-` / `ms-`: ink `#2A1520`, accent `#ab2261`, wash `#FBEEF4`, plum `#3E1F47`, line `#EDE3E8`; bo góc surface 20 / media 14 / control 12 / pill 999; `ease: cubic-bezier(0.16, 1, 0.3, 1)`.

Thanh bước ở mobile: dãy chấm câm (nhãn bị `display: none`) thay bằng một dòng đọc được `Bước 2 trên 5 · Stylist` kèm progress mảnh.

Bước cuối ở một cột: `Booking Summary` được đẩy lên **trước** phần chọn thanh toán bằng `order: -1`, vì đó là thứ khách cần đọc lại trước khi quyết.

---

## 4. Hai bug tôi tự tạo ra rồi phải sửa

### A. `aspect-ratio` + `min-height` làm tràn ngang bước 3

Để nâng vùng chạm ô lịch từ 36px lên chuẩn 44px, tôi viết:

```css
.bk-cal-day { aspect-ratio: 1; min-height: 44px; }
```

`aspect-ratio` **chuyển** ràng buộc chiều cao thành ràng buộc chiều rộng, và ô lịch là grid item (`min-width` mặc định là `auto`). Nên 7 cột không co xuống dưới 44px được:

```
7 × 44 + 6 × 4 (gap)  = 332   lưới lịch
+ 32                          padding .bk-cal-panel
+ 36                          padding .bk-content
= 400px bề rộng tối thiểu
```

Mọi máy 360-393px đều tràn, kéo ngang qua lại được. Chính cái dòng thêm vào để cải thiện lại phá layout.

**Sửa:** bỏ `min-height`, thêm `min-width: 0`, để `aspect-ratio` tự làm ô vuông theo bề rộng cột. Mua lại vùng chạm bằng cách siết padding panel 16→12px và gap 4→3px ở mobile:

| Viewport | Ô ngày |
|---|---|
| 360px | 40.3px |
| 390px | 44.6px |
| 414px | 48.0px |

Thêm `min-width: 0` cho `.bk-dt-grid > *` để chặn cùng loại lỗi từ phía panel khung giờ.

> **Bài học:** `aspect-ratio` cộng bất kỳ `min-height`/`height` nào trên một grid/flex item là bẫy tràn ngang. Ràng buộc một chiều sẽ truyền sang chiều kia. Muốn ô vuông co giãn thì chỉ đặt `aspect-ratio` và `min-width: 0`, đừng ghim kích thước tuyệt đối.

### B. Thanh dính đáy không hiện ở bước ngắn

Bản đầu tôi gate bằng hai điều kiện: `scrolledPast && !navOnScreen`, trong đó `scrolledPast` đo bằng một sentinel đặt ngay dưới tiêu đề bước (~250px trong tài liệu).

Bước 2 chỉ có 4 ô, cả trang cao ~680px, nên **tầm cuộn tối đa chỉ ~40-110px**. Không bao giờ vượt nổi mốc 250px → `scrolledPast` vĩnh viễn `false` → thanh không bao giờ hiện. Cùng lúc `.bk-nav` bị đẩy khỏi màn hình một chút, nên khách vừa không thấy nút thật vừa không thấy thanh.

Mốc đặt ở đâu cũng hỏng: bước càng ngắn tầm cuộn càng nhỏ, trong khi mốc thì đứng yên.

**Sửa:** bỏ hẳn điều kiện mốc, chỉ giữ `!navOnScreen`. Hai trạng thái này bù trừ nhau tuyệt đối nên ở mọi chiều cao nội dung khách luôn có **đúng một** nút Continue nhìn thấy được. Xoá được 1 observer, 9 thẻ sentinel và 1 rule CSS.

**Đánh đổi còn treo:** ở bước 1 thanh giờ hiện ngay khi vào bước chứ không đợi cuộn, vì nút thật nằm dưới 9 card nên đã ở ngoài màn hình từ đầu. Nếu thấy chướng thì đổi sang gate bằng `rootMargin` trên chính `.bk-nav` (chỉ hiện khi nút thật còn cách đáy hơn một màn). Cách đó không phụ thuộc chiều cao bước.

> **Bài học:** điều kiện hiện/ẩn UI nên đo **chính vật cần thay thế**, đừng đo một mốc đại diện. `.bk-nav` ở ngoài màn hình là định nghĩa chính xác của "khách đang không có nút bấm", còn "đã cuộn qua X pixel" chỉ là phỏng đoán về điều đó.

---

## 5. Bản dịch

6 chuỗi mới. `en` để trống msgstr theo đúng quy ước sẵn có (English là nguồn, tự fallback về msgid).

| msgid | vi | fi |
|---|---|---|
| Morning | Buổi sáng | Aamu |
| Afternoon | Buổi chiều | Iltapäivä |
| Evening | Buổi tối | Ilta |
| Step | Bước | Vaihe |
| Confirm | Xác nhận | Vahvista |
| Pick a time slot | Chọn khung giờ | Valitse aika |

`of` tái dùng entry có sẵn (`trên` / `/`, vốn dùng cho `Showing X of Y`, cùng ngữ nghĩa).

### `pybabel update` gán fuzzy bậy

Ba chuỗi bị đoán nhầm theo độ giống chuỗi:

| msgid | fuzzy gán vào (vi) | fuzzy gán vào (fi) |
|---|---|---|
| Morning | `phút` | `Verkossa` |
| Evening | `Chờ duyệt` | `Odottaa` |
| Confirm | `Đã xác nhận` | `Vahvistettu` |

Entry fuzzy bị gettext bỏ qua nên trước mắt chỉ ra tiếng Anh, nhưng nếu sau này ai gỡ cờ fuzzy thì thành sai nghĩa hẳn (`Morning` → `phút`). Đã ghi đè đúng và xoá cờ.

Bốn entry fuzzy còn lại (`Previous slide`, `Next slide`, `Mở menu`, và `JPG, PNG tối đa 10MB` ở fi) **vốn đã fuzzy từ trước đợt này**, không đụng tới.

### 60 entry chết bị dọn

`pybabel update` gỡ 60 entry khỏi cả ba catalog (tích tụ từ code đã xoá, phần lớn không liên quan booking). Đã verify bằng cách quét đúng dạng gọi `_()` trên toàn source: **0/60 chuỗi còn được dùng**. Chúng vẫn nằm trong `.po` dạng `#~` obsolete, chỉ không compile vào `.mo`.

`.mo` vì thế nhỏ đi: vi 39.5KB → 36.1KB, fi 37.5KB → 34.4KB.

---

## 6. Hợp đồng giữ nguyên

Backend và JS phụ thuộc các định danh sau, đã kiểm tự động là còn nguyên 100% sau khi viết lại:

- **Form:** `csrf_token`, `booking_date`, `start_time`, `service_id`, `staff_id`, `payment_method`, `full_name`, `phone`, `email`, `note`
- **ID:** `hidden-booking-date`, `hidden-start-time`, `confirm-btn`, `timeSlotGrid`, `calendar`, `calendarMonthLabel`, `prevMonth`, `nextMonth`, `progress-fill`, `step-circle-N`, `summary-*`
- **Class hook:** `.service-item`, `.service-radio`, `.slot-pill`
- **Endpoint:** `main.check_available_slot`, không đổi shape response

`CALENDAR_CONFIG` đổi tên thành `window.BOOKING_CONFIG` và gom thêm nhánh `i18n`. Ba khoá cũ chưa từng được dùng (`hiddenDateId`, `timeslotHeadingId`, `timeslotPlaceholderId`) đã bỏ.

---

## 7. Đã verify / chưa verify

**Đã chạy:**

| Kiểm tra | Kết quả |
|---|---|
| `node --check booking_wizard.js` | pass |
| Render `/public/booking` | 200 · 9 card · 4 chip · sticky bar |
| Render `/customer/booking` | 200 · `multiplier` 1.5 inject đúng · 0 field guest |
| Endpoint slot thật | 17 slot → gom 6/10/1 |
| Đối chiếu 17 id/name/class hợp đồng | còn nguyên ở cả 2 template |
| Cross-check class CSS ↔ markup ↔ JS | không có class mồ côi |
| Quét `aspect-ratio` + `min-height` toàn file | không còn bẫy nào |
| CSS cân bằng ngoặc, rule rỗng | 227 cặp, 0 rule rỗng |
| Đọc ngược 6 chuỗi từ `.mo` đã compile | đúng ở cả vi và fi |
| 60 entry bị gỡ có còn trong `_()` không | 0/60 |

**Chưa verify (cần xem trên trình duyệt):**

- Bước 1 mobile: lưới 2 cột, dải chip cuộn ngang, ảnh 4:3 với ảnh service thật
- Bước 3: tràn ngang đã hết chưa sau khi sửa, ô lịch có lệch cột không
- Bước 4 guest: `Continue` phải disabled tới khi đủ tên/SĐT/email
- Bước 5: ở mobile summary phải nằm trên phần thanh toán
- Submit thật một booking end-to-end, cả hai luồng
- `/customer/booking`: thanh bước dính đúng chỗ sau khi đổi `--bk-top`
- Đổi ngôn ngữ VIE/FIN rồi vào bước 3
- Desktop bước 2: `No Preference` full-width + 3 cột

---

## 8. File thay đổi

| File | Thay đổi |
|---|---|
| `app/static/js/booking_wizard.js` | **mới**, gộp 2 bản JS trùng |
| `app/static/css/public/public_booking.css` | viết lại |
| `app/templates/public/public_booking.html` | viết lại markup, bỏ `<script>` inline |
| `app/templates/customer/customer_booking.html` | như trên |
| `app/translations/{en,fi,vi}/LC_MESSAGES/messages.{po,mo}` | 6 chuỗi mới, 3 fuzzy sửa, 60 entry chết dọn |
| `messages.pot` | extract lại |

---

## 9. Nợ kỹ thuật còn lại

| Việc | Ghi chú |
|---|---|
| `.bk-summary-points-nudge--customer` | Class chết trong `customer_booking.html`, CSS chưa từng định nghĩa. Có từ trước đợt này, giữ nguyên |
| Prefix `bk-` dùng chung 5 nơi | Wizard đã scope token vào `.bk-wrap`. Bốn file kia vẫn dùng `bk-` với nghĩa khác. Nên đổi prefix khi có dịp chạm vào |
| 4 entry fuzzy cũ | `Previous slide`, `Next slide`, `Mở menu`, `JPG, PNG tối đa 10MB` |
| Category `test` trong DB | Đã ẩn khỏi chip, nhưng bản thân dữ liệu rác vẫn còn |
| Gate thanh dính đáy ở bước 1 | Xem mục 4B, đang chờ quyết định |
