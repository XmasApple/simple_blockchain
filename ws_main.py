import asyncio
import json
import socket
import time
import traceback
from typing import Any, List, Dict

import orjson
import websockets
from websockets import ConnectionClosedError, ConnectionClosedOK

from block import Block
from transaction import Transaction
from blockchain import AddBlockStatus
from ws_node import WsNode


async def send(ws, _type: str, data: Any = None):
    try:
        msg = {'type': _type}
        if data is not None:
            msg['data'] = data
        print('O', msg)
        await ws.send(orjson.dumps(msg))
    except websockets.ConnectionClosed:
        pass


async def handler(ws, _):
    await send(ws, 'connected', domain)
    await send(ws, 'nodelist', {'nodes': list(ws_node.nodes)})
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
    print('I', message)
    message_type = message['type']
    switcher = {
        'connect_nodes': connect_nodes,
        'get_connected_nodes': get_connected_nodes,
        'get_block': get_block,
        'get_last_block': get_last_block,
        'get_blockchain_difficulty': get_blockchain_difficulty,
        'get_blockchain': get_blockchain,
        'verify_blockchain': verify_blockchain,
        'add_block': add_block,
        'get_blockchain_len': get_blockchain_len,
        'get_blockchain_hashes': get_blockchain_hashes,
        'add_transaction': add_transaction,
        'get_transactions': get_transactions,
        'get_mem_pool': get_mem_pool,
    }
    if message_type in switcher:
        try:
            if 'data' in message and message['data'] is not None:
                res = await switcher[message_type](**message['data'])
            else:
                res = await switcher[message_type]()
            if res is not None:
                if type(res) == tuple:
                    await send(ws, *res)
                else:
                    await send(ws, res)
        except Exception as e:
            print(e)
            print(traceback.format_exc())
            await send(ws, 'error', e.__repr__())
    else:
        await send(ws, 'error', 'wrong message type')


async def connect_nodes(nodes):
    await ws_node.connect_nodes(nodes)
    return 'connect_nodes'


async def get_connected_nodes():
    return 'connected_nodes', ws_node.node_list


async def get_block(block_id) -> (str, dict):
    if block_id and int(block_id) < len(ws_node.blockchain.blocks):
        block = ws_node.blockchain.blocks[int(block_id)]
        return 'block', {'block': block.dict(), 'hash': block.hash}
    else:
        return 'error', {'message': f'wrong id {block_id}, chain length = {len(ws_node.blockchain.blocks)}'}


async def get_last_block() -> (str, dict):
    block = ws_node.blockchain.blocks[-1]
    return 'block', {'block': block.dict(), 'hash': block.hash}


async def get_blockchain_difficulty() -> (str, int):
    return 'difficulty', ws_node.blockchain.difficulty


async def get_blockchain(start: int = 0) -> (str, dict):
    return 'blockchain', {
        'chain': list(map(lambda x: {'block': x.dict(), 'hash': x.hash}, ws_node.blockchain.blocks[start:])),
        'length': len(ws_node.blockchain.blocks)
    }


async def get_blockchain_len() -> (str, int):
    return 'blockchain_len', ws_node.blockchain_len


async def get_blockchain_hashes() -> (str, List[str]):
    return 'hashes', ws_node.blockchain.hashes


async def verify_blockchain():
    number = ws_node.blockchain.verify()
    if number == -1:
        return 'verify', {'status': 'success'}
    else:
        return 'verify', {
            'status': 'error',
            'message': {'message': f'wrong block number {number}',
                        'block': ws_node.blockchain.blocks[number]}}


async def add_block(block) -> (str, Any):
    block = Block.parse_obj(block)
    switcher = {
        AddBlockStatus.OK: 'block_added',
        AddBlockStatus.EXIST: 'block_exist',
        AddBlockStatus.VERIFICATION_FAILED: 'block_verification_failed',
        AddBlockStatus.CURRENT_CHAIN_LONGER: ('current_longer', ws_node.blockchain_len),
        AddBlockStatus.CURRENT_CHAIN_TOO_SHORT: ('current_short', ws_node.blockchain_len),
    }
    status = ws_node.blockchain.add_block(block)

    if status == AddBlockStatus.OK:
        for transaction in block.payload['transactions']:
            print('remove', transaction)
            ws_node.mem_pool.discard(Transaction.parse_obj(transaction))
            print(ws_node.mem_pool)
        await ws_node.share_block(block)
    elif status in (AddBlockStatus.VERIFICATION_FAILED, AddBlockStatus.CURRENT_CHAIN_TOO_SHORT):
        await ws_node.pull_longest_chain()
    res = switcher[status]
    return res


async def add_transaction(transaction) -> (str, Any):
    transaction = Transaction.parse_obj(transaction)
    if transaction.timestamp == 0:
        transaction.timestamp = int(time.time())
    await ws_node.add_transaction(transaction)
    return 'transaction_added'


async def get_transactions():
    mem_pool = list(map(lambda x: x.dict(), ws_node.mem_pool_list))
    return 'transactions', {'transactions': mem_pool, 'count': len(mem_pool)}


async def get_mem_pool() -> (str, List[Dict]):
    return 'mem_pool', [transaction.dict() for transaction in ws_node.mem_pool_list]


async def main():
    async with websockets.serve(handler, host, port):
        await asyncio.Future()  # run forever


if __name__ == '__main__':
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    host = s.getsockname()[0]
    s.close()
    port = int(input())
    domain = f'{host}:{port}'
    ws_node = WsNode(domain)

    asyncio.run(main())
