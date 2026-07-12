# Chuẩn hoá cơ chế Upload ảnh — Work Log

**Ngày:** 2026-07-13 · **Trạng thái:** ✅ Hoàn tất (chưa commit)

Gộp tất cả tính năng upload ảnh về **một cơ chế chung** (theo pattern admin/carousel). Trước đó có 6 cơ chế gần giống nhau nhưng không đồng nhất.

---

## 1. Audit ban đầu — 6 tính năng upload

| Tính năng | uuid | Cột DB | Resolver | Xoá ảnh cũ | Guard |
|-----------|------|--------|----------|-----------|-------|
| Carousel (mẫu) | ✅ | `carousel_slides.image` | ✅ | ✅ | ✅ |
| Service | ✅ | `services.image` | ❌ | ✅ | ❌ |
| Gallery | ✅ | `gallery_images.image_url` | ❌ (chỉ http) | ✅ | ❌ |
| Reward | ✅ | `rewards.banner_image` | ❌ | ✅ | ❌ |
| Staff | ✅ | `staff.photo` | ✅ | ❌ **rác** | — |
| Customer | ❌ `{user_id}.ext` | ❌ không DB | ✅ (scan) | ✅ | — |

**Vấn đề:** 6 hàm `_save_*` + 18 hằng số gần trùng; render không đồng nhất (service/gallery/reward ghép cứng `uploads/` trong template); staff không xoá ảnh cũ → tích rác; customer đi pattern riêng.

**Quyết định (user chọn):**
- Customer avatar → đổi sang **uuid + cột DB** (đồng bộ hẳn).
- Refactor → **gộp DRY thành helper chung**.

---

## 2. Helper chung (thêm vào `routes.py`)

```python
_UPLOAD_ROOT, _UPLOAD_CONFIG   # config ext/size mỗi loại tại 1 chỗ
_size_label(n)                 # "2MB" / "800KB"
_save_upload(file, subdir)     # validate + lưu {uuid}.{ext}, trả tên file
_resolve_upload(image, subdir) # http/'/' → dùng thẳng; tên trần → /static/uploads/<subdir>/
_is_managed_upload(image)      # True nếu là file mình lưu (xoá an toàn)
_delete_upload(image, subdir)  # xoá có guard
@main.app_template_filter("img_src")   # {{ value | img_src('services') }}
```

## 3. Migrate 6 tính năng

- **Service / Gallery / Reward / Carousel / Staff:** đổi `_save_X_image(f)` → `_save_upload(f, "<sub>")`; xoá thủ công → `_delete_upload(...)`; render → resolver / `| img_src('<sub>')`.
- **Staff:** thêm bước xoá ảnh cũ khi up ảnh mới (`_delete_upload(old["photo"], "staff")`) — **fix bug rác file**.
- **Customer avatar (thay đổi lớn nhất):**
  - `schema.sql`: thêm cột `customers.avatar TEXT DEFAULT NULL`.
  - `db.py`: thêm `update_customer_avatar(customer_id, avatar)`.
  - `_resolve_customer_avatar` đọc từ DB thay vì scan file theo `{user_id}`.
  - Route `update_avatar`: `_save_upload` → `update_customer_avatar` → `_delete_upload` ảnh cũ.
  - Bỏ `?v=mtime` (uuid đổi mỗi lần up nên không cần chống cache).

## 4. Dọn dẹp (DRY)

Xoá **9 hàm trùng** (`_save_service_image`, `_save_gallery_image`, `_save_reward_image`, `_save_carousel_image`, `_save_staff_image`, `_save_avatar_image`, `_resolve_carousel_image`, `_resolve_staff_photo`, `_is_managed_carousel_image`) + **18 hằng số** (`_*_IMG_DIR`, `_ALLOWED_*`, `_MAX_*`). Giữ `_AVATAR_PALETTE` (initials) và `_name_initials`.

## 5. Render — các template đã đổi sang `img_src`

- Service: `public/index.html`, `public/services.html`, `public/public_booking.html`, `customer/customer_booking.html`, `customer/my_bookings.html` (×3) — kèm fallback placeholder `Default/Service/test.png`.
- Gallery: `public/gallery.html` (×2), `public/index.html`, `admin/admin_gallery.html`.
- Reward: `admin/admin_loyalty.html` (×2) + route customer.
- Staff: `public/public_booking.html`, `customer/customer_booking.html`, `public/about.html`, context `_get_current_staff`.
- Cập nhật 1 doc comment lỗi thời ở `customer_setting.html`.

## 6. Verification

- `py_compile` OK · không còn tham chiếu tên cũ.
- `/ /services /gallery /about` = 200.
- Service placeholder + gallery + carousel default render đúng.
- Customer avatar resolve từ DB → `/static/uploads/avatars/<uuid>.png`.

---

## ⚠️ Lưu ý sau refactor

1. **Schema đổi** (`customers.avatar`) → **phải re-init DB local**: `python -m app.init_db --seed`. Không thì trang customer lỗi thiếu cột. Avatar khách cũ (`{user_id}.ext`) không còn được tham chiếu — chấp nhận được vì chưa launch.
2. 2 chỗ JS preview admin (`admin_gallery.html`, `admin_services.html`) giữ base `uploads/` — vẫn đúng cho ảnh upload (tên trần), là edge case admin-edit, không đụng.

## Files đổi
- `app/routes.py` (chính — helper + migrate + dọn)
- `app/database/db.py` (+`update_customer_avatar`)
- `app/database/schema.sql` (+cột `customers.avatar`)
- ~15 template (render) + 1 doc comment

## Commit gợi ý
```
Standardize all image uploads to one shared mechanism

- Add generic _save_upload/_resolve_upload/_delete_upload + img_src filter
- Migrate service, gallery, reward, carousel, staff, customer avatar
- Staff: delete old file on re-upload (fixes orphan buildup)
- Customer avatar: uuid + customers.avatar column (was {user_id}.ext, no DB)
- Remove 9 duplicated helpers + per-type constants
```
