from __future__ import annotations

import time
from model import Model


class Transaction(Model):
    sender: str
    receiver: str
    amount: int
    timestamp: int = int(time.time())

    def __hash__(self):
        return hash(f'{self.sender}->{self.receiver}:{self.amount} at {self.timestamp}')
