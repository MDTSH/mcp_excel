import configparser
import json
import os
import threading
import time
import traceback

import websocket

from cgb.se.monitor.base import MonitorDataManager


class ConnectionStatusConst():
    Status_None = "Connecting"
    Status_Connected = "Connected"
    Status_OK = "OK"
    Status_LoginFail = "Login Fail"
    Status_Closed = "Closed"
    Status_Stopped = "Stopped"
    Status_Error = "Error"
    Status_HeartBeat = "HB"


class MdpWebSocketClient:
    """
    web socket 基类
    """

    def __init__(self, key="", url=""):
        self.ws = None
        self.uri = url
        self.status_func = []
        self.connection_status = ConnectionStatusConst.Status_None
        self.login_success = False
        self.is_init = False
        self.init_lock = threading.Lock()
        self.msg_cache = []
        self.stop = True
        self.reconnect_interval = 2
        self.is_reconnect = False
        self.client_key = key

    def initialize(self, url=None):
        if self.is_init:
            return
        self.stop = False
        self.init_lock.acquire(True)
        if not self.is_init:
            if url is not None:
                self.uri = url
            try:
                self.init_ws()
                self.is_init = True
            except:
                traceback.print_exc()
        self.init_lock.release()

    def websocket_send(self, msg):
        print(self.__class__.__name__, "send:", self.client_key, msg)
        self.ws.send(msg)

    def send_msg(self, msg):
        if self.login_success:
            self.websocket_send(msg)
        else:
            self.msg_cache.append(msg)
            print(self.__class__.__name__, "cache msg:", self.client_key, msg)
            if not self.is_init:
                print(self.__class__.__name__, self.client_key, "initialize")
                self.initialize()

    def subscribe_status(self, f):
        """
        订阅连接状态
        :param f:
        :return:
        """
        print(self.__class__.__name__, " subscribe_status:", self.client_key, str(f))
        self.status_func.append(f)
        self.notify_status_f(f, self.connection_status)
        print(self.__class__.__name__, " subscribe_status: len=", self.client_key, len(self.status_func))
        if not self.is_init:
            self.initialize()

    def unsubscribe_status(self, f):
        """
        退订连接状态
        :param f:
        :return:
        """
        print(self.__class__.__name__, " unsubscribe_status:", self.client_key, str(f))
        if self.status_func.count(f) > 0:
            # try:
            self.status_func.remove(f)
        # except:
        #     pass
        print(self.__class__.__name__, " unsubscribe_status: len=", self.client_key, len(self.status_func))

    def notify_status(self, status):
        """
        通知连接状态
        :param status:
        :return:
        """
        self.connection_status = status
        print("notify_status", type(self).__name__, self.client_key, self.connection_status)
        for f in self.status_func:
            self.notify_status_f(f, status)

    def notify_status_f(self, f, status):
        f(status)

    def init_ws(self):
        """
        初始化线程
        :return:
        """
        # print(self.__class__.__name__, "init_ws:", self.uri)
        wsThread = threading.Thread(target=self.ws_thread)
        wsThread.start()

    def ws_thread(self):
        """
        执行线程
        :return:
        """
        time.sleep(1)
        print(self.__class__.__name__, "ws_thread init: ", self.client_key, self.uri)
        self.ws = websocket.WebSocketApp(self.uri,
                                         on_message=self.on_message,
                                         on_error=self.on_error,
                                         on_close=self.on_close,
                                         on_open=self.on_open)
        self.ws.run_forever()

    def on_open(self, ws):
        try:
            self.notify_status(ConnectionStatusConst.Status_Connected)
            self.on_login_success()
        except:
            traceback.print_exc()

    def on_login_success(self):
        if len(self.msg_cache) > 0:
            to_send = self.msg_cache
            self.msg_cache = []
            for msg in to_send:
                self.websocket_send(msg)
        self.login_success = True
        self.is_reconnect = False
        self.notify_status(ConnectionStatusConst.Status_OK)

    def on_login_fail(self, msg):
        self.login_success = False
        if msg is not None and msg != "":
            msg = ConnectionStatusConst.Status_LoginFail + ": " + msg
        else:
            msg = ConnectionStatusConst.Status_LoginFail
        self.notify_status(msg)

    def on_message(self, ws, msg):
        pass

    def on_error(self, ws, error):
        print(self.__class__.__name__, "on_error: ", self.client_key, str(error))
        self.notify_status(ConnectionStatusConst.Status_Error)

    def on_close(self, ws):
        self.login_success = False
        print(self.__class__.__name__, "on_close:", self.client_key, "stop=", str(self.stop))
        self.notify_status(ConnectionStatusConst.Status_Closed)
        if not self.stop:
            time.sleep(self.reconnect_interval)
            self.is_reconnect = True
            self.init_ws()

    def dispose(self):
        self.login_success = False
        self.stop = True
        self.ws.close()
        self.is_init = False
        print(self.__class__.__name__, self.client_key, "dispose")
        # self.notify_status(ConnectionStatusConst.Status_Stopped)


class MonitorClient(MdpWebSocketClient):

    def __init__(self, env, url="ws://localhost:8050"):
        super().__init__(key=env, url=url)
        self.sub_dict = {}
        self.data_manager = MonitorDataManager()
        self.env = env
        self.request_dict = {}
        self.request_seq = 0

    # def on_open(self):
    #     self.on_login_success()

    # def notify_status_f(self, f, status):
    # f(self.env, status)

    def on_login_success(self):
        if self.is_reconnect:
            self.subscribe_all()
        super().on_login_success()

    def subscribe_all(self):
        for key in self.sub_dict:
            self.do_subscribe(key)

    def subscribe(self, key, f):
        key = str(key).lower()
        new_sub = False
        if key not in self.sub_dict:
            self.sub_dict[key] = []
            new_sub = True
        self.sub_dict[key].append(f)
        if new_sub:
            self.do_subscribe(key)
        else:
            image = self.data_manager.get_image(key)
            self.notify_data_f(f, self.env, key, image)

    def un_subscribe(self, key, f):
        key = str(key).lower()
        if key in self.sub_dict:
            funcs = self.sub_dict[key]
            funcs.remove(f)

    def notify_data(self, key, image):
        if key in self.sub_dict:
            funcs = self.sub_dict[key]
            for f in funcs:
                self.notify_data_f(f, self.env, key, image)

    def notify_data_f(self, f, env, key, image):
        f(image)

    def do_subscribe(self, key):
        data = {
            "key": key,
            "op": "subscribe",
        }
        self.send_msg(json.dumps(data, ensure_ascii=False))

    def update_args(self, category, key, data):
        k = (category + "." + key).lower()
        d = {
            "key": k,
            "op": "args",
            "data": str(data),
        }
        print("update_args:", self.env, category, key, data, d)
        self.send_msg(json.dumps(d, ensure_ascii=False))

    def send_control(self, key, ctrl_key):
        d = {
            "key": key,
            "op": "ctrl",
            "data": ctrl_key,
        }
        print("send_control:", self.env, key, ctrl_key, d)
        self.send_msg(json.dumps(d, ensure_ascii=False))

    def request(self, category, key, data, f):
        k = (category + "." + key).lower()
        self.request_seq += 1
        reply_to = f"replyTo{self.request_seq}"
        self.request_dict[reply_to] = f
        d = {
            "key": k,
            "op": "request",
            "data": str(data),
            'replyTo': reply_to,
        }
        print("request:", self.env, category, key, reply_to, data, d)
        self.send_msg(json.dumps(d, ensure_ascii=False))

    def on_message(self, ws, msg):
        print("on_message:", msg)
        try:
            data = json.loads(msg)
            op = data['op']
            if op == 'push':
                key = str(data["key"]).lower()
                self.data_manager.update_income(key, data)
                image = self.data_manager.get_image(key)
                self.notify_data(key, image)
            elif op == 'reply':
                reply_to = data['replyTo']
                if reply_to in self.request_dict:
                    f = self.request_dict[reply_to]
                    del self.request_dict[reply_to]
                    f(data['data'])
                else:
                    print(f"invalid replyTo: {reply_to}")
        except:
            traceback.print_exc()


class WorkbookClientManager:

    def __init__(self, cfg_file):
        self.client_seed = 0
        self.client_dict = {}
        cfg = configparser.ConfigParser()
        cfg.read(cfg_file)
        self.default_url = cfg.get("main", "monitor.url")
        self.wb_cfg_file = cfg.get("main", "server.cfg")
        self.is_running = True
        thread = threading.Thread(target=self.check_client_status)
        thread.start()

    def stop(self):
        self.is_running = False

    def check_client_status(self):
        print("WorkbookClientManager check thread start")
        while self.is_running:
            time.sleep(10)
            try:
                del_list = []
                info = []
                for key in self.client_dict:
                    client: MonitorClient = self.client_dict[key]
                    status_count = len(client.status_func)
                    topic_count = 0
                    topic_func_count = 0
                    for topic in client.sub_dict:
                        topic_count += 1
                        topic_func_count += len(client.sub_dict[topic])
                    info.append([client.env, status_count, topic_count, topic_func_count])
                    if status_count == 0 and topic_func_count == 0:
                        print("WorkbookClientManager stop:", info[-1])
                        client.dispose()
                        del_list.append(key)
                for key in del_list:
                    del self.client_dict[key]
                print("WorkbookClientManager check status:", info)
            except:
                traceback.print_exc()
        print("WorkbookClientManager check thread stop")

    def get_client_info(self, key):
        key = str(key).lower()
        result = {}
        if key in self.client_dict:
            client: MonitorClient = self.client_dict[key]
            result["url"] = client.uri
        return result

    def get_client(self, path, key):
        key = str(key).lower()
        if key not in self.client_dict:
            url = self.default_url
            self.client_seed += 1
            client_id = "wbc" + str(self.client_seed)
            wb_cfg_file = path + "/" + self.wb_cfg_file
            b = os.path.exists(wb_cfg_file)
            if b:
                with open(wb_cfg_file, 'r') as f:
                    config_string = '[main]\n' + f.read()
                cfg = configparser.ConfigParser()
                cfg.read_string(config_string)
                url = cfg.get("main", "monitor.url")
            client = MonitorClient(env=client_id, url=url)
            client.initialize()
            self.client_dict[key] = client
            print("WorkbookClientManager new client: %s=%s, id=%s, url=%s, key=%s, path=%s" %
                  (self.wb_cfg_file, b, client_id, url, key, path))
        return self.client_dict[key]


class MonitorClientManager:

    def __init__(self, cfg_file):
        self.client_dict = {}
        self.cat_env_dict = {}
        self.topic_cat_dict = {}
        self.cat_topic_dict = {}
        self.sub_dict = {}
        self.status_dict = {}
        cfg = configparser.ConfigParser()
        cfg.read(cfg_file)
        envs = cfg.get("main", "monitor.envs").split(",")
        self.env_default = str(cfg.get("main", "monitor.env.default")).lower()
        for env in envs:
            env = str(env).lower()
            self.client_dict[env] = {
                "env": env,
                "url": cfg.get("main", "monitor." + env + ".url"),
                "client": None,
            }

    def set_cat_env(self, cat, env):
        cat = str(cat).lower()
        env = str(env).lower()
        self.cat_env_dict[cat] = env
        ws = self.client_of_cat(cat)
        topics = None
        if cat in self.cat_topic_dict:
            topics = self.cat_topic_dict[cat]
            for topic in topics:
                ws.subscribe(topic, self.on_message)
        print("set_cat_env subscribe:", env, topics)
        self.on_status(env, ws.connection_status)

    def generate_topic(self, cat, key, cache_topic=False):
        topic = (cat + "." + key).lower()
        if cache_topic:
            self.topic_cat_dict[topic] = cat
            if cat not in self.cat_topic_dict:
                self.cat_topic_dict[cat] = []
            self.cat_topic_dict[cat].append(topic)
        return topic

    def topic_of_env(self, topic):
        if topic in self.topic_cat_dict:
            cat = self.topic_cat_dict[topic]
            return self.env_of_cat(cat)
        else:
            return ""

    def env_of_cat(self, cat):
        if cat not in self.cat_env_dict:
            self.cat_env_dict[cat] = self.env_default
        env = self.cat_env_dict[cat]
        return env

    def client_of_cat(self, cat) -> MonitorClient:
        if cat not in self.cat_env_dict:
            self.cat_env_dict[cat] = self.env_default
        env = self.cat_env_dict[cat]
        client = self.client_dict[env]
        self.ensure_start_client(client)
        return client["client"]

    def ensure_start_client(self, client):
        ws = client["client"]
        if ws is None:
            ws = MonitorClient(client["env"], url=client["url"])
            ws.subscribe_status(self.on_status)
            client["client"] = ws
            ws.initialize()

    def on_status(self, env, status):
        for cat in self.status_dict:
            cat_env = self.env_of_cat(cat)
            if env == cat_env:
                fs = self.status_dict[cat]
                content = cat + " " + env + " " + status
                for f in fs:
                    f(content)

    def subscribe_status(self, cat, f):
        cat = str(cat).lower()
        if cat not in self.status_dict:
            self.status_dict[cat] = []
        self.status_dict[cat].append(f)
        self.client_of_cat(cat)

    def unsubscribe_status(self, cat, f):
        cat = str(cat).lower()
        if cat in self.status_dict:
            fs: list = self.status_dict[cat]
            if fs.count(f) > 0:
                fs.remove(f)

    def on_message(self, env, topic, image):
        tp_env = self.topic_of_env(topic)
        # print("on_message manager:", env,tp_env, topic, image)
        if tp_env == env:
            self.notify_data(topic, image)

    def notify_data(self, topic, image):
        if topic in self.sub_dict:
            funcs = self.sub_dict[topic]
            for f in funcs:
                f(image)

    def send_control(self, cat, ctrl_key):
        cat = str(cat).lower()
        ws = self.client_of_cat(cat)
        ws.send_control(cat, ctrl_key)

    def update_args(self, cat, key, data):
        cat = str(cat).lower()
        ws = self.client_of_cat(cat)
        ws.update_args(cat, key, data)

    def subscribe(self, cat, key, f):
        cat = str(cat).lower()
        ws = self.client_of_cat(cat)
        topic = self.generate_topic(cat, key, True)
        is_new = False
        if topic not in self.sub_dict:
            self.sub_dict[topic] = []
            is_new = True
        self.sub_dict[topic].append(f)
        if is_new:
            ws.subscribe(topic, self.on_message)
        else:
            image = ws.data_manager.get_image(topic)
            f(image)

    def un_subscribe(self, cat, key, f):
        cat = str(cat).lower()
        topic = self.generate_topic(cat, key, False)
        if topic in self.sub_dict:
            funcs = self.sub_dict[topic]
            funcs.remove(f)
            if len(funcs) == 0:
                del self.sub_dict[topic]
                ws = self.client_of_cat(cat)
                ws.un_subscribe(topic, self.on_message)
