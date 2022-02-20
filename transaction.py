from __future__ import annotations

import time
from dataclasses import dataclass


@dataclass(order=True)
class Transaction:
    sender: str
    receiver: str
    amount: int
    timestamp: int = time.time()

    @staticmethod
    def from_json(data: dict) -> Transaction:
        return Transaction(*data.values())

    def __hash__(self):
        return hash(f'{self.sender}->{self.receiver}:{self.amount} at {self.timestamp}')
