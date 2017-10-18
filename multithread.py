import queue
import threading
import time
import json
from urllib import parse, request
from timeit import default_timer as timer
from dbutil.db_manager import DBConn

exitFlag = 0


class MyThread (threading.Thread):
    def __init__(self, t_id, name, queue):
        threading.Thread.__init__(self)
        self.t_id = threadID
        self.name = name
        self.work_queue = queue

    def run(self):
        print("new thread：" + self.name)
        send_post(self.name, self.work_queue)
        print("quit thread：" + self.name)


def send_post(t_name, queue):
    while not exitFlag:
        queue_lock.acquire()
        if not work_queue.empty():
            msg = queue.get()
            queue_lock.release()
            params = json.dumps({'msg': msg, 'uni': 'cmu'})
            headers = {
                "Host": "192.168.0.100:8000",
                "Connection": "keep-alive",
                "Accept": "*/*",
                "X-Requested-With": "XMLHttpRequest",
                "Content-type": "application/json",
                "Accept": "text/plain"
            }
            url = 'http://192.168.0.100:8000/debug'  # Set destination URL here
            req = request.Request(url, data=params.encode('ascii'), headers=headers, method='POST')
            response = request.urlopen(req)
            print("%s processing %s" % (t_name, msg))
        else:
            queue_lock.release()
        time.sleep(1)


db_conn = DBConn()


def fetch_data(target):
    sql = "SELECT user_input FROM whatsapp_record WHERE user_input LIKE %s LIMIT 100"
    result = db_conn.fetch_data(sql, target)
    ls_msg = [msg['user_input'] for msg in result]
    return ls_msg


def process_data(thread_name, q):
    while not exitFlag:
        queue_lock.acquire()
        if not work_queue.empty():
            data = q.get()
            queue_lock.release()
            print("%s processing %s" % (thread_name, data))
        else:
            queue_lock.release()
        time.sleep(1)

thread_list = ["thread-1", "thread-2", "thread-3","thread-4","thread-5","thread-6","thread-7","thread-8","thread-9","thread-10" ]
name_list = ["One", "Two", "Three", "Four", "Five"]
msg_list = ["1 Hi, can I borrow a book?", "2 Hi, can I borrow a book?", "3 Hi, can I borrow a book?", "4 Hi, can I borrow a book?", "5 Hi, can I borrow a book?"]
msg_list = fetch_data('%book%')
print(msg_list)
queue_lock = threading.Lock()
work_queue = queue.Queue(len(msg_list))
threads = []
threadID = 1

start = timer()
# create new threads
for t_name in thread_list:
    thread = MyThread(threadID, t_name, work_queue)
    thread.start()
    threads.append(thread)
    threadID += 1

# fill queue
queue_lock.acquire()
for msg in msg_list:
    work_queue.put(msg)
queue_lock.release()

# 等待队列清空
while not work_queue.empty():
    pass

# 通知线程是时候退出
exitFlag = 1

# 等待所有线程完成
for t in threads:
    t.join()
print("quit main thread")

end = timer()
print(end-start)
