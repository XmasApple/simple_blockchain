import asyncio
import json
import socket
import traceback

import orjson
import websockets
from websockets import ConnectionClosedError, ConnectionClosedOK
from ws_node import WsNode


async def send(ws, data):
    try:
        await ws.send(orjson.dumps(data))
    except websockets.ConnectionClosed:
        pass


async def handler(ws, path):
    await send(ws, {'type': 'connected', 'data': domain})
    await send(ws, {'type': 'nodelist', 'data': {'nodes': list(ws_node.nodes)}})
    while True:
        try:
            message = json.loads(await ws.recv())
            await handle_message(ws, message)
        except(ConnectionClosedError, ConnectionClosedOK):
            break
        except Exception as e:
            print(type(e))
            print(e)
            break


async def handle_message(ws, message):
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


def get_block():
    pass


def get_last_block():
    pass


def get_blockchain_difficulty():
    pass


def get_blockchain():
    pass


def verify_blockchain():
    pass


def add_block():
    pass


def get_blockchain_len():
    pass


def get_blockchain_hashes():
    pass


def add_transaction():
    pass


def get_transactions():
    pass


def get_mem_pool():
    pass


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
