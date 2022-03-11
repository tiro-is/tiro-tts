from src import db
from src.models.project import Project

class Key(db.Model):
        __tablename__ = "keys"

        project_id = db.Column(db.Integer, db.ForeignKey(Project.id), primary_key=True)
        key = db.Column(db.String, nullable=False, unique=True)
        is_active = db.Column(db.Boolean, nullable=False, default=True)
