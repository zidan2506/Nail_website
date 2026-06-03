from flask import Flask
from .config import Config
from flask_wtf.csrf import CSRFProtect
from app.template_filters import register_filters

csrf = CSRFProtect()

def create_app():
    app = Flask(__name__)

    app.config.from_object(Config)

    csrf.init_app(app)
    register_filters(app)

    from app.routes import main
    app.register_blueprint(main)
    

    return app