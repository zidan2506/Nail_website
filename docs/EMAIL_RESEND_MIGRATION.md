# Chuyển gửi email: Gmail SMTP → Resend API

## 1. Bối cảnh / Vấn đề

Sau khi deploy lên server production, chức năng **Verify Email** báo lỗi:

```
Flash: "Could not send verification email. Please try again."
```

Log server (`journalctl -u nail-app`) cho thấy nguyên nhân thật:

```
WARNING app.services.email_system: [email] gui that bai toi i***@gmail.com: timed out
```

**Chẩn đoán:**
- `timed out` = không kết nối được tới `smtp.gmail.com:587` (không phải sai mật khẩu — nếu sai sẽ là `SMTPAuthenticationError 535`).
- **Không liên quan** HTTPS/domain (đó là inbound; gửi mail là outbound).
- Test cổng trên server: **cả 587, 465, 25 đều bị chặn** → host chặn **toàn bộ SMTP outbound** (chính sách chống spam phổ biến của VPS).

**Kết luận:** Không dùng SMTP được nữa → chuyển sang **email API qua HTTPS (cổng 443, không bị chặn)**. Provider: **Resend**.

---

## 2. Giải pháp

Thay cơ chế gửi trong `send_email()` từ `smtplib` (SMTP) sang **HTTP POST tới Resend API** bằng thư viện `requests` (đã có sẵn trong `requirements.txt`, không cần cài thêm). **Giữ nguyên toàn bộ** phần validate, render HTML, exception, và mọi hàm gọi (`send_verification_email`, ...).

---

## 3. Các file thay đổi

### 3.1. `app/services/email_system.py`

**Imports:** bỏ `smtplib` + `from email.message import EmailMessage`, thêm `requests`.

**`send_email()`** — trước (SMTP):

```python
with smtplib.SMTP(current_app.config["MAIL_SERVER"],
                  current_app.config["MAIL_PORT"], timeout=10) as server:
    if current_app.config.get("MAIL_USE_TLS", False):
        server.starttls()
    server.login(current_app.config["MAIL_USERNAME"],
                 current_app.config["MAIL_PASSWORD"])
    server.send_message(msg)
```

**sau (Resend API / HTTPS):**

```python
def send_email(subject: str, body: str, to_email: str) -> None:
    if not is_valid_email(to_email):
        logger.warning("[email] dia chi nhan khong hop le: %s", mask_email(to_email))
        raise EmailSendError("Invalid recipient email")

    # Gui qua Resend API (HTTPS/443) thay vi SMTP — host chan cong SMTP outbound.
    try:
        resp = requests.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {current_app.config['RESEND_API_KEY']}",
                "Content-Type": "application/json",
            },
            json={
                "from": current_app.config["MAIL_DEFAULT_SENDER"],
                "to": [to_email],
                "subject": subject,
                "text": body,
                "html": _render_html(body),
            },
            timeout=10,
        )
    except requests.RequestException as e:
        logger.warning("[email] gui that bai toi %s: %s", mask_email(to_email), e)
        raise EmailSendError(str(e)) from e

    if resp.status_code >= 400:
        logger.warning("[email] Resend tu choi toi %s: %s %s",
                       mask_email(to_email), resp.status_code, resp.text[:300])
        raise EmailSendError(f"Resend {resp.status_code}")

    logger.debug("[email] da gui toi %s", mask_email(to_email))
```

### 3.2. `app/config.py`

Bỏ config SMTP Gmail (`MAIL_SERVER/PORT/USE_TLS/USERNAME/PASSWORD`), thêm `RESEND_API_KEY`:

```python
# Email gửi qua Resend API (HTTPS/443) — host chặn cổng SMTP outbound.
RESEND_API_KEY = os.environ.get("RESEND_API_KEY")
if not RESEND_API_KEY:
    raise RuntimeError("RESEND_API_KEY is not set. Add it to your .env file.")
# 'from': phải thuộc domain đã verify trên Resend, vd "Misa Nails <noreply@dahatrans.com>"
MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER")
if not MAIL_DEFAULT_SENDER:
    raise RuntimeError("MAIL_DEFAULT_SENDER is not set (địa chỉ thuộc domain đã verify trên Resend).")
```

### 3.3. `.env.example`

```diff
- MAIL_USERNAME=your-gmail@gmail.com
- MAIL_PASSWORD=your-gmail-app-password
- MAIL_DEFAULT_SENDER=your-gmail@gmail.com
+ # Email gửi qua Resend API (https://resend.com) — cổng HTTPS, không bị host chặn như SMTP
+ RESEND_API_KEY=re_your_api_key
+ # 'from' phải thuộc domain đã verify trên Resend
+ MAIL_DEFAULT_SENDER=Misa Nails <noreply@your-domain.com>
```

---

## 4. Việc cần làm để chạy (thủ công)

1. Đăng ký **resend.com** → **API Keys** → tạo key (`re_...`).
2. **Verify domain** (`dahatrans.com`) trong Resend → **Domains → Add Domain** → thêm bản ghi DNS (SPF/DKIM) họ đưa → chờ verify.
3. Sửa `.env` production (`/var/www/nail-app/.env`):
   ```
   RESEND_API_KEY=re_xxxxx
   MAIL_DEFAULT_SENDER=Misa Nails <noreply@dahatrans.com>
   ```
   (Xoá được 2 dòng `MAIL_USERNAME`/`MAIL_PASSWORD` cũ.)
4. Deploy code mới lên server → `sudo systemctl restart nail-app`.

> **Test nhanh trước khi verify domain:** đặt tạm `MAIL_DEFAULT_SENDER=onboarding@resend.dev` và chỉ gửi tới **email của chính chủ tài khoản Resend** (Resend cho phép khi chưa verify domain).

> **Local dev:** cũng phải có `RESEND_API_KEY` trong `.env`, nếu không app crash lúc khởi động (config bắt buộc).

---

## 5. Troubleshooting

Xem log: `sudo journalctl -u nail-app -f` rồi tái hiện gửi email.

| Log `Resend tu choi ...` | Nguyên nhân | Cách xử lý |
|---|---|---|
| `401` | Sai/thiếu `RESEND_API_KEY` | Kiểm tra lại API key trong `.env` |
| `403` | Domain (`from`) chưa verify | Verify domain, hoặc dùng tạm `onboarding@resend.dev` |
| `422` | `from`/`to` sai định dạng | Kiểm tra `MAIL_DEFAULT_SENDER` đúng dạng `Name <email@domain>` |
| `429` | Vượt giới hạn gửi (rate limit) | Chờ, hoặc nâng gói Resend |

---

## 6. Ghi chú

- Cổng **443 (HTTPS)** không bao giờ bị host chặn → cách gửi này ổn định hơn SMTP trên server.
- Free tier Resend: ~3.000 email/tháng — dư cho một tiệm nail.
- Toàn bộ luồng nghiệp vụ (đăng ký, đổi email, quên mật khẩu, xác nhận booking...) **không đổi** — chỉ thay lớp vận chuyển email bên dưới.
