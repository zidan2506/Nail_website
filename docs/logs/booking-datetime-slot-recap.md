# Recap — Select Date & Time (Booking Pages)

**Ngày:** 2026-07-15
**Phạm vi:** Section "Select Date & Time" (Step 3) ở 2 trang đặt lịch: `public_booking.html` (khách vãng lai) + `customer_booking.html` (khách đăng nhập).

## Yêu cầu
1. **Pre-select = current_day** — mặc định chọn sẵn ngày hôm nay và load slot khả dụng của hôm nay.
2. **Deactivate slot đã qua** — slot có giờ ≤ thời điểm hiện tại (trong ngày hôm nay) bị khóa.
3. **Disable nút Continue** — tắt nút Continue của Step 3 tới khi user chọn được 1 slot.

## Quyết định đã chốt
- **Nguồn giờ:** giờ **server (Helsinki)** làm chuẩn, **kèm chặn ở backend** — không chỉ ẩn ở frontend.
- **Phạm vi:** áp dụng **cả 2 trang** booking.

## Thay đổi

### Backend
| File | Thay đổi |
|------|----------|
| `app/services/booking_service.py` | Thêm `BookingService.ensure_slot_not_past(booking_date, start_time)` → raise `BookingValidatorError` nếu slot ≤ `now_helsinki()`. |
| `app/routes.py` — `create_customer_booking` | Gọi `ensure_slot_not_past(...)` ở đầu block `try` (tái dùng xử lý `BookingValidatorError` sẵn có). |
| `app/routes.py` — `create_public_booking` | Tương tự — chặn đặt slot đã qua ngay cả khi lách frontend. |
| `app/routes.py` — `check_available_slot` | Tính `now_hm` + `is_today`; thêm cờ `"disabled": is_today and time <= now_hm` vào slot ở **cả** nhánh "No Preference" lẫn nhánh chọn nhân viên. |

### Frontend (áp dụng cho cả `public_booking.html` + `customer_booking.html`)
1. **Pre-select hôm nay:** `selectedDate = todayDate`; sau `renderCalendar()` set `hiddenDate` + `updateDatetimeSummary()` + `tryLoadSlots()`.
2. **Deactivate slot đã qua:** `renderSlots` đọc `slot.disabled` → `btn.disabled = true` (tự ăn style `.slot-pill[disabled]` gạch ngang + không click sẵn có).
3. **Disable Continue:** `dtNextBtn = steps[2].querySelector('.bk-btn-next')` + hàm `syncContinueState()` (bật/tắt theo `hiddenTime.value`). Gọi khi: init (tắt), chọn slot (bật), đổi ngày & re-render slot (tắt + reset selection cho khớp trạng thái hiển thị).

### CSS
| File | Thay đổi |
|------|----------|
| `app/static/css/public/public_booking.css` (dùng chung 2 trang) | Thêm `.bk-btn-next:disabled { opacity:.55; cursor:not-allowed; }` |

## Kiểm tra
- `python -m py_compile app/routes.py app/services/booking_service.py` → **OK**.
- Chưa chạy verify end-to-end trên trình duyệt (đang chờ xác nhận).

## Ghi chú / ngoài phạm vi
- Trang **reschedule** dùng endpoint (`get_reschedule_available_slots`) + JS (`reschedule_calendar.js`) riêng → **không đụng tới**. Trang này hiện cũng **chưa** chặn slot đã qua trong ngày hôm nay. Cần báo nếu muốn áp dụng tương tự.
