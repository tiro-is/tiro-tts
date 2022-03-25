from secrets import token_urlsafe

from src import db
from src.models.project import Project


class Key(db.Model):
    __tablename__ = "keys"

    project_id = db.Column(db.Integer, db.ForeignKey(Project.id), primary_key=True)
    key = db.Column(db.String, nullable=False, unique=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    @staticmethod
    def create(project_id: int):
        """Adds a new entry to the table."""
        db.session.add(
            Key(
                project_id=project_id,
                key=token_urlsafe(64),
                is_active=True,
            )
        )
        db.session.commit()

    @staticmethod
    def erase():
        """Erases all table data."""
        db.session.query(Key).delete()
        db.session.commit()
