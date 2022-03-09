import asyncio
from typing import List, Any, Set, Dict, Iterator

import orjson
import websockets
from websockets import WebSocketServerProtocol

from blockchain import Blockchain
from block import Block
from transaction import Transaction


async def send(websocket: WebSocketServerProtocol, message: Any, need_result=False) -> bytes | None:
    try:
        await websocket.send(orjson.dumps(message))
        await websocket.recv()
    except websockets.ConnectionClosed:
        pass


class WsNode:
    def __init__(self, ip: str):
        self.ip: str = ip
        self.nodes: Set[str] = set()
        self.connects: Dict[str, WebSocketServerProtocol] = dict()
        self.blockchain: Blockchain = Blockchain()
        self.mem_pool: Set[Transaction] = set()

    async def broadcast(self, message: Any, need_result=False):#
        # for ws in self.connects.values():
        #     await ws.send(orjson.dumps(message))
        # for ws in self.connects.values():
        #     resp = await ws.recv()

        return await asyncio.gather(*[send(ws, message) for ws in self.connects.values()])

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
            # await self.broadcast({'type': 'connect_nodes', 'data': {'nodes': self.node_list}})
            # [asyncio.get_event_loop().create_task(self.share_nodes(*args)) for args in inputs]
            await asyncio.gather(*[self.share_nodes(*args) for args in inputs])

        # with ThreadPoolExecutor(len(nodes)) as executor:
        #     executor.submit(self.get_longest_chain)

    async def share_nodes(self, node: str, nodes: List[str]):
        print('share', nodes, 'to', node)
        if node != self.ip:
            ws = self.connects[node]
            await send(ws, {'type': 'connect_nodes', 'data': {'nodes': nodes}})

    async def share_block(self, block: Block) -> None:
        await self.broadcast({'type': 'add_block', 'data': {'block': block.dict()}})

    @property
    def blockchain_len(self) -> int:
        return len(self.blockchain)

    @property
    def node_list(self) -> List[str]:
        return list(self.nodes)

    @property
    def mem_pool_list(self) -> List[Transaction]:
        return list(self.mem_pool)
