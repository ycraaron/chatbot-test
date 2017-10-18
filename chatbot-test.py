from dbutil.db_manager import DBConn
from urllib import parse, request
from timeit import default_timer as timer
from queue import Queue
from threading import Thread

import queue
import json


class NLPDebuggerTest(object):

    def __init__(self, use_memory, memory_size=5):
        self.db_conn = DBConn()
        if use_memory:
            self.ls_memory = []
        else:
            self.ls_memory = False
        self.use_memory = use_memory
        self.memory_size = memory_size
        self.file_output = open('output.txt', 'wb')
        self.start = timer()

    def fetch_data(self, target):
        sql = "SELECT user_input FROM whatsapp_record WHERE user_input LIKE %s AND chinese = 0"
        result = self.db_conn.fetch_data(sql, target)
        return result

    def query(self, msg, uni):
        if not self.ls_memory:
            params = json.dumps({'msg': msg, 'uni': uni})
        else:
            params = json.dumps({'msg': msg, 'uni': uni, 'features': self.ls_memory})
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
        return response

    def transaction(self, word):
        message_queue = [msg['user_input'] for msg in self.fetch_data(word)]
        university = 'cmu'
        cnt = 0
        print(len(message_queue), 'messages to deal with.')
        component = len(message_queue) % 50
        mark = [i * 50 for i in range(1, component)]
        if message_queue:
            if self.use_memory:
                for msg in message_queue:
                    ls_intent = []
                    response = self.query(msg, university)
                    obj_json = json.loads(response.read())
                    # print(obj_json)
                    steps = obj_json['debug']
                    step_7 = steps['step_7']
                    step_8 = steps['step_8']
                    step_9 = steps['step_9']
                    if step_7:
                        all_intents = step_7['output']['all_intents']
                        if all_intents:
                            ls_intent = self.process_memory(all_intents, ls_intent)
                    if step_8:
                        all_intents = step_7['output']['all_intents']
                        if all_intents:
                            ls_intent = self.process_memory(all_intents, ls_intent)
                    if step_9:
                        all_intents = step_7['output']['all_intents']
                        if all_intents:
                            ls_intent = self.process_memory(all_intents, ls_intent)

                    self.file_output.write('msg: '.encode('utf-8'))
                    self.file_output.write(msg.encode('utf-8'))
                    self.file_output.write(';'.encode('utf-8'))
                    self.file_output.write('\n'.encode('utf-8'))
                    self.file_output.write('intents: '.encode('utf-8'))
                    if ls_intent:
                        for intent in ls_intent:
                            self.file_output.write(intent.encode('utf-8'))
                            self.file_output.write(','.encode('utf-8'))
                    self.file_output.write('\n'.encode('utf-8'))
                    cnt += 1
                    if cnt in mark:
                        end = timer()
                        print(end - self.start, ' seconds used for ', cnt, ' mesages.')

        end = timer()
        print(end - self.start, ' seconds used for ', len(message_queue), ' mesages.')
                    # print(self.ls_memory)

    def process_memory(self, all_intents, ls_intent):
        for intent in all_intents:
            dic = {}
            target_intent = intent['intent']
            dic['command'] = target_intent
            dic['features'] = intent['features']
            ls_intent.append(target_intent)
            if len(self.ls_memory) < self.memory_size:
                self.ls_memory.append(dic)
            else:
                # print("removed intent", self.ls_memory[0])
                del self.ls_memory[0]
                self.ls_memory.append(dic)
            return ls_intent

    def clear_memory(self):
        self.ls_memory = []

    def modify_memory_size(self, size):
        self.memory_size = size

    def test(self):
        response = self.query("Hi, I want to borrow a book!", 'cmu', False)
        print(response.code)
        obj_json = json.loads(response.read())
        print(obj_json)

ls_word = ['% borrow %', '% request %']
start = timer()
ins_test = NLPDebuggerTest(True)
for key_word in ls_word:
    ins_test.transaction(key_word)
    ins_test.clear_memory()

end = timer()
print((end - start))
