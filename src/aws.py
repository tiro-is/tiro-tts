import os
from boto3 import Session
from flask import current_app


class Polly:
    _session: Session

    def __init__(self):
        self._session = Session(
            aws_access_key_id=current_app.config["AWS_ACCESS_KEY_ID"],
            aws_secret_access_key=current_app.config["AWS_SECRET_ACCESS_KEY"],
            region_name=current_app.config["AWS_REGION"],
        )
        self._polly = self._session.client("polly")

    def synthesize_speech(self, *args, **kwargs):
        return self._polly.synthesize_speech(*args, **kwargs)
