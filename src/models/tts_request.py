from src import db
from src.models.project import Project

class TTSRequest(db.Model):
        __tablename__ = "tts_requests"

        id = db.Column(db.Integer, primary_key=True)
        project_id = db.Column(db.Integer, db.ForeignKey(Project.id), nullable=False)
        created_at = db.Column(db.DateTime, nullable=False)
        audio_duration = db.Column(db.Float, nullable=False, default=0.0)
