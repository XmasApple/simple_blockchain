from typing import Any

import hashlib
import orjson


class Block:
    def __init__(self, number: int, previous: str = "0" * 64, payload: Any = None) -> None:
        self.number = number
        self.previous = previous
        self.payload = payload
        self.nonce = 0

    def get_data(self) -> bytes:
        data = {
            "number": self.number,
            "previous": self.previous,
            "payload": self.payload,
            "nonce": self.nonce,
        }
        return orjson.dumps(data)

    def __repr__(self):
        return f'{self.get_hash()}: {self.get_data().decode(encoding="utf-8")}'

    def get_hash(self, nonce: int = None) -> str:
        if nonce is not None:
            self.nonce = nonce
        return hashlib.sha256(self.get_data()).hexdigest()
