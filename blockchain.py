from typing import List, Any, Optional
from enum import Enum, auto

from block import Block


class AddBlockStatus(Enum):
    OK = auto()
    VERIFICATION_FAILED = auto()
    CURRENT_CHAIN_LONGER = auto()
    CURRENT_CHAIN_TOO_SHORT = auto()


class Blockchain:
    def __init__(self) -> None:
        self.blocks: List[Block] = [Block(timestamp=0)]
        self.difficulty = 3

    def add_block(self, block: Block) -> AddBlockStatus:
        if block.id == len(self):
            if block.previous == self.last_hash and block.hash.startswith("0" * self.difficulty):
                self.blocks.append(block)
                return AddBlockStatus.OK
            else:
                return AddBlockStatus.VERIFICATION_FAILED
        elif block.id < len(self):
            return AddBlockStatus.CURRENT_CHAIN_LONGER
        return AddBlockStatus.CURRENT_CHAIN_TOO_SHORT

    def __len__(self) -> int:
        return len(self.blocks)

    @property
    def last(self) -> Block:
        assert len(self.blocks) != 0
        return self.blocks[-1]

    @property
    def last_hash(self) -> str:
        return self.last.hash

    @property
    def hashes(self) -> List[str]:
        return [block.hash for block in self.blocks]

    def verify(self) -> int:
        for block, next_hash in zip(self.blocks, map(lambda x: x.previous, self.blocks[1:])):
            # print(block, next_hash)
            if block.hash != next_hash:
                print(f"Verification failed at block {block.id}")
                return block.id
        return -1

    def mine_block(self, payload: Any = None) -> Optional[Block]:
        block = Block(id=len(self.blocks), previous=self.last_hash, payload=payload)
        while not block.hash.startswith("0" * self.difficulty):
            block.nonce += 1
        if self.add_block(block) == AddBlockStatus.OK:
            return block
        return None
