from abc import ABC, abstractmethod
from typing import Iterable

from messages import tts_frontend_message_pb2
from services import tts_frontend_service_grpc, tts_frontend_service_pb2


# FatToken has to support categories, pronunciation, keeping track of mapping from raw
# text to normalized text, time spans, etc.
class FatToken:
    pass


class NormalizerBase(ABC):
    @abstractmethod
    def normalize(self, tokens: Iterable[FatToken]) -> Iterable[FatToken]:
        return NotImplemented
