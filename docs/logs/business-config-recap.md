# Gom thông tin doanh nghiệp + nội dung tĩnh về `app/business.py`

**Ngày:** 2026-08-10 · **Phạm vi:** file mới `app/business.py` + 59 file sửa (10 chỗ hardcode liên hệ, 51 khoá text, 13 perks, 58 chỗ đổi tên thương hiệu, sync membership→DB, rebuild 3 catalog dịch) · **Trạng thái:** ⚠️ code xong, đã render-test 15 lần (5 trang × 3 ngôn ngữ) + 18 email + 47/47 template compile, **chưa xem trên trình duyệt thật**, **chưa commit**

Xuất phát từ một câu hỏi của Mon: *"deploy thật thì fill thông tin doanh nghiệp vào đâu — `.env` hay file nào đó, thay vì hardcode từng chỗ trên html/backend?"*

---

## 1. Audit trước: những gì đang hardcode

| Nhóm | Số chỗ | Ví dụ |
|---|---|---|
| Liên hệ (địa chỉ, SĐT, email, giờ, map) | 10 | `routes.py:825`, `helpers.py:118`, `index.html`, `view_booking_details.html` |
| Tên thương hiệu | 60 trên 44 file | **3 biến thể song song**: `MisaNails` / `DahaCare` / `Daha Care` |
| Text marketing trong `_()` | 51 khoá | story About, 2 testimonial, perks membership, 12 nội dung email |
| Số liệu quảng cáo | 6 | `5+` năm, `12k+` khách, `4.9` sao, `5K+`, `100%`, `10+` |

### 4 lỗi thật lộ ra trong lúc audit

1. **Footer `base.html` chưa từng chạy đúng.** Nó dùng `branches`, `business_id`, `current_year` nhưng **không context processor nào định nghĩa cả 3** (đã grep toàn repo). Hệ quả: vòng lặp chi nhánh chạy 0 lần, dòng `Business ID:` in ra rồi bỏ trống, `©` không có năm. Y-tunnus là **bắt buộc theo luật Phần Lan** khi bán hàng online.
2. **Giờ mở cửa mâu thuẫn.** Trang chủ quảng cáo `Mon-Fri 9:00-20:00`, nhưng `booking_service.py:10-11` chỉ mở slot `09:00`–`18:00`. Khách đọc web tưởng đặt được 19:00 rồi mở wizard không thấy giờ nào.
3. **Sai chính tả địa chỉ.** `view_booking_details.html` in `Kyykysmäki` (thiếu chữ `h`), khác với `Kyyhkysmäki` ở mọi chỗ còn lại.
4. **SĐT/email trong trang chi tiết booking là `<span>` chết** — trên mobile không gọi/không gửi mail được.

### Rủi ro pháp lý đã nêu (Mon quyết định giữ)

`index.html` có **2 review bịa**: "Sarah Jenkins" (Gold member) và "Maria Rodriguez" (First-time client), kèm 5 sao. Directive (EU) 2019/2161 + `Kuluttajansuojalaki` cấm đăng review giả; KKV xử phạt được. Mon chọn **giữ**, nhưng nay sửa được trong `business.py` thay vì phải đụng template.

---

## 2. Vì sao KHÔNG dùng `.env`

`.env` hợp với **bí mật** (API key) — thứ không được vào git. Nhưng địa chỉ, SĐT, giờ mở cửa không phải bí mật, và là **dữ liệu có cấu trúc** (nhiều chi nhánh, perks lồng nhau, 3 ngôn ngữ). Nhét vào `.env` sẽ thành `BRANCH_1_NAME=` / `BRANCH_1_ADDRESS=`: khó đọc, không version được, sai một ký tự là chạy sai mà không báo lỗi.

**Chốt: 2 tầng.** `.env` giữ secret. `app/business.py` giữ mọi thứ còn lại, commit vào git.

---

## 3. Xung đột thiết kế phải giải trước khi viết code

### 3.1 i18n: rút text ra khỏi `_()` là rời luôn hệ `.po`

Toàn bộ text dài đang nằm trong `_()` → dịch qua `.po` (819 msgid; fi 95%, vi 83% đã dịch). Rút ra `business.py` thì chúng không còn được `gettext` tra nữa. Hai lối:

- **Chỉ lưu tiếng Anh, vẫn bọc `_()`** → sửa file xong, khách fi/vi **vẫn thấy text cũ** cho tới khi chạy lại `pybabel` + dịch tay. Không đạt mục tiêu Mon đặt ra.
- **Lưu cả 3 ngôn ngữ trong file** → sửa 1 file là đổi thật cho cả 3, **không cần `pybabel`**.

Mon chọn lối 2. Khả thi vì **bản dịch fi/vi đã có sẵn trong `.po`** — viết script parse `.po` rồi trích thẳng sang `business.py`, không phải dịch lại chữ nào.

### 3.2 Ranh giới: cái gì admin sửa được thì KHÔNG vào `business.py`

Mon muốn `business.py` là "source chính cho pricing, stripe, loyalty points". Kiểm tra thực tế cho ra kết quả khác nhau theo từng loại:

| Dữ liệu | Admin sửa được? | Kết luận |
|---|---|---|
| Tier: price, point_multiplier, duration_days | ❌ **không có route admin nào ghi** | ✅ vào `business.py` |
| Perks từng hạng | ❌ hardcode trong template | ✅ vào `business.py` |
| `loyalty_config` (review/birthday/streak/referral bonus) | ✅ `/admin/loyalty/missions/<key>/update` + toggle | ❌ **ở lại DB** |
| Giá dịch vụ | ✅ `/admin/services` | ❌ **ở lại DB** |

> **Lý do từ chối 2 dòng cuối:** đưa vào `business.py` thì mỗi lần redeploy sẽ **ghi đè con số admin vừa chỉnh trong panel**. Admin sửa `review_bonus = 80`, deploy phát → về lại 50, không ai hiểu tại sao. Đây đúng loại "thay thế được từ admin form" mà chính Mon đã nói loại trừ.

`membership_tiers.description` bị bỏ khỏi phạm vi vì **không render ở đâu** — dữ liệu chết.

### 3.3 Tier price ↔ Stripe: vấn đề tiền thật

Stripe Price object là **immutable**. Sửa `price: 49.99 → 59.99` rồi redeploy:
- Web hiện €59.99, Stripe vẫn thu **€49.99**
- `setup_stripe_prices.py` skip tier đã có `stripe_price_id` → chạy lại cũng không sửa

**Cách xử lý** (tận dụng logic sẵn có ở `routes.py`, dòng `"buyable"`):

`sync_membership_tiers()` chạy lúc app khởi động (`app/__init__.py`):
1. Ghi `name`/`price`/`point_multiplier`/`duration_days` xuống `membership_tiers` → **10 chỗ đọc tier sẵn có không phải sửa dòng nào** (`loyalty.py`, `payment_service.py`, template), và `customer_memberships.tier_id` còn khoá ngoại trỏ vào.
2. Giá đổi mà tier đã có `stripe_price_id` → **set NULL** + log cảnh báo.
3. `buyable` tự thành `False` → **nút mua bị khoá** thay vì charge sai giá.
4. Mở lại: `python -m app.database.setup_stripe_prices`

Khách **đang** subscribe vẫn giữ giá cũ — đúng về mặt hợp đồng, Stripe không cho đổi ngầm.

> `membership_tiers` từ nay chỉ là **bản sao** của `business.py`, không còn là nguồn.

---

## 4. Kiến trúc đã dựng

```
app/business.py  (437 dòng)
├── BUSINESS    brand_name, brand_logo_parts, business_id, phone, email,
│               address, address_lines, branches[], hours, discount, stats
├── MEMBERSHIP  3 hạng × (price, point_multiplier, duration_days, perks[3 lang])
├── CONTENT     51 khoá × {en, fi, vi}
├── txt(key, **kw)   → chọn ngôn ngữ theo session, fallback 'en'; có kwargs
│                      thì nội suy %(name)s (dùng cho email + số chèn vào câu)
└── perks(tier_name) → list quyền lợi đã chọn đúng ngôn ngữ
```

- `template_filters.py`: đăng ký `txt` / `perks` thành Jinja global (cùng chỗ với `tr` sẵn có)
- `routes.py`: context processor `inject_business` → `biz`, `branches`, `business_id`, `current_year`
- Template dùng `{{ txt('about.story_lead') }}`, Python dùng `from app.business import txt`

### Vì sao dùng `%(brand)s` thay vì ghi thẳng tên

Nội dung email và vài câu marketing có chứa tên tiệm. Nếu ghi cứng thì đổi `brand_name` sẽ không lan tới chúng. Nay `txt('email.thank_you_body', brand=BUSINESS['brand_name'], ...)` → đổi tên một chỗ là xong.

**Bẫy tiếng Phần Lan:** bản cũ viết `DahaCaressa` (inessiivi) và `DahaCaren` (genetiivi) — thay `%(brand)s` thẳng vào sẽ sai ngữ pháp. Đã viết lại câu ở chủ cách (`%(brand)s uskoo, että…`) và dạng ghép gạch nối (`%(brand)s-ero`, `%(brand)s-salonki`), là cách chuẩn cho danh từ riêng nước ngoài. **Nên nhờ người bản ngữ đọc lại.**

---

## 5. Đã sửa những gì

| File / nhóm | Thay đổi |
|---|---|
| `app/business.py` | **mới**, 437 dòng |
| `template_filters.py` | +4 dòng: đăng ký `txt` / `perks` |
| `routes.py` | context processor `inject_business`; bỏ 2 địa chỉ hardcode; CSV báo cáo dùng `brand_name` |
| `database/db.py` | +`sync_membership_tiers()` (40 dòng) |
| `__init__.py` | gọi sync lúc khởi động, bọc try/except như `reset_stuck_video_jobs` |
| `services/email_system.py` | −95/+... : 5 nhánh `if/elif` gộp thành 1 bảng tra `_VERIFY_CONTENT_KEYS`; brand vào header/footer HTML; **hết sạch `_()`** |
| `utils/helpers.py` | Google Calendar lấy tên + địa chỉ từ `BUSINESS` |
| `database/setup_stripe_prices.py` | tên Stripe Product theo `brand_name` |
| 20 template public/customer/Auth | 51 chỗ `_()` → `txt()`; liên hệ/giờ/map → `biz.*` |
| 44 file | 58 chỗ đổi tên thương hiệu → `{{ biz.brand_name }}` |
| 3 catalog + `.pot` | rebuild: 819 → **757 msgid** |

**Dùng chung khoá:** `public_booking.html` và `customer_booking.html` có 4 chuỗi trùng nhau → chung 1 khoá, sửa 1 lần đổi cả 2 trang.

**Logo tách đôi:** navbar tô màu nhấn nửa sau của tên nên thêm `brand_logo_parts: ["Misa", "Nails"]`. Ghép lại phải đúng bằng `brand_name`.

---

## 6. Verify

| Kiểm tra | Kết quả |
|---|---|
| Render 5 trang công khai × 3 ngôn ngữ | 15/15 HTTP 200, footer có chi nhánh + năm, không còn `Mon-Fri` / `Kyykysm` / `9:00-20:00` |
| Compile template | 47/47 |
| Render email (6 loại × 3 ngôn ngữ) | 18/18, brand đúng, placeholder được thay, mã xác thực chèn đúng, không còn tên cũ |
| **Mọi `txt('key')` trỏ tới khoá có thật** | **51/51 — 0 gõ sai, 0 khoá thừa** |
| Guard Stripe | giá không đổi → giữ `stripe_price_id`; giá đổi → xoá + cảnh báo ✓ |
| Catalog | 819 → 757 msgid, **đúng bằng** 49 chuỗi CONTENT từng là msgid + 13 perks |
| `fuzzy` | về đúng mức ban đầu (fi 4 / en 4 / vi 3) |

> **Kiểm tra quan trọng nhất là dòng in đậm.** Gõ sai tên khoá `txt()` không ném lỗi — nó trả **chuỗi rỗng**, trang vẫn 200, chữ biến mất âm thầm. Script `checkkeys.py` đối chiếu hai chiều: mọi khoá được dùng phải tồn tại, mọi khoá khai báo phải được dùng.

> **`fuzzy` là bẫy thứ hai.** Khi msgid đổi (`'Why MisaNails?'` → `'Why %(brand)s?'`), `pybabel update` đánh dấu `fuzzy` — và `pybabel compile` **bỏ qua** mục fuzzy. Nếu không để ý, 2 chuỗi đã dịch sẽ lặng lẽ tụt về tiếng Anh. Đã sửa tay 2 mục, đưa số fuzzy về đúng mức trước khi làm.

---

## 7. Còn phải điền trước khi mở cho khách

1. **`business_id` đang rỗng** — Y-tunnus bắt buộc theo luật Phần Lan. Footer đang in nhãn rồi bỏ trống.
2. **Số liệu quảng cáo tự mâu thuẫn** — trang chủ `5K+` khách / `10+` thợ; trang About `12k+` khách / đếm nhân viên thật trong DB (**hiện 1 người**). Đã gom vào `BUSINESS` kèm cảnh báo trong comment.
3. **2 review giả** — Mon quyết định giữ; rủi ro pháp lý đã nêu ở mục 1.
4. **`placeholder="you@dahacare.com"`** ở 2 trang đăng nhập staff — đây là **domain**, không phải brand, không tự đoán được.
5. **12 nội dung email chưa có bản Phần Lan** — ô `"fi"` đang bằng tiếng Anh. **Không phải hồi quy**: `.po` cũng đang bỏ trống 12 mục này, khách Phần Lan xưa nay vẫn nhận email tiếng Anh.
6. **Câu tiếng Phần Lan đã viết lại** ở `about.story_lead` và `about.cta_sub` — nhờ người bản ngữ đọc lại.

---

## 8. Ghi chú cho agent sau

- **Đừng đưa `loyalty_config` hay giá dịch vụ vào `business.py`.** Admin sửa được qua panel; đưa vào là mỗi lần redeploy ghi đè thứ admin vừa chỉnh. Lý do đầy đủ ở mục 3.2. Danh sách loại trừ nằm luôn trong docstring của `business.py`.
- **Đổi `MEMBERSHIP[...]["price"]` là khoá nút mua** cho tới khi chạy `python -m app.database.setup_stripe_prices`. Đây là **cố ý**, không phải bug.
- **Sau khi sửa `CONTENT` thì KHÔNG cần chạy `pybabel`** — đó là toàn bộ mục đích của đợt này. Chỉ chạy `pybabel` khi đụng vào chuỗi còn nằm trong `_()`.
- `messages.pot` còn **136–141 mục obsolete** (`#~`) trong mỗi `.po` — đó là các msgid đã chuyển sang `business.py`, `pybabel` tự đánh dấu. Không cần xoá tay.
- **`app/static/css/customer/booking_details.css` có thay đổi trong working tree KHÔNG thuộc đợt này** (màu nhãn trạng thái `in-progress` / `no-show`). Chưa rõ nguồn gốc, đã để nguyên — cần tách ra khi commit.
- `seed.sql` vẫn còn `'Welcome to MisaNails'` (badge carousel) + 2 comment `DahaCare Nail Salon`. Slide là nội dung **admin sửa được** nên đúng quy tắc là không đưa vào `business.py`.

---

## Tham chiếu

- Nguồn: `app/business.py` (docstring giải thích ranh giới)
- Checklist deploy: `docs/PRE_PRODUCTION_CHECKLIST.md` (phần hạ tầng — domain nginx, Stripe live key, OAuth redirect — không lặp ở đây)
