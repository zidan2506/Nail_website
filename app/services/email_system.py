import html
import logging
import re
import secrets
import requests
from flask import current_app
from app.business import BUSINESS, txt
from app.utils.helpers import mask_email

logger = logging.getLogger(__name__)

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _render_html(body: str) -> str:
    """Boc noi dung plain-text thanh mot email HTML co thuong hieu cua tiem."""
    safe_body = html.escape(body).replace("\n", "<br>")
    brand = html.escape(BUSINESS["brand_name"])
    return (
        '<div style="margin:0;padding:24px;background:#f4f4f5;">'
        '<div style="max-width:560px;margin:0 auto;font-family:Arial,Helvetica,sans-serif;color:#1f2937;">'
        '<div style="background:#ffffff;border-radius:12px;padding:32px;">'
        f'<h1 style="margin:0 0 16px;font-size:20px;color:#111827;">{brand}</h1>'
        f'<div style="font-size:15px;line-height:1.6;">{safe_body}</div>'
        '</div>'
        f'<p style="text-align:center;font-size:12px;color:#9ca3af;margin-top:16px;">© {brand}</p>'
        '</div></div>'
    )


class EmailSendError(Exception):
    """Gui email that bai: dia chi nhan sai dinh dang hoac loi SMTP."""
    pass


def is_valid_email(email: str) -> bool:
    return bool(email and _EMAIL_RE.match(email))


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
        logger.warning(
            "[email] Resend tu choi toi %s: %s %s",
            mask_email(to_email), resp.status_code, resp.text[:300],
        )
        raise EmailSendError(f"Resend {resp.status_code}")

    logger.debug("[email] da gui toi %s", mask_email(to_email))


def generate_verification_code() -> str:
    return f"{secrets.randbelow(1000000):06d}"


# verification_type -> tien to khoa trong CONTENT. Type la nao khac -> "booking".
_VERIFY_CONTENT_KEYS = {
    "register": "verify_register",
    "password_change": "verify_password_change",
    "email_change": "verify_email_change",
    "forgot_password": "verify_forgot_password",
}


def send_verification_email(to_email: str, verification_code: str, verification_type: str = "booking") -> None:
    key = _VERIFY_CONTENT_KEYS.get(verification_type, "verify_booking")
    brand = BUSINESS["brand_name"]
    subject = txt(f"email.{key}_subject", brand=brand)
    body = txt(f"email.{key}_body", code=verification_code, brand=brand)
    send_email(subject, body, to_email)


def send_thank_you_email(
    to_email: str,
    customer_name: str,
    service_name: str,
    staff_name: str,
    booking_date: str,
    start_time: str,
    end_time: str,
) -> None:
    brand = BUSINESS["brand_name"]
    subject = txt("email.thank_you_subject", brand=brand)
    body = txt(
        "email.thank_you_body",
        name=customer_name,
        service=service_name,
        staff=staff_name,
        date=booking_date,
        start=start_time,
        end=end_time,
        brand=brand,
    )
    send_email(subject, body, to_email)
