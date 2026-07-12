from flask import Flask, session
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
    """Chọn ngôn ngữ theo session (do route /set-language set). Fallback về 'fi'."""
    lang = session.get("lang")
    if lang in LANGUAGES:
        return lang
    return "fi"

def create_app():
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
    

    return app