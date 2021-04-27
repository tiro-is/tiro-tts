import os
from boto3 import Session


class Polly:
    _session: Session

    def __init__(self):
        self._session = Session(
            aws_access_key_id=os.environ["TIRO_TTS_AWS_ACCESS_KEY_ID"],
            aws_secret_access_key=os.environ["TIRO_TTS_AWS_SECRET_ACCESS_KEY"],
            region_name=os.environ.get("TIRO_TTS_AWS_REGION", "eu-west-1"),
        )
        self._polly = self._session.client("polly")

    def synthesize_speech(self, *args, **kwargs):
        return self._polly.synthesize_speech(*args, **kwargs)
