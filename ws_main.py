import asyncio
import json
import socket
import traceback

import orjson
import websockets
from ws_node import WsNode


async def send(ws, data):
    await ws.send(orjson.dumps(data))


async def handler(ws, path):
    await send(ws, {'type': 'connected', 'data': domain})
    await send(ws, {'type': 'nodelist', 'data': {'nodes': list(ws_node.nodes)}})
    while True:
        message = json.loads(await ws.recv())
        print(message)
        message_type = message['type']
        switcher = {
            'connect_nodes': ws_connect_nodes,
            'get_connected_nodes': get_connected_nodes,
        }
        if message_type in switcher:
            try:
                await switcher[message_type](ws, message['data'])
            except Exception as e:
                print(e)
                print(traceback.format_exc())
                await send(ws, {'type': 'error', 'data': e.__repr__()})
        else:
            await send(ws, {'type': 'error', 'data': 'wrong message type'})


async def ws_connect_nodes(ws, data):
    nodes = data['nodes']
    await ws_node.connect_nodes(nodes)


async def get_connected_nodes(ws, data):
    await send(ws, list(ws_node.nodes))


if __name__ == '__main__':
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    host = s.getsockname()[0]
    s.close()
    port = int(input())
    domain = f'{host}:{port}'
    ws_node = WsNode(domain)
    start_server = websockets.serve(handler, host, port)

    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()
