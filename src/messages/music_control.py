from dataclasses import dataclass
from enum import Enum

import jsonpickle


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


def cmd_to_json(cmd: MusicCommand) -> str:
    return jsonpickle.encode(cmd)


def cmd_from_json(text: str) -> MusicCommand:
    return jsonpickle.decode(text)
