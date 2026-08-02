# IMAGE AUDIT — Danh sách toàn bộ chỗ render ảnh

> Mục đích: làm cơ sở tạo bộ ảnh **Default** (AI Studio / Stitch) cho từng vị trí.
> Kích thước ghi theo dạng: `khung CSS thực tế` → `khuyến nghị export (@2x retina)`.
> Container nội dung public = `max-width 1280px, padding 0 80px` → vùng nội dung **1120px**.

---

## 0. Tổng quan cơ chế ảnh
./venv/bin/python -m app.init_db
| Hạng mục | Chi tiết |
|---|---|
| Filter resolve | `img_src(subdir)` — `app/routes.py:120` (`_resolve_upload` `app/routes.py:96`) |
| Quy tắc | Giá trị bắt đầu bằng `http://`, `https://`, `/` → dùng thẳng. Ngược lại → `/static/uploads/<subdir>/<file>` |
| Thư mục upload | `services`, `gallery`, `rewards`, `carousels`, `staff`, `avatars` (`_UPLOAD_CONFIG` `app/routes.py:60`) |
| Giới hạn upload | 2MB (jpg/jpeg/png/webp) — riêng `avatars` 800KB (jpg/jpeg/png/gif) |
| Ảnh default hiện có | `images/Default/Service/test.png`, `images/Default/Homepage_Carousel_Slides/homepage-slide-{1,2,3}.webp`, `images/Default/avatar-default.svg`, `images/public/About_img.png`, `images/public/nail_studio.jpg`, `images/customer/Loyalty Points/*.png`, `images/social/{google,facebook}.svg` |
| Thư mục rỗng | `images/services/`, `images/staff/`, `images/customer/Profile/` (chưa dùng) |

---

## 1. PUBLIC — Trang chủ `app/templates/public/index.html`

| # | Vị trí | Nguồn ảnh | Khung CSS | Khuyến nghị | Gợi ý nội dung |
|---|---|---|---|---|---|
| 1.1 | **Hero carousel slide** — `index.html:26` `.hero__bg-img` | `homepage_slides.image` → `uploads/carousels/`; seed default `/static/images/Default/Homepage_Carousel_Slides/homepage-slide-{1,2,3}.webp` | `.hero` 100% × **500px** (mobile 420px), `object-fit: cover`, `opacity .6` + `mix-blend-mode: overlay` trên nền deep-plum `#3E1F47`, có hiệu ứng Ken Burns scale 1.06 | **1920×800** (≈12:5), export **2560×1080** cho retina | Ảnh không gian salon rộng, tone hồng-be, **chừa vùng giữa trống** vì text + 2 nút CTA đè lên. Vì bị phủ overlay tím + opacity 0.6 → chọn ảnh **sáng, contrast thấp**, tránh chi tiết vụn |
| 1.2 | **Service card thumbnail** — `index.html:77-80` `.service-card__img-wrap` | `services.image` → `uploads/services/`; fallback `images/Default/Service/test.png` | **100% × 192px** cố định; grid 4 cột trong 1120px → ~**262×192** (≈4:3), cover | **800×600** (4:3) | Cận cảnh bàn tay/bộ nail đã hoàn thiện, nền trơn pastel. Nên làm **1 bộ 4-6 biến thể** theo nhóm dịch vụ (manicure, pedicure, gel, nail art, chăm sóc, spa tay) |
| 1.3 | **Gallery preview — ô thường** — `index.html:115-118` `.gallery-item img` | `gallery_images.image_url` → `uploads/gallery/` | `.gallery-grid` 3 cột, `grid-auto-rows: 250px` → ô ~**363×250**, cover | **1080×1080** (1:1, dùng chung với mục 3.1) | Ảnh mẫu nail thành phẩm |
| 1.4 | **Gallery preview — ô cao** `.gallery-item--tall` | như trên | span 2 hàng → ~**363×516** (≈5:7 dọc) | **1080×1500** (≈3:4 dọc) | Ảnh dọc: bàn tay đặt dọc, hoặc chai sơn dựng đứng |
| 1.5 | *(Chưa có ảnh)* Testimonial avatar `.testimonial-card__avatar` | — | 48×48 tròn, hiện đang render **chữ cái viết tắt** | Nếu muốn ảnh: **144×144** | Ảnh chân dung khách hàng (nếu có) |

---

## 2. PUBLIC — Dịch vụ `app/templates/public/services.html`

| # | Vị trí | Nguồn ảnh | Khung CSS | Khuyến nghị | Gợi ý nội dung |
|---|---|---|---|---|---|
| 2.1 | **Service card** — `services.html:86-88` `.svc-card__img` | `services.image` → `uploads/services/`; fallback `images/Default/Service/test.png` | `aspect-ratio: 4/3`, grid 3 cột trong 1120px → ~**357×268**, cover | **800×600** (4:3) | Dùng chung bộ ảnh với 1.2. Đây là khung lớn nhất của service image → **build bộ default gốc ở size này** |

---

## 3. PUBLIC — Gallery `app/templates/public/gallery.html`

| # | Vị trí | Nguồn ảnh | Khung CSS | Khuyến nghị | Gợi ý nội dung |
|---|---|---|---|---|---|
| 3.1 | **Gallery grid item** — `gallery.html:44, 59` `.gal-item__img` | `gallery_images.image_url` → `uploads/gallery/` | `.gal-item` `aspect-ratio: 1/1`; 3 cột (1024px→2 cột, 768px→1 cột) → ~**357×357**, cover, hover scale 1.05 | **1600×1600** (1:1) — file gốc dùng luôn cho lightbox | Bộ 8-12 ảnh mẫu nail đa dạng style: French, ombre, chrome, nail art hoa, nude, đỏ đô… |
| 3.2 | **Lightbox** — `gallery.html:105` `.gal-lightbox__img` | **cùng file** với 3.1 (JS swap src) | `max-width 960px`, `max-height 80vh`, `object-fit: contain` | Vì contain nên **cạnh dài ≥1600px** | Không cần file riêng — chỉ cần ảnh gallery đủ lớn |

---

## 4. PUBLIC — Giới thiệu `app/templates/public/about.html`

| # | Vị trí | Nguồn ảnh | Khung CSS | Khuyến nghị | Gợi ý nội dung |
|---|---|---|---|---|---|
| 4.1 | **Our Story** — `about.html:32-34` `.abt-story__img` | **hardcode** `images/public/About_img.png` | `.abt-story__img-wrap` `aspect-ratio: 4/5`, ~nửa grid → ~**540×675**, cover | **1080×1350** (4:5 dọc) | Nội thất salon: ghế nail, kệ sơn, ánh sáng ấm, tone blossom-pink + stone-white (đúng alt text hiện tại) |
| 4.2 | **Team avatar (static)** — `about.html:106` `.abt-team__avatar` | `member.photo_url` (list cứng trong template) | **96×96** tròn, cover, border 2px | **288×288** (1:1) | Chân dung nhân viên, crop vai trở lên, nền trơn |
| 4.3 | **Team avatar (DB)** — `about.html:126` | `staff.photo` → `uploads/staff/` | **96×96** tròn | **288×288** (1:1) | ⚠️ Đây là chỗ **cần ảnh default nhân viên** — hiện chưa có fallback, staff không có ảnh sẽ ra `src=""` (ảnh vỡ) |

---

## 5. PUBLIC — Đặt lịch `public_booking.html` + `customer/customer_booking.html`

> 2 file dùng **chung CSS** `css/public/public_booking.css`, markup gần như giống hệt.

| # | Vị trí | Nguồn ảnh | Khung CSS | Khuyến nghị | Gợi ý nội dung |
|---|---|---|---|---|---|
| 5.1 | **Thumbnail dịch vụ (Step 1)** — `public_booking.html:85`, `customer_booking.html:85` `.bk-svc-thumb img` | `services.image` → `uploads/services/`; fallback `images/Default/Service/test.png` | **96×96** vuông bo góc, cover | **288×288** (1:1) | ⚠️ Ảnh service gốc là 4:3 → khi crop 1:1 sẽ **mất 2 mép**. Nên chuẩn bị thêm **biến thể vuông** hoặc thiết kế ảnh 4:3 có chủ thể nằm gọn giữa khung |
| 5.2 | **Avatar stylist (Step 2)** — `public_booking.html:144`, `customer_booking.html:144` `.bk-staff-avatar` (CSS `background-image`) | `staff.photo` → `uploads/staff/` | **96×96** tròn, `background-size: cover` | **288×288** (1:1) | ⚠️ Không có fallback ảnh — nếu `photo` rỗng thì `url('')`, ra ô nền hồng nhạt. **Cần ảnh default staff** |

---

## 6. PUBLIC — Xác nhận đặt lịch `app/templates/public/success.html`

| # | Vị trí | Nguồn ảnh | Khung CSS | Khuyến nghị | Gợi ý nội dung |
|---|---|---|---|---|---|
| 6.1 | **Ảnh dịch vụ đã đặt** — `success.html:106` `.bkc-card__img` | `service_image` (`routes.py:4000`) → `uploads/services/` | **256×256** cố định, cover. Có fallback icon `spa` khi rỗng | **768×768** (1:1) | Cùng bộ với 5.1 (biến thể vuông) |
| 6.2 | **Ảnh bản đồ salon** — `success.html:161-163` `.bkc-location__map-img` | **hardcode** `/static/images/public/nail_studio.jpg` | 100% × **256px**, rộng tối đa ~1120 → ≈**1120×256** (≈4.4:1), cover, filter grayscale 25% + brightness 0.95 | **1600×640** (5:2) | Ảnh chụp/render **bản đồ** vị trí salon hoặc mặt tiền tiệm. Vì bị grayscale nhẹ → chọn ảnh có **contrast rõ** |
| 6.3 | **Background CTA tạo tài khoản** — `success.css:304` `.bkc-account-cta__bg-img` | ⚠️ **Hardcode URL ngoài** `https://lh3.googleusercontent.com/aida/...` | full card ~**1120×250**, `background-size: cover`, `opacity 0.2` + `mix-blend-mode: overlay` trên nền deep-plum | **1600×500** (≈16:5) | 🔴 **Ưu tiên thay** — đây là link CDN Google tạm, có thể chết bất kỳ lúc nào. Cần texture/pattern trừu tượng tone hồng, rất mờ (vì opacity 0.2) |

---

## 7. AUTH — `auth_base.html`, `customer_login.html`, `customer_register.html`

| # | Vị trí | Nguồn ảnh | Khung CSS | Khuyến nghị | Gợi ý nội dung |
|---|---|---|---|---|---|
| 7.1 | **Panel ảnh bên trái** — `auth_base.html:33` `.auth-panel__img` (CSS `background-image`) | **hardcode** `images/public/nail_studio.jpg` | Panel chiếm ~nửa màn hình, full height, `background-size: cover` + gradient overlay tối từ dưới lên | **1200×1600** (3:4 dọc) | ⚠️ Hiện dùng **chung file** với ảnh bản đồ (6.2) — 1 ảnh ngang bị kéo vào khung dọc → crop xấu. **Nên tách 1 file riêng dạng dọc**: không gian salon, tone ấm, phần dưới tối/đơn giản để chữ trắng đè lên đọc được. `staff/login.css:12` ẩn panel này ở trang login staff |
| 7.2 | **Icon Google** — `customer_login.html:36`, `customer_register.html:46` | `images/social/google.svg` ✅ đã có | **20×20** | SVG — giữ nguyên | Đã ổn |
| 7.3 | **Icon Facebook** — `customer_login.html:40`, `customer_register.html:50` | `images/social/facebook.svg` ✅ đã có | **20×20** | SVG — giữ nguyên | Đã ổn |

---

## 8. CUSTOMER — Dashboard `app/templates/customer/customer_dashboard.html`

| # | Vị trí | Nguồn ảnh | Khung CSS | Khuyến nghị | Gợi ý nội dung |
|---|---|---|---|---|---|
| 8.1 | **Hero carousel** — `customer_dashboard.html:607` `.hero__bg-img` | `homepage_slides.image` → `uploads/carousels/` (`routes.py:310`) | `.hero` 100% × **420px**, cover, opacity .6 + overlay, Ken Burns | **1920×700** (≈12:5) | Dùng chung bộ với 1.1 |
| 8.2 | **Ảnh lịch hẹn sắp tới** — `customer_dashboard.html:646` `.upcoming-card__image img` | `upcoming_booking.service_img` → `uploads/services/` (`routes.py:299`) | **132×168** (≈11:14 dọc), cover. Có fallback icon | **400×510** (≈3:4 dọc) | ⚠️ Khung **dọc** — ảnh service 4:3 ngang bị crop mạnh. Nên có **biến thể dọc** của ảnh dịch vụ |

---

## 9. CUSTOMER — Lịch hẹn của tôi `app/templates/customer/my_bookings.html`

| # | Vị trí | Nguồn ảnh | Khung CSS | Khuyến nghị | Gợi ý nội dung |
|---|---|---|---|---|---|
| 9.1 | **Ảnh "lịch kế tiếp"** — `my_bookings.html:27` | `nevi_service_image` → `uploads/services/` | `.appointment-card__image` **132×168** (mobile: 100% × 220px), cover | **400×510** (≈3:4) | Cùng bộ với 8.2 |
| 9.2 | **Ảnh trong tab Upcoming** — `my_bookings.html:158` | `booking.service_image` → `uploads/services/` | như trên | như trên | như trên |
| 9.3 | **Ảnh trong tab Past** — `my_bookings.html:217` | như trên | như trên | như trên | như trên |
| 9.4 | **Ảnh trong tab Cancelled** — `my_bookings.html:274` | như trên | như trên | như trên | như trên |

> ⚠️ Cả 4 chỗ đều **không có fallback** — service không có ảnh → `src=""` → ảnh vỡ. Cần default.

---

## 10. CUSTOMER — Đổi lịch `app/templates/customer/reschedule.html`

| # | Vị trí | Nguồn ảnh | Khung CSS | Khuyến nghị | Gợi ý nội dung |
|---|---|---|---|---|---|
| 10.1 | **Ảnh buổi hẹn hiện tại** — `reschedule.html:38-42` `.current-session-image` | `booking.image_url`; fallback `images/Default/Service/test.png` ✅ | **84×84** bo góc 20px, cover | **256×256** (1:1) | Cùng bộ vuông với 5.1 |

---

## 11. CUSTOMER — Chi tiết lịch hẹn `app/templates/customer/view_booking_details.html`

| # | Vị trí | Nguồn ảnh | Khung CSS | Khuyến nghị | Gợi ý nội dung |
|---|---|---|---|---|---|
| 11.1 | **Avatar kỹ thuật viên** — `view_booking_details.html:67` `.technician-box__avatar` | **hardcode** `images/Default/avatar-default.svg` ✅ | **68×68** tròn, nền `#f1e8ec` | SVG (vector) hoặc **204×204** PNG | Đã có file. Nếu muốn đẹp hơn: silhouette người tone hồng nhạt hợp brand |
| 11.2 | **Ảnh bản đồ salon** — `view_booking_details.html:109` | **hardcode** `images/public/nail_studio.jpg` | `.location-card__map` 100% × **220px**, cover | **1600×440** (≈3.6:1) | Cùng bộ với 6.2 (ảnh bản đồ ngang) |

---

## 12. CUSTOMER — Cài đặt `app/templates/customer/customer_setting.html`

| # | Vị trí | Nguồn ảnh | Khung CSS | Khuyến nghị | Gợi ý nội dung |
|---|---|---|---|---|---|
| 12.1 | **Avatar khách hàng** — `customer_setting.html:677-680` `.avatar-circle` | `current_user.profile_picture` → `uploads/avatars/` (`routes.py:775`) | **120×120** tròn, viền dashed hồng `#d64682`. Fallback hiện tại = **chữ cái viết tắt** trên nền màu random | **360×360** (1:1) | Có thể dùng lại `avatar-default.svg` (11.1). Comment ở `customer_setting.html:648` còn tham chiếu `images/default-avatar.png` — **file này không tồn tại** |

---

## 13. CUSTOMER — Điểm thưởng `app/templates/customer/loyalty_points.html`

| # | Vị trí | Nguồn ảnh | Khung CSS | Khuyến nghị | Gợi ý nội dung |
|---|---|---|---|---|---|
| 13.1 | **Banner voucher/phần thưởng** — `loyalty_points.html:1180` `.reward-img-wrap img` | `rewards.banner_image` → `uploads/rewards/` (`routes.py:1520`) | `aspect-ratio: 4/3`, grid 3 cột → ~**316×237**, cover | **800×600** (4:3) | Banner ưu đãi: hộp quà, voucher, % giảm giá, tone hồng-vàng gold |
| 13.2 | **Background mission card** — `loyalty_points.html:1132` (CSS `background: url()`) | `mission_slides.image` → `uploads/carousels/`; seed default: `images/customer/Loyalty Points/{leave_review,invite_friends,first_visit}.png` ✅ | `.mission-card` `min-height: 300px`, `background: center/cover`. Có fallback màu gradient `m.bg` | **900×900** (1:1, an toàn cho cover) | Đã có 3 ảnh cho 3 mission. Nếu thêm mission mới cần thêm ảnh cùng style |

---

## 14. STAFF

| # | Vị trí | Nguồn ảnh | Khung CSS | Khuyến nghị | Gợi ý nội dung |
|---|---|---|---|---|---|
| 14.1 | **Avatar nhân viên** — `staff_profile.html:212` `.sf-avatar img` | `current_staff.avatar` → `uploads/staff/` (`routes.py:254`) | **84×84** tròn, viền 2px. Fallback = **chữ cái viết tắt** | **256×256** (1:1) | Dùng chung ảnh default staff với 4.3 / 5.2 |

---

## 15. ADMIN

| # | Vị trí | Nguồn ảnh | Khung CSS | Khuyến nghị | Gợi ý nội dung |
|---|---|---|---|---|---|
| 15.1 | **Avatar sidebar** — `admin_base.html:444` `.adm-sidebar__avatar` | `session.admin_avatar` | **36×36** tròn | **108×108** (1:1) | Dùng `avatar-default.svg` |
| 15.2 | **Avatar topbar** — `admin_base.html:492` `.adm-topbar__avatar` | `session.admin_avatar` | **32×32** tròn | **96×96** (1:1) | như trên |
| 15.3 | **Thumbnail slide carousel** — `admin_carousels.html:460, 529` `.cr-slide-thumb` | `s.image_url` → `uploads/carousels/` | **88×56** (11:7) bo 8px, cover | dùng chính ảnh carousel gốc (1.1) | Không cần file riêng |
| 15.4 | **Preview dropzone carousel** — `admin_carousels.html:619, 770, 891` `.cr-dropzone` | ảnh vừa upload (JS) | 100% × **120px** | — | Preview runtime, không cần default |
| 15.5 | **Preview dropzone dịch vụ** — `admin_services.html:1200, 1349` `.sv-dropzone` | ảnh vừa upload / `uploads/services/` | 100% × **140px** | — | như trên |
| 15.6 | **Thumbnail thư viện ảnh** — `admin_gallery.html:996` `.gl-card__thumb` | `img.image_url` → `uploads/gallery/` | grid: 100% `aspect-ratio 1/1`; list: **140×140**, cover | dùng ảnh gallery gốc (3.1) | Không cần file riêng |
| 15.7 | **Preview edit gallery** — `admin_gallery.html:1107` `.gl-edit-preview` | ảnh gallery | 100% × `aspect-ratio 16/9` | — | Preview runtime |
| 15.8 | **Banner voucher** — `admin_loyalty.html:1158` `.ly-voucher-card__banner img` | `v.banner_image` → `uploads/rewards/` | 100% × **120px**, cover | dùng banner reward gốc (13.1) | Không cần file riêng |
| 15.9 | **Preview dropzone voucher** — `admin_loyalty.html:1428` `.ly-dropzone` | ảnh vừa upload | 100% × **130px** | — | Preview runtime |

---

## 16. Chỗ CHƯA dùng ảnh nhưng nên bổ sung

| # | Vị trí | Hiện trạng | Khuyến nghị | Gợi ý nội dung |
|---|---|---|---|---|
| 16.1 | **Favicon** | ❌ **Không tồn tại** trong bất kỳ template nào (`base.html`, `auth_base.html`, `customer_base.html`, `admin_base.html`, `staff_base.html`) | `favicon.ico` (32×32 + 16×16) + `favicon-32.png`, `apple-touch-icon.png` **180×180** | Logo mark chữ "D" hoặc icon móng tay/hoa, nền hồng `#d64682` |
| 16.2 | **OG image (social share)** | ❌ Không có `og:image` / `twitter:image` | **1200×630** (1.91:1) | Ảnh salon + logo + slogan — hiển thị khi share link lên Facebook/Zalo |
| 16.3 | **Logo header/footer** | Đang là **text thuần**: `.logo-text` "Daha" + `.logo-accent` "Care" (`base.css:124-139`, footer `base.css:669`) | SVG logo, cao **~28px** (header) / **28px** (footer, nền tối) | Cần **2 biến thể**: logo tối (nền trắng) + logo trắng (nền deep-plum ở footer) |
| 16.4 | **Logo trong email** | Text `<h1>Daha Care</h1>` (`email_system.py:22`) | PNG **560px** rộng tối đa, logo ~**200×60** | Email client hay chặn ảnh → cần alt text tốt. Phải là **URL tuyệt đối** (https), không dùng `url_for` |
| 16.5 | **Ảnh default cho STAFF** | 🔴 **Thiếu hoàn toàn** — `about.html:126`, `public_booking.html:144`, `customer_booking.html:144` không có fallback | **288×288** (1:1) | Cần nhất trong danh sách này |
| 16.6 | **Ảnh default cho GALLERY** | 🔴 Thiếu — `gallery.html:44,59`, `index.html:116`, `admin_gallery.html:996` không có fallback | **1600×1600** (1:1) | Placeholder "chưa có ảnh" hoặc mẫu nail generic |
| 16.7 | **Ảnh default cho REWARDS** | 🔴 Thiếu — `loyalty_points.html:1180`, `admin_loyalty.html:1158` không có fallback | **800×600** (4:3) | Banner voucher generic |
| 16.8 | **Ảnh default cho AVATAR khách** | ⚠️ Có `avatar-default.svg` nhưng chỉ dùng ở `view_booking_details.html:67`; các nơi khác dùng chữ cái viết tắt | — | Thống nhất hoặc giữ nguyên initials (đang khá đẹp) |

---

## 17. Tóm tắt bộ ảnh Default cần tạo

| Bộ ảnh | Kích thước export | Tỉ lệ | Số lượng đề xuất | Dùng ở |
|---|---|---|---|---|
| **Hero carousel** | 1920×800 | 12:5 | 3 | 1.1, 8.1 |
| **Service — ngang** | 800×600 | 4:3 | 4-6 | 1.2, 2.1 |
| **Service — vuông** | 768×768 | 1:1 | 4-6 | 5.1, 6.1, 10.1 |
| **Service — dọc** | 400×510 | 3:4 | 4-6 | 8.2, 9.1-9.4 |
| **Gallery — vuông** | 1600×1600 | 1:1 | 8-12 | 1.3, 3.1, 3.2, 15.6, 16.6 |
| **Gallery — dọc** | 1080×1500 | 3:4 | 2-3 | 1.4 |
| **Staff avatar** | 288×288 | 1:1 | 1 default (+ ảnh thật) | 4.2, 4.3, 5.2, 14.1, 16.5 |
| **Customer avatar** | 360×360 | 1:1 | 1 | 11.1, 12.1, 15.1, 15.2 |
| **Reward banner** | 800×600 | 4:3 | 2-3 | 13.1, 15.8, 16.7 |
| **Mission card bg** | 900×900 | 1:1 | 3 (đã có) | 13.2 |
| **About — Our Story** | 1080×1350 | 4:5 | 1 | 4.1 |
| **Auth panel — dọc** | 1200×1600 | 3:4 | 1 | 7.1 |
| **Bản đồ salon — ngang** | 1600×640 | 5:2 | 1 | 6.2, 11.2 |
| **CTA background texture** | 1600×500 | 16:5 | 1 | 6.3 🔴 (đang là URL ngoài) |
| **Favicon set** | 32/16 ico + 180×180 | 1:1 | 1 bộ | 16.1 |
| **OG image** | 1200×630 | 1.91:1 | 1 | 16.2 |
| **Logo SVG** | cao 28px | — | 2 (dark + light) | 16.3, 16.4 |

---

## 18. Lưu ý kỹ thuật khi tạo ảnh

1. **Giới hạn dung lượng:** upload qua admin bị chặn ở **2MB** (avatar khách: **800KB**). Ảnh default đặt trong `static/` thì không bị chặn nhưng nên nén.
2. **Định dạng:** hệ thống chấp nhận `jpg/jpeg/png/webp`. **WebP nhẹ nhất** cho ảnh photo; PNG cho ảnh có nền trong suốt; SVG cho icon/logo.
3. **`object-fit: cover` ở mọi chỗ** → chủ thể phải nằm **giữa khung**, chừa lề an toàn ~10% mỗi cạnh.
4. **Ảnh bị overlay** (1.1, 8.1 opacity .6 + blend overlay; 6.3 opacity .2) → chọn ảnh **sáng, ít chi tiết**, nếu không sẽ thành mảng màu bẩn.
5. **Tone màu brand:** primary `#d64682` (hồng), deep-plum `#3E1F47`, stone-white, blossom-pink `#efdee4`, surface `#faf7f8`.
6. Đặt ảnh default vào `app/static/images/Default/<nhóm>/` theo đúng convention đang có.
