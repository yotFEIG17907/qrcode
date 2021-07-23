from dataclasses import dataclass
from typing import Any

import jsonpickle


@dataclass
class MusicPlayCommand(object):
    # The payload for the command, types etc really depend on the command
    payload: int


@dataclass
class MusicStopCommand(object):
    pass


@dataclass
class MusicPauseCommand(object):
    pass


@dataclass
class MusicUnpauseCommand(object):
    pass


@dataclass
class MusicVolumeCommand(object):
    # What value to set for the volume
    payload: int


@dataclass
class TextToSpeech(object):
    # Convert this text to speech
    payload: str



