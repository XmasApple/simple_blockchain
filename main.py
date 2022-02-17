import validators
from flask import Flask, jsonify, request

from block import Block
from blockchain import Blockchain, AddBlockStatus
from node import Node

app = Flask(__name__)


@app.route('/mine_block', methods={'GET'})
def mine_block():
    block = blockchain.mine_block()
    return jsonify(block.get_json()), 200


@app.route('/get_block', methods={'GET', 'POST'})
def get_block():
    block_id = request.args.get('id')
    if block_id.isdigit() and int(block_id) < len(blockchain.blocks):
        block = blockchain.blocks[int(block_id)]
        return jsonify(block.get_json()), 200
    else:
        return jsonify({"status": "error",
                        "message": f"wrong id {block_id}, chain length = {len(blockchain.blocks)}"}), 400


@app.route('/get_blockchain', methods={'GET'})
def get_blockchain():
    return jsonify({
        "chain": list(map(lambda x: x.get_json(), blockchain.blocks)),
        "length": len(blockchain.blocks)
    }), 200


@app.route('/verify_blockchain', methods={'GET'})
def verify_blockchain():
    number = blockchain.verify()
    if number == -1:
        return jsonify({"status": "success"}), 200
    else:
        return jsonify({"status": "error", "message": {"message": f"wrong block number {number}",
                                                       "block": blockchain.blocks[number]}}), 412


@app.route("/connect_nodes", methods={'POST'})
def connect_nodes():
    nodes = request.get_json()
    # print(nodes)
    if type(nodes) == list and all(map(
            lambda x: type(x) == str and validators.url(x if x.startswith("http://") else f"http://{x}/") is True,
            nodes)):
        if len(nodes) > 0:
            node.connect_nodes(nodes)
        return jsonify(list(node.nodes)), 201
    return jsonify({'message': 'some_nodes_has_wrong_url'}), 400


@app.route("/add_block", methods={'POST'})
def add_block():
    block = request.get_json()
    if type(block) == dict and all([x in block for x in ["id", "previous", "payload", "nonce"]]):
        switcher = {
            AddBlockStatus.OK: ({'message': 'block added'}, 201),
            AddBlockStatus.VERIFICATION_FAILED: ({'message:': 'verification failed'}, 409),
            AddBlockStatus.CURRENT_CHAIN_LONGER: ({'message:': f'current longer', 'len': len(blockchain)}, 409),
            AddBlockStatus.CURRENT_CHAIN_TOO_SHORT: ({'message:': f'current too short', 'len': len(blockchain)}, 409),
        }
        res = switcher[blockchain.add_block(Block.from_json(block))]
        return jsonify(res[0]), res[1]
    return jsonify({'message': 'wrong format, block should contain "id", "previous", "payload", "nonce"'}), 400


if __name__ == '__main__':
    blockchain = Blockchain()
    host = "127.0.0.1"
    port = int(input())
    node = Node(f"{host}:{port}")
    app.run(host=host, port=port)
