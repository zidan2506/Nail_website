# Redesign UI khách hàng: My bookings + Upcoming card

**Ngày:** 2026-08-08 · **Phạm vi:** `/customer/my-booking` (redesign toàn trang) + `/customer/dashboard` (chỉ upcoming-card) · **Trạng thái:** ✅ code xong, chưa chạy với DB thật, chưa deploy

Viết lại trang lịch hẹn của khách theo hướng gọn và dễ đọc hơn, đồng thời sửa một luồng nghiệp vụ đang chết. Sau đó port ngôn ngữ thị giác của card mới sang dashboard.

---

## 1. Vì sao làm

Trang `my_bookings` nói cùng một chuyện nhiều lần:

- Lịch gần nhất render 2 lần (Next Visit card + item đầu tab Upcoming), cùng 3 dòng detail, CTA chồng nhau
- 3 layout family cho cùng một object "lịch hẹn": `next-visit-card`, `appointment-card`, `history-row`
- Section "Recent History" trùng với page `customer_history` đã có, lại nằm ngay cạnh link "View All History"
- Loyalty card lạc chỗ: đã có trên Dashboard, ở đây ăn 1/3 chiều ngang mà không phục vụ task nào
- CTA "Book" lặp 4 lần với 2 nhãn khác nhau
- 3 dòng icon+text mỗi card, 3 card = 9 dòng, tín hiệu thấp

Cộng thêm sai lệch kỹ thuật:

| Vấn đề | Chi tiết |
|---|---|
| Font sai brand | Base template load Plus Jakarta Sans, `my_bookings.css` lại set `--font-main: "Inter"` |
| 2 màu hồng đánh nhau | File này `#f43f84`, dashboard `#ab2261` |
| Emoji lẫn icon | Modal dùng 📅 👤 ⚠ ✕ trong khi cả trang dùng Material Symbols |
| CSS chết | ~60 dòng `.appointment-search-*` không có markup nào dùng |
| Row không truy cập được bằng bàn phím | `onclick="window.location.href=..."` trên `<article>` |

---

## 2. 🔴 Bug đã sửa: nút Cancel chết hoàn toàn

`app/static/js/my_booking.js` đọc class không tồn tại:

```js
const label = row.querySelector(".detail-label").textContent.trim();
```

`.detail-label` **không có ở bất kỳ đâu trong `app/`** (đã grep toàn repo). Template dùng `.detail-icon` + `.detail-value`. Nên `querySelector` trả `null` → TypeError → `openCancelModal()` chết giữa chừng → modal không mở. Mà `e.preventDefault()` đã chạy trước đó, nên form cũng không submit.

**Hệ quả: bấm Cancel không làm gì cả.** Console báo `Cannot read properties of null`.

Cách sửa: dữ liệu lấy từ `data-*` trên chính form thay vì dò DOM của card. Không còn phụ thuộc vào cấu trúc markup, nên đổi layout sau này không làm chết lại.

```jinja
<form class="bk-cancel-form"
      data-service="{{ ... }}" data-when="{{ ... }}" data-staff="{{ ... }}">
```

---

## 3. My bookings: thay đổi cấu trúc

Prefix CSS mới: `bk-`.

### Ý tưởng lõi

Một lịch hẹn chỉ có **hai trọng lượng**, không phải ba:

1. **Focus card** (`.bk-focus`) - lịch kế tiếp. Vật thể duy nhất trên trang có ảnh, nền tối, có chiều sâu.
2. **Ledger row** (`.bk-row`) - mọi lịch còn lại. Hàng phẳng, không shadow, ngăn nhau bằng một hairline. Khối ngày bên trái (`14` / `AUG`) là mỏ neo thị giác, thay cho việc lặp icon lịch trên từng dòng.

### Information architecture

| Trước | Sau |
|---|---|
| 4 section: Next Visit + Loyalty, Manage (3 tab), Recent History | 2 section: Next Visit, Ledger (4 tab) |
| Recent History là section riêng | Thành tab thứ 4 "History", dùng chung `.bk-row` |
| Loyalty card | Bỏ khỏi trang này (vẫn còn trên Dashboard) |
| Lịch gần nhất hiện 2 lần | Dedupe bằng `rejectattr('booking.id', 'equalto', next_visit['id'])` |
| Thumbnail trên mọi card | Chỉ focus card có ảnh, các hàng bỏ thumbnail |

Dữ liệu `recent_history` đã được truyền sẵn vào template nên **không cần đụng Python**.

### Trạng thái đọc qua cách vẽ, không qua badge

- `confirmed` - mặc định, **không nhãn**
- `pending` - nhãn hổ phách cạnh tên dịch vụ
- `cancelled` - tên bị gạch ngang, cả hàng chìm màu
- `completed` - mặc định, cột giá vẫn hiện

Số badge trên trang giảm từ mọi-dòng xuống gần như không.

### Design tokens

```
accent    #ab2261 (bỏ #f43f84)
plum      #3E1F47 - bề mặt focus card
pearl     #FBF4F8 - chữ trên plum
font      Plus Jakarta Sans (bỏ Inter)
bo góc    surface 20 · media 14 · control 12 · pill 999
```

Trên nền plum, accent chuyển thành pearl vì hồng `#ab2261` trên plum chỉ đạt **~1.7:1**, không đọc được.

### Motion

Hai chuyển động, mỗi cái trả lời một câu hỏi:

- Marker của segmented control trượt → "bạn vừa đổi sang danh sách khác"
- Hàng dâng lên so le (`--row-i` × 45ms) → "đây là nội dung mới của danh sách đó"

Có block `prefers-reduced-motion: reduce`.

### Accessibility

- Bỏ `onclick` trên `<article>`, thay bằng stretched link (`.bk-row__link::after { inset: 0 }`). Phần tử focus được là một `<a>` thật, tab tới được.
- Tabs có `role="tablist"` / `role="tab"` / `aria-selected` cập nhật bằng JS
- Phân cấp heading: `h1 Appointments` → `h2 Next Visit` → `h3 tên dịch vụ`
- Escape đóng modal
- Select trong modal `font-size: 16px` để chặn iOS auto-zoom

### i18n: 0 msgid mới

Cố tình chỉ dùng lại msgid đã có. `History` mượn từ sidebar, `Book appointment` mượn từ nav, `Next Visit` còn nguyên từ bản cũ (VI "Lần ghé tiếp theo", FI "Seuraava käynti"). **Không cần chạy `pybabel extract` / `compile`.**

---

## 4. Câu chuyện "card này là card gì?"

Đáng ghi lại vì mất 3 vòng.

**Vòng 1.** Khi redesign, nhãn `Next Visit` bị xoá, viện dẫn quy tắc "eyebrow restraint" của skill design. Sai: quy tắc đó dành cho eyebrow **trang trí** trên landing page, không dành cho nhãn **chức năng** của product UI. Card mất danh tính, user hỏi "đây là card gì vậy?".

**Vòng 2.** Giải bằng khối ngày `08` / `AUG` cỡ lớn + dòng "In 3 days" (dùng lại `_relative_day()` của dashboard). User đánh giá **xấu hơn bản cũ**, revert toàn bộ.

**Vòng 3.** Đặt `<h2>Next Visit</h2>` **ngoài** card. Đạt.

> **Bài học:** khiếu nại mang tính **ngữ nghĩa** thì lời giải phải là **chữ**. Motif và cấu trúc có thể củng cố, không thể thay thế. Khối ngày chỉ ngụ ý được "đây là một lịch hẹn", không nói được "đây là lịch **kế tiếp** của bạn".

Ràng buộc rút ra: user đã nói card cũ đẹp hơn, nên **không thêm phần tử vào bên trong card**, nhãn đặt bên ngoài.

> **Ghi chú quy trình:** revert ở vòng 2 chạy 3 edit rời trên `routes.py`. Giữa edit 1 và edit 3 tồn tại một cửa sổ vài giây mà biến `nevi_relative` được *dùng* nhưng chưa được *gán*. Flask reloader nạp đúng lúc đó và giữ module hỏng trong bộ nhớ, sinh `NameError: name 'nevi_relative' is not defined`. File trên đĩa vẫn đúng, chỉ cần restart dev server. Khi sửa nhiều chỗ phụ thuộc lẫn nhau trên một file Python mà app đang chạy live, nên gộp thành một lần ghi.

---

## 5. Dashboard: port `.bk-focus` sang `.upcoming-card`

### Xung đột phát hiện trước khi làm

`.dashboard-grid` là `2fr 1fr`: upcoming-card nằm ngay cạnh `.loyalty-card`, mà loyalty-card **đã là plum tối rồi**. Bê nguyên nền plum sang là dashboard có hai khối tối cạnh nhau, cả row 2 thành một dải đen.

Đã nêu rủi ro, **user chọn lấy plum**. Làm theo.

### Cái gì port, cái gì không

| Đặc điểm của `.bk-focus` | Port? |
|---|---|
| Grid 2 cột, ảnh chiếm trọn cột và tràn sát mép | ✅ thay ảnh 132px bo góc trôi trong padding 22px |
| Nền plum + radial glow + chữ pearl | ✅ |
| Cột chữ căn giữa dọc, bỏ `margin-top: auto` | ✅ |
| Trạng thái rỗng dùng nền sáng | ✅ `.upcoming-card--empty` |
| Tiêu đề ngoài card | ✅ `Upcoming Appointment` (msgid có sẵn) |
| Facts strip gạch mảnh | Đã giống sẵn, chỉ đổi màu sang pearl |
| Bo góc 20px | ❌ giữ 26px theo thang riêng của dashboard |

### Ba quyết định kỹ thuật

1. **`.upcoming-card__when` từ `#ab2261` → pearl.** Hồng trên plum ~1.7:1.
2. **Badge `confirmed` xanh mint → pearl mờ.** Trên nền sáng thì ổn, trên plum nó là màu duy nhất lạc khỏi palette hồng/plum. `pending` và `cancelled` giữ màu vì màu đó mang thông tin thật. Badge chỉ dùng đúng 1 chỗ nên override an toàn.
3. **Căn đỉnh loyalty-card.** Thêm tiêu đề sẽ đẩy upcoming-card xuống ~35px. Giải bằng `grid-template-areas` 2 hàng (tiêu đề chiếm hàng 1 cột trái, hai card cùng hàng 2) thay vì bù `margin-top` bằng số ước lượng.

```css
.dashboard-grid {
    grid-template-areas:
        "heading ."
        "upcoming loyalty";
    column-gap: 24px;
    row-gap: 14px;
}
```

Override nút có phạm vi `.upcoming-card:not(.upcoming-card--empty)` nên không rò ra chỗ khác của dashboard.

---

## 6. Files

| File | Nội dung |
|---|---|
| `app/templates/customer/my_bookings.html` | Viết lại. Macro `ledger_row` dùng chung cho 4 tab, focus card, modal |
| `app/static/css/customer/my_bookings.css` | Viết lại, prefix `bk-` |
| `app/static/js/my_booking.js` | Sửa bug cancel, thêm marker + aria cho tab |
| `app/templates/customer/customer_dashboard.html` | Chỉ khối upcoming-card (CSS inline trong file) |

**Không đụng:** `app/routes.py` (identical với HEAD), file `.po` / `.mo`, `customer_base.html`, các page khác.

`my_bookings` giảm ~570 dòng so với bản cũ mà làm nhiều việc hơn.

---

## 7. Đã verify

- Render 3 trạng thái dữ liệu (đầy / rỗng / next_visit là pending) qua harness stub
- Render qua **Jinja env thật của app** (`create_app()`, filter và loader thật), cả 2 trang
- Dedupe: upcoming 2 → 1 hàng; khi `next_visit` là pending thì tab Pending mới rỗng
- Phân cấp heading: đúng 1 `h2` cho khối next-visit ở cả hai trạng thái
- Modal cancel: mở được, điền đúng service / when / stylist từ `data-*`
- Xem thật trong Chrome ở **1440px và 390px**, dashboard xem trong shell đầy đủ (sidebar + CSS base thật)
- Tab switching + marker trượt + `--tab-i`
- 0 em-dash trong phần render ra cho user

**Chưa verify:** chạy app với DB thật, ảnh dịch vụ thật, bản dịch VI hiển thị trên trình duyệt (mới chỉ thấy FI qua render).

---

## 8. Còn tồn đọng

| Việc | Ghi chú |
|---|---|
| Status in ra thô, chưa dịch | `{{ upcoming_booking.status }}` và `nevi_status` render thẳng chuỗi DB, luôn tiếng Anh kể cả khi UI là FI/VI. Lỗi có sẵn từ trước |
| `msgstr` tiếng Anh của "Next Visit" rỗng | Fallback về msgid nên hiện "Next Visit" (title case). Muốn "Next visit" thì điền `msgstr` trong `app/translations/en/LC_MESSAGES/messages.po`, không cần đụng code |
| Context thừa | `loyalty_points`, `next_reward`, `progress_pct` vẫn được `routes.py` truyền vào `my_bookings` nhưng template không còn dùng. Chưa xoá trong Python |
| Không có dark mode | Cả app không có dark mode ở đâu. Một trang tối nằm trong sidebar sáng sẽ hỏng hơn là không có |
| 3 em-dash trong comment CSS dashboard | Dòng 39 / 70 / 74, có sẵn từ HEAD, không render ra cho user |
| Row 2 dashboard là dải tối | Hệ quả đã biết của việc chọn plum. Nếu sau này thấy vướng, đảo `.loyalty-card` sang nền sáng là cách gỡ |

---

## 9. Ghi chú cho lần sau

- Icon dùng Material Symbols (cả app đang dùng), không đổi sang Phosphor/Tabler dù skill design ưu tiên
- Trước khi thêm chữ mới, kiểm `app/translations/*/LC_MESSAGES/messages.po` xem msgid cũ còn không. Cả redesign này giữ được **0 msgid mới** nhờ vậy
- Codebase không có reset `box-sizing: border-box` toàn cục. CSS mới tự khai trong phạm vi `.bk`
- `format_date` filter nhận format arg (`| format_date('%d')`) nên tách được ngày / tháng trong template mà không cần đụng Python
