from concurrent.futures import ThreadPoolExecutor, Future
from typing import List, Any

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

    def broadcast_get(self, route: str, nodes: List[str] = None) -> List[Future]:
        if not nodes:
            nodes = list(self.nodes)
        if self.ip in nodes:
            nodes.remove(self.ip)
        if len(nodes) > 0:
            with ThreadPoolExecutor(len(nodes)) as executor:
                futures = [executor.submit(requests.get, f'http://{node}/{route}') for node in nodes]
                return futures
        return []

    def broadcast_post(self, route: str, json: Any = None, nodes: List[str] = None) -> List[Future]:
        if not nodes:
            nodes = list(self.nodes)
        if self.ip in nodes:
            nodes.remove(self.ip)
        if len(nodes) > 0:
            with ThreadPoolExecutor(len(nodes)) as executor:
                futures = [executor.submit(requests.post, f'http://{node}/{route}', json=json) for node in nodes]
                return futures
        return []

    def connect_nodes(self, nodes: List[str]) -> None:
        olds = [self.ip] + list(self.nodes)
        news = []
        for node in nodes:
            if node not in self.nodes:
                news.append(node)
                self.nodes.add(node)
        inputs = [(node, olds + news) for node in news] + [(node, news) for node in olds]
        if len(news) > 1 or (len(news) > 0 and self.ip not in news):
            with ThreadPoolExecutor(len(inputs)) as executor:
                futures = [executor.submit(self.share_nodes, *args) for args in inputs]
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
        futures = self.broadcast_get('get_blockchain_len', nodes)
        lens = [future.result().json() for future in futures]
        longest = max(lens)
        longest_node = nodes[lens.index(longest)]
        if longest > len(self.blockchain):
            hashes = requests.get(f'http://{longest_node}/get_blockchain_hashes').json()
            start = 0
            for i, (a, b) in enumerate(zip(hashes, self.blockchain.hashes)):
                if a != b:
                    start = i
                    break
            blockchain_data = requests.get(f'http://{longest_node}/get_blockchain?start={start}').json()
            self.blockchain.blocks = [Block.from_json(block_data['block']) for block_data in
                                      blockchain_data['chain']]
            return True
        return False

    def share_block(self, block: Block, nodes: List[str] = None) -> None:
        print('share')
        futures = self.broadcast_post('add_block', vars(block), nodes)
        print(list(map(lambda x: (x.status_code, x.json()), [futures.result() for futures in futures])))
        # failed = list(map(lambda x: x.url.split('/')[2],
        #                   filter(lambda x: x.status_code == 409, map(lambda x: x.result(), futures))))

    def add_transaction(self, transaction: Transaction) -> bool:
        if transaction in self.mem_pool:
            return False
        self.mem_pool.add(transaction)
        self.broadcast_post('add_transaction', vars(transaction))
        return True
