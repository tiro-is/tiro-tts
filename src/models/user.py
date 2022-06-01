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
from datetime import datetime

from src import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    email = db.Column(db.String, unique=True, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False)
    updated_at = db.Column(db.DateTime, nullable=False)

    projects = db.relationship(
        "Project", backref="user", lazy=True, cascade="all, delete, delete-orphan"
    )

    @staticmethod
    def create(name: str, email: str):
        """Adds a new entry to the table."""
        db.session.add(
            User(
                name=name,
                email=email,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
        )
        db.session.commit()

    @staticmethod
    def erase():
        """Erases all table data."""
        db.session.query(User).delete()
        db.session.commit()
