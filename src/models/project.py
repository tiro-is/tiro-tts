from datetime import datetime

from src import db
from src.models.user import User


class Project(db.Model):
    __tablename__ = "projects"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey(User.id), nullable=False)
    name = db.Column(db.String, nullable=False)
    description = db.Column(db.String, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False)
    updated_at = db.Column(db.DateTime, nullable=False)

    key = db.relationship(
        "Key",
        backref="project",
        uselist=False,
        lazy=True,
        cascade="all, delete, delete-orphan",
    )
    tts_requests = db.relationship(
        "TTSRequest", backref="project", lazy=True, cascade="all, delete, delete-orphan"
    )

    @staticmethod
    def create(user_id: int, name: str, description: str):
        """Adds a new entry to the table."""
        db.session.add(
            Project(
                user_id=user_id,
                name=name,
                description=description,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
        )
        db.session.commit()

    @staticmethod
    def erase():
        """Erases all table data."""
        db.session.query(Project).delete()
        db.session.commit()
