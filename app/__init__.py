import logging
import os
from flask import Flask, session, flash, redirect, request, url_for
from werkzeug.middleware.proxy_fix import ProxyFix
from .config import Config
from flask_wtf.csrf import CSRFProtect
from flask_babel import Babel
from authlib.integrations.flask_client import OAuth
from app.template_filters import register_filters

csrf = CSRFProtect()
oauth = OAuth()
babel = Babel()

# Ngôn ngữ hỗ trợ. Default = 'fi'
LANGUAGES = ["fi", "en", "vi"]


def select_locale():
    """Chọn ngôn ngữ theo session (do route /set-language set). Fallback về 'fi'.

    Riêng /admin luôn là 'vi': toàn bộ template admin viết cứng tiếng Việt, nên
    nếu để flash message chạy theo bộ chọn ngôn ngữ của khách thì admin sẽ thấy
    thông báo tiếng Phần Lan xen giữa giao diện tiếng Việt."""
    if request.path.startswith("/admin"):
        return "vi"
    lang = session.get("lang")
    if lang in LANGUAGES:
        return lang
    return "fi"

def create_app():
    # Log ra stderr (journald của systemd bắt). Mặc định INFO; set LOG_LEVEL=DEBUG
    # để bật các log chi tiết ở tầng db.
    logging.basicConfig(
        level=os.environ.get("LOG_LEVEL", "INFO").upper(),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    app = Flask(__name__)
    # Sau nginx: tin X-Forwarded-Proto/Host để url_for(_external=True) sinh URL
    # https đúng (Google OAuth callback + Stripe redirect). x_*=1 = 1 proxy (nginx).
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    app.config.from_object(Config)

    app.config["BABEL_DEFAULT_LOCALE"] = "fi"

    csrf.init_app(app)
    babel.init_app(app, locale_selector=select_locale)
    oauth.init_app(app)
    oauth.register(
        name="google",
        client_id=app.config["GOOGLE_CLIENT_ID"],
        client_secret=app.config["GOOGLE_CLIENT_SECRET"],
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={"scope": "openid email profile"},
    )
    register_filters(app)

    from app.routes import main
    app.register_blueprint(main)

    # Body vượt MAX_CONTENT_LENGTH -> Werkzeug ném 413 trước khi vào view, nên
    # phải bắt ở đây mới báo được cho admin thay vì trả trang lỗi trống.
    @app.errorhandler(413)
    def _too_large(_e):
        flash("File gửi lên quá lớn. Video tối đa 300MB, ảnh tối đa 10MB.", "error")
        return redirect(request.referrer or url_for("main.home")), 302

    # Thread transcode video là daemon nên chết theo process. Job nào còn
    # 'processing' lúc này chắc chắn không còn ai xử lý -> dọn để khỏi kẹt.
    from app.database.db import reset_stuck_video_jobs
    from app.routes import _cleanup_stale_temp
    try:
        reset_stuck_video_jobs()
    except Exception:
        # DB chưa init (lần chạy đầu / CI) thì bỏ qua, không chặn app khởi động
        logging.getLogger(__name__).warning("Bỏ qua dọn job video treo: DB chưa sẵn sàng")
    try:
        _cleanup_stale_temp()
    except Exception:
        logging.getLogger(__name__).warning("Bỏ qua dọn file video tạm")

    return app