import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY")
    if not SECRET_KEY:
        raise RuntimeError("SECRET_KEY is not set. Add it to your .env file.")

    MAIL_SERVER = "smtp.gmail.com"
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = "dahacaree@gmail.com"
    MAIL_PASSWORD = "tedm cqsv gnkr gwmn"
    MAIL_DEFAULT_SENDER = "dahacaree@gmail.com"

    # Session security
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = False  # set True in production (HTTPS)
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)
