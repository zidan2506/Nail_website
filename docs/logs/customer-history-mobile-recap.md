# Redesign UI khách hàng: trang History

**Ngày:** 2026-08-08 · **Phạm vi:** `/customer/history` (viết lại toàn trang) · **Trạng thái:** ⚠️ code xong, verify chưa đủ (xem mục 8), chưa chạy với DB thật, chưa deploy

Nối tiếp `docs/CUSTOMER_UI_REDESIGN.md`. Trang History là mảnh cuối của bộ ba portal khách hàng (Dashboard → My bookings → History) và là trang duy nhất còn giữ ngôn ngữ thị giác cũ.

---

## 1. Vì sao làm

Yêu cầu: redesign mobile UI/UX, gọn gàng, mượt, vibe luxury, và **đồng bộ** với Dashboard + My bookings đã redesign.

Audit trạng thái cũ:

| Vấn đề | Chi tiết |
|---|---|
| **Stats ăn hết màn hình đầu** | ≤700px: 4 stat-card × 140px + gap = ~620px, cộng header ~150px. Trên 390×844, bản ghi đầu tiên nằm dưới ~800px scroll. Mà người vào History là để **tìm** một lịch / một hoá đơn |
| **Bảng đổ thành card kiểu `data-label`** | `td::before` in "STYLIST" / "PRICE" / "STATUS" lên **mỗi** giá trị → 5 khối có nhãn cho 1 lịch hẹn, × 8 hàng/trang |
| **Filter bar là pattern desktop** | `.filter-panel` là `position:absolute; left:0; min-width:180px`. Chip bên phải mở ra là tràn khỏi viewport |
| **Ba màu hồng trong cùng portal** | `#d63384` (trang này) vs `#ab2261` (bk-) vs `#f43f84` (book-btn dashboard) |
| **Emoji làm icon** | 📅 € ✦ 🧾 ⤓ ⇅ ▾ ✓ ⋮ trong khi cả portal dùng Material Symbols |
| **Hàng không truy cập được bằng bàn phím** | `onclick="window.location.href=..."` trên `<tr>`. Đúng lỗi đã sửa ở My bookings |
| **Pagination số trang trên mobile** | Nút 36px xếp cạnh nhau, dưới ngưỡng chạm 44px |
| **Hai hệ tab khác nhau** | Underline tab ở đây vs segmented pill ở My bookings |

Quyết định phạm vi (user chốt trước khi code): **viết lại cả trang**, bỏ `<table>`, không chỉ vá mobile. Lý do: khối ngày `[14]/[AUG]` neo bên trái là motif nhận diện của `.bk-row`, mà giữ `<table>` thì không dựng được nó vì thứ tự `<td>` cố định.

---

## 2. Cấu trúc mới

Prefix CSS: `ch-`. Token lấy **đúng giá trị** của `bk-` (không import chéo được: hai trang nạp hai file CSS rời).

### Information architecture

| Trước | Sau |
|---|---|
| 4 stat-card trắng | 1 băng plum (`.ch-summary`) |
| Underline tabs | Segmented pill + marker trượt (`.ch-tabs`, `--tab-i`) |
| Chip + dropdown absolute | Chip cuộn ngang + sheet đáy ở mobile |
| `<table>` + `data-label` fallback | Ledger row `.ch-row` (grid 4 cột → 3 cột → 2 hàng) |
| Không có mốc thời gian | Dải tháng dính `.ch-month` |
| Pagination số trang | Desktop giữ số trang, mobile đổi sang "Load more" dồn |

### A. Băng tổng kết thay 4 stat-card

Hai con số có trọng lượng chia đôi bằng hairline dọc; hai fact "ai / cái gì" rơi xuống dải gạch mảnh bên dưới, đúng motif `.bk-focus__facts`. **~150px thay cho ~620px**, và là vật thể tối duy nhất của trang, cùng họ với `.bk-focus` (My bookings) và `.upcoming-card` (Dashboard).

Ở mobile hai fact xếp dọc và **bỏ gạch dọc** giữa chúng: gạch ngăn chỉ có nghĩa khi hai vật nằm cùng hàng.

### B. Ledger row

```
[14]   Gel Manicure               45,00 €
[AUG]  10:30 │ Mai N.
       [ Jätä arvostelu ] [ Varaa uudelleen ]
```

Trạng thái đọc qua **cách vẽ**, không dán badge mọi dòng:

- `completed` / `paid` - mặc định, **không nhãn** (trên trang History đây mới là chuẩn)
- `cancelled` - tên gạch ngang, cả hàng chìm màu, cột giá để trống
- `pending` / `refunded` (hoá đơn) - nhãn cạnh số hoá đơn
- `reviewed` - `.ch-done`, một trạng thái chứ không phải nút

Số badge trên trang giảm từ mọi-dòng xuống gần như không.

### C. Dải tháng dính - nét riêng của trang này

History vốn là dòng thời gian. Nhãn tháng dính đỉnh cho tới khi nhóm sau đẩy đi.

Hai ràng buộc kỹ thuật:

1. **Phải có `.ch-group` bọc từng tháng.** `position: sticky` chỉ dừng ở biên phần tử cha; để phẳng thì nhãn tháng đầu dính suốt chiều dài danh sách.
2. **Chỉ có nghĩa khi sắp xếp theo ngày.** JS tự gỡ nhóm khi `sort` là `amount_*`.

JS dựng nhóm sau khi phân trang, và **gỡ nhóm trước** mỗi lần lọc lại (`ungroup` → `sort` → `filter` → `paginate` → `regroup`) nên thao tác là idempotent.

### D. Sheet đáy thay dropdown ở mobile

Cùng markup cho cả hai breakpoint, chuyển bằng CSS, JS không phân nhánh: `.ch-panel-menu` từ `position:absolute` thành `position:fixed; inset:auto 0 0 0`, bo `24px 24px 0 0`, `padding-bottom: calc(10px + env(safe-area-inset-bottom))`. Tiêu đề sheet (`.ch-panel-menu__head`) chỉ hiện ở mobile, để biết đang lọc theo cái gì.

Kèm scrim mờ + `body.ch-sheet-open { overflow: hidden }`.

### E. "Load more" thay số trang ở mobile

`startIdx = 0` khi mobile nên bấm là danh sách **dài ra**, không thay nội dung dưới ngón tay. Desktop giữ nguyên nút số trang (có `chevron_left/right`, ellipsis).

Nghe `matchMedia('(max-width: 768px)').change` để reset về trang 1 khi xoay máy.

---

## 3. Motion: một sửa lỗi đáng ghi lại

Ý định ban đầu: hàng dâng lên so le mỗi lần đổi bộ lọc, giống `.bk-row`.

**Không làm được ở trang này.** Mọi thao tác (gom tháng, sắp xếp, phân trang) đều phải **chuyển chỗ `<article>` trong DOM**, mà chuyển chỗ là CSS animation chạy lại từ đầu. Bấm "Load more" mà cả danh sách đang đọc dở nhấp nháy lại thì đó là lỗi, không phải hiệu ứng.

Giải: hiệu ứng dâng gắn vào class `.ch-list--enter` đặt sẵn trong markup, JS gỡ sau lần dựng đầu tiên của **mỗi** danh sách (`setTimeout 900ms` trong `apply()`). Kết quả: vào trang thì animate, sang tab Laskut lần đầu thì animate, mọi lần sau tức thì.

Còn lại 4 chuyển động, mỗi cái trả lời một câu hỏi:

| Chuyển động | Trả lời |
|---|---|
| Marker tab trượt | "bạn vừa đổi sang danh sách khác" |
| Hàng dâng so le (`--row-i` × 45ms) | "danh sách này vừa được nạp" |
| Sheet trượt lên + scrim mờ dần | "đây là một lớp mới, không phải trang mới" |
| `scale(0.98)` khi ấn | phản hồi chạm |

Có block `prefers-reduced-motion: reduce`.

---

## 4. Accessibility

- Bỏ `onclick` trên `<tr>`, thay bằng stretched link (`.ch-row__link::after { inset: 0 }`). Phần tử focus được là một `<a>` thật. **Đã verify:** `document.activeElement` = `.ch-row__link`
- Tabs có `role="tablist"` / `role="tab"` / `aria-selected` cập nhật bằng JS
- Phân cấp heading: `h1 History` → `h3` tên dịch vụ / số hoá đơn (không có `h2` vì trang không có section cần đặt tên)
- Escape đóng sheet; click scrim đóng sheet
- Mọi vùng chạm ở mobile ≥ 42px (`.ch-chip` 42, `.ch-opt` 50, `.ch-btn` 44, "Load more" 48)

---

## 5. i18n: 3 msgid mới

Đã kiểm `app/translations/*/LC_MESSAGES/messages.po` trước khi thêm chữ. Tái dùng được: `Date` `Status` `Stylist` `Service` `Payment` (bản không dấu hai chấm, đã có sẵn), `Clear all`, `Showing`, `of`, `No result`, `No history yet.`, `Rebook`, `Leave Review`, `Reviewed`, `Download PDF`, toàn bộ nhãn sort và nhãn filter.

Ba msgid **phải** thêm:

| msgid | vi | fi |
|---|---|---|
| `Load more` | Xem thêm | Näytä lisää |
| `Sort` | Sắp xếp | Järjestä |
| `No invoices yet.` | Chưa có hoá đơn nào. | Ei vielä laskuja. |

Cách thêm: **append tay** vào cuối 3 file `.po` + `messages.pot` rồi `python -m babel.messages.frontend compile -d app/translations`. Không chạy `extract`/`update` để tránh viết lại toàn bộ file (diff sẽ phình lên hàng trăm dòng vô ích).

> ⚠️ Nếu render template **trước** khi compile `.mo` thì chuỗi mới lọt ra dạng tiếng Anh. Đã dính đúng bẫy này một lần trong lúc test: HTML render ra chữ "Load more" thay vì "Näytä lisää". Thứ tự đúng: sửa `.po` → compile → render.

---

## 6. Sửa kèm

| Việc | Ghi chú |
|---|---|
| Trạng thái hoá đơn được dịch | Trước in thẳng `{{ invoice.invoice_status }}` từ DB, luôn tiếng Anh kể cả UI là FI/VI. Là mục tồn đọng số 1 của recap trước. Nay map sang `_('Pending')` / `_('Refunded')` |
| Bỏ nút `.btn-more` (⋮) | Grep toàn repo: không có handler nào. Nút chết |
| Bỏ `N/A` và `0,00 €` ở hàng đã huỷ | Thay bằng để trống, theo quy ước `.bk-row__price--none` |

---

## 7. Files

| File | Nội dung |
|---|---|
| `app/templates/customer/customer_history.html` | Viết lại (721 → 741 dòng). Markup + JS inline |
| `app/static/css/customer/customer_history.css` | Viết lại, prefix `ch-` (705 → 971 dòng) |
| `app/translations/{en,fi,vi}/LC_MESSAGES/messages.po` + `.mo` | +3 msgid |
| `messages.pot` | +3 msgid |

**Không đụng:** `app/routes.py`, `app/template_filters.py`, `app/database/db.py`, `customer_base.html`, các page khác. Dữ liệu context đã đủ, không cần đụng Python.

Số dòng tăng vì trang này gánh nhiều thứ hơn My bookings (2 loại bản ghi, 6 bộ lọc, 4 kiểu sort, phân trang 2 chế độ, gom tháng).

---

## 8. Đã verify / chưa verify

### Đã verify

- Render qua **Jinja env thật của app** (`create_app()`, filter và loader thật), 3 trạng thái dữ liệu: đầy (10 lịch + 5 hoá đơn) / rỗng / chỉ có lịch đã huỷ
- Xem thật trong Chrome ở **390px** (qua iframe 390×844) và **desktop**
- **Luồng tương tác đầy đủ ở 390px**, đo bằng JS trên DOM thật:

  | Bước | Kết quả |
  |---|---|
  | init | 8/10 hàng, có "Näytä lisää", 4 nhóm tháng |
  | Load more | 10/10 hàng, 6 nhóm tháng, nút biến mất |
  | status = completed | 8/8, chip bật viền hồng, `has-filters` bật |
  | sort = amount_desc | nhóm tháng **biến mất**, thứ tự `60, 60, 45, 45, 45, 38.5, 38.5, 38.5` |
  | Clear all | về mặc định, trang reset về 1 |
  | sang tab Laskut | 5/5, 3 nhóm tháng |
  | payment = google_pay | 0 hàng, hiện trạng thái rỗng đã lọc |
  | date = 30 ngày (Laskut) | 3/3 |

- **Sheet đáy:** `bottom = 844 = viewport height`, rộng đủ 390, scrim phủ kín, `body.ch-sheet-open` bật
- **Sticky tháng:** nhãn July dính ở `top = 56px`, đúng mép dưới `.customer-topbar` (`bottom = 57`)
- **Không tràn ngang:** `documentElement.scrollWidth === clientWidth === 376`
- Bàn phím: `.ch-row__link` focus được
- **0 em-dash** trong cả hai file mới

### Chưa verify

| Việc | Ghi chú |
|---|---|
| Phân trang số ở desktop | Chưa bấm thử nút trang / ellipsis. Logic `pageNumbers()` bê nguyên từ bản cũ nhưng chưa chạy tay |
| Tab Laskut ở desktop | Mới xem tab Varaukset |
| `prefers-reduced-motion` | Có block CSS nhưng chưa bật thử |
| Chạy app với DB thật | Chưa. Toàn bộ test dùng stub |
| Bản dịch VI trên trình duyệt | Mới thấy FI qua render |
| Sheet trên Safari iOS thật | `position: fixed` nằm trong `.ch-filters__strip` (`overflow-x: auto`). Theo spec thì fixed không bị overflow clip, Chrome đúng như vậy. Safari từng có bug ở chỗ này. **Nếu sheet bị cắt trên iOS: bỏ `overflow-x: auto` của `.ch-filters__strip`, cho chip `flex-wrap: wrap` xuống 2 hàng** |

---

## 9. Còn tồn đọng

| Việc | Ghi chú |
|---|---|
| **Tên tháng in ra tiếng Anh** | `.ch-month` hiện "August 2026" kể cả khi UI là FI/VI, vì `data-month` dùng `format_date('%B %Y')` mà filter này là `strftime` thuần, không qua locale. Cả app đang thế (mọi ngày tháng đều tiếng Anh) nên **không phải regression**, nhưng ở đây nó to và nổi. Cách gỡ: thêm một jinja global bọc `flask_babel.format_date` rồi dùng riêng cho `data-month`. Là thay đổi Python nên chưa làm |
| **Nút "Leave Review" vẫn chết** | Grep toàn repo: không có handler. Đã có sẵn từ trước, giữ nguyên hành vi, không tự ý bịa modal |
| Cột giá desktop không thẳng hàng | Mỗi `.ch-row` là một grid riêng nên track `auto` co theo nội dung từng hàng; hàng có "Reviewed" và hàng có "Leave Review" đẩy cột giá lệch nhau ~40px. `.bk-row` bên My bookings **cũng vậy**, giữ để đồng bộ. Muốn thẳng thì phải cố định width cột giá + cột hành động, đổi lại là rủi ro tràn với bản dịch dài |
| Context thừa chưa dọn | `routes.py` vẫn tính `fav_stylist['count']` / `top_service['count']`; template có dùng, nên lần này không thừa. Nhưng `stylists` / `services` truyền cả object trong khi chỉ cần `id` + tên |
| Không có dark mode | Cả app không có dark mode ở đâu |

---

## 10. Ghi chú cho lần sau

- **Icon dùng Material Symbols** (cả app đang dùng), không đổi sang Phosphor/Tabler dù skill design ưu tiên. Dấu tick trong `.ch-opt.is-active::after` dùng ligature: `content: "check"` + `font-family: "Material Symbols Outlined"`
- **`[hidden]` thua class selector.** `.ch-empty { display: flex }` và `.ch-scrim { display: block }` sẽ nuốt `[hidden]` của UA stylesheet. Phải khai thêm `.ch-empty[hidden] { display: none }`, hoặc dùng class trạng thái thay vì thuộc tính `hidden`
- **Test animation trong tab nền là vô nghĩa.** Chrome đóng băng CSS animation khi `document.visibilityState === "hidden"`; đo `getBoundingClientRect()` lúc đó ra toạ độ của khung hình đầu tiên. Mất một vòng debug vì tưởng `bottom: 0` sai. Cách gỡ: `document.getAnimations().forEach(a => a.finish())` rồi mới đo
- **Cửa sổ Chrome đang maximize thì `resize_window` không ăn.** Test mobile bằng `<iframe width="390">`: media query và `matchMedia` bên trong iframe chạy theo viewport của iframe, đúng như thiết bị thật
- Codebase không có reset `box-sizing: border-box` toàn cục. CSS mới tự khai trong phạm vi `.ch`
- `format_date` filter nhận format arg nên tách được ngày / tháng / nhãn tháng trong template mà không cần đụng Python
