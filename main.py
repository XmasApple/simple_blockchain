from blockchain import Blockchain
from flask import Flask, jsonify

app = Flask(__name__)


@app.route('/mine_block', methods={'GET'})
def mine_block():
    block = blockchain.mine_block(3)
    return jsonify(block.get_block()), 200


@app.route('/get_blockchain', methods={'GET'})
def get_blockchain():
    return jsonify(list(map(lambda x: x.get_block(), blockchain.blocks))), 200


@app.route('/verify_blockchain', methods={'GET'})
def verify_blockchain():
    number = blockchain.verify()
    if number == -1:
        return jsonify({"status": "success"}), 200
    else:
        return jsonify({"status": "error", "message": f"wrong block number {number}"}), 409


if __name__ == '__main__':
    blockchain = Blockchain()
    app.run()
