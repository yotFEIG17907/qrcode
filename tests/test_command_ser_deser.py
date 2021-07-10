"""
Serializing and de-serializing the music commands. Using jsonpickle:
it increases message size but it is much simpler and requires no
special encoder/decoder classes
"""

import jsonpickle

from messages.music_control import MKommand, MusicCommand


def test_ser_deser():
    payload = 1
    test_command = MusicCommand(command=MKommand.PLAY,
                                payload=payload)
    as_json = jsonpickle.encode(test_command)

    got_obj = jsonpickle.decode(as_json)
    assert isinstance(got_obj, MusicCommand)
    assert got_obj.payload == 1
    assert got_obj.command == MKommand.PLAY
