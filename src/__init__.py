import os

from apispec import APISpec, BasePlugin
from apispec.ext.marshmallow import MarshmallowPlugin
from flask import Flask
from flask_cors import CORS
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from werkzeug.middleware.proxy_fix import ProxyFix

from src.config import EnvvarConfig
from src.middleware import RequestIdWrapper

db: SQLAlchemy = SQLAlchemy()


class DisableOptionsOperationPlugin(BasePlugin):
    # See https://github.com/jmcarp/flask-apispec/issues/155#issuecomment-562542538
    def operation_helper(self, operations, **kwargs):
        # flask-apispec auto generates an options operation, which cannot handled by apispec.
        # apispec.exceptions.DuplicateParameterError: Duplicate parameter with name body and location body
        # => remove
        operations.pop("options", None)


def setup_db(app: Flask):
    db_username: str = os.environ.get("POSTGRESQL_USERNAME", "")
    db_password: str = os.environ.get("POSTGRESQL_PASSWORD", "")
    db_name: str = os.environ.get("POSTGRESQL_DATABASE", "")

    if not db_username or not db_password or not db_name:
        raise Exception("One or more database credentials are missing!")

    app.config[
        "SQLALCHEMY_DATABASE_URI"
    ] = f"postgresql://{db_username}:{db_password}@{db_name}"

    db.init_app(app)
    migrate: Migrate = Migrate(app, db)


def init_app():
    app = Flask(__name__)
    app.config["JSON_AS_ASCII"] = False
    app.config["APISPEC_SWAGGER_URL"] = "/v0/swagger.json"
    app.config["APISPEC_SWAGGER_UI_URL"] = None
    app.config.from_object(EnvvarConfig)

    # Fix access to client remote_addr when running behind proxy
    setattr(app, "wsgi_app", ProxyFix(app.wsgi_app))

    app.config["JSON_AS_ASCII"] = False
    app.config["MAX_CONTENT_LENGTH"] = 1 * 1024 * 1024

    cors = CORS(app)

    app.config["APISPEC_SPEC"] = APISpec(
        title="TTS",
        version="v0",
        host=app.config["HOST"],
        openapi_version="2.0",
        plugins=[MarshmallowPlugin(), DisableOptionsOperationPlugin()],
        tags=[{"name": "speech", "description": "Synthesize speech from input text"}],
    )

    if not app.config["AUTH_DISABLED"]:
        setup_db(app)

    request_id = RequestIdWrapper(app)

    with app.app_context():
        if not app.config["AUTH_DISABLED"]:
            from src.models.user import User  # noqa:E402 isort:skip
            from src.models.project import Project  # noqa:E402 isort:skip
            from src.models.key import Key  # noqa:E402 isort:skip
            from src.models.tts_request import TTSRequest  # noqa:E402 isort:skip
            # Create tables if they don't exist
            db.create_all()

        import src.app

        return app
