import time
from queue import Queue
from urllib.request import urlopen
from bs4 import BeautifulSoup
from threading import Thread, Lock


class Bot:
    def __init__(self):
        self.res_queue = Queue()
        self.size = 0

    @staticmethod
    def get_data_url(url):
        with urlopen(url) as r:
            bs = BeautifulSoup(r.read(), 'html.parser')
            res = bs.select('a[href*="tvn24"]:not([href^="mailto"])')
            res = {re.get('href') for re in res if not re.get('href').endswith('/')}
            return res

    def get_data(self, link_queue, size_lock):
        while not link_queue.empty():
            url = link_queue.get(block=False)
            with urlopen(url) as r:
                bs = BeautifulSoup(r.read(), 'html.parser')
                res = bs.select('a[href*="tvn24"]:not([href^="mailto"])')
                res = {re.get('href') for re in res if not re.get('href').endswith('/')}

            link_queue.task_done()
            self.res_queue.put(res)

            with size_lock:
                self.size += 1

    def manage_threads(self, url, n):
        start_queue = Queue()
        size_lock = Lock()
        start_queue.put(url)
        self.get_data(start_queue, size_lock)

        start = time.perf_counter()
        # TODO create method for multiply run this code
        # TODO add docstrings, DRY, KISS pylint
        for _ in range(n):
            link_queue = Queue()
            print("zaczynamy")
            print(self.res_queue.qsize())

            for url in range(self.res_queue.qsize()):
                for item in self.res_queue.get():
                    link_queue.put(item)

            num_thread = 6

            for _ in range(num_thread):
                t = Thread(target=self.get_data, args=(link_queue, size_lock))
                t.start()

            link_queue.join()

            end = time.perf_counter()
            print(end - start)

        links_sum = sum(len(self.res_queue.get()) for _ in range(self.res_queue.qsize()))

        print(links_sum, self.size)

    def manage_without_threads(self, url):

        results = self.get_data_url(url)
        start = time.perf_counter()
        links = []
        for url in results:
            links.append(self.get_data_url(url))

        end = time.perf_counter()
        print(end - start)

        links_sum = sum(len(result) for result in links)

        print(links_sum)


if __name__ == "__main__":
    g = Bot()
    g.manage_threads("https://www.tvn24.pl", 1)
