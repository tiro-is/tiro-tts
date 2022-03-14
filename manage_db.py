#!/usr/bin/env python

import argparse
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv

from src import init_app
from src.models.user import User


def seed(table: Literal["all", "users", "projects", "keys", "tts_requests"], overwrite: bool = False):
    if table == "all" or == "users":
        User.create(name="Smári Freyr Guðmundsson", email="smari@tiro.is")
        User.create(name="Róbert Kjaran", email="robert@tiro.is")
    if table == "all" or  table == "projects":
        pass
    if table == "all" or  table == "keys":
        pass
    if table == "all" or  table == "tts_requests":
        pass

def clear(table: Literal["all", "users", "projects", "keys", "tts_requests"]):
    pass

def route_action(
    action: Literal["seed", "clear"],
    table: Literal["all", "users", "projects", "keys", "tts_requests"],
    overwrite: bool = False,
) -> None:
    if action not in ["seed", "clear"] or table not in [
        "all",
        "users",
        "projects",
        "keys",
        "tts_requests",
    ]:
        raise Exception("Illegal argument!")

    load_dotenv(Path(".env.local"))
    app = init_app()
    with app.app_context():
        if action == "seed":
            seed(table, overwrite)
        elif action == "clear":
            clear(table)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="This script is used to interact with, test and develop a local instance of a tiro-tts database."
    )

    parser.add_argument(
        "--action",
        "-a",
        choices=["seed", "clear"],
        dest="action",
        help="Possible actions to perform on the database.",
        required=True,
    )
    parser.add_argument(
        "--table",
        "-t",
        choices=["all", "users", "projects", "keys", "tts_requests"],
        dest="table",
        help="Database table to apply the action on.",
        required=True,
    )
    parser.add_argument(
        "--overwrite",
        "-o",
        dest="overwrite",
        help="A boolean: If your action involves data insertion (seed), do you wish to overwrite the existing data? If not, data will be appended to existing data (default behavior).",
        default=False,
        required=False,
    )

    args = parser.parse_args()
    route_action(
        action=args.action,
        table=args.table,
        overwrite=args.overwrite,
    )
