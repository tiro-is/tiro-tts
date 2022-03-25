#!/usr/bin/env python

import argparse
from pathlib import Path
from types import LambdaType
from typing import Literal

from flask_migrate import migrate, upgrade, downgrade, history
from dotenv import load_dotenv
from random import uniform
from intervals import IllegalArgument
from sqlalchemy.exc import IntegrityError

from src import init_app, db
from src.models.key import Key
from src.models.user import User
from src.models.project import Project
from src.models.tts_request import TTSRequest

force: bool = False
overwrite: bool = False

def seed(table: Literal["all", "users", "projects", "keys", "tts_requests"]) -> None:
    """Populates database table specified by input parameter. A single table or all of them."""

    try:
        if overwrite:
            if not clear(table):
                return

        if table == "all" or table == "users":
            User.create(name="Smári Freyr Guðmundsson", email="smari@tiro.is")
            User.create(name="Róbert Kjaran", email="robert@tiro.is")
            User.create(name="Eydís Huld Magnúsdóttir", email="eydis@tiro.is")
            User.create(name="Júlíus Reynald Björnsson", email="julius@tiro.is")
            User.create(name="David Erik Mollberg", email="david@tiro.is")
        if table == "all" or table == "projects":
            Project.create(
                user_id=db.session.query(User.id).filter(User.name == "Róbert Kjaran"),
                name="Mbl.is",
                description="Morgunblaðið er með afspilunartakka fyrir hverja frétt í viðmótinu hjá sér.",
            )
            Project.create(
                user_id=db.session.query(User.id).filter(User.name == "Róbert Kjaran"),
                name="Visir.is",
                description="Vísir.is er með afspilunartakka fyrir hverja frétt í viðmótinu hjá sér.",
            )
            Project.create(
                user_id=db.session.query(User.id).filter(
                    User.name == "Smári Freyr Guðmundsson"
                ),
                name="WebRICE",
                description="WebRICE, íslenski veflesarinn, notar Tiro TTS til að sækja mælt mál til afspilunar.",
            )
            Project.create(
                user_id=db.session.query(User.id).filter(
                    User.name == "Eydís Huld Magnúsdóttir"
                ),
                name="Tiro.is",
                description="Vefur Tiro notar nú sinn eigin veflesara sem notast við Tiro TTS.",
            )
            Project.create(
                user_id=db.session.query(User.id).filter(
                    User.name == "Eydís Huld Magnúsdóttir"
                ),
                name="Háskólinn í Reykjavík",
                description="Háskólinn í Reykjavík býður upp á upplestur á öllum verkefnalýsingum fyrir verkefni í tölvunarfræðideild.",
            )
            Project.create(
                user_id=db.session.query(User.id).filter(
                    User.name == "David Erik Mollberg"
                ),
                name="Alþingi - upplýsingaspjöld",
                description="Alþingi notar þjónustuna okkar til að lesa upp af upplýsingaspjöldum í Alþingishúsinu.",
            )
            Project.create(
                user_id=db.session.query(User.id).filter(
                    User.name == "David Erik Mollberg"
                ),
                name="Reykjavíkurborg",
                description="Borgin notar þjónustuna okkar til að lesa upp vikulegt blogg borgarstjóra.",
            )
        if table == "all" or table == "keys":
            Key.create(
                project_id=db.session.query(Project.id).filter(Project.name == "Mbl.is"),
            )
            Key.create(
                project_id=db.session.query(Project.id).filter(Project.name == "Visir.is"),
            )
            Key.create(
                project_id=db.session.query(Project.id).filter(Project.name == "WebRICE"),
            )
            Key.create(
                project_id=db.session.query(Project.id).filter(Project.name == "Tiro.is"),
            )
            Key.create(
                project_id=db.session.query(Project.id).filter(
                    Project.name == "Háskólinn í Reykjavík"
                ),
            )
            Key.create(
                project_id=db.session.query(Project.id).filter(
                    Project.name == "Alþingi - upplýsingaspjöld"
                ),
            )
            Key.create(
                project_id=db.session.query(Project.id).filter(
                    Project.name == "Reykjavíkurborg"
                ),
            )
        if table == "all" or table == "tts_requests":
            TTSRequest.create(
                project_id=db.session.query(Project.id).filter(Project.name == "Mbl.is"),
                audio_duration=uniform(2.5, 60.0),
            )
            TTSRequest.create(
                project_id=db.session.query(Project.id).filter(Project.name == "Mbl.is"),
                audio_duration=uniform(2.5, 60.0),
            )
            TTSRequest.create(
                project_id=db.session.query(Project.id).filter(Project.name == "Visir.is"),
                audio_duration=uniform(2.5, 60.0),
            )
            TTSRequest.create(
                project_id=db.session.query(Project.id).filter(Project.name == "Visir.is"),
                audio_duration=uniform(2.5, 60.0),
            )
            TTSRequest.create(
                project_id=db.session.query(Project.id).filter(Project.name == "Visir.is"),
                audio_duration=uniform(2.5, 60.0),
            )
            TTSRequest.create(
                project_id=db.session.query(Project.id).filter(Project.name == "WebRICE"),
                audio_duration=uniform(2.5, 60.0),
            )
            TTSRequest.create(
                project_id=db.session.query(Project.id).filter(Project.name == "WebRICE"),
                audio_duration=uniform(2.5, 60.0),
            )
            TTSRequest.create(
                project_id=db.session.query(Project.id).filter(Project.name == "WebRICE"),
                audio_duration=uniform(2.5, 60.0),
            )
            TTSRequest.create(
                project_id=db.session.query(Project.id).filter(Project.name == "WebRICE"),
                audio_duration=uniform(2.5, 60.0),
            )
            TTSRequest.create(
                project_id=db.session.query(Project.id).filter(Project.name == "Tiro.is"),
                audio_duration=uniform(2.5, 60.0),
            )
            TTSRequest.create(
                project_id=db.session.query(Project.id).filter(Project.name == "Tiro.is"),
                audio_duration=uniform(2.5, 60.0),
            )
            TTSRequest.create(
                project_id=db.session.query(Project.id).filter(Project.name == "Tiro.is"),
                audio_duration=uniform(2.5, 60.0),
            )
            TTSRequest.create(
                project_id=db.session.query(Project.id).filter(Project.name == "Tiro.is"),
                audio_duration=uniform(2.5, 60.0),
            )
            TTSRequest.create(
                project_id=db.session.query(Project.id).filter(Project.name == "Tiro.is"),
                audio_duration=uniform(2.5, 60.0),
            )
            TTSRequest.create(
                project_id=db.session.query(Project.id).filter(
                    Project.name == "Háskólinn í Reykjavík"
                ),
                audio_duration=uniform(2.5, 60.0),
            )
            TTSRequest.create(
                project_id=db.session.query(Project.id).filter(
                    Project.name == "Háskólinn í Reykjavík"
                ),
                audio_duration=uniform(2.5, 60.0),
            )
            TTSRequest.create(
                project_id=db.session.query(Project.id).filter(
                    Project.name == "Háskólinn í Reykjavík"
                ),
                audio_duration=uniform(2.5, 60.0),
            )
            TTSRequest.create(
                project_id=db.session.query(Project.id).filter(
                    Project.name == "Háskólinn í Reykjavík"
                ),
                audio_duration=uniform(2.5, 60.0),
            )
            TTSRequest.create(
                project_id=db.session.query(Project.id).filter(
                    Project.name == "Háskólinn í Reykjavík"
                ),
                audio_duration=uniform(2.5, 60.0),
            )
            TTSRequest.create(
                project_id=db.session.query(Project.id).filter(
                    Project.name == "Háskólinn í Reykjavík"
                ),
                audio_duration=uniform(2.5, 60.0),
            )
            TTSRequest.create(
                project_id=db.session.query(Project.id).filter(
                    Project.name == "Alþingi - upplýsingaspjöld"
                ),
                audio_duration=uniform(2.5, 60.0),
            )
            TTSRequest.create(
                project_id=db.session.query(Project.id).filter(
                    Project.name == "Alþingi - upplýsingaspjöld"
                ),
                audio_duration=uniform(2.5, 60.0),
            )
            TTSRequest.create(
                project_id=db.session.query(Project.id).filter(
                    Project.name == "Alþingi - upplýsingaspjöld"
                ),
                audio_duration=uniform(2.5, 60.0),
            )
            TTSRequest.create(
                project_id=db.session.query(Project.id).filter(
                    Project.name == "Alþingi - upplýsingaspjöld"
                ),
                audio_duration=uniform(2.5, 60.0),
            )
            TTSRequest.create(
                project_id=db.session.query(Project.id).filter(
                    Project.name == "Alþingi - upplýsingaspjöld"
                ),
                audio_duration=uniform(2.5, 60.0),
            )
            TTSRequest.create(
                project_id=db.session.query(Project.id).filter(
                    Project.name == "Alþingi - upplýsingaspjöld"
                ),
                audio_duration=uniform(2.5, 60.0),
            )
            TTSRequest.create(
                project_id=db.session.query(Project.id).filter(
                    Project.name == "Alþingi - upplýsingaspjöld"
                ),
                audio_duration=uniform(2.5, 60.0),
            )
            TTSRequest.create(
                project_id=db.session.query(Project.id).filter(
                    Project.name == "Reykjavíkurborg"
                ),
                audio_duration=uniform(2.5, 60.0),
            )
            TTSRequest.create(
                project_id=db.session.query(Project.id).filter(
                    Project.name == "Reykjavíkurborg"
                ),
                audio_duration=uniform(2.5, 60.0),
            )
            TTSRequest.create(
                project_id=db.session.query(Project.id).filter(
                    Project.name == "Reykjavíkurborg"
                ),
                audio_duration=uniform(2.5, 60.0),
            )
            TTSRequest.create(
                project_id=db.session.query(Project.id).filter(
                    Project.name == "Reykjavíkurborg"
                ),
                audio_duration=uniform(2.5, 60.0),
            )
            TTSRequest.create(
                project_id=db.session.query(Project.id).filter(
                    Project.name == "Reykjavíkurborg"
                ),
                audio_duration=uniform(2.5, 60.0),
            )
            TTSRequest.create(
                project_id=db.session.query(Project.id).filter(
                    Project.name == "Reykjavíkurborg"
                ),
                audio_duration=uniform(2.5, 60.0),
            )
            TTSRequest.create(
                project_id=db.session.query(Project.id).filter(
                    Project.name == "Reykjavíkurborg"
                ),
                audio_duration=uniform(2.5, 60.0),
            )
            TTSRequest.create(
                project_id=db.session.query(Project.id).filter(
                    Project.name == "Reykjavíkurborg"
                ),
                audio_duration=uniform(2.5, 60.0),
            )
    except IntegrityError:
        print(f"ERROR: Unable to seed one or more table(s) due to a unique constraint violation!\nERROR: Please make sure to modify the data accordingly, clear the table(s) first or overwrite.\nTerminating...")
        return
    except KeyError:
        print("ERROR: SQLAlchemy has encountered an error. This is most likely due to auth being disabled. Make sure that AUTH_DISABLED is set to \"False\" in src/config.py.\nTerminating...")
        return

    print(f"SEED: Finished adding data to {'all tables' if table == 'all' else f'the {table} table'}.")
    if overwrite:
        print("SEED: Preexisting data was overwritten.")


def clear(table: Literal["all", "users", "projects", "keys", "tts_requests"]):
    """Clears (or overwrites) table(s). Returns a boolean indicating success."""

    inp: str = ""
    CONFIRMATION_STR: str = "do it, NOW!"
    if not force:
        print(
            f"WARNING: {'You are about to overwrite' if overwrite else 'This action clears'} the {'ENTIRE database' if table == 'all' else f'{table} table'}!"
        )
        inp = input(
            f'WARNING: To proceed, enter "{CONFIRMATION_STR}" (without the quotes) and hit enter. Input anything else to cancel: '
        )

    if force or inp == CONFIRMATION_STR:
        print(
            f"CLEAR: {'Overwriting' if overwrite else 'Erasing'} {'all tables' if table == 'all' else f'the {table} table'}..."
        )

        try:
            if table == "all" or table == "keys":
                Key.erase()
                print(f"CLEAR: \"keys\" {'overwritten' if overwrite else 'erased'}.")
            if table == "all" or table == "tts_requests":
                TTSRequest.erase()
                print(f"CLEAR: \"tts_requests\" {'overwritten' if overwrite else 'erased'}.")
            if table == "all" or table == "projects":
                Project.erase()
                print(f"CLEAR: \"projects\" {'overwritten' if overwrite else 'erased'}.")
            if table == "all" or table == "users":
                User.erase()
                print(f"CLEAR: \"users\" {'overwritten' if overwrite else 'erased'}.")

            print(
                f"CLEAR: Finished {'overwriting' if overwrite else 'erasing'} {'all tables' if table == 'all' else f'the {table} table'}."
            )
        except IntegrityError:
            print(f"ERROR: Unable to {'overwrite' if overwrite else 'clear'} one or more table(s) due to foreign key constraints!\nERROR: Please make sure to avoid leaving orphans in children tables ({'overwrite' if overwrite else 'clear'} children tables first).\nTerminating...")
            return False
        except KeyError:
            print("ERROR: SQLAlchemy has encountered an error. This is most likely due to auth being disabled. Make sure that AUTH_DISABLED is set to \"False\" in src/config.py.\nTerminating...")
            return False

        return True
    else:
        print(f"CLEAR: {'Overwrite' if overwrite else 'Clear'} confirmation failed!\nCLEAR: Database {'seed-with-overwrite' if overwrite else 'clear'} action cancelled.\nTerminating...")
        return False


def create_migration():
    """Creates a new migration by automatically detecting schema changes in models. Prompts for a migration message."""
    message: str = ""
    message_bad: LambdaType = lambda msg: len(msg) < 5 or msg.isspace()
    CANCEL_CHAR: str = "x"
    while message_bad(message):
        message = input(f"MIGRATION: Please input a migration message (\"{CANCEL_CHAR}\" to cancel): ")
        if message.lower() == CANCEL_CHAR:
            print("MIGRATION: Migration action cancelled.\nTerminating...")
            return
        elif message_bad(message):
            print(f"MIGRATION: Please write a proper migration message with at least 5 characters (\"{CANCEL_CHAR}\" to cancel).")
        else:
            break

    print(f"MIGRATION: Creating new migration with message: \"{message}\".")
    migrate(message=message)


def validate_args(action: Literal["seed", "clear", "migrate", "upgrade", "downgrade", "history"],
                  table: Literal["all", "users", "projects", "keys", "tts_requests"],
    ) -> None:
    """Makes sure that all script input arguments are correctly formed."""
    
    if action not in ["seed", "clear", "migrate", "upgrade", "downgrade", "history"]:
        raise IllegalArgument("ERROR: Illegal action argument!\nERROR: Please specify action with \"-a\", pick one of the following: \"seed\", \"clear\", \"migrate\", \"upgrade\", \"downgrade\" or \"history\".")

    if action == "seed" and force and not overwrite:
        raise IllegalArgument(f"ERROR: Please don't provide the \"force\" flag while seeding if you don't intend to overwrite existing data.")

    if (action == "seed" or action == "clear") and (not table or table not in [
        "all",
        "users",
        "projects",
        "keys",
        "tts_requests",
    ]):
        raise IllegalArgument(f"ERROR: Illegal table argument!\nERROR: Please specify which table to {action} with \"-t\".\nERROR: Possible table names are \"all\" (for all tables), \"users\", \"projects\", \"keys\" and \"tts_requests\".")

    if action == "clear" and overwrite:
        raise IllegalArgument(f"ERROR: Please don't provide the \"overwrite\" flag while performing a database clear action.")

    if (action == "migrate" or action == "upgrade" or action == "downgrade" or action == "history") and (table or overwrite or force):
        raise IllegalArgument(f"ERROR: Please don't provide additional arguments or flags while performing migrations, upgrades, downgrades or viewing migration history.")


def route_action(
    action: Literal["seed", "clear", "migrate", "upgrade", "downgrade", "history"],
    table: Literal["all", "users", "projects", "keys", "tts_requests"],
) -> None:
    """Makes decisions based on input arguments and routes control accordingly."""

    try:
        validate_args(action, table)
    except Exception as e:
        print(f"ERROR: Bad input parameters detected!\n{str(e)}\n\nTerminating...")
        return

    load_dotenv(Path(".env.local"))
    app = init_app()
    with app.app_context():
        if action == "seed":
            seed(table)
        elif action == "clear":
            clear(table)

        try:
            if action == "migrate":
                create_migration()
            elif action == "upgrade":
                upgrade()
            elif action == "downgrade":
                downgrade()
            elif action == "history":
                history(indicate_current=True)
        except KeyError:
            print("ERROR: SQLAlchemy has encountered an error. This is most likely due to auth being disabled. Make sure that AUTH_DISABLED is set to \"False\" in src/config.py.\nTerminating...")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="This script is used to interact with, test and develop a local instance of a tiro-tts database."
    )

    parser.add_argument(
        "--action",
        "-a",
        choices=["seed", "clear", "migrate", "upgrade", "downgrade", "history"],
        dest="action",
        help="Possible actions to perform on the database.",
        required=True,
    )
    parser.add_argument(
        "--table",
        "-t",
        choices=["all", "users", "projects", "keys", "tts_requests"],
        dest="table",
        help="Database table to apply the seed or clear action on.",
        required=False,
    )
    parser.add_argument(
        "--overwrite",
        "-o",
        dest="overwrite",
        action="store_true",
        help="If your action involves data insertion (seed), add this flag if you wish to overwrite existing data.",
        default=False,
        required=False,
    )
    parser.add_argument(
        "--force",
        "-f",
        dest="force",
        action="store_true",
        help="If your action involves data deletion (seed and overwrite or clear), and this flag is set, you will not be prompted to confirm deletion. Use with caution.",
        default=False,
        required=False,
    )

    args = parser.parse_args()

    overwrite = args.overwrite
    force = args.force
    route_action(
        action=args.action,
        table=args.table,
    )
