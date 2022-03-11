import asyncio
from typing import List, Any, Set, Dict

import orjson
import websockets
from websockets import WebSocketServerProtocol

from blockchain import Blockchain
from block import Block
from transaction import Transaction


async def send(websocket: WebSocketServerProtocol, _type: str, data: Any = None) -> None:
    try:
        msg = {'type': _type}
        if data is not None:
            msg['data'] = data
        print('nO', msg)
        await websocket.send(orjson.dumps(msg))
    except websockets.ConnectionClosed:
        pass


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
        print('nI', message)
        switcher = {
            'blockchain_len': self.handle_blockchain_len,
            'hashes': self.handle_hashes,
        }
        message_type = message['type']
        if message_type in switcher:
            if 'data' in message and message['data'] is not None:
                data = message['data']
                print(data)
                if type(data) == dict:
                    res = await switcher[message_type](**data)
                else:
                    res = await switcher[message_type](data)
            else:
                res = await switcher[message_type]()
            if res is not None:
                if type(res) == tuple:
                    await send(ws, *res)
                else:
                    await send(ws, res)

    async def broadcast(self, _type: str, data: Any = None, nodes: List[str] = None) -> None:
        print('broadcast')
        sockets = self.connects.values() if nodes is None else [self.connects[node] for node in nodes]
        print(sockets)
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

    async def share_block(self, block: Block) -> None:
        await self.broadcast('add_block', {'block': block.dict()})

    async def pull_longest_chain(self, nodes: List[str] = None):
        print('pulling')
        await self.broadcast('get_blockchain_len', nodes=nodes)

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
        print('handle_blockchain_len')
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
