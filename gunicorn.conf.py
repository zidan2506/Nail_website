import os

# nginx reverse-proxy vào đây (không expose ra ngoài)
bind = os.environ.get("GUNICORN_BIND", "127.0.0.1:8000")
# SQLite ghi tuần tự -> giữ số worker vừa phải để tránh "database is locked"
workers = int(os.environ.get("GUNICORN_WORKERS", "3"))
timeout = 60
accesslog = "-"  # stdout -> journald (systemd) bắt log
errorlog = "-"
