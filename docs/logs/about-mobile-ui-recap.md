# Recap — Mobile UI cho trang About

**Ngày:** 2026-08-07
**Phạm vi:** Trang `/about` (`app/templates/public/about.html` + `app/static/css/public/about.css`). Chỉ layout mobile (≤768px) + lớp motion dùng chung. **Không** đụng nội dung copy, chuỗi i18n, IA, route, hay layout desktop.

## Yêu cầu
UI/UX thân thiện với người dùng, hoạt động mượt mà, sáng tạo, giữ vibe luxury.

## Design read
Trang About của tiệm nail cao cấp, khách chủ yếu vào bằng điện thoại để "soi" tay nghề và đội ngũ trước khi đặt lịch. Token màu/typo đã có sẵn trong `base.css` → xử lý theo hướng **redesign - preserve**: giữ nguyên token và IA, chỉ dựng lại layout mobile.
Dials: `DESIGN_VARIANCE 6 / MOTION_INTENSITY 5 / VISUAL_DENSITY 3`.

## Vấn đề đã phát hiện

| # | Vấn đề | Vị trí gốc |
|---|--------|-----------|
| 1 | Ảnh story `aspect-ratio: 4/5` full-width → ở 390px cao 468px, nuốt trọn 1 màn trước khi thấy chữ | `about.css:61` |
| 2 | Team grid 2 cột ở 360px chỉ còn ~146px/card, trừ padding còn 98px cho avatar 96px → tên nhân viên gãy dòng | `about.css:393`, `189-213` |
| 3 | Panel team bo góc 24px nhưng margin ngang = 0 → dính sát mép màn, nhìn như lỗi render | `about.css:388-391` |
| 4 | Không có `:active` feedback, cả trang chỉ có `:hover` → tap trên touch cảm giác chết | `about.css:202`, `343` |
| 5 | Thiếu `.mobile-book-bar` (index + gallery đều có) → khách đọc giữa trang không còn đường đặt lịch ngoài hamburger | — |
| 6 | Thiếu block `prefers-reduced-motion` | — |
| 7 | Values 4 card center-aligned + xếp dọc → mỗi thẻ cao ~180px, chữ căn giữa khó quét | `about.css:402-406` |
| 8 | Type scale mobile cứng (32px, 26px), không fluid | `about.css:368`, `412` |

## Quyết định đã chốt (user chọn)
- **Scope:** làm tất cả (sửa lỗi + nâng vibe + polish type scale/nhịp section).
- **Team mobile:** rail scroll-snap ngang (giống `.services-grid` ở `index.css`), thay vì list 1 cột hay giữ grid 2 cột.
- **Hero + ảnh story:** ảnh tràn viền (full-bleed) sát ngay dưới hero.

## Thay đổi

### `app/templates/public/about.html`

| Thay đổi | Chi tiết |
|----------|----------|
| Class `abt-reveal` | Gắn cho: `.abt-story__img-wrap`, `.abt-story__text`, 4 × `.abt-stats__item`, `.abt-team__header`, `.abt-team__grid`, 4 × `.abt-value` |
| `id="abt-stats"` | Mốc cho IntersectionObserver của count-up |
| Sticky book bar | Thêm `<a class="mobile-book-bar">` — tái dùng component chung ở `base.css`, không viết CSS mới |
| Script (1 block) | Scroll reveal + count-up + toggle book bar |

**Chi tiết script:**
1. **Scroll reveal** — IntersectionObserver (`threshold 0.12`, `rootMargin 0 0 -40px 0`), stagger 70ms **theo từng đợt IO báo về** chứ không theo index toàn cục (nếu không khối cuối trang phải chờ cả giây). Class enable `.js-reveal` do JS gắn vào `<html>`, **không viết sẵn trong HTML** → JS lỗi/bị chặn thì nội dung hiện bình thường thay vì kẹt ở `opacity: 0`.
2. **Count-up stats** — đọc thẳng số đang render rồi tách phần số / phần đuôi bằng regex `^(\d+(?:\.\d+)?)(.*)$`, nên `"5+"`, `"12k+"`, `"4.9"` và số nhân viên từ DB đều chạy đúng; thêm bớt số liệu trong HTML **không cần sửa JS**. Ease-out-cubic 900ms, chạy đúng 1 lần (`statsIO.disconnect()`), kết thúc gán lại chuỗi gốc.
3. **Book bar** — observe `.abt-hero`, toggle `.mobile-book-bar--visible` khi hero rời viewport (cùng cơ chế `index.html` / `gallery.html`).

Cả reveal lẫn count-up **tự bỏ qua** khi `prefers-reduced-motion: reduce`.

**Reveal gắn ở cả khối `.abt-team__grid` thay vì từng card:** trên mobile grid này là rail ngang, card nằm ngoài mép phải chỉ intersect khi khách vuốt tới → fade từng cái lúc đang vuốt trông giật.

### `app/static/css/public/about.css`

| Section | Thay đổi (≤768px) |
|---------|-------------------|
| Hero | `padding: 40px 24px 26px`; title `clamp(30px, 8.2vw, 38px)`, `line-height: 1.15` + `padding-bottom: 2px` (title italic, chữ "Story" có đuôi 'y' — leading chặt là cắt chân chữ); subtitle 15px / `max-width: 34ch` |
| Story | `padding: 0` để ảnh tràn viền; ảnh `aspect-ratio: 4/3` (239px thay vì 416px), `border-radius: 0 0 24px 24px`, bỏ `box-shadow` (tràn sát mép thì shadow chỉ còn thấy ở cạnh dưới, thành vệt bẩn); text tự giữ `padding: 0 24px` |
| Stats | 2×2 `gap: 0`, chia bằng hairline `rgba(248,249,250,0.14)` (`:nth-child(odd)` → `border-right`, `:nth-child(-n+2)` → `border-bottom`); number 32px |
| Team | Panel `margin: 0 16px 56px` + `padding: 36px 0`; grid → `display: flex` + `scroll-snap-type: x mandatory`, `justify-content: flex-start`, `scroll-padding-left: 20px`, ẩn scrollbar; card `flex: 0 0 clamp(150px, 44vw, 190px)`; avatar 80px |
| Values | Bỏ `flex-direction: column` + `text-align: center` → icon trái / chữ trái; padding 18px, icon-wrap 40px, title 17px, desc 14px |
| CTA | Nút `width: 100%` + `justify-content: center`; title `clamp(24px, 6.6vw, 30px)` |
| Touch | `.abt-team__card`, `.abt-cta__btn` → `transition: transform 0.12s` + `:active { scale(0.98) }` |

**Ngoài media query:**
- `.js-reveal .abt-reveal` / `.abt-reveal--in` — fade + `translateY(16px)`, `cubic-bezier(0.16, 1, 0.3, 1)` 0.55s.
- `.abt-stats__number` thêm `font-variant-numeric: tabular-nums` — count-up đếm qua nhiều chữ số, chữ số không đều bề ngang thì cả cụm co giật.
- Block `@media (prefers-reduced-motion: reduce)` — tắt transition + hover transform của team card.

### Bẫy đã tránh
- **`justify-content: center` trên rail:** giữ giá trị của desktop thì phần nội dung tràn **bên trái** không cuộn tới được. Rail bắt buộc `flex-start`.
- **Reveal viết sẵn trong HTML:** JS hỏng là nội dung kẹt vô hình. Class enable phải do JS gắn.

## Kiểm chứng (render thật, Flask dev :5000)

| Kiểm tra | Kết quả |
|----------|---------|
| Viewport 333px (hẹp hơn iPhone 12 → ca xấu nhất) | Hero + trọn ảnh story lọt fold đầu |
| Tràn ngang | `scrollWidth == clientWidth == 318` → không tràn |
| Console | Không lỗi |
| Rail team (test nhân bản 5 card bằng JS, không đụng DB) | Cuộn được 838px, card thứ 2 lộ mép đúng thiết kế, card rộng 150px |
| Count-up | Chạy 1 lần, về đúng `5+ / 12k+ / 2 / 4.9` |
| Footer vs book bar | `padding-bottom: 96px` áp đúng qua `body:has(.mobile-book-bar)` ở `base.css` |
| Desktop 1440px | Không đổi — story vẫn 2 cột, team vẫn grid căn giữa, reveal chạy mượt |

## Ghi chú / ngoài phạm vi
- **i18n:** chuỗi duy nhất thêm mới là `Book Now`, đã có sẵn bản dịch ở cả `vi` / `fi` / `en` (verify live: bản Phần Lan hiện "Varaa nyt"). **Không cần** cập nhật `.po` / build lại `.mo`.
- **Chưa test trên thiết bị thật:** cảm giác vuốt rail và `:active` bằng ngón tay. Nếu card team thấy nhỏ so với gu, chỉnh `44vw` → `52vw` trong `.abt-team__card`.
- **Chưa đụng:** stats `5+` / `12k+` / `4.9` vẫn hardcode trong HTML (chỉ `Master Artists` lấy từ `staff_members | length`). Ý định đưa qua context của `main.about` đã ghi sẵn trong comment ở `about.html`, chưa làm.
