from typing import List, Any

from block import Block


class Blockchain:
    def __init__(self) -> None:
        self.blocks: List[Block] = [Block(0)]

    def add_block(self, block: Block) -> None:
        self.blocks.append(block)

    def get_last(self) -> Block:
        assert len(self.blocks) != 0
        return self.blocks[-1]

    def get_last_hash(self) -> str:
        return self.get_last().get_hash()

    def verify(self) -> int:
        for block, next_hash in zip(self.blocks, map(lambda x: x.previous, self.blocks[1:])):
            # print(block, next_hash)
            if block.get_hash() != next_hash:
                print(f"Verification failed at block {block.number}")
                return block.number
        return -1

    def mine_block(self, difficulty: int, payload: Any = None) -> Block:
        block = Block(len(self.blocks), self.get_last_hash(), payload)
        while not block.get_hash().startswith("0" * difficulty):
            block.nonce += 1

        self.add_block(block)
        return block
