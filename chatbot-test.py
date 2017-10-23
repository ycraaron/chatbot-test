from urllib import request
import requests
from timeit import default_timer as timer
from chatbot_nlp_model.nlp_debugger_test.mysql_utils.db_manager import DBConn

from intent_rules_generator.foundation.universal_rules.facilities import combination as type_facilities
from intent_rules_generator.foundation.universal_rules.action_types_temp import combination as type_actions
from intent_rules_generator.foundation.universal_rules.intended_action_types import combination as type_inten_actions
from intent_rules_generator.foundation.universal_rules.object_types import combination as type_object
from intent_rules_generator.foundation.universal_rules.function_types import combination as type_function
from intent_rules_generator.foundation.universal_rules.book_status import combination as type_book_status
from intent_rules_generator.foundation.universal_rules.indirect_action_types import combination as type_indirect_actions
from intent_rules_generator.foundation.universal_rules.query_types import combination as type_query

import json
import re


class NLPDebuggerTest(object):

    def __init__(self, use_memory, university, memory_size=5):
        self.db_conn = DBConn()
        if use_memory:
            self.ls_memory = []
        else:
            self.ls_memory = False
        self.use_memory = use_memory
        self.memory_size = memory_size
        self.start = timer()
        self.ls_word = ['% borrow %', '% request %']
        self.university = university

        self.dic_item_keyword = {
            'borrow': ['book', 'av', 'laptop', 'privilege'],
            'request': ['book', 'av', 'laptop', 'storage', 'hkall', 'facilities', 'cancel']
            # add more action here
        }

        self.dic_action_regex = {
            'borrow': [type_actions['CIRCULATION_BORROW'], type_inten_actions['CIRCULATION BORROW']],
            'request': [type_actions['CIRCULATION_REQUEST'], type_inten_actions['CIRCULATION REQUEST']]
            # add more regex for action here
        }
        self.dic_item_regex = {
            'book': [type_object['BOOK'], type_object['NEW BOOK'], type_object['LEISURE BOOK']],
            'av': [type_object['AV'], type_facilities['AV ROOM'], type_facilities['AV ROOMS']],
            'privilege': [type_query['PRIVILEGE']],
            'laptop': [type_object['LAPTOP / TABLET']],
            'storage': [type_function['STORAGE'], type_book_status['STORAGE']],
            'hkall': [[{'hkall': r'HKALL'}]],
            'facilities': [type_function['FACILITIES']],
            'cancel': [type_actions['CANCELLATION'], type_inten_actions['CANCELLATION'],
                       type_indirect_actions['CANCELLATION']]
            # add more regex for item here
        }

        self.ls_borrow_item_reg = []
        self.ls_request_item_reg = []

    def fetch_message_by_parent(self, conver_id):
        sql = "SELECT user_input_slot FROM whatsapp_record_slot WHERE parent = %s AND chinese = 0 and multimedia = 0"
        result = self.db_conn.fetch_data(sql, conver_id)
        return result

    def fetch_parent_id(self):
        sql = "select DISTINCT(parent) as parent_id from whatsapp_record_slot where chinese = 0 and multimedia = 0 and parent > 0"
        result = self.db_conn.fetch_data(sql, [])
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
        req = requests.post(url, data=params.encode('ascii'), headers=headers)
        # response = request.urlopen(req)
        # print(req.text)
        return req
        # return response

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

    def action_filter(self, msg):
        ls_result = []

        # borrow = type_actions['CIRCULATION_BORROW']
        # borrow_inten = type_inten_actions['CIRCULATION BORROW']
        # for regex in borrow_inten:
        #     borrow.append(regex)
        #
        # request = type_actions['CIRCULATION_REQUEST']
        # request_inten = type_inten_actions['CIRCULATION REQUEST']
        #
        # for regex in request_inten:
        #     request.append(regex)

        # iterate through the action dictionary.
        for key_action in self.dic_action_regex:
            tag_found = 0
            for ls_regex_action in self.dic_action_regex[key_action]:
                # print(ls_regex_action)
                for dic_regex in ls_regex_action:
                    for key in dic_regex:
                        result = re.findall(dic_regex[key], msg, flags=re.IGNORECASE)
                        if result:
                            # go to next action
                            tag_found = 1
                            break
                    if tag_found:
                        # go to next action
                        break
                if tag_found:
                    # go to next action
                    # print('action found:', key_action)
                    ls_result.append(key_action)
                    break
        return ls_result

    def item_filter(self, msg='', action=''):
        # type_object['BOOK']
        # type_object['NEW BOOK']
        # type_object['LEISURE BOOK']
        # type_object['AV']
        # type_object['LAPTOP / TABLET']
        # type_object['PRIVILEGE']
        # type_facilities['AV ROOM']
        # type_facilities['AV ROOMS']
        #
        # type_function['STORAGE']
        # type_book_status['STORAGE']
        # reg_HKALL = r'HKALL'
        # type_facilities['FACILITIES']
        # type_actions['CANCELLATION']
        # type_inten_actions['CANCELLATION']
        # type_indirect_actions['CANCELLATION']
        ls_item_found = []
        for item in self.dic_item_keyword[action]:
            # print(item)
            found_tag = 0
            for ls_item_regex in self.dic_item_regex[item]:
                # print(ls_item_regex)
                for dic_item_regex in ls_item_regex:
                    for key in dic_item_regex:
                        # print(dic_item_regex[key])
                        result = re.findall(dic_item_regex[key], msg, flags=re.IGNORECASE)
                        if result:
                            found_tag = 1
                            # go to next item
                            break
                    if found_tag:
                        # go to next item
                        break
                if found_tag:
                    # go to next item
                    ls_item_found.append(item)
                    break
        return ls_item_found

    def process_response(self, msg, response, dic_msg):
        ls_intent = []
        # print(response.code)
        # obj_json = json.loads(response.read())
        obj_json = response.json()
        # print(obj_json)
        steps = obj_json['debug']
        step_1 = steps['step_1']
        step_7 = steps['step_7']
        step_8 = steps['step_8']
        step_9 = steps['step_9']

        if step_1:
            all_intents = [item['name'] for item in step_1['debug']]
            ls_intent = all_intents
        if step_7:
            all_intents = step_7['output']['all_intents']
            if all_intents:
                ls_intent = self.process_memory(all_intents, ls_intent)
        if 'output' in step_8.keys():
            all_intents = step_8['output']['all_intents']
            if all_intents:
                ls_intent = self.process_memory(all_intents, ls_intent)
        if 'output' in step_9.keys():
            all_intents = step_9['output']['all_intents']
            if all_intents:
                ls_intent = self.process_memory(all_intents, ls_intent)

        return ls_intent
        # self.file_output.write('msg: '.encode('utf-8'))
        # self.file_output.write(msg.encode('utf-8'))
        # self.file_output.write(';'.encode('utf-8'))
        # self.file_output.write('\n'.encode('utf-8'))
        # self.file_output.write('intents: '.encode('utf-8'))
        # if ls_intent:
        #     for intent in ls_intent:
        #         self.file_output.write(intent.encode('utf-8'))
        #         self.file_output.write(','.encode('utf-8'))
        # self.file_output.write('\n'.encode('utf-8'))

    def process_messsage(self, msg):
        # search first place keyword (borrow and request):
        # msg = 'Can I borrow paperback books for electronic LEXICA_LibraryMaterial_resources?'
        # msg = 'Good morning. If I request a book from another university through HKALL, and borrow it with my Organization_phrases studentcard, can I borrow and return the book from LEXICA_LibraryBranch_main_library @ HKU?'
        dic_msg = {'msg': msg, 'keyword_action': [], 'keyword_item': [], 'intent': []}
        action_result = self.action_filter(msg)
        # print(action_result)
        # if action is found
        if action_result:
            for action in action_result:
                if action not in dic_msg['keyword_action']:
                    dic_msg['keyword_action'].append(action)
                ls_item_result = self.item_filter(msg, action)
                # print(ls_item_result)
                # item found, action found
                if ls_item_result:
                    for item in ls_item_result:
                        if item not in dic_msg['keyword_item']:
                            dic_msg['keyword_item'].append(item)

        response = self.query(msg, self.university)
        ls_intent = self.process_response(msg, response, dic_msg)
        if ls_intent:
            for intent in ls_intent:
                if intent not in dic_msg['intent']:
                    dic_msg['intent'].append(intent)
        # print(dic_msg)
        return dic_msg

    def conversation(self, conversation_id, order_id, use_msg = 0, ls_msg = []):
        start = timer()

        if use_msg and ls_msg:
            message_queue = ls_msg
        else:
            message_queue = [msg['user_input_slot'] for msg in self.fetch_message_by_parent(conversation_id)]

        print(len(message_queue), 'messages to deal with for conversation', order_id, ' conversation parent id:', conversation_id)
        ls_db_data = []
        if message_queue:
            if self.use_memory:
                for msg in message_queue:
                    print(msg)
                    # return the processed msg dictionary
                    process_result = self.process_messsage(msg)
                    msg = process_result['msg']
                    ls_action = process_result['keyword_action']
                    ls_item = process_result['keyword_item']
                    ls_intent = process_result['intent']

                    str_action = ''
                    str_item = ''
                    str_intent = ''

                    if ls_action:
                        for action in ls_action:
                            if str_action == '':
                                str_action += action
                            else:
                                str_action = str_action + ',' + action

                    if ls_item:
                        for item in ls_item:
                            if str_item == '':
                                str_item += item
                            else:
                                str_item = str_item + ',' + item

                    if ls_intent:
                        for intent in ls_intent:
                            if str_intent == '':
                                str_intent += intent
                            else:
                                str_intent = str_intent + ',' + intent

                    result_tuple = (msg, str_action, str_item, str_intent, str(conversation_id))
                    ls_db_data.append(result_tuple)

                self.save_result_to_db(ls_db_data)
        end = timer()
        print(round(end - start, 2), ' seconds used for ', len(message_queue), ' mesages in conversation parent', conversation_id)

    def save_result_to_db(self, params):
        # print(params)
        sql = 'INSERT INTO nlp_debugger_test_result(msg_slot, keyword_action, keyword_item, intent, conversation_id) VALUES(%s,%s,%s,%s,%s)'
        print(self.db_conn.insert_data(sql, params))

    def __test(self):
        response = self.query("Hi, I want to borrow a book!", 'cmu', False)
        print(response.code)
        obj_json = json.loads(response.read())
        print(obj_json)
