import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY")
    if not SECRET_KEY:
        raise RuntimeError("SECRET_KEY is not set. Add it to your .env file.")

    # Google OAuth
    GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET")

    # Stripe
    STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY")
    STRIPE_PUBLISHABLE_KEY = os.environ.get("STRIPE_PUBLISHABLE_KEY")
    STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET")

    # Email gửi qua Resend API (HTTPS/443) — host chặn cổng SMTP outbound.
    RESEND_API_KEY = os.environ.get("RESEND_API_KEY")
    if not RESEND_API_KEY:
        raise RuntimeError("RESEND_API_KEY is not set. Add it to your .env file.")
    # 'from': phải thuộc domain đã verify trên Resend, vd "Misa Nails <noreply@dahatrans.com>"
    MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER")
    if not MAIL_DEFAULT_SENDER:
        raise RuntimeError("MAIL_DEFAULT_SENDER is not set (địa chỉ thuộc domain đã verify trên Resend).")

    # Trần dung lượng request. Không có nó thì Werkzeug ghi TOÀN BỘ body xuống đĩa
    # rồi handler mới kiểm tra được kích thước — gửi 5GB là server ghi đủ 5GB.
    # 310MB = 300MB (trần video trong routes.py) + chỗ dư cho phần multipart khác.
    # Phải >= client_max_body_size của nginx, nếu không nginx cho qua mà Flask chặn.
    MAX_CONTENT_LENGTH = 310 * 1024 * 1024

    # Session security
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    # True ở production (HTTPS). Để false ở local vì dev chạy http://localhost.
    SESSION_COOKIE_SECURE = os.environ.get("SESSION_COOKIE_SECURE", "false").lower() == "true"
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)
