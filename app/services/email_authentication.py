import secrets
import hashlib
import smtplib
from email.message import EmailMessage
from flask import current_app

def generate_random_digits():
    return f"{secrets.randbelow(1000000):06d}"

def generate_verification_code() -> str:
    code = generate_random_digits()
    print(f"Code: {code}")
    return code

def send_email(subject,body, to_email):
    
    
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = current_app.config["MAIL_DEFAULT_SENDER"]   
    msg["to"] = to_email
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

def send_verification_email(to_email: str , verification_code: str) -> None:
    subject = "Your Booking Verification Code"
    body = f"""
Hello,

Your verification code is: {verification_code}

Please enter this code on the verification page to confirm your booking.

If you did not request this, please ignore this email.
""" 
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = current_app.config["MAIL_DEFAULT_SENDER"]   
    msg["to"] = to_email
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

# send_verification_email("iamduyahihi@gmail.com","1234")

def send_thank_you_email(to_email: str, customer_name, service_name, staff_name, booking_date, start_time, end_time,) -> None:
    subject = "Your booking request has been received"
    body = f"""
Hi {customer_name},

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
    # send_email(subject, body, to_email)
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = current_app.config["MAIL_DEFAULT_SENDER"]   
    msg["to"] = to_email
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
        
    return print("Send thank you email successfully")
    