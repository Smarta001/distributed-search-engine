from queue import Queue

crawl_queue = Queue()

visited = set()

def add_url(url):
    if url not in visited:
        visited.add(url)
        crawl_queue.put(url)

def get_url():
    if crawl_queue.empty():
        return None
    return crawl_queue.get()