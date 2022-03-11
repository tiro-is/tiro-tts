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

        key = db.relationship("Key", backref="project", uselist=False, lazy=True)
        tts_requests = db.relationship("TTSRequest", backref="project", lazy=True)
