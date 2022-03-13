import socket
from typing import Any, List
from concurrent.futures import ThreadPoolExecutor, Future

import time
import requests

from block import Block

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.connect(("8.8.8.8", 80))
nodes = [f"{s.getsockname()[0]}:5000"]
s.close()


def broadcast_get(route: str) -> List[Future]:
    if len(nodes) > 0:
        with ThreadPoolExecutor(len(nodes)) as executor:
            futures = [executor.submit(requests.get, f'http://{node}/{route}') for node in nodes]
            return futures
    return []


def broadcast_post(route: str, json: Any) -> List[Future]:
    if len(nodes) > 0:
        with ThreadPoolExecutor(len(nodes)) as executor:
            futures = [executor.submit(requests.post, f'http://{node}/{route}', json=json) for node in nodes]
            return futures
    return []


def mine():
    while True:
        latest = list(zip(nodes, [future.result().json() for future in broadcast_get('get_last_block')]))
        print(latest)
        node, previous_block = max(latest, key=lambda x: x[1]['block']['id'])

        mem_pool = requests.get(f'http://{node}/get_mem_pool').json()
        difficulty = requests.get(f'http://{node}/get_blockchain_difficulty').json()['difficulty']
        print(previous_block)
        print(mem_pool)
        print('diff', difficulty)
        block = Block(id=previous_block['block']['id'] + 1,
                      previous=previous_block['hash'],
                      payload={'transactions': [transaction for transaction in mem_pool]})
        while not block.hash.startswith("0" * difficulty):
            block.nonce += 1
            block.timestamp = int(time.time())
        print(block)
        print([future.result().json() for future in broadcast_post('add_block', block.dict())])


if __name__ == '__main__':
    mine()
