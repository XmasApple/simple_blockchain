from blockchain import Blockchain

if __name__ == '__main__':

    blockchain = Blockchain()
    for i in range(10):
        blockchain.mine_block(3)
    print(blockchain.verify())

    blockchain = Blockchain()
    for i in range(10):
        blockchain.mine_block(3)
    blockchain.blocks[5].payload = "some fake"
    print(blockchain.verify())

