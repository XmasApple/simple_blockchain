from typing import List

import asyncio

import orjson
import websockets
from websockets.legacy.client import Connect

from blockchain import Blockchain
from transaction import Transaction


async def send(websocket, message):
    try:
        await websocket.send(orjson.dumps(message))
    except websockets.ConnectionClosed:
        pass


class WsNode:
    def __init__(self, ip: str):
        self.ip: str = ip
        self.blockchain: Blockchain = Blockchain()
        self.nodes: set[str] = set()
        self.connects: set[websockets.WebSocketServerProtocol] = set()
        self.mem_pool: set[Transaction] = set()

    async def broadcast(self, message):
        [asyncio.get_event_loop().create_task(send(ws, message)) for ws in self.connects]

    async def connect_nodes(self, nodes: List[str]):
        olds = [self.ip] + list(self.nodes)
        news = []
        for node in [node for node in nodes if node not in self.nodes]:
            news.append(node)
            websocket = await websockets.connect(f'ws://{node}')
            await websocket.recv()
            await websocket.recv()
            self.nodes.add(node)
            self.connects.add(websocket)
        inputs = [(node, olds + news) for node in news] + [(node, news) for node in olds]
        if len(news) > 1 or (len(news) > 0 and self.ip not in news):
            await self.broadcast({'type': 'connect_nodes', 'data': {'nodes': list(self.nodes)}})
        # with ThreadPoolExecutor(len(nodes)) as executor:
        #     executor.submit(self.get_longest_chain)


async def listen():
    url = 'ws://127.0.0.1:987'

    async with websockets.connect(url) as ws:
        await ws.send('Hello world')
        while True:
            msg = await ws.recv()
            print(msg)


if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(listen())
