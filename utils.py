import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict

import orjson
import websockets
from websockets import WebSocketServerProtocol


async def send(websocket: WebSocketServerProtocol, _type: str, data: Any = None) -> None:
    try:
        msg = {'type': _type}
        if data is not None:
            msg['data'] = data
        print('sO', msg)
        await websocket.send(orjson.dumps(msg))
    except websockets.ConnectionClosed:
        pass


async def handle(switcher: Dict, ws, message):
    print('hI', message)
    message_type = message['type']
    if message_type in switcher:
        if 'data' in message and message['data'] is not None:
            data = message['data']
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
    else:
        print(f'unhandled {message_type}')


def async_from_thread(coro):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(coro)
    loop.close()
