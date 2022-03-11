#!/usr/bin/env python

from dotenv import load_dotenv
from pathlib import Path

from src import init_app
from src.models.user import User

if __name__ == "__main__":
    load_dotenv(Path(".env.local"))
    app = init_app()
    with app.app_context():
        User.create(
            name="Smári Freyr Guðmundsson",
            email="smari@tiro.is"
        )
        User.create(
            name="Róbert Kjaran",
            email="robert@tiro.is"
        )
        