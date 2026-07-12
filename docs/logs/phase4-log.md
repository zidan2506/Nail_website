# Phase 4 — Work Log

**Ngày:** 2026-07-12 · **Phase:** 4 (`print()` → `logging`) · **Trạng thái:** ✅ Hoàn tất (chờ commit)

Chuyển `print()` sang `logging` để có timestamp/level và bắt được trên production (journald của systemd).

---

## 1. Cấu hình logging 1 lần (`app/__init__.py`)

Trong `create_app()`:
```python
logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
```
- Log ra stderr → journald bắt.
- Mặc định INFO; set `LOG_LEVEL=DEBUG` để bật log chi tiết tầng db.

## 2. Nhóm 1 — log lỗi/cảnh báo thật (`routes.py` 8 + `payment_service.py` 5)

Tất cả là `[payment] ...` trong khối `except` hoặc điều kiện lỗi. Mỗi file thêm `logger = logging.getLogger(__name__)`.
- Trong `except`: `logger.exception(...)` — tự kèm traceback.
- Cảnh báo config/nghiệp vụ (tier thiếu price, không map được tier, slot bị chiếm...): `logger.warning(...)`.
- Dùng lazy formatting `%s` thay vì f-string. Giữ prefix `[payment]` để dễ grep.

> Ghi chú: các `except Exception as e:` giờ có `e` không còn dùng (logger.exception tự lấy traceback). Để nguyên — `except Exception as e:` xuất hiện rất nhiều chỗ trong routes.py, sửa hàng loạt dễ nhầm, và `e` thừa là vô hại.

## 3. Nhóm 2 — debug noise (`db.py` 16)

Các print kiểu "Create new booking done!", "Verify customer...", "Updating status success!" → `logger.debug(...)`. Im lặng ở INFO (không spam production), bật lại bằng `LOG_LEVEL=DEBUG` khi cần.
- 1 chỗ đặc biệt: `return print(...)` ở `update_status` → đổi thành `logger.debug(...)` (bỏ `return`, hàm vẫn trả None như cũ).

## 4. Nhóm 3 — CLI scripts: GIỮ NGUYÊN `print()`

`reset_db.py`, `test_data.py`, `setup_stripe_prices.py` — chạy tay ở terminal, `print()` là output đúng chỗ cho người xem. Không đụng (Karpathy: đừng sửa cái không hỏng).

## 5. `.env.example`

Thêm `LOG_LEVEL=INFO` + chú thích.

## 6. Verification

- Không còn `print()` thật trong routes.py / payment_service.py / db.py / __init__.py (chỉ còn match giả `register_blueprint`).
- CLI scripts vẫn giữ print (1/1/2).
- `create_app()` OK, 111 routes.
- `logger.warning` hiện đúng format `... WARNING app.routes: ...`; `logger.debug` bị ẩn ở INFO mặc định.

---

## Kết quả git (Phase 4 chờ commit)

```
M  app/__init__.py                  ← logging config
M  app/routes.py                    ← 8 [payment] logs
M  app/services/payment_service.py  ← 5 [payment] logs + logger
M  app/database/db.py               ← 16 debug logs
M  .env.example                     ← LOG_LEVEL
?? docs/logs/phase4-log.md
```
