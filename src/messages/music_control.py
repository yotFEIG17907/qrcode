from dataclasses import dataclass
from enum import Enum


class MKommand(Enum):
    STOP = 0
    PLAY = 1
    VOLUME_UP = 2


@dataclass
class MusicCommand(object):
    # Control the music
    command: MKommand
    # The payload for the command, types etc really depend on the command
    payload: int
