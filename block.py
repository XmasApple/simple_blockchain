from typing import Any

import hashlib
import orjson


class Block:
    def __init__(self, block_id: int, previous: str = "0" * 64, payload: Any = None) -> None:
        self.id = block_id
        self.previous = previous
        self.payload = payload
        self.nonce = 0

    def __repr__(self):
        return f'{self.get_hash()}: {self.get_data()}'

    def get_data(self) -> bytes:
        return orjson.dumps({
            "number": self.id,
            "previous": self.previous,
            "payload": self.payload,
            "nonce": self.nonce,
        })

    def get_hash(self, nonce: int = None) -> str:
        if nonce is not None:
            self.nonce = nonce
        return hashlib.sha256(self.get_data()).hexdigest()

    def get_block(self):
        return {
            "id": self.id,
            "previous": self.previous,
            "payload": self.payload,
            "nonce": self.nonce,
            "hash": self.get_hash(),
        }
