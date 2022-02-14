from blockchain import Blockchain
from flask import Flask, jsonify, request

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
        return jsonify({"status": "error", "message": f"wrong id {block_id}"})


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
                                                       "block": blockchain.blocks[number]}}), 409


if __name__ == '__main__':
    blockchain = Blockchain()
    app.run(host="localhost", port=80)
