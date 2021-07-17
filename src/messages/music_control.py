from dataclasses import dataclass

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


def cmd_to_json(cmd: MusicPlayCommand) -> str:
    return jsonpickle.encode(cmd)


def cmd_from_json(text: str) -> MusicPlayCommand:
    return jsonpickle.decode(text)
