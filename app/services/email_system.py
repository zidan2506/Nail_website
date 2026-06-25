import secrets
import smtplib
from email.message import EmailMessage
from flask import current_app


def send_email(subject: str, body: str, to_email: str) -> None:
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = current_app.config["MAIL_DEFAULT_SENDER"]
    msg["To"] = to_email
    msg.set_content(body)

    with smtplib.SMTP(
        current_app.config["MAIL_SERVER"],
        current_app.config["MAIL_PORT"]
    ) as server:
        if current_app.config.get("MAIL_USE_TLS", False):
            server.starttls()
        server.login(
            current_app.config["MAIL_USERNAME"],
            current_app.config["MAIL_PASSWORD"]
        )
        server.send_message(msg)


def generate_verification_code() -> str:
    return f"{secrets.randbelow(1000000):06d}"


def send_verification_email(to_email: str, verification_code: str, verification_type: str = "booking") -> None:
    if verification_type == "register":
        subject = "Verify your email – Daha Care"
        body = f"""Hello,

Your verification code is: {verification_code}

Please enter this code to confirm your email address and complete your registration.

If you did not create an account with Daha Care, please ignore this email.
"""
    elif verification_type == "password_change":
        subject = "Password Change Request – Daha Care"
        body = f"""Hello,

Your verification code is: {verification_code}

Please enter this code to confirm your password change request.

If you did not request this, please ignore this email and your password will remain unchanged.
"""
    elif verification_type == "email_change":
        subject = "Email Change Request – Daha Care"
        body = f"""Hello,

Your verification code is: {verification_code}

Please enter this code to confirm your email address change request.

If you did not request this, please ignore this email and your email address will remain unchanged.
"""
    elif verification_type == "forgot_password":
        subject = "Reset Your Password – Daha Care"
        body = f"""Hello,

Your password reset code is: {verification_code}

Please enter this code to reset your password. This code expires in 10 minutes.

If you did not request a password reset, please ignore this email.
"""
    else:
        subject = "Your Booking Verification Code – Daha Care"
        body = f"""Hello,

Your verification code is: {verification_code}

Please enter this code on the verification page to confirm your booking.

If you did not request this, please ignore this email.
"""
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
    subject = "Your booking request has been received"
    body = f"""Hi {customer_name},

Thank you for your booking.

We have received your booking request and it is currently pending confirmation.

Booking details:
- Service: {service_name}
- Staff: {staff_name}
- Date: {booking_date}
- Time: {start_time} - {end_time}

We will contact you again once your booking has been confirmed.

Best regards,
Dahacare
"""
    send_email(subject, body, to_email)
