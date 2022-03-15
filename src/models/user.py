from datetime import datetime
from src import db

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    email = db.Column(db.String, unique=True, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False)
    updated_at = db.Column(db.DateTime, nullable=False)

    projects = db.relationship("Project", backref="user", lazy=True,
                                cascade="all, delete, delete-orphan")

    @staticmethod
    def create(name: str, email: str):
        db.session.add(
            User(
                name=name,
                email=email,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
        )
        db.session.commit()
