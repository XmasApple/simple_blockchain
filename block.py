from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

import hashlib
import orjson


@dataclass(order=True)
class Block:
    id: int = 0
    nonce: int = 0
    payload: Any = None
    previous: str = '0' * 64
    timestamp: int = int(time.time())

    def __repr__(self):
        return f'{self.hash}: {self.get_data()}'

    def get_data(self) -> bytes:
        return orjson.dumps(vars(self))

    @property
    def hash(self, nonce: int = None) -> str:
        if nonce is not None:
            self.nonce = nonce
        return hashlib.sha256(self.get_data()).hexdigest()

    @staticmethod
    def from_json(data: dict) -> Block:
        return Block(*data.values())

