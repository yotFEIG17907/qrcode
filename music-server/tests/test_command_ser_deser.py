"""
Serializing and de-serializing the music commands. Using jsonpickle:
it increases message size but it is much simpler and requires no
special encoder/decoder classes
"""

import jsonpickle

from messages.music_control import MusicPlayCommand, MusicStopCommand


def test_ser_deser_music_play():
    payload = 1
    test_command = MusicPlayCommand(payload=payload)
    as_json = jsonpickle.encode(test_command)

    got_obj = jsonpickle.decode(as_json)
    assert isinstance(got_obj, MusicPlayCommand)
    assert got_obj.payload == payload


def test_ser_deser_music_stop():
    test_command = MusicStopCommand()
    as_json = jsonpickle.encode(test_command)

    got_obj = jsonpickle.decode(as_json)
    assert isinstance(got_obj, MusicStopCommand)
