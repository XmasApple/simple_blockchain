import asyncio
from concurrent.futures import ThreadPoolExecutor
import socket
import time
from typing import Any, List, Dict, Set

import orjson
import websockets

from block import Block
from transaction import Transaction
from utils import send, handle, async_from_thread

BASE_NONCE = 1000000000


class Miner:
    def __init__(self, nodes: List[str]):
        self.nodes: Set[str] = set(nodes)
        self.connects: Dict[str, websockets.WebSocketServerProtocol] = dict()
        self.mem_pool: Set[Transaction] = set()
        self.to_mine: Block = Block(payload={'transactions': list(self.mem_pool)})
        self.difficulty: int = 5
        self.miner_executor: ThreadPoolExecutor | None = None

    async def broadcast(self, _type: str, data: Any = None, nodes: List[str] = None) -> None:
        print('broadcast', _type, data)
        sockets = self.connects.values() if nodes is None else [self.connects[node] for node in nodes]
        await asyncio.gather(*[send(ws, _type, data) for ws in sockets])

    async def serve(self, node: str):
        ws = self.connects[node]
        while True:
            try:
                await self.handle(ws, orjson.loads(await ws.recv()))
            except websockets.ConnectionClosed:
                print(f'close {node}')
                self.nodes.remove(node)
                self.connects.pop(node)
                break

    async def handle(self, ws, message):
        switcher = {
            'mem_pool': self.handle_mem_pool,
            'last_block': self.handle_last_block,
            'difficulty': self.handle_difficulty,
            'add_block': self.handle_add_block,
        }
        await handle(switcher, ws, message)

    async def handle_last_block(self, block: dict, block_hash: str):
        print('handle_last_block')
        block = Block.parse_obj(block)
        if block.id > self.to_mine.id - 1:
            self.to_mine = Block(
                id=block.id + 1,
                nonce=BASE_NONCE,
                payload=self.to_mine.payload,
                previous=block_hash,
                timestamp=int(time.time())
            )
        elif block.id < self.to_mine.id - 1:
            return 'pull_longest_chain'
        else:
            self.to_mine.previous = block_hash
            self.to_mine.timestamp = int(time.time())
        print(self.to_mine)

    async def handle_mem_pool(self, mem_pool):
        print('handle_mem_pool')
        self.mem_pool.union(set(map(Transaction.parse_obj, mem_pool)))
        print('mem_pool', self.mem_pool)
        self.to_mine.payload = {'transactions': list(map(lambda x: x.dict(), self.mem_pool))}
        print(self.to_mine.dict())

    async def handle_difficulty(self, difficulty):
        print('handle_difficulty')
        self.difficulty = difficulty

    async def handle_add_block(self, block):
        block = Block.parse_obj(block)
        if block.id == self.to_mine.id + 1:
            self.to_mine = Block(
                id=block.id + 1,
                nonce=BASE_NONCE,
                payload={'transactions': list(self.mem_pool)},
                previous=block.hash,
                timestamp=int(time.time()))
        elif block.id != self.to_mine.id:
            return 'get_last_block'

    async def connect(self):
        for node in self.nodes.copy():
            print(node)
            ws = await websockets.connect(f'ws://{node}/miner')
            asyncio.get_event_loop().create_task(self.serve(node))
            self.connects[node] = ws
            await send(ws, 'get_last_block')
            await send(ws, 'get_mem_pool')
            await send(ws, 'get_blockchain_difficulty')
        print('connect to all nodes')
        self.miner_executor = ThreadPoolExecutor()
        self.miner_executor.submit(self.mine)

        await asyncio.Future()  # run forever

    def run_mine(self):
        self.miner_executor.shutdown(wait=False)
        self.miner_executor = ThreadPoolExecutor(max_workers=1)
        print('executor')
        self.miner_executor.submit(self.mine)

    def mine(self):
        while True:
            print('mine', self.to_mine)
            while not self.to_mine.hash.startswith('0' * self.difficulty):
                self.to_mine.nonce += 1
            print('mined', self.to_mine.hash)
            self.miner_executor.submit(async_from_thread, self.broadcast('add_block', {'block': self.to_mine.dict()}))
            self.to_mine = Block(
                id=self.to_mine.id + 1,
                nonce=BASE_NONCE,
                payload={'transactions': list(self.mem_pool)},
                previous=self.to_mine.hash,
                timestamp=int(time.time()))


if __name__ == '__main__':
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    miner = Miner([f"{s.getsockname()[0]}:5000"])
    s.close()
    asyncio.run(miner.connect())
