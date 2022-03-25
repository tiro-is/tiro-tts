from datetime import datetime

from src import db
from src.models.project import Project


class TTSRequest(db.Model):
    __tablename__ = "tts_requests"

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey(Project.id), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False)
    audio_duration = db.Column(db.Float, nullable=False, default=0.0)

    @staticmethod
    def create(project_id: int, audio_duration: float):
        """Adds a new entry to the table."""
        db.session.add(
            TTSRequest(
                project_id=project_id,
                created_at=datetime.utcnow(),
                audio_duration=audio_duration,
            )
        )
        db.session.commit()

    @staticmethod
    def erase():
        """Erases all table data."""
        db.session.query(TTSRequest).delete()
        db.session.commit()
