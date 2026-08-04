# Service Video + Modal chi tiết

**Ngày:** 2026-08-05 · **Phạm vi:** `/services` (public) + `/admin/services` · **Trạng thái:** ✅ cả 2 giai đoạn xong, chưa deploy

Tính năng: mỗi dịch vụ có một video minh hoạ. Khách bấm vào card trên trang `/services` để mở lớp chi tiết (bottom sheet ở mobile, modal ở desktop) chứa video + toàn bộ thông tin. Admin upload video qua form, server tự nén.

---

## 1. Vì sao làm

Xuất phát từ audit UI mobile của `services.html`, không phải từ yêu cầu về video.

Card cũ ở mobile cao khoảng **480px** (ảnh 4:3 + tên + mô tả 2 dòng + giá + nút full-width), tức là **chưa tới 1.5 card mỗi màn hình**. Danh sách 12 dịch vụ bắt user vuốt qua 8 màn hình.

Hướng xử lý đầu tiên là chuyển card sang layout hàng ngang. Nhưng làm vậy thì mất chỗ cho description. Đã cân nhắc accordion mở rộng tại chỗ, rồi **bỏ** khi có kế hoạch thêm video: video không nhét vừa accordion, và modal giải quyết triệt để hơn.

Kết quả ngược đời nhưng đúng: **có modal rồi thì card nên gọn hơn nữa, không phải nhiều hơn.** Card chỉ cần mời user tap; mọi thông tin nằm trong modal.

---

## 2. Các quyết định kiến trúc

Phần quan trọng nhất của tài liệu này. Mỗi quyết định đều có lý do cụ thể, đọc lại sau vài tháng sẽ hiểu vì sao không làm cách khác.

### 2.1 Modal thay vì trang chi tiết riêng

Trang riêng (`/services/<slug>`) sẽ tốt hơn về SEO và chia sẻ link, nhưng đắt hơn nhiều (route, template, IA mới). Với tiệm khoảng 20 dịch vụ thì modal đủ. Nếu sau này muốn từng dịch vụ lên Google thì phải làm trang thật, modal không thay thế được.

### 2.2 `<dialog>` native, không tự dựng bằng `<div>`

Được miễn phí: focus trap, phím Esc, `::backdrop`. Modal tự chế bằng `<div>` gần như luôn hỏng phần focus management.

**Bẫy đã gặp:** `display` chỉ được set trong `[open]`. Set ở rule gốc sẽ ghi đè `display: none` của UA và dialog hiện cả khi đang đóng.

### 2.3 Nội dung modal render sẵn ở server trong `<template>`

Mỗi card chứa một `<template class="svc-card__detail">` do Jinja render đầy đủ. JS chỉ `cloneNode` sang `<dialog>` khi mở.

Lý do: giữ toàn bộ i18n (`tr()`, `_()`) trong Jinja. Nếu nhét dữ liệu vào `data-*` rồi dựng chuỗi ở client thì phải xử lý escape và dịch thuật ở JS.

`<template>` không nằm trong document nên id trùng nhau giữa các card không xung đột; chỉ bản đã clone mới sống.

### 2.4 `video_url` CHỈ được ghi khi transcode thành công

Quyết định quan trọng nhất của giai đoạn 2.

Trong lúc xử lý, `video_url` giữ nguyên giá trị cũ (hoặc `NULL`), trạng thái nằm ở cột riêng `video_status`. Hệ quả:

- Trang public **không cần biết gì về `video_status`**, không sửa một dòng nào khi làm giai đoạn 2
- Không bao giờ có nguy cơ khách thấy video hỏng hoặc đang xử lý dở
- Thay video thì khách vẫn xem được bản cũ cho tới khi bản mới sẵn sàng

### 2.5 `video_url` trung lập nhà cung cấp

Chứa **tên file trần** (`abc123.mp4` → `uploads/videos/abc123.mp4`) **hoặc URL đầy đủ** (`https://cdn...`). Dùng lại `_resolve_upload()` sẵn có của hệ thống ảnh, qua filter `video_src`.

Nghĩa là chuyển từ self-host sang CDN chỉ cần đổi giá trị trong DB. Không migration, không sửa template.

> Giai đoạn 1 ban đầu làm sai quy ước này (lưu path `uploads/videos/x.mp4` và tự viết logic nhận diện trong Jinja). Đã sửa ở bước 2 giai đoạn 2.

### 2.6 Poster dùng lại cột `image` sẵn có

Không trích frame đầu video, không thêm cột. Bớt được một lần gọi ffmpeg và một pipeline nén ảnh.

### 2.7 Self-host + transcode trên server, không dùng dịch vụ video bên thứ ba

Đã cân nhắc 3 hướng: self-host thuần · self-host + CDN · dịch vụ Stream (Bunny/Cloudflare).

Chọn self-host vì:
- **Traffic gói gọn trong Phần Lan, server đặt tại Helsinki.** Lợi ích chính của CDN là giảm độ trễ theo địa lý, mà độ trễ đã tối ưu sẵn (5-15ms)
- **Phần Lan có hạ tầng di động rất tốt**, nên adaptive bitrate (điểm mạnh nhất của dịch vụ Stream) mất phần lớn giá trị
- Băng thông ước tính ~1.6 GB/tháng, khoảng 0.01% hạn mức của VPS

> **CDN không bị loại vĩnh viễn.** Nó là nâng cấp gắn thêm sau, không tốn dòng code nào (mô hình proxy toàn site còn không đổi URL). Đáng gắn khi một video nổi trên mạng xã hội và traffic dồn về.

### 2.8 Transcode chạy nền bằng thread, không đồng bộ

`gunicorn.conf.py` để `timeout = 60`. Transcode video 60 giây có thể mất 1-3 phút trên VPS nhỏ → worker bị giết, upload fail.

Nên: request trả về ngay sau khi lưu file thô, thread nền lo phần còn lại.

**Chống trạng thái treo:** thread là `daemon=True` nên chết theo process. `reset_stuck_video_jobs()` chạy lúc `create_app()` đánh mọi dòng còn `processing` thành `failed` — vì chắc chắn không còn thread nào xử lý chúng. Không bao giờ kẹt "đang xử lý" vĩnh viễn.

**Semaphore giới hạn 1 ffmpeg cùng lúc.** VPS nhỏ, SQLite ghi tuần tự.

### 2.9 Upload nặng KHÔNG cần sửa `gunicorn.conf.py`

nginx mặc định buffer toàn bộ request body rồi mới đẩy sang gunicorn, nên gunicorn chỉ thấy một request nhanh. Chỉ cần nâng `client_max_body_size`.

---

## 3. Giai đoạn 1 — Hiển thị

| Hạng mục | Chi tiết |
|---|---|
| Schema | `services.video_url` |
| Card mobile | Layout hàng ngang: ảnh 80px trái, nội dung phải. Bỏ description (modal đã có đủ), tên 1 dòng ellipsis |
| Card desktop | **Giữ nguyên** 3 cột, vẫn có description 2 dòng |
| Dấu hiệu video | Nút play mờ trên poster, chỉ render khi `video_url` có giá trị |
| Modal | Một `<dialog>` duy nhất cuối trang, nội dung clone từ `<template>` của card vừa bấm |
| Mobile | Bottom sheet trượt lên từ đáy, bo góc trên, `max-height: 88dvh` |
| Desktop | Modal căn giữa, `min(560px, 100vw - 48px)` |
| Video | Một thẻ `<video>` tại một thời điểm. `preload="none"`, `poster` = ảnh service |
| Đóng modal | `pause()` + gỡ `src` + `load()` để ngắt tải dở, rồi xoá nội dung |
| Không có video | Fallback về ảnh poster, `object-fit: cover` |
| Video dọc 9:16 | Khung `aspect-ratio: 16/9` nền tối + `object-fit: contain`, letterbox trông có chủ ý |

Kèm theo trong cùng đợt (từ audit mobile, không thuộc phần video): sửa filter tab không scroll ngang được (`flex-wrap: wrap` chưa reset nên `overflow-x` vô hiệu), tap target lên 44px, gate hover bằng `@media (hover: hover)`, thêm `:active`, empty state khi filter rỗng, `prefers-reduced-motion`, thu glow CTA 800px→420px.

---

## 4. Giai đoạn 2 — Upload + transcode

| Bước | Nội dung |
|---|---|
| 1 | Cột `video_status` (`NULL`/`processing`/`ready`/`failed`) + `video_error` |
| 2 | Sửa quy ước sang tên file trần, thêm filter `video_src` |
| 3 | `_save_raw_video()` — whitelist MP4/MOV/WEBM/M4V, trần 300MB, lưu vào `app/_tmp/` **ngoài `static/`** để file thô không bị serve ra ngoài |
| 4 | `_transcode_video_job()` — thread nền + semaphore. `ffprobe` đo chiều cao để **chỉ hạ xuống 720p, không phóng to** video vốn nhỏ hơn |
| 5 | `reset_stuck_video_jobs()` trong `create_app()` |
| 6 | Helper DB: `set_video_processing/ready/failed`, `clear_service_video` |
| 7 | Nối vào create/update service. Video cũ xoá **sau khi** bản mới xong |
| 8 | UI admin: dropzone, badge trạng thái trong bảng, khối trạng thái trong modal, nút Đổi/Xóa |
| 9 | Xoá service thì xoá cả ảnh lẫn video |
| 10 | `FFMPEG_BIN` / `FFPROBE_BIN` đọc từ env |

**Lệnh ffmpeg:**
```
ffmpeg -y -v error -i <src> [-vf scale=-2:720] \
  -c:v libx264 -preset veryfast -crf 23 \
  -c:a aac -b:a 96k -movflags +faststart <out>
```

`-preset veryfast` thay vì `slow`: VPS nhỏ, ưu tiên xong nhanh hơn nén tối ưu.

**Auto-refresh admin:** trang tự reload mỗi 10s khi còn badge `processing` trên DOM. Không dựng endpoint polling riêng. Bỏ qua khi đang mở modal để không mất dữ liệu form admin đang điền.

**Ô `video_url` dán tay vẫn giữ** dưới dropzone — đó là cửa duy nhất để trỏ sang CDN sau này. Upload file luôn thắng ô dán URL.

---

## 5. Số liệu thật đo được

| | Trước | Sau |
|---|---|---|
| Chiều cao card mobile | ~480px | ~116px |
| Card mỗi màn hình (iPhone SE) | ~1.4 | ~4.6 |
| Video test (16s, 1908x1080@60fps) | 53 MB @ 26.6 Mbps | **3.2 MB** @ 720p |
| Trust bar mobile | ~330px | ~90px |

Bitrate 26.6 Mbps của file gốc là mức gần như không nén. Đây là bằng chứng transcode phía server là bắt buộc chứ không phải tuỳ chọn.

**`+faststart`:** file gốc có box `moov` nằm **sau** `mdat`, tức là trình duyệt phải tải hết 53MB mới bắt đầu phát được. Sau transcode: `ftyp → moov → free → mdat`.

> ⚠️ **Test local che mất vấn đề băng thông.** Đọc từ SSD nên file 150MB chưa nén cũng tải tức thì. Đừng lấy kết quả local làm căn cứ đánh giá.

---

## 6. File đã đụng

| File | Nội dung |
|---|---|
| `app/database/schema.sql` | 3 cột video |
| `app/database/db.py` | 5 helper trạng thái video, `video_url` vào create/update |
| `app/routes.py` | Khối video upload/transcode, filter `video_src`, nối 3 route admin |
| `app/__init__.py` | Gọi `reset_stuck_video_jobs()` |
| `app/templates/public/services.html` | Card, `<template>`, `<dialog>`, JS |
| `app/static/css/public/services.css` | Modal, bottom sheet, card mobile, reduced-motion |
| `app/templates/admin/admin_services.html` | Dropzone, badge, JS, auto-refresh |
| `app/translations/*` + `messages.pot` | `View details`, `No services in this category yet.` |
| `.gitignore` | `app/_tmp/` |

---

## 7. Yêu cầu khi deploy

Chi tiết trong `docs/DEPLOYMENT_RUNBOOK.md`. Tóm tắt:

1. `sudo apt install -y ffmpeg` — **gói hệ điều hành, không phải package Python**, không có trong `requirements.txt`
2. nginx `client_max_body_size` 10M → **300M**
3. ALTER **đủ 3 cột** `video_url`, `video_status`, `video_error`. `git pull` không tự thêm cột

---

## 8. Đã verify

Toàn bộ ở tầng render HTML, DB và filesystem. **Chưa ai mở trình duyệt xem thật.**

- `/services` trả 200, đúng số card / template / dialog
- Filter `video_src` đúng với tên file trần, URL đầy đủ, và giá trị rỗng
- Upload sai định dạng bị từ chối kèm thông báo
- Upload hợp lệ: request trả về ngay với `processing`, thread hoàn tất, output có faststart
- Thay video: file cũ bị xoá, file mới tồn tại
- Xoá video và xoá service: DB sạch, file bị xoá
- Job treo: set `processing` rồi khởi động lại → tự thành `failed` kèm lý do
- Không sót file tạm lần nào
- 3 locale (en/fi/vi) hiển thị đúng chuỗi mới

---

## 9. Còn thiếu / nợ đã biết

**Thuộc tính năng này:**
- ❌ **Chưa kiểm tra trên trình duyệt thật.** Modal, bottom sheet, chevron ligature chưa ai nhìn bằng mắt
- `video_url` dán tay **không được validate**. Gõ sai thì video im lặng không chạy, không cảnh báo
- Video dọc 9:16 hiện letterbox hai bên. Muốn khít hoàn hảo thì đọc `videoWidth/videoHeight` ở `loadedmetadata` rồi set `aspect-ratio`
- Chưa đồng bộ URL (`?service=<id>`), nên không share link tới một dịch vụ cụ thể được và nút Back không đóng modal

**Nợ có sẵn phát hiện trong quá trình làm, chưa xử:**
- `admin_delete_staff` và `admin_delete_customer` **không xoá file ảnh** khi xoá (cả hai đều là xoá cứng). Mỗi chỗ một dòng
- Giá hardcode `$` trong `services.html` nhưng business là Phần Lan, đúng ra là `€`
- Hero subtitle `/services` vẫn 22 từ, khoảng 7 dòng ở mobile
- 4 mục fuzzy trong `.po` thuộc phần carousel đang dở, không compile vào `.mo`. Trong đó `JPG, PNG tối đa 10MB` dịch thành `enintään 2MB` là sai số liệu

---

## 10. Cách test lại

```bash
# 1. Public page
python -m flask --app run:app run
# mở /services, card có dấu play -> tap -> modal -> bấm play
# DevTools Network: video CHỈ được request khi bấm play, không tải lúc load trang

# 2. Admin upload (cần ffmpeg trên PATH)
# /admin/services -> Sửa một dịch vụ -> kéo thả video -> Lưu
# Bảng hiện badge "Đang xử lý video", tự reload sau 10s, chuyển thành "Có video"

# 3. Kiểm tra output có faststart
ffprobe -v error -show_entries format=duration,bit_rate -of default=noprint_wrappers=1 \
  app/static/uploads/videos/<file>.mp4
```
