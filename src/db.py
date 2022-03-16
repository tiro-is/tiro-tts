import os

from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy


def setup_db(app: Flask):
    db_username: str = os.environ.get("POSTGRESQL_USERNAME", "")
    db_password: str = os.environ.get("POSTGRESQL_PASSWORD", "")
    db_name: str = os.environ.get("POSTGRESQL_DATABASE", "")

    if not db_username or not db_password or not db_name:
        raise Exception("One or more database credentials are missing!")

    app.config[
        "SQLALCHEMY_DATABASE_URI"
    ] = f"postgresql://{db_username}:{db_password}@{db_name}"

    db: SQLAlchemy = SQLAlchemy(app)
    migrate: Migrate = Migrate(app, db)

    class User(db.Model):
        __tablename__ = "users"

        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String, nullable=False)
        email = db.Column(db.String, unique=True, nullable=False)
        created_at = db.Column(db.DateTime, nullable=False)
        updated_at = db.Column(db.DateTime, nullable=False)

        projects = db.relationship("Project", backref="user", lazy=True)

    class Project(db.Model):
        __tablename__ = "projects"

        id = db.Column(db.Integer, primary_key=True)
        user_id = db.Column(db.Integer, db.ForeignKey(User.id), nullable=False)
        name = db.Column(db.String, nullable=False)
        description = db.Column(db.String, nullable=True)
        created_at = db.Column(db.DateTime, nullable=False)
        updated_at = db.Column(db.DateTime, nullable=False)

        key = db.relationship("Key", backref="project", uselist=False, lazy=True)
        tts_requests = db.relationship("TTSRequest", backref="project", lazy=True)

    class Key(db.Model):
        __tablename__ = "keys"

        project_id = db.Column(db.Integer, db.ForeignKey(Project.id), primary_key=True)
        key = db.Column(db.String, nullable=False, unique=True)
        is_active = db.Column(db.Boolean, nullable=False, default=True)

    class TTSRequest(db.Model):
        __tablename__ = "tts_requests"

        id = db.Column(db.Integer, primary_key=True)
        project_id = db.Column(db.Integer, db.ForeignKey(Project.id), nullable=False)
        created_at = db.Column(db.DateTime, nullable=False)
        audio_duration = db.Column(db.Float, nullable=False, default=0.0)
