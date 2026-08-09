# Content spec: trang FAQs (và Terms of Service)

**Ngày soạn:** 2026-08-09 · **Trạng thái:** 🔴 **HOÃN, chưa viết dòng code nào** · **Mở khoá khi:** 9 dữ kiện kinh doanh ở mục 4 được chốt và 2 lỗ hổng ở mục 5 được xử lý

Tài liệu này giữ lại toàn bộ phần audit và soạn nội dung cho trang FAQs, để khi hệ thống hoàn thiện thì mở ra code được ngay, không phải audit lại từ đầu.

---

## 0. Vì sao hoãn

FAQ chỉ mô tả lại những gì hệ thống **đã chốt**. Hiện có ba tầng chưa chốt:

1. **Tính năng có config nhưng chưa nối dây.** `referral_bonus` (200), `review_bonus` (50), `birthday_bonus` (100) đều nằm trong bảng `loyalty_config` và hiện trong panel admin, nhưng **không có `award_points()` nào gọi tới**. Khách thấy trong UI mà FAQ không dám nhắc thì kỳ; nhắc thì thành hứa suông.
2. **Chính sách và cơ chế lệch nhau.** Checkout ghi *"you agree to our 24h cancellation policy"* nhưng route huỷ không có check thời gian. FAQ buộc phải chọn một cách diễn đạt, và đó là quyết định kinh doanh chứ không phải kỹ thuật.
3. **Chín dữ kiện chưa tồn tại** (mục 4).

Nghịch lý khiến quyết định hoãn là đúng: phương án lưu nội dung đã chốt là **Python constants + gettext**, mà với phương án đó, sửa chữ tiếng Anh sau này sẽ tạo msgid mới, làm mồ côi bản dịch cũ, và `pybabel` fuzzy-match lại thì gettext bỏ qua entry fuzzy nên câu đó âm thầm rơi về tiếng Anh. Tức là **không thể "làm chắc" về những dữ kiện chưa có**. Làm bây giờ nghĩa là viết hai lần, và lần hai là lần đắt.

---

## 1. Quyết định kiến trúc đã chốt

| Hạng mục | Chốt | Lý do |
|---|---|---|
| Lưu nội dung | **Python constants + gettext**, file `app/faq_content.py` | FAQ sửa vài lần một năm; pipeline dịch đã có sẵn; dịch giả nhìn cả 3 ngôn ngữ cạnh nhau trong `.po`. Không tạo bảng DB, không dựng trang admin |
| Vị trí link | **Chỉ footer** | `base.html:186` cột Support đã có sẵn `<li><a href="#">{{ _('FAQs') }}</a></li>`, chuỗi đã nằm trong cả 3 file dịch. Chỉ cần đổi `href`. **Không đổi IA, không thêm mục vào nav trên** (nav 4 mục + 2 nút, thêm nữa thì 1024px có nguy cơ xuống 2 dòng) |
| Hàm dịch | `from flask_babel import lazy_gettext as _` | Xem mục 6, đây là bẫy |

**Hệ quả đã chấp nhận:** chủ tiệm **không tự sửa được** nội dung. Sửa một chữ = sửa `faq_content.py` + chạy lại pybabel + deploy.

**Đường chuyển sang DB + admin sau này** (nếu đổi ý), nội dung không bị nhốt:

1. Tạo bảng `faqs` theo pattern `field` / `field_fi` / `field_vi`
2. Script seed một lần: duyệt `FAQ_GROUPS`, với mỗi ngôn ngữ ép `str()` lên lazy proxy trong `force_locale(lang)` → ra sẵn 3 bản dịch, ghi thẳng vào DB
3. Route đọc DB thay vì constants
4. Template đổi `item.question` sang `tr(item, 'question')`, **vòng lặp giữ nguyên hình dạng**
5. Dựng `admin_faqs.html` + 4 route CRUD

Bước 1-4 nhỏ. Bước 5 mới là phần lớn.

---

## 2. Thiết kế trang (đã chốt, chưa code)

**Design read:** greenfield, trang tiện ích hỗ trợ, ngôn ngữ luxury-calm, bám thang token `bd-` / `lp-` / `ms-` / `bk-` / `bkc-`.

**Dials:** `VARIANCE 5` / `MOTION 3` / `DENSITY 5`. Khách vào mang sẵn một câu hỏi cụ thể và muốn ra khỏi trang càng nhanh càng tốt.

**Stack:** Flask + Jinja + CSS thuần. Skill design mặc định React/Next/Tailwind/Motion, **không áp dụng ở đây**. Không cài gì mới.

### Hai ý tưởng cốt lõi

**1. FAQ là bộ định tuyến, không phải bức tường chữ.** Phần lớn câu hỏi của khách salon đều có đích đến trong chính sản phẩm. Câu trả lời nào làm được thì gắn link thẳng vào route thật:

```
"Tôi đổi được lịch không?"
  → …giải thích trong 14 ngày…
  → [Xem lịch hẹn của tôi]   main.my_bookings
```

**2. Nhóm theo hành trình khách, không theo bảng chữ cái.** Trước khi đặt → Buổi hẹn → Giá và thanh toán → Điểm và hạng → Tài khoản. Khớp thứ tự khách thật sự gặp vấn đề.

### Cấu trúc (4 khối)

```
1  Đầu trang     tiêu đề + 1 dòng mô tả + ô tìm kiếm
2  Rail nhóm     desktop: cột trái dính, có đếm số câu
                 mobile: dải chip cuộn ngang (pattern .lp-strip đã có)
3  Danh sách     <details> theo nhóm, câu đầu của nhóm 1 mở sẵn
4  Chưa tìm ra?  khối đóng, dẫn sang Contact và Book Now
```

**Accordion dùng `<details>` / `<summary>` gốc**, không hand-roll ARIA: bàn phím và trình đọc màn hình có sẵn, chạy được cả khi JS lỗi, Chrome tự bung khi Ctrl+F trúng chữ bên trong (Safari/Firefox chưa hỗ trợ tự bung).

### Logic client (vanilla, không thư viện)

- Tìm kiếm lọc realtime theo cả câu hỏi lẫn nội dung trả lời, debounce 150ms
- Số đếm trên mỗi chip cập nhật theo kết quả lọc
- Empty state khi không khớp: nêu lại từ khoá + nút xoá bộ lọc + lối sang Contact
- Deep-link: mỗi câu có `id` slug, vào `/faqs#huy-lich` tự mở và cuộn tới. Dùng được trong email support
- Rail active bằng IntersectionObserver, **không** `scroll` listener

### Logic server

- Route `GET /faqs` → `main.faqs`
- `base.html:186` đổi `href="#"` thành `url_for('main.faqs')`
- **JSON-LD `FAQPage`** trong head, để Google hiện rich result

### File dự kiến

| Loại | Đường dẫn |
|---|---|
| Mới | `app/faq_content.py` |
| Mới | `app/templates/public/faqs.html` |
| Mới | `app/static/css/public/faqs.css` |
| Mới | `app/static/js/faqs.js` |
| Sửa | `app/routes.py` (thêm 1 route) |
| Sửa | `app/templates/base.html` (1 thuộc tính `href`) |

---

## 3. Nội dung đã soạn: 21 câu, 5 nhóm

Cột **Nguồn** là chỗ đã verify trong code. Mọi con số dưới đây đều đọc ra từ source, không suy đoán.

### Nhóm 1 · Trước khi đặt

| slug | Câu hỏi | Trả lời | Nguồn |
|---|---|---|---|
| `gio-mo-cua` | Giờ mở cửa? | 09:00 - 18:00. Khung giờ chia mỗi 30 phút | `booking_service.py:10-12` |
| `dat-truoc-bao-lau` | Đặt trước được bao xa? | Tối đa 60 ngày | `routes.py:4201` |
| `chon-tho` | Chọn được thợ không? | Được. Hoặc chọn "No preference", hệ thống tự xếp thợ đang rảnh | wizard bước 2 |
| `can-tai-khoan` | Có cần tài khoản không? | Không. Đặt với tư cách khách, xác thực bằng email. Có tài khoản thì được tích điểm và đổi lịch. **CTA: Tạo tài khoản** | luồng public |
| `bao-lau` | Một buổi mất bao lâu? | Tuỳ dịch vụ, 20 tới 90 phút, ghi trên từng dịch vụ. **CTA: Xem dịch vụ** | DB `duration_minutes` |

### Nhóm 2 · Buổi hẹn của bạn

| slug | Câu hỏi | Trả lời | Nguồn |
|---|---|---|---|
| `sao-chua-xac-nhan` | Sao lịch của tôi ghi "đang chờ"? | Đã nhận, salon xác nhận trong giờ mở cửa rồi gửi email | luồng status |
| `doi-lich` | Đổi lịch được không? | Được, cần đăng nhập, trong vòng 14 ngày tới. **CTA: Lịch hẹn của tôi** | `routes.py:853` |
| `huy-lich` | Huỷ thế nào? | Trong chi tiết lịch hẹn, khi còn "đang chờ" hoặc "đã xác nhận". **Câu chữ về 24h phụ thuộc mục 4.1** | `routes.py:643` |
| `den-muon` | Đến muộn thì sao? | ⚠️ **CHỜ CHỐT** (mục 4.2) | |
| `khach-vang-lai` | Có nhận khách vãng lai? | ⚠️ **CHỜ CHỐT** (mục 4.3) | |

### Nhóm 3 · Giá và thanh toán

| slug | Câu hỏi | Trả lời | Nguồn |
|---|---|---|---|
| `vat` | Giá đã gồm VAT chưa? | Giá dịch vụ **chưa gồm** VAT. VAT 25.5% cộng ở bước xác nhận, tổng hiện rõ trước khi bấm | `VAT = 0.255`, `subtotal = price` |
| `cach-tra` | Trả tiền kiểu gì? | Trả tại tiệm, hoặc thẻ online lúc đặt | `payment_method` |
| `tra-online-khac-gi` | Trả online khác gì? | Xác nhận ngay, bỏ qua bước nhập mã email | `fulfill_booking_payment` |
| `tien-mat` | Có nhận tiền mặt? | ⚠️ **CHỜ CHỐT** (mục 4.4) | |

### Nhóm 4 · Điểm và hạng thành viên

| slug | Câu hỏi | Trả lời | Nguồn |
|---|---|---|---|
| `kiem-diem` | Tích điểm thế nào? | Mỗi buổi **hoàn tất** cộng điểm của dịch vụ nhân hệ số hạng | `booking_service.py:194` |
| `chua-thay-diem` | Đặt rồi mà chưa thấy điểm? | Điểm vào sau khi buổi hẹn **hoàn tất**, không phải lúc đặt. **CTA: Điểm của tôi** | cùng trên |
| `hang-thanh-vien` | Có mấy hạng? | Silver miễn phí ×1.0 · Gold €49.99/năm ×1.5 · Diamond €99.99/năm ×2.0. **CTA: Xem hạng** | `membership_tiers` |
| `doi-thuong` | Đổi điểm lấy gì? | Đổi ở trang Loyalty Points. **CTA: Đổi thưởng** | `rewards` |

### Nhóm 5 · Tài khoản

| slug | Câu hỏi | Trả lời | Nguồn |
|---|---|---|---|
| `tao-tai-khoan` | Lợi ích khi có tài khoản? | Tích điểm, đổi lịch, xem lịch sử, hoá đơn. **CTA: Đăng ký** | portal |
| `dang-nhap-google` | Đăng nhập bằng Google được không? | Được | `/auth/google` |
| `quen-mat-khau` | Quên mật khẩu? | Đặt lại qua email. **CTA: Đăng nhập** | `/set-new-password` |

### Nguồn điểm: chỉ được viết về những nguồn THẬT SỰ chạy

Trace hết qua `award_points()`:

| Nguồn | Có chạy? | Chi tiết |
|---|---|---|
| `booking` | ✅ | `service.points × tier multiplier`, cộng khi status thành `done` |
| `double_points` | ✅ | Cộng thêm bằng đúng base points. `double_points_day = 2` (thứ Ba). ⚠️ cần xác nhận là cấu hình thật hay dữ liệu test, mục 4.9 |
| `first_booking` | ✅ | 99 điểm, buổi **hoàn tất** đầu tiên |
| `streak` | ✅ | 100 điểm, đặt 3 tháng liên tiếp |
| `admin_adjustment` | ✅ | Thủ công |
| `reward_redemption` | ✅ | Trừ điểm khi đổi thưởng |
| `referral_bonus` | ❌ | **Có config, không có `award_points()`** |
| `review_bonus` | ❌ | **Có config, không có `award_points()`** |
| `birthday_bonus` | ❌ | **Có config, không có `award_points()`** |

---

## 4. Chín dữ kiện cần chốt trước khi code

Code không nói được, và không được bịa. Mục nào không chốt thì **bỏ hẳn câu đó**, không viết chung chung.

| # | Câu hỏi cần chốt | Ghi chú |
|---|---|---|
| 1 | **Huỷ 24h** có phải chính sách thật không? Có phí huỷ muộn không? | Code **không** chặn (mục 5.2). Câu chữ phải khớp thực tế salon làm |
| 2 | **Đến muộn** bao lâu thì mất lượt? | |
| 3 | **Khách vãng lai** có nhận không? | |
| 4 | **Tiền mặt** có nhận không? | |
| 5 | **Gift card** có bán không? | |
| 6 | **Phụ thu** móng dài, đắp bột, tháo gel cũ? | |
| 7 | **Dị ứng / mang thai** có lưu ý cần nói trước? | Liên quan mục 5.3 |
| 8 | **Đỗ xe** ở Kyyhkysmäki 9 có chỗ không? | |
| 9 | **Thứ Ba nhân đôi điểm** có đang chạy thật không? | `double_points_day = 2` đang bật trong `loyalty_config` |

---

## 5. Ba lỗ hổng tìm ra khi audit, độc lập với FAQ

Ba mục này tồn tại kể cả khi không bao giờ làm trang FAQ. Đáng vào backlog riêng.

### 5.1 Ba nguồn điểm hiện trong admin nhưng không bao giờ trả điểm

`referral_bonus` (200), `review_bonus` (50), `birthday_bonus` (100) nằm trong `loyalty_config`, có tên và icon trong panel admin (`routes.py:3274-3282`), nhưng **không có lời gọi `award_points()` nào**. Bảng `loyalty_points_log` thực tế chỉ có `admin_adjustment` và `reward_redemption`.

Hoặc nối dây, hoặc gỡ khỏi UI admin. Để nguyên là admin tưởng đang chạy.

### 5.2 Chính sách huỷ 24h chỉ tồn tại trong câu chữ

Checkout hiển thị *"By confirming, you agree to our 24h cancellation policy"*, nhưng `routes.py:643` chỉ kiểm tra quyền sở hữu và `status in ("pending", "confirmed")`. **Không có check thời gian nào.** Khách huỷ trước giờ hẹn 1 tiếng vẫn huỷ được bình thường.

Hoặc enforce trong code, hoặc sửa câu chữ, hoặc chấp nhận đây là chính sách salon tự xử lý thủ công. Cả ba đều hợp lệ, nhưng phải chọn một.

### 5.3 Form booking đang mời khách nhập dữ liệu sức khoẻ

Ô ghi chú bước 4 có placeholder *"Any special requests or allergies..."*, tức là site **chủ động mời** khách nhập thông tin dị ứng vào `bookings.notes`.

Dưới GDPR đó là dữ liệu sức khoẻ, thuộc nhóm đặc biệt Điều 9, yêu cầu căn cứ pháp lý cao hơn dữ liệu thường. Nêu ở đây như một phát hiện kỹ thuật, không phải tư vấn pháp lý. Liên quan trực tiếp tới trang Privacy Policy.

---

## 6. Bẫy kỹ thuật đã xác minh, nhớ khi code

### 6.1 Phải dùng `lazy_gettext`, và phải đặt tên là `_`

Nội dung FAQ là hằng ở cấp module, đánh giá lúc **import**, ngoài request context. Dùng `gettext` thường sẽ đóng băng ngôn ngữ theo lần import đầu tiên, bug rất khó thấy. Phải dùng `lazy_gettext` (trả proxy, đánh giá lúc render).

Nhưng **`_l` KHÔNG nằm trong keyword mặc định của pybabel**. Đã verify:

```python
from babel.messages.extract import DEFAULT_KEYWORDS
'_l' in DEFAULT_KEYWORDS   # False
```

Nếu đặt tên `_l` thì lệnh `pybabel extract -F babel.cfg -o messages.pot .` hiện tại **âm thầm bỏ qua toàn bộ ~50 chuỗi FAQ**, và không ai phát hiện cho tới khi mở trang bằng tiếng Việt.

**Cách làm đúng:**

```python
# app/faq_content.py
# `_` ở file này là LAZY gettext, khác với `_` ở nơi khác. Nội dung FAQ là hằng
# cấp module nên phải đánh giá lúc render, không phải lúc import. Đặt tên `_`
# (không phải `_l`) để pybabel bắt được bằng keyword mặc định, khỏi phải đổi
# lệnh extract và khỏi có cách nào hỏng âm thầm.
from flask_babel import lazy_gettext as _
```

### 6.2 Lô dịch này là lô lớn nhất từ trước tới nay

21 câu × 2 phần (hỏi + đáp) + CTA label ≈ **50 chuỗi mới** trong một đợt.

`pybabel update` đã gán fuzzy **sai nghĩa** 2 lần liên tiếp trong project này:

| Đợt | msgid | Fuzzy gán vào |
|---|---|---|
| Booking wizard | `Morning` | `phút` |
| Booking wizard | `Evening` | `Chờ duyệt` |
| Success page | `Booking received` | `Đã xác nhận đặt lịch` (nghĩa **ngược**) |

Bắt buộc: sau `update`, liệt kê **từng** entry fuzzy mới và đọc trước khi `compile`.

### 6.3 Đề xuất chưa chốt: `python dev_tools.py i18n sync`

`dev_tools.py` đã là CLI argparse có subcommand. Thêm một lệnh gộp `extract` → `update` → **in ra toàn bộ chuỗi mới và fuzzy** → chỉ `compile` sau khi xác nhận. Khoảng 40 dòng.

Bịt được cả hai bẫy: quên `-k`, và quên đọc fuzzy. Dùng cho mọi đợt dịch sau, không riêng FAQ. **Chưa được duyệt.**

---

## 7. Terms of Service ghép chung tài liệu này

ToS bị chặn bởi **đúng cùng bộ quyết định** với FAQ: chính sách huỷ, hoàn tiền, no-show, đến muộn (mục 4.1 - 4.4). Chốt một lần là mở khoá cả hai.

**Privacy Policy thì KHÁC, không nên đợi.** Nó không phụ thuộc tính năng chưa xong; dữ liệu thu thập và bên thứ ba đã ổn định. Thêm tính năng sau này chỉ **thêm đoạn**, không làm sai đoạn đã viết. Trong khi đó site đã đang thu thập họ tên, email, số điện thoại, ngày sinh, IP, và ghi chú có thể chứa thông tin dị ứng, đồng thời chia sẻ với Google OAuth, Stripe và nhà cung cấp SMTP. Địa chỉ Espoo, tính EUR → GDPR áp dụng ngay.

Cả ba link `FAQs`, `Privacy Policy`, `Terms of Service` trong `base.html` hiện đều là `href="#"`.

---

## 8. Việc cần làm khi mở khoá

```
1. Chốt 9 dữ kiện ở mục 4
2. Xử lý 3 lỗ hổng ở mục 5 (hoặc quyết định để nguyên và ghi rõ lý do)
3. Rà lại mục 3: câu nào nói về tính năng chưa nối dây thì bỏ
4. Quyết có làm dev_tools i18n sync không (mục 6.3)
5. Code theo mục 2
6. Dịch: extract → update → ĐỌC TỪNG FUZZY → compile
```
