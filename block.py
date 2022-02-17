from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import hashlib
import orjson


@dataclass
class Block:
    id: int = 0
    previous: str = "0" * 64
    payload: Any = None
    nonce: int = 0

    def __repr__(self):
        return f'{self.hash}: {self.get_data()}'

    def get_data(self) -> bytes:
        return orjson.dumps({
            "id": self.id,
            "previous": self.previous,
            "payload": self.payload,
            "nonce": self.nonce,
        })

    @property
    def hash(self, nonce: int = None) -> str:
        if nonce is not None:
            self.nonce = nonce
        return hashlib.sha256(self.get_data()).hexdigest()

    def get_json(self):
        return {
            "id": self.id,
            "previous": self.previous,
            "payload": self.payload,
            "nonce": self.nonce,
            "hash": self.hash,
        }

    @staticmethod
    def from_json(data: dict) -> Block:
        return Block(data["id"], data["previous"], data["payload"], data["nonce"])
