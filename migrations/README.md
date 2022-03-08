# tiro-tts database

This simple SQLAlchemy+Flask-Migrate PostgreSQL database is used to keep records of endpoint calls to Tiro TTS.

## How to modify
This section explains the step that must be taken to apply modificatinos to the database.

### Your own changes
To apply your own changes to the database, the following steps must be taken:

    1. Make your changes (e.g. alter or add tables or models).
    2. Generate a migration script that adds your changes to the database (remember to include a nice message which explains what you changed and why):
        Use this command: `TIRO_TTS_SYNTHESIS_SET_PB=$PWD/conf/synthesis_set.local.pbtxt FLASK_APP="src/app.py" bazel-bin/repl -m flask db migrate -m "<Some nice message here>"`
    3. Upgrade the database using the migration script:
        Use this command: `TIRO_TTS_SYNTHESIS_SET_PB=$PWD/conf/synthesis_set.local.pbtxt FLASK_APP="src/app.py" bazel-bin/repl -m flask db upgrade`
    4. Add all additions and modifications inside the `migrations` folder to version control.

### Pulled changes
To apply changes you have pulled from a remote repository, do the following:

    Upgrade the database using the migration script you just pulled (Flask-Migrate will automatically detect the new unapplied migration):
        Use this command: `TIRO_TTS_SYNTHESIS_SET_PB=$PWD/conf/synthesis_set.local.pbtxt FLASK_APP="src/app.py" bazel-bin/repl -m flask db upgrade`
        