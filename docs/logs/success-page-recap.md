# Redesign UI: Success Page

**Ngày:** 2026-08-09 · **Phạm vi:** `/success` (viết lại template + CSS) + guard trong `main.success` + 12 chuỗi dịch · **Trạng thái:** ⚠️ code xong, đã render-test cả 5 status × 3 ngôn ngữ, Mon đã bắt 1 bug sticky và đã sửa, **chưa xem hết trên trình duyệt**, chưa commit

Nối tiếp `docs/logs/booking-wizard-recap.md` (`1ce00c2`). Đây là bước cuối của luồng đặt lịch: khách vừa rời wizard thì rơi vào trang này.

---

## 1. Đợt này ĐẢO một quyết định cũ

`success.html` bản trước có một khối comment 7 dòng ghi rõ:

> *"trạng thái booking thực tế lúc này là 'pending' trong DB (chưa được salon xác nhận), nhưng theo quyết định của Mon, nội dung trang VẪN giữ nguyên wording 'Booking Confirmed!' ... Đây là lựa chọn UX có chủ đích (ưu tiên cảm giác an tâm cho khách hơn là phản ánh chính xác trạng thái backend), Claude Code không cần 'sửa lại cho đúng'"*

Mon đảo lại: trang phải nói đúng trạng thái thật. Comment đó đã được viết lại kèm ngày, vì nếu để nguyên thì agent sau sẽ đọc và revert nguyên đợt này.

> **Bài học:** một chỉ thị "đừng sửa" nằm trong code phải được cập nhật ngay khi quyết định thay đổi, không phải chỉ sửa code rồi để comment nói ngược lại.

**Thay đổi này chạm tới cảm nhận thật của khách**, không chỉ là UI: trước đây 100% khách chọn "pay at salon" đều đọc thấy "Booking Confirmed!" dù DB là `pending`.

---

## 2. Tranh luận về status, và Mon đúng

Bản plan đầu tôi định dựng **bốn** biến thể status (`confirmed`, `pending`, `unverified`, `cancelled`), lập luận rằng `unverified` rò được vì `session["booking_id"]` set trước cổng xác thực.

Mon phản biện: `/success` chỉ mở sau khi verify email (pay at salon) hoặc sau khi thanh toán xong (pay online), nên chỉ có `pending` và `confirmed`.

**Đo lại thay vì cãi.** Kết quả: cả hai đều đúng một nửa.

| | |
|---|---|
| Mon đúng | Trong luồng chủ đích, chỉ `pending` và `confirmed` xảy ra |
| Tôi đúng | Route không có guard status nào. Test: cả 5 status đều render HTTP 200 |

Cơ chế rò, xác nhận bằng code:

```
routes.py:4302 / 1447   session["booking_id"] = ...  ngay trước redirect /email-verification
routes.py:4283 / 1428   session["booking_id"] = ...  ngay trước redirect sang Stripe
```

`BookingService.create()` tạo booking với `"unverified"`; OTP mới đổi sang `pending`. **Không chỗ nào clear `session["booking_id"]`**, session sống 8h (`config.py:41`). Nên:

1. Bỏ ngang OTP hoặc Stripe rồi gõ lại `/success` → `unverified`
2. Trong 8h sau khi đặt xong, salon huỷ / admin đánh `no-show` → khách quay lại từ history → `cancelled` / `no-show`

**Nhưng phản biện làm thiết kế gọn hơn.** Dựng biến thể cho `cancelled` là vẽ thêm: với một booking đã huỷ thì mọi câu chữ của trang xác nhận đều sai, không có wording nào cứu được. Chốt lại:

- Dựng **2** biến thể (`pending`, `confirmed`), bỏ 2 biến thể và 4 chuỗi dịch
- Thêm **guard 2 dòng** vào route, cùng phong cách với hai guard đã có sẵn ngay trên nó

```python
if booking["status"] not in ("pending", "confirmed"):
    return redirect(url_for("main.home"))
```

> **Bài học:** khi user phản biện một giả định, đo lại chứ đừng bảo vệ. Ở đây đo xong ra kết quả tốt hơn cả hai phương án ban đầu: ít code hơn *và* không bao giờ render được câu sai.

---

## 3. Audit trạng thái cũ

### A. Bốn tell của UI do AI sinh

| Vấn đề | Chi tiết |
|---|---|
| **URL ảnh sẽ chết** | `.bkc-account-cta__bg-img` hardcode `lh3.googleusercontent.com/aida/AP1WRL...`, asset do Stitch sinh ra |
| **Màu hồng thứ tư** | `rgba(214, 70, 130, ...)` = `#d64682`, ba chỗ. Chính màu mà đợt Loyalty và Membership đã xoá khỏi project |
| **Hai blob blur 120px** | Trang trí gradient blob kinh điển |
| **Hai card đều nhau** | Khối "What's Next" là hai ô giống hệt, cạnh nhau |

### B. Vòng lặp animation nói sai

```css
.bkc-header__icon-ping { animation: bkc-ping 2s ... infinite; }
```

Vòng ping lặp vô hạn quanh icon `check_circle`. Nhịp lặp nói "đang chờ" trong khi hình vẽ nói "đã xong", và không có guard `prefers-reduced-motion`.

### C. Alt text sai vật thể

```html
<img src="/static/images/public/nail_studio.jpg" alt="{{ _('Map location') }}">
```

Ảnh chụp tiệm, không phải bản đồ. Trình đọc màn hình đọc ra một vật không tồn tại.

### D. Header CSS mô tả sai file

Ghi *"BOOKING_PENDING.CSS ... dùng riêng cho templates/booking_pending.html"*. File đó không tồn tại.

---

## 4. Các thay đổi

### Chữ theo status

Không nội suy thô `Booking {{ status }}`, vì ba lý do: `Booking pending` là tiếng Anh dở; **gettext không dịch được phần nội suy** nên VIE/FIN sẽ kẹt tiếng Anh; và `no-show` / `done` sẽ cho ra chữ vô nghĩa. Thay bằng ánh xạ, mỗi status một chuỗi trọn vẹn.

| status | Tiêu đề | Phụ đề |
|---|---|---|
| `confirmed` | Booking confirmed | *(giữ nguyên câu cũ)* We've reserved your spot. Get ready for some well-deserved pampering. |
| `pending` | Booking received | We've got your request. We'll email you as soon as the salon confirms your appointment. |

Badge cũng đổi: `check_circle` trên nền xanh `#A7E0C0` khi confirmed, `hourglass_top` trên nền hổ phách `#FBF0D8` khi pending. Dùng đúng token semantic đã có, không chế màu mới. Accent `#ab2261` vẫn là accent duy nhất của trang.

### Dải tiến trình ba mốc

Thay khối "What's Next". Mốc giữa là `--current` và **thở** khi pending, thành `--done` và tắt hẳn khi confirmed.

```
pending    ●━━━━━━━━◉┄┄┄┄┄┄┄┄○
           Đã nhận   Salon      Buổi hẹn
           yêu cầu   xác nhận   của bạn
                     ↑ thở

confirmed  ●━━━━━━━━●┄┄┄┄┄┄┄┄○
```

Đây là câu trả lời cho "sao chưa confirmed", và là **animation lặp duy nhất còn lại** trên trang. Vòng ping từ chỗ vô nghĩa (icon của trạng thái đã xong) chuyển sang đúng mốc đang chờ, nên nhịp lặp mang đúng nghĩa.

### Vé hẹn

Thay card kính. Thân vé và cuống tách bằng đường `border-top: 1px dashed`, hai khuyết tròn nền trang đè lên mép trái phải ăn mất cả viền lẫn đường răng cưa ở đúng chỗ đó. Cuống chỉ chứa Add to Calendar.

Không dùng `overflow: hidden` trên thẻ vé vì hai khuyết phải tràn ra ngoài mép; ảnh tự bo góc riêng.

Ở mobile ảnh nhảy lên trên bằng `order: -1` và đổi sang 16:9, vì ở một cột thì ảnh vuông 190px cạnh chữ sẽ bóp cột chữ còn quá hẹp.

### Còn lại

- Account CTA: bỏ URL Google chết, dùng nền plum đặc. Nút đổi sang pearl với chữ plum vì hồng trên plum chỉ đạt ~1.7:1, cùng cách xử lý `lp-` và `ms-` đã dùng
- Location: sửa `alt` thành "DahaCare studio", thêm pill "Open in Maps" để nói rõ click sẽ đi đâu
- Token scope vào `.bkc`, thang bo góc 20/14/12/999, box-sizing khai trong phạm vi

---

## 5. Bug Mon bắt được: `<header>` dính lên đỉnh màn hình

Sau khi ship, Mon báo tiêu đề "Booking received" và dòng phụ đề bị kéo theo khi cuộn xuống.

Grep `success.css`: **không có `position: sticky` hay `fixed` nào**. Nguyên nhân nằm ở `base.css:98`:

```css
header {
    position: sticky;
    top: 0;
    z-index: 100;
}
```

**Selector thẻ trần**, viết cho navbar của site. Bản cũ dùng `<div class="bkc-header">` nên không dính. Trong bản viết lại tôi đổi thành `<header class="bkc-head">` cho đúng ngữ nghĩa (h1 + mô tả trang), và thế là nó ăn nguyên rule đó.

Sửa: trả `.bkc-head` về `static` ngay trong `success.css`, giữ thẻ `<header>` vì ngữ nghĩa đúng. Không sửa `base.css` vì rule đó phục vụ navbar toàn site.

Đã quét lại: `base.css` chỉ có **đúng một** selector thẻ trần loại này; trong ba template vừa động tới chỉ `success.html` dùng `<header>`.

> **Bài học:** đổi một thẻ `<div>` sang thẻ ngữ nghĩa (`header`, `footer`, `nav`, `main`, `section`) là một thay đổi CSS, không chỉ là thay đổi HTML. Grep selector thẻ trần trong stylesheet toàn cục trước khi đổi.

---

## 6. Bản dịch

12 chuỗi mới, điền đủ cho vi và fi. `en` để trống msgstr theo quy ước sẵn có.

| msgid | vi | fi |
|---|---|---|
| Booking confirmed | Đã xác nhận lịch hẹn | Varaus vahvistettu |
| Booking received | Đã nhận lịch hẹn | Varaus vastaanotettu |
| Request received | Đã nhận yêu cầu | Pyyntö vastaanotettu |
| Salon confirms | Salon xác nhận | Salonki vahvistaa |
| Your appointment | Buổi hẹn của bạn | Varattu aikasi |
| Your time is locked in. | Giờ hẹn của bạn đã được giữ. | Aikasi on varmistettu. |
| Open in Maps | Mở trong Maps | Avaa kartalla |
| DahaCare studio | Tiệm DahaCare | DahaCare-salonki |

*(cùng 4 chuỗi câu dài: phụ đề pending, ghi chú của ba mốc)*

### `pybabel` fuzzy suýt phá đúng thứ đợt này sinh ra để sửa

| msgid | fuzzy gán vào (vi) | fuzzy gán vào (fi) |
|---|---|---|
| **Booking received** | **Đã xác nhận đặt lịch** | **Varaus vahvistettu** |
| Salon confirms | Liên hệ salon | Salongin yhteystiedot |
| Your appointment | Đặt lịch hẹn | Varaa aika |
| Open in Maps | Bản đồ vị trí salon | Salongin sijaintikartta |

Dòng đầu là **nghĩa ngược hoàn toàn**: "Booking received" bị gán bản dịch của "Booking confirmed". Nếu ai gỡ cờ fuzzy thì trang tiếng Việt sẽ nói "Đã xác nhận" cho một booking đang chờ, tức là đúng cái sai mà đợt này sinh ra để sửa. Đã ghi đè cả 12 và xoá cờ.

Bốn entry fuzzy còn lại (`Previous slide`, `Next slide`, `Mở menu`, `JPG, PNG tối đa 10MB` ở fi) vốn đã fuzzy từ trước, không đụng.

> **Bài học:** đây là lần thứ hai liên tiếp `pybabel update` gán fuzzy sai nghĩa (đợt trước: `Morning` → `phút`, `Evening` → `Chờ duyệt`). Sau mỗi lần `update`, luôn liệt kê fuzzy mới và đọc từng dòng trước khi compile.

---

## 7. Đã verify / chưa verify

**Đã chạy:**

| Kiểm tra | Kết quả |
|---|---|
| Guard trên cả 5 status | `pending` `confirmed` → 200 · `unverified` `cancelled` `no-show` → 302 |
| Nội dung theo status | pending: 1 mốc `--current` + 1 `--done` · confirmed: 0 `--current` + 2 `--done` |
| Guest vs đã đăng nhập | khối mời tạo tài khoản: guest có, logged-in không |
| 3 ngôn ngữ × 2 status | tiêu đề, phụ đề, ba nhãn mốc đều đúng |
| Đọc ngược 12 chuỗi từ `.mo` | đúng ở cả vi và fi |
| CSS | 97 cặp ngoặc cân bằng, 0 rule rỗng, 0 `:root` trần |
| Dọn slop | 0 `#d64682`, 0 `googleusercontent` trong markup, 0 blob, 0 `Map location`, 0 em-dash |
| Đối chiếu class CSS ↔ markup | không có class mồ côi |
| Quét selector thẻ trần trong `base.css` | chỉ 1 (`header`), đã xử lý |

**Chưa verify (cần xem trên trình duyệt):**

- Hai khuyết vé ở mobile, chỗ dễ lệch nhất
- Nhịp thở của mốc giữa, và nó tắt hẳn khi `confirmed`
- Ảnh service `order: -1` + 16:9 ở mobile
- Nút "Open in Maps" trên ảnh có đủ tương phản với mọi vùng ảnh không

---

## 8. File thay đổi

| File | Thay đổi |
|---|---|
| `app/routes.py` | guard 2 dòng + truyền `booking_status` |
| `app/templates/public/success.html` | viết lại, đảo chỉ thị cũ |
| `app/static/css/public/success.css` | viết lại |
| `app/translations/{en,fi,vi}/LC_MESSAGES/messages.{po,mo}` | 12 chuỗi mới, 7 fuzzy sửa |
| `messages.pot` | extract lại |

---

## 9. Nợ kỹ thuật còn lại

| Việc | Ghi chú |
|---|---|
| `session["booking_id"]` không ai clear | Gốc rễ của việc booking chưa xác thực còn nằm trong session 8h. Guard mới chặn được phần hiển thị, chưa dọn gốc. Task riêng |
| `header {}` selector thẻ trần trong `base.css` | Vẫn còn. Mọi trang dùng thẻ `<header>` cho mục đích khác đều sẽ dính. Nên đổi thành `.site-header` khi có dịp chạm vào |
| 4 entry fuzzy cũ | `Previous slide`, `Next slide`, `Mở menu`, `JPG, PNG tối đa 10MB` |
| `payment/success.html` | Trang trung gian sau Stripe, chưa redesign, không nằm trong đợt này |
