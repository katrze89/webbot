""" Package for bot """
import logging
from queue import Queue
import time
from urllib.request import urlopen
from threading import Thread
from bs4 import BeautifulSoup

NUM_THREADS = 6

FORMAT = "[%(threadName)s, %(asctime)s] %(message)s"
logging.basicConfig(filename="logfile.log", level=logging.DEBUG, format=FORMAT)


def count_time(func):
    """Decorator to count duration of function

    :param func:
    :return:
    """

    def decorated_func(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        end = time.perf_counter()
        logging.info(f"performance time: {end - start}")
        return result

    return decorated_func


class Bot:
    """Bot to count number of internal a href's

    """

    def __init__(self):
        """Init class

        """
        self.res_queue = Queue()
        self.results = 0

    def get_data(self, link_queue):
        """Obtained set of urls for given queue

        :param link_queue: queue with url links
        :return:
        """
        while not link_queue.empty():
            url = link_queue.get(block=False)
            try:
                with urlopen(url) as url_open:
                    beautys = BeautifulSoup(url_open.read(), 'html.parser')
                    res = beautys.select('a[href*="tvn24"]:not([href^="mailto"])')
                    res = {re.get('href') for re in res if not re.get('href').endswith('/')}
            except:  # pylint: disable=bare-except
                pass
            else:
                link_queue.task_done()
                self.res_queue.put(res)

    def fill_link_queue(self, link_queue=Queue()):
        """fill the link_queue with urls

        :param link_queue: link Queue
        :return: link_queue
        """
        while not self.res_queue.empty():
            for urls in self.res_queue.get():
                link_queue.put(urls)
        self.results += link_queue.qsize()

        return link_queue

    @count_time
    def manage_bot(self, url, concurrency=True, levels=1):
        """Manage counting with threads

        :param url: main url
        :param concurrency: yes or no to run function in threads
        :param levels: how deep counts the internal url's
        :return:
        """
        start_queue = Queue()
        start_queue.put(url)

        self.get_data(start_queue)

        for level in range(levels):
            logging.info(f"start level {level}")

            link_queue = self.fill_link_queue()

            if concurrency:
                for _ in range(NUM_THREADS):
                    thread = Thread(target=self.get_data, args=(link_queue,))
                    thread.start()
                link_queue.join()
            else:
                self.get_data(link_queue)

        for _ in range(self.res_queue.qsize()):
            self.results += len(self.res_queue.get())
        logging.info(f"number of results: {self.results}")


if __name__ == '__main__':
    bot = Bot()  # pylint: disable=invalid-name
    bot.manage_bot('https://www.tvn24.pl', concurrency=False)
