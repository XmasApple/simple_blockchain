import validators
from flask import Flask, jsonify, request

from blockchain import Blockchain
from node import Node

app = Flask(__name__)


@app.route('/mine_block', methods={'GET'})
def mine_block():
    block = blockchain.mine_block(3)
    return jsonify(block.get_block()), 200


@app.route('/get_block', methods={'GET', 'POST'})
def get_block():
    block_id = request.args.get('id')
    if block_id.isdigit() and int(block_id) < len(blockchain.blocks):
        block = blockchain.blocks[int(block_id)]
        return jsonify(block.get_block()), 200
    else:
        return jsonify({"status": "error",
                        "message": f"wrong id {block_id}, chain length = {len(blockchain.blocks)}"}), 400


@app.route('/get_blockchain', methods={'GET'})
def get_blockchain():
    return jsonify({
        "chain": list(map(lambda x: x.get_block(), blockchain.blocks)),
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
    if type(nodes) == list and all(map(lambda x: validators.url(f"http://{x}/") is True, nodes)):
        if len(nodes) > 0:
            node.connect_nodes(nodes)
        return jsonify(list(node.nodes)), 201
    return jsonify({'message': 'some_nodes_has_wrong_url'}), 400


if __name__ == '__main__':
    blockchain = Blockchain()
    host = "127.0.0.1"
    port = int(input())
    node = Node(f"{host}:{port}")
    app.run(host=host, port=port)
