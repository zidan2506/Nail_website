from flask import Flask
from .config import Config
from flask_wtf.csrf import CSRFProtect
from authlib.integrations.flask_client import OAuth
from app.template_filters import register_filters

csrf = CSRFProtect()
oauth = OAuth()

def create_app():
    app = Flask(__name__)

    app.config.from_object(Config)

    csrf.init_app(app)
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