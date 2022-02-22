from __future__ import annotations

import time

from pydantic import BaseModel


class Transaction(BaseModel):
    sender: str
    receiver: str
    amount: int
    timestamp: int = int(time.time())

    @staticmethod
    def from_json(data: dict) -> Transaction:
        transaction = Transaction(**data)
        if type(transaction.timestamp) == float:
            transaction.timestamp = int(transaction.timestamp)
        return transaction

    def __hash__(self):
        return hash(f'{self.sender}->{self.receiver}:{self.amount} at {self.timestamp}')
