# Copyright 2022 Tiro ehf.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
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
