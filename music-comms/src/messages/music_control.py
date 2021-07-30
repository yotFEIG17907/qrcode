from dataclasses import dataclass


@dataclass
class MusicStatusReport(object):
    # Report the status, how many playlists, how many songs in each playlist
    # and so on
    pass


@dataclass
class MusicListCommand(object):
    # Pick a new playlist, payload between 1 and N where N is the number of
    # playlists. Leave alone if there the payload value is greater than N
    # The payload for the command, types etc really depend on the command
    payload: int


@dataclass
class MusicPlayCommand(object):
    # The payload for the command, types etc really depend on the command
    payload: int


@dataclass
class MusicNextCommand(object):
    pass


@dataclass
class MusicPrevCommand(object):
    pass


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
