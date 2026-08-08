# Redesign UI khách hàng: Loyalty Points

**Ngày:** 2026-08-09 · **Phạm vi:** `/customer/loyalty-points` (viết lại toàn trang) + partial `redeem_confirm_modal.html` · **Trạng thái:** ⚠️ code xong, chưa xem trên trình duyệt với DB thật, nhiều nhánh chỉ test bằng stub vì DB chưa có dữ liệu, chưa deploy

Trang phức tạp nhất của bộ portal khách hàng. Nối tiếp `docs/CUSTOMER_UI_REDESIGN.md` (My bookings + Dashboard), `docs/logs/customer-history-mobile-recap.md` (History) và `docs/logs/booking-invoice-detail-recap.md` (Booking details + Invoice detail).

Trước đợt này, `loyalty_points.html` là **1498 dòng trong một file**: 1069 dòng `<style>` inline, 153 dòng `<script>` inline, và là trang duy nhất của portal không có file CSS riêng.

---

## 1. Phát hiện làm đổi thiết kế giữa lúc lên plan: tier không dựa trên điểm

Đề xuất ban đầu của tôi là một "thang tier" có ngưỡng điểm, kiểu `còn 1 250 pts tới Gold`. **Sai mô hình nghiệp vụ.**

`membership_tiers` có `price`, `duration_days`, `stripe_price_id`, và `get_customer_current_tier()` đọc từ `customer_memberships` với `stripe_subscription_id IS NOT NULL`. Tier là **gói subscription trả tiền**, Silver là bậc miễn phí mặc định:

| Tier | price | point_multiplier |
|---|---|---|
| Silver | 0.00 | ×1.0 |
| Gold | 49.99 | ×1.5 |
| Diamond | 99.99 | ×2.0 |

Nghĩa là bản cũ **nói sai**, không chỉ nhập nhằng: nó đặt `.tier-badge` ("Silver Tier") ngay cạnh một progress bar tính theo `balance / next_reward_pts`, nên khách đọc ra là tích đủ điểm sẽ tự lên tier. Thực tế muốn lên Gold thì phải mua.

Thang tier mới: ba mốc, **không có ngưỡng điểm nào**, và thứ nó nói là quyền lợi thật (`point_multiplier`) cùng ngày hết hạn gói.

> **Bài học:** đọc schema trước khi thiết kế thứ hiển thị schema đó. Cả `price` và `stripe_price_id` đều nằm ngay trong bảng, chỉ cần mở ra xem.

---

## 2. Audit trạng thái cũ

### A. Lệch khỏi hệ thống portal

| Vấn đề | Chi tiết |
|---|---|
| **Màu hồng thứ tư** | `#d64682` xuất hiện ~30 lần. Portal đã chuẩn hoá `#ab2261` sau hai đợt trước |
| **Màu hồng thứ năm** | `#ef3976` trong `redeem_confirm_modal.html`, kèm cả một bộ token riêng (`#221016`, `#5a4045`, `#e2bdc3`, `#fdf2f5`) |
| **Dải tím** | Tier diamond dùng `#8a2be2`, `#7c3aed`, `#c084fc`, `#e6e6fa`. Đúng "AI purple" |
| **8 màu tag ngoài palette** | `.reward-meta-tag` dùng 4 cặp xanh dương / xanh lá / vàng / đỏ. Cộng mint `#dff3e7` và xanh `#228b5d` ở history |
| **3 gradient ngoài palette nữa** | `_MISSION_SLOT_BG` trong `routes.py`: vàng `#f59e0b`, tím `#8b5cf6`, xanh lá `#059669` |
| **Font không tồn tại** | Modal set `font-family: 'Manrope'` và comment ghi "loaded từ customer_base.html". Base nạp Plus Jakarta Sans, chưa từng nạp Manrope, nên nó luôn rơi về mặc định |
| **0 Material Symbols, 16 emoji làm icon** | ⭐ 🔒 🚫 ✅ 💅 🎁 ➕ ✕ ✓ ✦ ← → |
| **Hệ tab thứ ba** | Underline tab ở đây, segmented pill ở My bookings và History |
| CSS nằm inline | 1069 dòng trong `<style>` |
| Nạp lại font | Template tự `<link>` Plus Jakarta Sans dù base đã nạp. Một request thừa |
| 24 em-dash | 7 trong template, 17 trong modal |

### B. Ba bug thật trên mobile

**1. Nút mission vô hình nhưng vẫn bấm được.**
```css
.carousel-slide a       { opacity: 0; transform: translateY(8px); }
.carousel-slide:hover a { opacity: 1; }
```
Không có hover trên cảm ứng nên nút CTA luôn `opacity: 0`. Và vì không có `pointer-events: none`, nó **vẫn nhận tap**: khách bấm trúng một vật mình không nhìn thấy. Ẩn thị giác mà vẫn bấm được là tệ hơn cả hai lựa chọn.

**2. Mũi tên carousel cũng hover-only.** `.mission-card:hover .mission-arrow { opacity: 1 }`. Điều hướng duy nhất còn lại ở mobile là dot 6px.

**3. Autoplay 3 giây không pause được ở mobile.** `pauseCarousel()` gắn vào `onmouseenter` / `onmouseleave`. Khách đang đọc thì slide tự trượt đi.

Kèm: `.mission-arrow` 36px và `.carousel-dot` 6px, đều dưới ngưỡng chạm 44px.

### C. Voucher không truy cập được bằng bàn phím

`onclick="openVoucherDetail(this)"` trên `<div>` + `cursor: pointer`. Đây là **lần thứ ba** cùng một lỗi trong portal: đã sửa ở `my_bookings` (`<article>`) rồi `customer_history` (`<tr>`).

### D. Nhập nhằng ngữ nghĩa và IA

| Vấn đề | Chi tiết |
|---|---|
| Progress bar nói một chuyện, badge cạnh nó nói chuyện khác | Xem mục 1 |
| **Nhãn section sai** | Heading là `Available Vouchers` nhưng nội dung bên dưới là **rewards** (thứ để đổi), không phải vouchers (thứ đã đổi rồi). Hai khái niệm tồn tại song song trong trang |
| Voucher bị nhét làm tab 2 của history card | Voucher active là tài sản dùng được ngay; history là sổ ghi đã xong |
| 3 reward card bằng nhau | `repeat(3, 1fr)`, ở mobile thành 1 cột × N card ảnh 4:3 |
| Hai khối 300px chiếm màn hình đầu | `.balance-card` và `.mission-card` đều `min-height: 300px` |
| **Fake data trong template** | `\| default(1250)`, `'Free Gel Manicure'`, `'Transaction #8842'`, `'Oct 12, 2023'`. Route luôn truyền đủ nên là dead code, nhưng là dữ liệu bịa nằm trong file |

### E. Chuỗi tiếng Anh ghép trong Python

Trang duy nhất còn lỗi này:

| Dòng | Vấn đề |
|---|---|
| `1804` | `f"{'Earned on' if ... else 'Redeemed on'} {date_str}"` |
| `1807` | `ref = row["source"].replace("_"," ").title()` |
| `1788` | `next_reward_name = "All rewards unlocked!"` |
| `1844` | `f"Redeemed on {date_str}"` |
| `1840`, `1850` | ký tự U+2014 nằm trong chuỗi fallback |
| `1847` | `status: "active"` hardcode cho **mọi** voucher |

---

## 3. Cấu trúc mới

Prefix CSS: `lp-` (giữ tên cũ vì nó đã là `lp-`).

```
Điểm thưởng                          h1
┌ THẺ THÀNH VIÊN (plum) ────────────┐
│ SỐ ĐIỂM              [SILVER]     │
│ 1 250 điểm                        │
│ ─────────────────────────────────  │
│  ●──────────○──────────○          │  thang tier
│  Silver     Gold       Diamond    │
│  ×1.0       ×1.5       ×2.0       │
│ [ Xem quyền lợi ]                 │
└───────────────────────────────────┘
VOUCHER CỦA TÔI  2                     dải cuộn ngang
TÍCH ĐIỂM                              dải cuộn ngang
PHẦN THƯỞNG          Xem tất cả        cuộn ngang mobile / lưới desktop
LỊCH SỬ ĐIỂM  7                        hàng phẳng + Load more
```

### Một pattern cuộn ngang cho ba dải

`.lp-strip` dùng cho cả ví voucher, nhiệm vụ và phần thưởng. Ở mobile cuộn tràn ra mép để card thứ hai hé ra (người dùng thấy ngay là còn nữa mà không cần dot hay mũi tên). Ở desktop mỗi dải nở ra theo cách riêng:

- `--wallet` và `--mission`: `flex: 1 1 0`, chia đều chiều ngang
- `--reward`: `grid-template-columns: repeat(auto-fill, minmax(250px, 1fr))`, vì số lượng do DB quyết định và có thể nhiều hơn 3

Cùng markup, không phân nhánh JS.

### Plum ở đây là nối tiếp, không phải trùng lặp

`.loyalty-card` trên Dashboard đã là plum, và trang này là bản đầy đủ của đúng card đó, giống quan hệ Next Visit card → Booking details.

### Thang tier

Đường nối chạy từ **tâm** mốc đầu tới **tâm** mốc cuối. Ba cột đều nhau nên tâm cột 1 ở 1/6 chiều rộng, tâm cột 3 ở 5/6, vẽ bằng `inset: 16.667%` hai bên chứ không bằng số px ước lượng. Dot của mốc hiện tại đục màu plum để che đường nối phía sau.

### Bỏ carousel, dùng scroll-snap native

Giải cả ba bug mục 2B mà không phải vá: nút CTA luôn trong tầm nhìn theo cơ chế mới (mục 4), không có gì tự trượt, swipe là hành vi native. Bỏ được ~60 dòng JS.

### Bỏ eyebrow và bỏ thanh progress reward

- Eyebrow `Rewards Club`: trang đã có `h1` và nav item đang active. Khác với `Next Visit` ở My bookings (nhãn **chức năng**, trả lời "card này là card gì"), nhãn này không trả lời câu hỏi nào.
- Thanh "tới reward kế tiếp": mỗi reward locked đã tự nói thiếu bao nhiêu điểm, nên thanh tổng ở đầu trang là lặp.

### Lý do khoá nói bằng chữ

Bản cũ đè emoji 🔒 🚫 ✅ ⏳ lên ảnh reward: không đọc được bằng screen reader, không dịch được. Nay là chữ (`Không đủ điểm`, `Hết hàng`, `Đã đạt giới hạn` + `làm mới sau N ngày`), và thẻ khoá thì ảnh xám + chìm màu, cùng quy ước `.bk-row--cancelled`.

---

## 4. Nút mission: ẩn rồi trồi lên, ba đường kích hoạt

User muốn quay lại pattern ẩn/hiện, nhưng khác bản cũ ở một điểm quyết định: **`pointer-events: none` khi ẩn**. Bản cũ thiếu nó nên nút vô hình vẫn nhận tap.

| Đường | Dành cho | Ghi chú |
|---|---|---|
| `:hover` | chuột | Gated trong `@media (hover: hover) and (pointer: fine)`. Trên cảm ứng `:hover` dính lại sau tap và nhả ra tuỳ trình duyệt, nên không dùng nó làm cơ chế chính ở đó |
| `:focus-within` | bàn phím | Không có nhánh này thì tab tới nút là **focus mù**: nút nhận focus mà vẫn vô hình |
| `.is-open` | cảm ứng | JS toggle khi chạm card. Chỉ một card mở tại một thời điểm; chạm ra ngoài đóng hết |

Nút của mission **đã hoàn thành** là ngoại lệ: nó là **nhãn trạng thái**, không phải hành động. Ẩn nó là mất thông tin, và nó `disabled` nên `:focus-within` không bao giờ bật để hiện lại. Template gắn `.lp-mis__cta--static` cho card đó.

Quét kiểm: mọi khối đặt `opacity` trên `.lp-mis__cta` đều kèm `pointer-events` đúng chiều.

---

## 5. Text trong mission card + trạng thái hoàn thành

### Text

Hai dòng chữ trắng xếp dọc cùng trọng lượng đọc ra như một khối xám. Nay:

- **Chip điểm**: pill kính nhỏ. Là *dữ liệu* (số điểm thưởng) chứ không phải nhãn phân loại, nên không vi phạm quy tắc tiết chế eyebrow. `pts_label` do admin nhập nên giữ nguyên chuỗi, chỉ đổi cách vẽ
- **Tên**: `1.06rem / 800`, cắt ở **2 dòng** bằng `line-clamp`. Tên do admin nhập dài ngắn khác nhau ("Book Your First Appointment" vs "Write a Review"), hai card lệch chiều cao thì dải cuộn trông như lỗi
- `text-shadow` nhẹ: scrim lo phần lớn độ đọc, shadow lo phần còn lại khi admin tải ảnh sáng
- Thứ tự đọc: phần thưởng trước, việc phải làm sau

**Tên và điểm luôn hiện kể cả khi slide có ảnh.** Bản cũ `{% if not m.img %}` nên slide có ảnh thì không có chữ nào: chữ nằm trong ảnh không dịch được và screen reader không đọc được.

### Trạng thái hoàn thành (`.lp-mis--done`)

Card đổi hẳn bố cục: nhãn về **giữa** làm tâm điểm, tên tụt xuống đáy làm chú thích. Nó không còn là lời mời nên không cần cấu trúc của một lời mời.

**Chip điểm bị bỏ ở trạng thái này** vì điểm đã vào ví; in lại "+50 pts" là mời gọi một việc không còn làm được. Đây cũng là thứ giải phóng chỗ cho nhãn giữa mà không chồng lên text.

Xanh lá là **màu thứ ba mang thông tin** của portal, cùng loại với hổ phách (`pending`) và đỏ (`cancelled`), không phải màu trang trí. Token `--lp-done: #A7E0C0`, chọn tông pastel cùng độ sáng với hổ phách `#F4DFA8` vốn đã dùng trên plum, **không phải mint sáng** mà đợt Dashboard đã bỏ vì lạc palette.

| Đo | Kết quả |
|---|---|
| `#A7E0C0` trên nền nút | **8.3:1** (đạt AAA) |
| `#A7E0C0` trên scrim | 12.1:1 |
| đối chiếu: hổ phách trên plum | 10.7:1 |

Nút vẫn là lớp kính cùng họ `.lp-btn--glass`, chỉ đổi hue, nên hai trạng thái đọc ra là **cùng một vật ở hai tình huống**.

Ảnh nền `blur(3px) saturate(0.8) brightness(0.92)`, scrim nhạt lại vì ảnh đã mờ (cộng scrim dày nữa thì card thành mảng xám).

---

## 6. Ba bug cascade quanh `scale(1.06)`

`scale(1.06)` trên ảnh mờ **không phải hiệu ứng**: blur lấy mẫu cả vùng ngoài biên nên mép ảnh nhoè thành viền sáng nếu không phóng bù. Ba chỗ suýt xoá nó:

| Chỗ | Vấn đề | Sửa |
|---|---|---|
| Rule hover chung nằm **sau** khối `--done`, cùng specificity `(0,3,0)` | ghi đè `1.06` thành `1.04` | `:not(.lp-mis--done)` |
| `prefers-reduced-motion` đặt `transform: none` khi hover | **xoá hẳn scale → lộ viền sáng** | `:not(.lp-mis--done)`, kèm comment nói rõ đây là transform tĩnh chứ không phải chuyển động |
| `prefers-reduced-transparency` chỉ xử lý `.lp-btn--glass` | chip điểm trong suốt khi tắt transparency | thêm `.lp-mis__pts`; nút done giữ hue xanh khi đục lại |

> **Bài học:** khi một `transform` phục vụ mục đích kỹ thuật (bù blur, che mép) chứ không phải thị giác, mọi block `prefers-reduced-*` đều là nơi nó có thể bị xoá oan. Ghi chú ngay tại chỗ.

---

## 7. Hai bug user bắt được, và vì sao chúng xảy ra

### Modal chi tiết voucher trong suốt

Token CSS khai trên `.lp`. Nhưng hai modal là **sibling** của `.lp` trong DOM, không phải con:

```
<div class="lp"> … </div>
{% include redeem_confirm_modal %}  → .rdm
<div class="lp-vd">                 → .lp-vd
```

Tôi phát hiện vấn đề này cho `.rdm` và thêm nó vào scope, rồi **bỏ sót `.lp-vd`**. `background: var(--lp-surface)` với biến undefined là invalid → card không có nền → nhìn xuyên qua backdrop.

Sửa: token khai cho cả ba gốc. Verify không bằng mắt mà bằng cách quét mọi `var(--lp-*)` dùng trong khối `.lp-vd` / `.rdm` rồi đối chiếu danh sách token được khai: `.lp-vd` dùng 18 var, `.rdm` dùng 15 var, thiếu khai 0.

### Tab "My Vouchers" luôn rỗng

Tôi tách voucher hai nơi bằng `rejectattr('status','equalto','active')`, trong khi **biết** `routes.py` hardcode `status: "active"` cho mọi voucher. Nhánh "đã xong" toán học không bao giờ có phần tử.

Vòng sửa 1: tab hiện tất cả voucher. Nhưng như vậy dải ví và tab cùng nhãn cùng nội dung. Tôi nêu nó là "hệ quả cần bạn biết" thay vì sửa, và user chỉ ra rằng đó là trùng lặp.

Vòng sửa 2 (đúng): **bỏ tab, giữ dải ví**. Voucher có một nơi duy nhất, dùng được xếp trước, đã dùng / hết hạn xếp sau và vẽ mờ. Dải cuộn ngang nên chứa thêm không tốn chiều dọc.

> **Bài học 1:** không lọc theo một field mình biết là hardcode. Nếu buộc phải giữ field đó, thiết kế phải không phụ thuộc vào giá trị của nó.
> **Bài học 2:** khi phát hiện hệ quả xấu của chính thiết kế mình đưa ra, sửa nó, đừng ghi nó thành ghi chú cho user.

### Khoảng cách section dính nhau

Nguyên nhân: tôi đặt khoảng cách ở `.lp-head` (`margin-top: 34px`) thay vì ở section. Khối sổ điểm mở đầu bằng tabs chứ không bằng `.lp-head` nên nó dính sát khối trên.

Sửa gốc: `.lp-sec { margin-top: 34px }` và `.lp-head { margin: 0 0 14px }`. Giờ khoảng cách không phụ thuộc việc section có heading hay không.

Bỏ tab cũng làm CSS tabs thành dead code, nên xoá luôn phần vừa viết: `.lp-tabs`, `.lp-tabs__marker`, `.lp-tab`, `.lp-tab__n`, `.lp-panel`, `.lp-old*`, `--tab-i`, cùng ~25 dòng JS.

---

## 8. i18n: 10 msgid mới

Nhiều hơn hai đợt trước (0 và 1) vì trang này là trang duy nhất còn ghép chuỗi tiếng Anh **trong Python**.

| msgid | en | fi | vi |
|---|---|---|---|
| `Rewards` | (fallback) | Palkinnot | Phần thưởng |
| `Earned on` | (fallback) | Ansaittu | Nhận ngày |
| `All rewards unlocked!` | (fallback) | Kaikki palkinnot avattu! | Đã mở hết phần thưởng! |
| `Booking` | (fallback) | Varaus | Lịch hẹn |
| `Double points` | (fallback) | Tuplapisteet | Điểm nhân đôi |
| `First booking` | (fallback) | Ensimmäinen varaus | Lịch hẹn đầu tiên |
| `Streak bonus` | (fallback) | Putkibonus | Thưởng chuỗi |
| `Manual adjustment` | (fallback) | Manuaalinen korjaus | Điều chỉnh thủ công |
| `Reward redemption` | (fallback) | Palkinnon lunastus | Đổi phần thưởng |
| `No rewards available` | (fallback) | Ei palkintoja saatavilla | Chưa có phần thưởng nào |

Sáu nhãn nguồn điểm map từ giá trị `source` thật, đã trace hết `award_points()`: `booking`, `double_points`, `first_booking`, `streak` (`booking_service.py:196-220`), `admin_adjustment` (`routes.py:3146, 3235`), `reward_redemption` (`db.py:1084`). Đúng 6 giá trị, hữu hạn.

Giảm được 3 msgid bằng cách tái dùng: empty state của sổ điểm dùng `No history yet.` của trang History; nút gọi salon không cần `Call` vì nó hiện chính số điện thoại.

---

## 9. `format_number`: sai quy ước locale

Filter trả `1,250`. Ở fi/vi dấu phẩy là dấu **thập phân**, nên `1,250` đọc thành "một phẩy hai lăm", trong khi `format_currency` cùng repo trả `1 234,50 €` với khoảng trắng ngăn nghìn.

Grep toàn repo: `format_number` có **đúng một** consumer, chính là dòng tôi vừa viết. Nên sửa filter là zero-risk:

```
1250 -> '1 250'    (nbsp, khớp format_currency)
```

---

## 10. Files

| File | Trước | Sau |
|---|---|---|
| `app/templates/customer/loyalty_points.html` | 1498 | **477** |
| `app/static/css/customer/loyalty_points.css` | (không tồn tại) | 1521 |
| `app/templates/customer/redeem_confirm_modal.html` | 520 | **168** |
| `app/routes.py` | | +69 / -14 |
| `app/template_filters.py` | | `format_number` |
| `app/translations/{en,fi,vi}/LC_MESSAGES/messages.po` + `.mo` | | +10 msgid |
| `messages.pot` | | +10 msgid |

**Không đụng:** `app/database/db.py`, `customer_base.html`, `customer_membership.html` (trang tier benefits riêng, ngoài scope), `my_booking.js`, các trang khác, URL slug, nav label.

Template giảm **68%** vì CSS ra file riêng và ~85 dòng JS (carousel + tabs) bị bỏ. Modal giảm 68% vì `<style>` chuyển vào file CSS chung, và vì partial chỉ được include ở đúng một nơi (đã grep) nên đặt ở đó là đủ.

---

## 11. Đã verify / chưa verify

### Đã verify

Toàn bộ bằng render qua **Jinja env thật của app** (`create_app()`, filter và loader thật), **không dùng browser** (xem mục 13).

**8 nhánh trạng thái**, mỗi nhánh đúng số khối và đúng số empty state:

| Nhánh | ví | mission | reward | hàng sổ | empty | Load more |
|---|---|---|---|---|---|---|
| đầy đủ | 1 | 2 | 4 | 8 | 0 | có |
| không voucher | 0 | 2 | 4 | 8 | 0 | có |
| không reward | 1 | 2 | 0 | 8 | 1 | có |
| không history | 1 | 2 | 4 | 0 | 1 | không |
| không mission | 1 | 0 | 4 | 8 | 0 | có |
| tier Gold + expiry | 1 | 2 | 4 | 8 | 0 | có |
| balance 0 | 1 | 2 | 4 | 8 | 0 | có |
| rỗng hết | 0 | 0 | 0 | 0 | 2 | không |

Luôn đúng **1** mốc tier được đánh dấu ở mọi nhánh.

**Ví voucher:**

| Dữ liệu | dải ví | mờ | badge |
|---|---|---|---|
| 2 active + 1 used | 3 | 1 | `Đã dùng` |
| chỉ 1 used | 1 | 1 | `Đã dùng` |
| không có | section ẩn hẳn | | |

**Mission card, 3 biến thể:** có ảnh (chip + tên, cta ẩn) · đã xong (`--done`, không chip, cta static) · không ảnh (emoji fallback hiện).

**Nội dung dịch, `vi` và `fi`** (mỗi lần một `test_request_context` riêng):
```
vi  1 250 điểm · Gold · Hết hạn 12.09.2026 · ×1.0/×1.5/×2.0 điểm
    Voucher của tôi · Tích điểm · Phần thưởng · Lịch sử điểm
    +85 / -800 điểm · Đã đạt giới hạn (làm mới sau 12 ngày)
fi  Kuponkini · Ansaitse pisteitä · Palkinnot · Pistehistoria
    Vanhenee 12.09.2026 · Raja saavutettu (uusiutuu 12 päivää)
```

**Kiểm cơ học:**
- Palette lock: `#d64682`, `#ef3976`, dải tím, `#228b5d`, `Manrope` chỉ còn trong **comment giải thích**, không còn giá trị sống nào
- 0 em-dash / en-dash trong cả ba file
- CSS braces cân bằng, template braces cân bằng
- 0 CSS dead còn sót, 0 class dùng trong template mà CSS không có
- Mọi `var(--lp-*)` dùng trong `.lp-vd` (18) và `.rdm` (15) đều được khai
- Mọi khối đặt `opacity` trên `.lp-mis__cta` đều kèm `pointer-events` đúng chiều
- Mọi rule đặt `transform` trên `.lp-mis__bg` đều phân định rõ done / không-done
- Contrast: xanh 8.3:1 trên nền nút, 12.1:1 trên scrim; tên mờ 11.8:1
- `create_app()` load sạch, 110 route

### Chưa verify

| Việc | Ghi chú |
|---|---|
| **Chạy trên trình duyệt với DB thật** | Toàn bộ test dùng stub context |
| **`loyalty_points_log` đang rỗng (0 dòng)** | Nên empty state của sổ điểm là thứ đầu tiên khách gặp, không phải trường hợp biên. Mọi nhánh "có lịch sử" chỉ test bằng stub |
| **`rewards` chỉ có 1 dòng** (`Test`, 100 pts, không ảnh, không stock) | Nhánh reward có ảnh, stock thấp, cooldown, limit chưa từng chạy với dữ liệu thật |
| **Chưa có tier trả tiền nào trong DB** | `tier Gold` / `Diamond`, và `tier_expiry` chỉ test bằng stub |
| **Voucher `used` / `expired` không tồn tại được** | `routes.py` hardcode `active`. Xem mục 12 |
| Cuộn ngang trên Safari iOS thật | `scroll-snap-type: x proximity` + `-webkit-overflow-scrolling` |
| Sheet modal trên Safari iOS thật | Cùng rủi ro đã ghi ở recap History |
| `prefers-reduced-motion` / `prefers-reduced-transparency` | Có block CSS nhưng chưa bật thử |
| `line-clamp: 2` với tên rất dài | Chỉ test tên tối đa 27 ký tự |
| Ảnh mission thật ở tỉ lệ mới | Ba ảnh trong `static/images/customer/Loyalty Points/` |

---

## 12. Còn tồn đọng

| Việc | Ghi chú |
|---|---|
| **Quy tắc hết hạn voucher (mục số 1)** | `routes.py` hardcode `status: "active"` cho mọi voucher. CSS và markup đã sẵn nhánh `used` / `expired` nhưng chúng không thể chạy. Cần: quy tắc hết hạn sau bao nhiêu ngày, và một cột đánh dấu đã dùng. User đã chốt để lại đợt này |
| **`note` trong DB không dịch được** | `award_points()` ghi `note` thành chuỗi cố định: `f"Redeemed: {reward_name}"` (`db.py:1084`, tiếng Anh) và `f"Điều chỉnh bởi {admin_name}"` (`routes.py:3146`, **tiếng Việt cứng**). Khách dùng UI tiếng Phần Lan sẽ thấy dòng tiếng Việt đó. Sửa được chỉ bằng cách đổi kiến trúc log (lưu key thay vì câu). Cái đã làm được: khi `note` rỗng thì fallback về nhãn source **đã dịch** |
| **`_MISSION_SLOT_BG` giờ là context thừa** | `routes.py:1691-1695`, gradient vàng / tím / xanh lá. Markup mới không dùng `m.bg` (rơi về nền plum khi không có ảnh) để palette tự lock. Chưa xoá trong Python |
| `progress_pct` / `next_reward_name` / `next_reward_pts` thừa với trang này | Vẫn được truyền nhưng template mới không dùng. Không xoá vì hai route khác (`customer_dashboard`, `my_bookings`) cũng tính ba biến này |
| **Emoji icon của mission nằm trong DB** | `carousel_slides.icon` chứa ⭐ 👥 📅 do admin nhập qua `/admin/carousels`. Đổi sang Material Symbols phải đụng form admin + dữ liệu. Hiện chỉ hiện khi slide không có ảnh, mà cả ba slide đều có ảnh, nên thực tế không hiện |
| Nhãn nút "đã xong" dùng `✓` là ký tự Unicode | `gettext("✓ Claimed")` trong `routes.py`. Đổi sang Material Symbols cần msgid mới |
| Không có dark mode | Cả app không có dark mode ở đâu |
| Comment tiếng Anh + 1 em-dash trong comment Python | `routes.py:1744` `# User just completed a full cycle ...` (ký tự U+2014 ở giữa), có sẵn từ HEAD, không render ra cho user |

---

## 13. Ghi chú cho lần sau

- **Không tự động verify bằng Claude-in-Chrome.** Browser automation tốn rất nhiều quota và token, chỉ dùng khi user cho phép rõ ràng trong lượt đó. Đã lưu memory
- **CSS variables theo DOM scope, không theo file.** Khai token trên `.page` thì mọi thứ nằm **ngoài** `.page` trong DOM đều không thấy chúng. Modal include sau khi đóng div là sibling, không phải con. Cách kiểm không cần mắt: quét mọi `var()` dùng trong khối của gốc đó rồi đối chiếu danh sách token được khai
- **Đặt khoảng cách ở section, không ở heading.** Section nào không có heading sẽ dính sát khối trên nó
- **`transform` phục vụ mục đích kỹ thuật là nạn nhân của `prefers-reduced-*`.** `scale()` bù blur, bù mép, chống nhoè đều không phải chuyển động. Mọi block reduced-motion là nơi nó có thể bị xoá oan
- **Rule đặt sau với cùng specificity thắng.** Khi viết một biến thể (`--done`) rồi thêm rule chung phía dưới, rule chung sẽ ghi đè biến thể. Dùng `:not()` để loại trừ tường minh, đừng dựa vào thứ tự
- **Không lọc theo field mình biết là hardcode.** Nếu buộc phải giữ field đó, thiết kế phải không phụ thuộc giá trị của nó
- **Phát hiện hệ quả xấu của chính thiết kế mình đưa ra thì sửa nó**, đừng ghi thành ghi chú cho user
- **Đọc schema trước khi thiết kế thứ hiển thị schema đó.** Xem mục 1
- **Render nhiều locale phải mỗi lần một `test_request_context` riêng.** Flask-Babel resolve locale một lần rồi cache cho request đó
- **`grep -c` trả exit code 1 khi đếm được 0.** Nối bằng `&&` là các lệnh sau không chạy. Dùng `;` khi kiểm "phải bằng 0"
- **stdout của Python trên Windows là cp1252.** `print` chuỗi tiếng Việt là `UnicodeEncodeError` dù việc **ghi file** với `encoding="utf-8"` đã thành công. Bọc `sys.stdout` bằng `TextIOWrapper(..., encoding='utf-8')`
- **Trước khi thêm chữ mới, audit `.po`.** Compile `.mo` **trước** khi render, và kiểm mtime `.mo` mới hơn `.po`
- Icon dùng **Material Symbols** (cả app đang dùng), không đổi sang Phosphor/Tabler dù skill design ưu tiên
- Codebase không có reset `box-sizing: border-box` toàn cục. CSS mới tự khai trong phạm vi prefix, và phải khai cho **cả** các gốc modal nằm ngoài wrapper trang
