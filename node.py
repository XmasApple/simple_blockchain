from concurrent.futures import ThreadPoolExecutor
from typing import List

import requests

from block import Block
from blockchain import Blockchain
from transaction import Transaction


class Node:
    def __init__(self, ip: str):
        self.ip: str = ip
        self.blockchain: Blockchain = Blockchain()
        self.nodes: set = set()
        self.mem_pool: set[Transaction] = set()

    def connect_nodes(self, nodes: List[str]) -> None:
        olds = [self.ip] + list(self.nodes)
        news = []
        for node in nodes:
            if node not in self.nodes:
                news.append(node)
                self.nodes.add(node)
        inputs = [(node, olds + news) for node in news] + [(node, news) for node in olds]
        if len(news) > 1 or (len(news) > 0 and self.ip in news):
            with ThreadPoolExecutor(len(inputs)) as executor:
                futures = [executor.submit(self.share_nodes, *args) for args in inputs]
                [f.result() for f in futures]
                # [f.result() for f in futures]  # not necessary and too slow for network
        with ThreadPoolExecutor(len(nodes)) as executor:
            executor.submit(self.get_longest_chain)

    def share_nodes(self, node: str, nodes: List[str]) -> bool:
        if node != self.ip:
            for i in range(5):
                try:
                    print(requests.post(f'http://{node}/connect_nodes', json=nodes).status_code)
                    return True
                except ConnectionError:
                    pass
        return False

    def get_longest_chain(self, nodes: List[str] = None) -> bool:
        if not nodes:
            nodes = list(self.nodes)
        with ThreadPoolExecutor(len(nodes)) as executor:
            futures = [executor.submit(requests.get, f'http://{node}/get_blockchain_len') for node in nodes]
            lens = [future.result().json() for future in futures]
            print(lens)
            print(nodes)
            longest = max(lens)
            longest_node = nodes[lens.index(longest)]
            print(longest_node)
            print(longest, len(self.blockchain))
            if longest > len(self.blockchain):
                hashes = requests.get(f'http://{longest_node}/get_blockchain_hashes').json()
                start = 0
                for i, (a, b) in enumerate(zip(hashes, self.blockchain.hashes)):
                    if a != b:
                        start = i
                        break
                blockchain_data = requests.get(f'http://{longest_node}/get_blockchain?start={start}').json()
                self.blockchain.blocks = [Block(block_data['block']) for block_data in
                                          blockchain_data['chain']]
                return True

        return False

    def share_block(self, block: Block, nodes: List[str] = None) -> None:
        if not nodes:
            nodes = list(self.nodes)
        with ThreadPoolExecutor(len(nodes)) as executor:
            features = [executor.submit(requests.post, f'http://{node}/add_block', json=vars(block)) for node in nodes]
            # failed = list(map(lambda x: x.url.split('/')[2],
            #                   filter(lambda x: x.status_code == 409, map(lambda x: x.result(), features))))

    def add_transaction(self, transaction: Transaction) -> bool:
        if transaction not in self.mem_pool:
            self.mem_pool.add(transaction)
            nodes = list(self.nodes)
            with ThreadPoolExecutor(len(nodes)) as executor:
                features = [executor.submit(requests.post, f'http://{node}/add_transaction', json=vars(transaction)) for node in nodes]
                return True
        return False
