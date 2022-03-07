from __future__ import annotations

from typing import Any

import hashlib
from model import Model


class Block(Model):
    id: int = 0
    nonce: int = 0
    payload: Any = None
    previous: str = '0' * 64
    timestamp: int = 0

    def __repr__(self):
        if type(self.id) != int:
            print('id not int', self.id)
            assert type(self.id) == int
        return f'{self.hash}: {self.dict()}'

    @property
    def hash(self, nonce: int = None) -> str:
        if type(self.id) != int:
            print('id not int', self.id)
            assert type(self.id) == int
        if nonce is not None:
            self.nonce = nonce
        return hashlib.sha256(self.json().encode(encoding='utf-8')).hexdigest()
