import asyncio
from typing import List, Any, Set, Dict

import orjson
import websockets
from websockets import WebSocketServerProtocol

from blockchain import Blockchain
from block import Block
from transaction import Transaction


async def send(websocket: WebSocketServerProtocol, _type: str, data: Any = None) -> Any:
    try:
        msg = {'type': _type}
        if data is not None:
            msg['data'] = data
        print('nO', msg)
        await websocket.send(orjson.dumps(msg))
        response = await websocket.recv()
        print('nI', response)
        return orjson.loads(response)
    except websockets.ConnectionClosed:
        pass


class WsNode:
    def __init__(self, ip: str):
        self.ip: str = ip
        self.nodes: Set[str] = set()
        self.connects: Dict[str, WebSocketServerProtocol] = dict()
        self.blockchain: Blockchain = Blockchain()
        self.mem_pool: Set[Transaction] = set()

    async def broadcast(self, _type: str, data: Any = None):
        return await asyncio.gather(*[send(ws, _type, data) for ws in self.connects.values()])

    async def connect_nodes(self, nodes: List[str]):
        olds = [self.ip] + self.node_list
        news = []
        for node in filter(lambda x: x not in olds, nodes):
            news.append(node)
            websocket = await websockets.connect(f'ws://{node}')
            await websocket.recv()
            await websocket.recv()
            self.nodes.add(node)
            self.connects[node] = websocket
        inputs = [(node, olds + news) for node in news] + [(node, news) for node in olds]
        if len(news) > 1 or (len(news) > 0 and self.ip not in news):
            await asyncio.gather(*[self.share_nodes(*args) for args in inputs])

    async def share_nodes(self, node: str, nodes: List[str]):
        print('share', nodes, 'to', node)
        if node != self.ip:
            ws = self.connects[node]
            await send(ws, 'connect_nodes', {'nodes': nodes})

    async def share_block(self, block: Block) -> None:
        await self.broadcast('add_block', {'block': block.dict()})

    async def pull_longest_chain(self, nodes: List[str] = None):
        nodes = nodes or self.nodes
        lens = list(map(lambda x: x['data'], await self.broadcast('get_blockchain_len')))
        print('lens', lens)
        longest = max(lens)
        ws = self.connects[nodes[lens.index(longest)]]
        if longest > len(self.blockchain):
            hashes: List[str] = await send(ws, 'get_blockchain_hashes')
            start = 0
            for i, (a, b) in enumerate(zip(hashes, self.blockchain.hashes)):
                if a != b:
                    start = i
                    break
            blockchain_data: Dict = await send(ws, 'get_blockchain', {'start': start})
            self.blockchain.blocks[start:] = [Block.parse_obj(block_data['block']) for block_data in
                                              blockchain_data['chain']]

    @property
    def blockchain_len(self) -> int:
        return len(self.blockchain)

    @property
    def node_list(self) -> List[str]:
        return list(self.nodes)

    @property
    def mem_pool_list(self) -> List[Transaction]:
        return list(self.mem_pool)
