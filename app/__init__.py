from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap
from config import config
from .match import matcher

bootstrap = Bootstrap()
db = SQLAlchemy()

def create_app(config_name):
    # a new one
    app = Flask(__name__)
    # with the proper config
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    db.init_app(app)
    bootstrap.init_app(app)

    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    return app
