from __future__ import annotations

from typing import Any

import hashlib
import orjson
from pydantic import BaseModel


class Block(BaseModel):
    id: int = 0
    nonce: int = 0
    payload: Any = None
    previous: str = '0' * 64
    timestamp: int = 0

    def __repr__(self):
        if type(self.id) != int:
            print('id not int', self.id)
            assert type(self.id) == int
        return f'{self.hash}: {self.get_data()}'

    def get_data(self) -> bytes:
        if type(self.id) != int:
            print('id not int', self.id)
            assert type(self.id) == int
        return orjson.dumps(vars(self))

    @property
    def hash(self, nonce: int = None) -> str:
        if type(self.id) != int:
            print('id not int', self.id)
            assert type(self.id) == int
        if nonce is not None:
            self.nonce = nonce
        return hashlib.sha256(self.get_data()).hexdigest()

    @staticmethod
    def from_json(data: dict) -> Block:
        if type(data['id']) != int:
            print('id not int', data)
            assert type(data['id']) == int
        block = Block(**data)
        print(block)
        return block
