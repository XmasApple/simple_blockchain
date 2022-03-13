import asyncio
from typing import List, Any, Set, Dict

import orjson
import websockets
from websockets import WebSocketServerProtocol

from blockchain import Blockchain
from block import Block
from transaction import Transaction
from utils import send, handle


class WsNode:
    def __init__(self, domain: str):
        self.domain: str = domain
        self.nodes: Set[str] = set()
        self.connects: Dict[str, WebSocketServerProtocol] = dict()
        self.blockchain: Blockchain = Blockchain()
        self.mem_pool: Set[Transaction] = set()

    async def serve(self, node: str):
        ws = self.connects[node]
        while True:
            try:
                await self.handle(ws, orjson.loads(await ws.recv()))
            except websockets.ConnectionClosed:
                self.nodes.remove(node)
                self.connects.pop(node)
                break

    async def handle(self, ws, message):
        switcher = {
            'blockchain_len': self.handle_blockchain_len,
            'blockchain': self.handle_blockchain,
            'hashes': self.handle_hashes,
        }
        await handle(switcher, ws, message)

    async def broadcast(self, _type: str, data: Any = None, nodes: List[str] = None) -> None:
        sockets = self.connects.values() if nodes is None else [self.connects[node] for node in nodes]
        await asyncio.gather(*[send(ws, _type, data) for ws in sockets])

    async def connect_nodes(self, nodes: List[str]):
        olds = [self.domain] + self.node_list
        news = []
        for node in filter(lambda x: x not in olds, nodes):
            news.append(node)
            websocket = await websockets.connect(f'ws://{node}')
            asyncio.get_event_loop().create_task(self.serve(node))
            self.nodes.add(node)
            self.connects[node] = websocket
        inputs = [(node, olds + news) for node in news] + [(node, news) for node in olds]
        if len(news) > 1 or (len(news) > 0 and self.domain not in news):
            await asyncio.gather(*[self.share_nodes(*args) for args in inputs])
            await self.pull_longest_chain(news)

    async def share_nodes(self, node: str, nodes: List[str]):
        print('share', nodes, 'to', node)
        if node != self.domain:
            ws = self.connects[node]
            await send(ws, 'connect_nodes', {'nodes': nodes})

    async def share_block(self, block: Block):
        await self.broadcast('add_block', {'block': block.dict()})

    async def pull_longest_chain(self, nodes: List[str] = None):
        await self.broadcast('get_blockchain_len', nodes=nodes)

    async def add_transaction(self, transaction: Transaction):
        if transaction in self.mem_pool:
            return
        self.mem_pool.add(transaction)
        await self.broadcast('add_transaction', {'transaction': transaction.dict()})

    @property
    def blockchain_len(self) -> int:
        return len(self.blockchain)

    @property
    def node_list(self) -> List[str]:
        return list(self.nodes)

    @property
    def mem_pool_list(self) -> List[Transaction]:
        return list(self.mem_pool)

    async def handle_blockchain_len(self, length: int) -> str:
        if length > self.blockchain_len:
            return 'get_blockchain_hashes'

    async def handle_hashes(self, hashes: List[str]):
        start = 0
        for i, (a, b) in enumerate(zip(hashes, self.blockchain.hashes)):
            if a != b:
                start = i
                break
        return 'get_blockchain', {'start': start}

    async def handle_blockchain(self, chain):
        if chain[-1]['id'] > self.blockchain_len:
            self.blockchain.blocks[chain[0]['id']:] = [Block.parse_obj(block_data['block']) for block_data in chain]
