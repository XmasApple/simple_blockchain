from typing import List, Any

from block import Block


class Blockchain:
    def __init__(self) -> None:
        self.blocks: List[Block] = [Block(0)]
        self.difficulty = 3

    def add_block(self, block: Block) -> int:
        if block.id == len(self):
            if block.previous == self.last_hash and block.hash.startswith("0" * self.difficulty):
                self.blocks.append(block)
                return 0
            else:
                return 1
        elif block.id < len(self):
            return 2
        return 3

    def __len__(self) -> int:
        return len(self.blocks)

    @property
    def last(self) -> Block:
        assert len(self.blocks) != 0
        return self.blocks[-1]

    @property
    def last_hash(self) -> str:
        return self.last.hash

    def verify(self) -> int:
        for block, next_hash in zip(self.blocks, map(lambda x: x.previous, self.blocks[1:])):
            # print(block, next_hash)
            if block.hash != next_hash:
                print(f"Verification failed at block {block.id}")
                return block.id
        return -1

    def mine_block(self, payload: Any = None) -> Block:
        block = Block(len(self.blocks), self.last_hash, payload)
        while not block.hash.startswith("0" * self.difficulty):
            block.nonce += 1

        print(self.add_block(block))
        return block
