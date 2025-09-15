import datetime
import logging
import threading
import time
import traceback

from pyxll import RTD

from mcp.utils.async_process import process_pool


class AsyncProcessRtd(RTD):

    def __init__(self, mcp_object, method, args):
        self.value = ""
        self.mcp_object = mcp_object
        self.method = method
        self.args = args;

    def connect(self):
        print("AsyncProcessRtd connect:", self.method)
        if process_pool.is_sync_execute:
            self.value = process_pool.sync_execute(self.mcp_object, self.method, self.args)
        else:
            self.value = ""
            process_pool.execute_job(self.mcp_object, self.method, self.args, self.callback)

    def callback(self, data):
        self.value = data


class AsyncFuncRtd(RTD):

    def __init__(self):
        print("AsyncFuncRtd __init__", self)
        # self.func = f
        self.id = ""
        self.is_connected = False

    # def execute(self, data=None):
    #     # print("AsyncFuncRtd execute", self)
    #     if self.is_connected:
    #         print("AsyncFuncRtd execute", self)
    #         self.func(self)

    def connect(self):
        # print("AsyncFuncRtd connect", self)
        self.is_connected = True
        self.value = ""
        async_func_manager.add_rtd(self)

    def disconnect(self):
        # print("AsyncFuncRtd disconnect", self)
        self.is_connected = False


class ThreadFuncRtd(RTD):

    def __init__(self, f):
        print("ThreadFuncRtd __init__", self)
        self.func = f
        self.id = ""
        self.is_connected = False
        self._thread = threading.Thread(target=self.run)

    def run(self):
        for i in range(10):
            time.sleep(0.5)
            self.value = datetime.datetime.now()
        # val = self.func()
        # self.value = val

    # def execute(self, data=None):
    #     # print("AsyncFuncRtd execute", self)
    #     if self.is_connected:
    #         print("AsyncFuncRtd execute", self)
    #         self.func(self)

    def connect(self):
        # print("AsyncFuncRtd connect", self)
        self.is_connected = True
        self.value = ""
        self._thread.start()
        # async_func_manager.add_rtd(self)

    def disconnect(self):
        # print("AsyncFuncRtd disconnect", self)
        self.is_connected = False


# class AsyncFuncThread(AsyncBase):
#
#     def __init__(self):
#         super().__init__("", None)
#
#     def process(self, data):
#         data.execute()

# class AsyncFuncExecutor:
#
#     def __init__(self, f):
#         self.func = f
#
#     def execute(self, data=None):
#         pass

class MultiTimer(threading.Thread):
    """
    timer类
    """

    def __init__(self, id):
        self._thread = threading.Thread(target=self.run)
        self.log = logging.getLogger(__name__)
        self.id = id
        self.is_running = False
        self.check_interval = 0.1
        self.execute_delay = 0.01
        self.item_dict = {}
        self.item_key_seed = 0
        self.is_execute_delay = True

    def start(self):
        self.is_running = True
        self._thread.start()

    def _item_id(self):
        self.item_key_seed += 1
        return str(self.item_key_seed)

    def add_delay_execute(self, delay_seconds, f, data=None):
        """
        延迟delay_seconds秒执行
        :param delay_seconds:
        :param f:
        :param data:
        :return:
        """
        dt = datetime.datetime.now() + datetime.timedelta(seconds=delay_seconds)
        return self.add_execute(dt, f, data)

    def add_delay_execute_ms(self, ms, f, data=None):
        """
        延迟ms毫秒执行
        :param ms:
        :param f:
        :param data:
        :return:
        """
        dt = datetime.datetime.now() + datetime.timedelta(microseconds=ms * 1000)
        return self.add_execute(dt, f, data)

    def add_interval_execute(self, interval, f, data=None):
        """
        周期性执行
        :param interval:
        :param f:
        :param data:
        :return:
        """
        item_id = self._item_id()
        self.item_dict[item_id] = {
            "dt": datetime.datetime.now(),
            "interval": interval / 1000.0,
            "f": f,
            "data": data
        }
        return item_id

    def add_execute(self, dt, f, data=None):
        """
        指定时间执行
        :param dt:
        :param f:
        :param data:
        :return:
        """
        item_id = self._item_id()
        self.item_dict[item_id] = {
            "dt": dt,
            "interval": 0,
            "f": f,
            "data": data
        }
        # print("add_execute:", item_id, dt, str(f))
        return item_id

    def cancel_execute(self, item_id):
        if item_id in self.item_dict:
            del self.item_dict[item_id]
            return True
        else:
            return False

    def run(self):
        self.log.info("MultiTimer initialize: %s", self.id)
        self.initialize()
        self.log.info("MultiTimer run: %s", self.id)
        while self.is_running:
            try:
                time.sleep(self.check_interval)
                # print("MultiTimer execute:", self.id)
                keys = list(self.item_dict.keys())
                cur_time = datetime.datetime.now()
                for key in keys:
                    if key not in self.item_dict:
                        continue
                    item = self.item_dict[key]
                    if item["interval"] > 0:
                        # 周期性执行
                        td = cur_time - item["dt"]
                        if td.total_seconds() > item["interval"]:
                            f = item["f"]
                            f(item["data"])
                            item["dt"] = datetime.datetime.now()
                            if self.is_execute_delay:
                                time.sleep(self.execute_delay)
                    else:
                        # 指定时间执行
                        if item["dt"] <= cur_time:
                            # print("execute:", str(item))
                            del self.item_dict[key]
                            f = item["f"]
                            f(item["data"])
                            if self.is_execute_delay:
                                time.sleep(self.execute_delay)
            except:
                traceback.print_exc()
        self.log.info("MultiTimer dispose: %s", self.id)
        self.dispose()
        self.log.info("MultiTimer exit: %s", self.id)

    def initialize(self):
        pass

    def dispose(self):
        pass


class AsyncFuncManager:

    def __init__(self, thread_count, is_sync_execute=False):
        self.thread_group = []
        self.func_dict = {}
        self.rtd_dict = {}
        self.count = 1
        self.is_sync_execute = is_sync_execute
        if not is_sync_execute:
            for i in range(thread_count):
                t = MultiTimer("AFM.thread" + str(i + 1))
                t.is_execute_delay = False
                self.thread_group.append(t)
                t.start()

    def add_rtd(self, rtd):
        # if self.is_sync_execute:
        #     return
        # self.count += 1
        # index = self.count % len(self.thread_group)
        print("add_rtd:", rtd.id)
        id = rtd.id
        if self.is_sync_execute:
            if id in self.func_dict:
                f = self.func_dict[id]
                del self.func_dict[id]
                val = f()
                data = (val, id)
                self.set_value(data)
        else:
            self.thread_group[0].add_delay_execute_ms(0, self.execute, rtd.id)

    def execute(self, id):
        print("execute:", id)
        if id in self.func_dict:
            f = self.func_dict[id]
            del self.func_dict[id]
            time.sleep(0.05)
            val = f()
            self.thread_group[1].add_delay_execute_ms(0, self.set_value, (val, id))
            time.sleep(0.05)
            # self.set_value((val, id))

    def set_value(self, data):
        val, id = data
        print("set_value:", id)
        if id in self.rtd_dict:
            rtd = self.rtd_dict[id]
            del self.rtd_dict[id]
            rtd.value = val

    def create(self, func):
        rtd = AsyncFuncRtd()
        rtd.id = str(rtd)
        self.func_dict[rtd.id] = func
        self.rtd_dict[rtd.id] = rtd
        return rtd


async_func_manager = AsyncFuncManager(2, True)
