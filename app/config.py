import os
class Config:
    SECRET_KEY = "callmemon2506"
    MAIL_SERVER = "smtp.gmail.com"
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = "dahacaree@gmail.com"
    MAIL_PASSWORD = "tedm cqsv gnkr gwmn"
    MAIL_DEFAULT_SENDER = "dahacaree@gmail.com"
    SECRET_KEY = os.environ.get("SECRET_KEY", "mon-dev-key-2506")