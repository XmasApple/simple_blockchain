import threading
import time
from typing import List

import requests


class Node:
    def __init__(self, ip: str):
        self.ip = ip
        self.nodes: set = set()
        self.mem_pool = []

    def connect_nodes(self, nodes: List[str]) -> None:
        olds = [self.ip] + list(self.nodes)
        news = []
        for node in nodes:
            if node not in self.nodes:
                news.append(node)
                self.nodes.add(node)
        inputs = [(node, olds + news) for node in news] + [(node, news) for node in olds]
        if not olds[1:] == list(self.nodes):
            threads = [threading.Thread(target=self.share_nodes, args=args, name=f"share_to {args[0]}") for args in
                       inputs]
            [t.start() for t in threads]
            # [t.join() for t in threads] # not necessary and too slow for network

    def share_nodes(self, node, nodes: List[str]) -> None:
        if node != self.ip:
            for i in range(5):
                try:
                    print(requests.post(f"http://{node}/connect_nodes", json=nodes).status_code)
                    break
                except ConnectionError:
                    pass
