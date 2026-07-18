import html
import logging
import re
import secrets
import smtplib
from email.message import EmailMessage
from flask import current_app
from flask_babel import gettext as _
from app.utils.helpers import mask_email

logger = logging.getLogger(__name__)

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _render_html(body: str) -> str:
    """Boc noi dung plain-text thanh mot email HTML co thuong hieu Daha Care."""
    safe_body = html.escape(body).replace("\n", "<br>")
    return (
        '<div style="margin:0;padding:24px;background:#f4f4f5;">'
        '<div style="max-width:560px;margin:0 auto;font-family:Arial,Helvetica,sans-serif;color:#1f2937;">'
        '<div style="background:#ffffff;border-radius:12px;padding:32px;">'
        '<h1 style="margin:0 0 16px;font-size:20px;color:#111827;">Daha Care</h1>'
        f'<div style="font-size:15px;line-height:1.6;">{safe_body}</div>'
        '</div>'
        '<p style="text-align:center;font-size:12px;color:#9ca3af;margin-top:16px;">© Daha Care</p>'
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

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = current_app.config["MAIL_DEFAULT_SENDER"]
    msg["To"] = to_email
    msg.set_content(body)
    msg.add_alternative(_render_html(body), subtype="html")

    try:
        with smtplib.SMTP(
            current_app.config["MAIL_SERVER"],
            current_app.config["MAIL_PORT"],
            timeout=10,
        ) as server:
            if current_app.config.get("MAIL_USE_TLS", False):
                server.starttls()
            server.login(
                current_app.config["MAIL_USERNAME"],
                current_app.config["MAIL_PASSWORD"]
            )
            server.send_message(msg)
        logger.debug("[email] da gui toi %s", mask_email(to_email))
    except (smtplib.SMTPException, OSError) as e:
        logger.warning("[email] gui that bai toi %s: %s", mask_email(to_email), e)
        raise EmailSendError(str(e)) from e


def generate_verification_code() -> str:
    return f"{secrets.randbelow(1000000):06d}"


def send_verification_email(to_email: str, verification_code: str, verification_type: str = "booking") -> None:
    if verification_type == "register":
        subject = _("Verify your email – Daha Care")
        body = _(
            "Hello,\n\n"
            "Your verification code is: %(code)s\n\n"
            "Please enter this code to confirm your email address and complete your registration.\n\n"
            "If you did not create an account with Daha Care, please ignore this email.\n"
        ) % {"code": verification_code}
    elif verification_type == "password_change":
        subject = _("Password Change Request – Daha Care")
        body = _(
            "Hello,\n\n"
            "Your verification code is: %(code)s\n\n"
            "Please enter this code to confirm your password change request.\n\n"
            "If you did not request this, please ignore this email and your password will remain unchanged.\n"
        ) % {"code": verification_code}
    elif verification_type == "email_change":
        subject = _("Email Change Request – Daha Care")
        body = _(
            "Hello,\n\n"
            "Your verification code is: %(code)s\n\n"
            "Please enter this code to confirm your email address change request.\n\n"
            "If you did not request this, please ignore this email and your email address will remain unchanged.\n"
        ) % {"code": verification_code}
    elif verification_type == "forgot_password":
        subject = _("Reset Your Password – Daha Care")
        body = _(
            "Hello,\n\n"
            "Your password reset code is: %(code)s\n\n"
            "Please enter this code to reset your password. This code expires in 10 minutes.\n\n"
            "If you did not request a password reset, please ignore this email.\n"
        ) % {"code": verification_code}
    else:
        subject = _("Your Booking Verification Code – Daha Care")
        body = _(
            "Hello,\n\n"
            "Your verification code is: %(code)s\n\n"
            "Please enter this code on the verification page to confirm your booking.\n\n"
            "If you did not request this, please ignore this email.\n"
        ) % {"code": verification_code}
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
    subject = _("Your booking request has been received")
    body = _(
        "Hi %(name)s,\n\n"
        "Thank you for your booking.\n\n"
        "We have received your booking request and it is currently pending confirmation.\n\n"
        "Booking details:\n"
        "- Service: %(service)s\n"
        "- Staff: %(staff)s\n"
        "- Date: %(date)s\n"
        "- Time: %(start)s - %(end)s\n\n"
        "We will contact you again once your booking has been confirmed.\n\n"
        "Best regards,\n"
        "Dahacare\n"
    ) % {
        "name": customer_name,
        "service": service_name,
        "staff": staff_name,
        "date": booking_date,
        "start": start_time,
        "end": end_time,
    }
    send_email(subject, body, to_email)
