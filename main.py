import socket
import time
from typing import List

import uvicorn
import validators
from fastapi import FastAPI, HTTPException

from block import Block
from blockchain import AddBlockStatus
from node import Node
from transaction import Transaction

app = FastAPI()


@app.get('/get_block')
def get_block(block_id: int = 0):
    if block_id and int(block_id) < len(node.blockchain.blocks):
        block = node.blockchain.blocks[int(block_id)]
        return {'block': vars(block), 'hash': block.hash}
    else:
        raise HTTPException(status_code=400,
                            detail={'status': 'error',
                                    'message': f'wrong id {block_id}, chain length = {len(node.blockchain.blocks)}'})


@app.get('/get_last_block')
def get_last_block():
    block = node.blockchain.blocks[-1]
    return {'block': vars(block), 'hash': block.hash}


@app.get('/get_mem_pool')
def get_mem_pool():
    return list(node.mem_pool)


@app.get('/get_blockchain_difficulty')
def get_blockchain_difficulty():
    return {'difficulty': node.blockchain.difficulty}


@app.get('/get_blockchain')
def get_blockchain(start: int = 0):
    return {
        'chain': list(map(lambda x: {'block': vars(x), 'hash': x.hash}, node.blockchain.blocks[start:])),
        'length': len(node.blockchain.blocks)
    }


@app.get('/verify_blockchain')
def verify_blockchain():
    number = node.blockchain.verify()
    if number == -1:
        return {'status': 'success'}
    else:
        raise HTTPException(status_code=412,
                            detail={'status': 'error', 'message': {'message': f'wrong block number {number}',
                                                                   'block': node.blockchain.blocks[number]}})


@app.get('/get_connected_nodes')
def get_connected_nodes():
    return node.nodes


@app.post('/connect_nodes', status_code=201)
def connect_nodes(nodes: List[str]):
    print(nodes)
    if type(nodes) == list and all(map(
            lambda x: type(x) == str and validators.url(x if x.startswith('http://') else f'http://{x}/') is True,
            nodes)):
        if len(nodes) > 0:
            node.connect_nodes(nodes)
        return list(node.nodes)
    raise HTTPException(status_code=400, detail={'message': 'some_nodes_has_wrong_url'})


@app.post('/add_block', status_code=201)
def add_block(block: Block):
    switcher = {
        AddBlockStatus.OK: ({'message': 'block added'}, 201),
        AddBlockStatus.EXIST: ({'message': 'block exist'}, 201),
        AddBlockStatus.VERIFICATION_FAILED: ({'message:': 'verification failed'}, 409),
        AddBlockStatus.CURRENT_CHAIN_LONGER: ({'message:': f'current longer', 'len': len(node.blockchain)}, 409),
        AddBlockStatus.CURRENT_CHAIN_TOO_SHORT: (
            {'message:': f'current too short', 'len': len(node.blockchain)}, 409),
    }
    status = node.blockchain.add_block(block)
    if status == AddBlockStatus.OK:
        print(block.payload['transactions'])
        node.share_block(block)
        node.mem_pool -= set(map(Transaction.from_json, block.payload['transactions']))
    elif status in (AddBlockStatus.VERIFICATION_FAILED, AddBlockStatus.CURRENT_CHAIN_TOO_SHORT):
        node.get_longest_chain()
    res = switcher[status]
    if res[1] == 201:
        return res[0]
    raise HTTPException(status_code=res[1], detail=res[0])


@app.get('/get_blockchain_len')
def get_blockchain_len():
    return len(node.blockchain)


@app.get('/get_blockchain_hashes')
def get_blockchain_hashes():
    return node.blockchain.hashes


@app.post('/add_transaction', status_code=201)
def add_transaction(transaction: Transaction):
    if transaction.timestamp == 0:
        transaction.timestamp = time.time()
    node.add_transaction(transaction)
    return 'ok'


@app.get('/get_transactions')
def get_transactions():
    mem_pool = list(node.mem_pool)
    return {'transactions': mem_pool, 'count': len(mem_pool)}


if __name__ == '__main__':
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    host = s.getsockname()[0]
    s.close()
    port = int(input())
    node = Node(f'{host}:{port}')
    uvicorn.run(app, host=host, port=port, log_level="info")
