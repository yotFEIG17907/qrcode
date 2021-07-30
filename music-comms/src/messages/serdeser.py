from typing import Any

import jsonpickle


def cmd_to_json(cmd: Any) -> str:
    return jsonpickle.encode(cmd)


def cmd_from_json(text: str) -> Any:
    return jsonpickle.decode(text)
