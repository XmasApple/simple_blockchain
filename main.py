import threading
import time
from threading import Thread

import requests
import validators
from flask import Flask, jsonify, request

from block import Block
from blockchain import AddBlockStatus
from node import Node
from transaction import Transaction

app = Flask(__name__)


def mine():
    print(0)
    time.sleep(3)
    print(10)
    while True:
        print('loop')
        transactions = node.mem_pool
        block = node.blockchain.mine_block(payload={'transactions': [vars(transaction) for transaction in transactions]})
        if block:
            node.share_block(block)
            node.mem_pool -= transactions


@app.route('/get_block', methods={'GET', 'POST'})
def get_block():
    block_id = request.args.get('id', type=int)
    if block_id and int(block_id) < len(node.blockchain.blocks):
        block = node.blockchain.blocks[int(block_id)]
        return jsonify({'block': vars(block), 'hash': block.hash}), 200
    else:
        return jsonify({'status': 'error',
                        'message': f'wrong id {block_id}, chain length = {len(node.blockchain.blocks)}'}), 400


@app.route('/get_blockchain', methods={'GET'})
def get_blockchain():
    start = request.args.get('start', 0, int)
    return jsonify({
        'chain': list(map(lambda x: {'block': vars(x), 'hash': x.hash}, node.blockchain.blocks[start:])),
        'length': len(node.blockchain.blocks)
    }), 200


@app.route('/verify_blockchain', methods={'GET'})
def verify_blockchain():
    number = node.blockchain.verify()
    if number == -1:
        return jsonify({'status': 'success'}), 200
    else:
        return jsonify({'status': 'error', 'message': {'message': f'wrong block number {number}',
                                                       'block': node.blockchain.blocks[number]}}), 412


@app.route('/get_connected_nodes', methods={'GET'})
def get_connected_nodes():
    return jsonify(len(node.blockchain)), 200


@app.route('/connect_nodes', methods={'POST'})
def connect_nodes():
    nodes = request.get_json()
    # print(nodes)
    if type(nodes) == list and all(map(
            lambda x: type(x) == str and validators.url(x if x.startswith('http://') else f'http://{x}/') is True,
            nodes)):
        if len(nodes) > 0:
            node.connect_nodes(nodes)
        return jsonify(list(node.nodes)), 201
    return jsonify({'message': 'some_nodes_has_wrong_url'}), 400


@app.route('/add_block', methods={'POST'})
def add_block():
    block = request.get_json()
    if type(block) == dict and all([x in block for x in Block.__annotations__]):
        switcher = {
            AddBlockStatus.OK: ({'message': 'block added'}, 201),
            AddBlockStatus.VERIFICATION_FAILED: ({'message:': 'verification failed'}, 409),
            AddBlockStatus.CURRENT_CHAIN_LONGER: ({'message:': f'current longer', 'len': len(node.blockchain)}, 409),
            AddBlockStatus.CURRENT_CHAIN_TOO_SHORT: (
                {'message:': f'current too short', 'len': len(node.blockchain)}, 409),
        }
        status = node.blockchain.add_block(Block.from_json(block))
        if status == AddBlockStatus.OK:
            node.mem_pool -= set(map(Transaction.from_json, block['payload']['transactions']))
        elif status in (AddBlockStatus.VERIFICATION_FAILED, AddBlockStatus.CURRENT_CHAIN_TOO_SHORT):
            node.get_longest_chain()
        res = switcher[status]
        return jsonify(res[0]), res[1]
    return jsonify({'message': f'wrong format, block should contain {Block.__annotations__.keys()}'}), 400


@app.route('/get_blockchain_len', methods={'GET'})
def get_blockchain_len():
    return jsonify(len(node.blockchain)), 200


@app.route('/get_blockchain_hashes', methods={'GET'})
def get_blockchain_hashes():
    return jsonify(node.blockchain.hashes), 200


@app.route('/add_transaction', methods={'POST'})
def add_transaction():
    transaction = request.json
    if 'timestamp' not in transaction:
        transaction['timestamp'] = time.time()
    if type(transaction) == dict and all([x in transaction for x in Transaction.__annotations__]):
        node.add_transaction(Transaction.from_json(transaction))
        return jsonify('ok'), 201
    return jsonify({'message': 'error'}), 400


@app.route('/get_transactions', methods={'GET'})
def get_transactions():
    mem_pool = list(node.mem_pool)
    return jsonify({'transactions': mem_pool, 'count': len(mem_pool)}), 200


if __name__ == '__main__':
    host = '127.0.0.1'
    port = int(input())
    node = Node(f'{host}:{port}')
    print(1)
    threading.Thread(target=mine).start()
    print(3)
    app.run(host=host, port=port)
