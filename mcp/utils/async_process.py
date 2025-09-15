import threading
import traceback
from datetime import datetime
from multiprocessing import Process, Pool, Pipe

from os import path

from mcp.wrapper import create_object, trace_args


def get_cur_path():
    cur_path = path.realpath(__file__)
    print("version 1.0.0, build 2022-03-18")
    print("cur_path origin: " + str(cur_path))
    cur_path = cur_path[0:cur_path.rfind("\\mcp\\async_process")]
    print("cur_path: " + str(cur_path))
    return cur_path



class AsyncProcessLog():

    def __init__(self):
        # file_path = get_cur_path()
        # file_path = file_path + "\\..\\logs\\Async_process.log"
        # print("TfOrderLog file_path:", file_path)
        # self.file = open(file_path, "a", encoding="UTF8")
        pass

    def write(self, data):
        # if self.file is None:
        #     return
        # temp = str(datetime.datetime.now())
        # for item in data:
        #     temp += ","
        #     temp += str(item)
        # self.file.write(temp)
        # self.file.write("\n")
        # self.file.flush()
        pass

    def write_line(self, line):
        # temp = str(datetime.now()) + "\t"
        # temp += line + "\n"
        # self.file.write(temp)
        # self.file.flush()
        pass

    def dispose(self):
        # if self.file is not None:
        #     file = self.file
        #     self.file = None
        #     file.close()
        pass


process_log = AsyncProcessLog()


def wrapper_process(id, wrapper, method, args, conn):
    try:
        process_log.write_line("%s, %s start" % (id, method))
        print(id, "start", id)
        mcp_object = create_object(wrapper)
        process_log.write_line("%s create_object, %s, %s" % (id, method, wrapper))
        t1 = datetime.now()
        f = getattr(mcp_object, method)
        data = f(*args)
        t2 = datetime.now()
        ms = (t2 - t1).total_seconds()
        print(id, "finish: time=", ms)
        process_log.write_line("%s, %s finish=%s, time=%s" % (id, method, data, ms))
        conn.send({
            "id": id,
            "data": data,
        })
    except:
        traceback.print_exc(None, process_log.file)
        process_log.write_line("%s, %s except" % (id, method))
        conn.send({
            "id": id,
            "data": method + " Fail: " + str(args),
        })


class ProcessPool:

    def __init__(self, process_count):
        self.process_count = process_count
        self.pool = None
        self.main_conn = None
        self.sub_conn = None
        self.job_id_seed = 0
        self.func_dict = {}
        self.is_running = False
        self._thread = None
        self.is_sync_execute = False

    def initialize(self):
        print("ProcessPool initialize start")
        if not self.is_sync_execute:
            self.pool = Pool(self.process_count)
            self.main_conn, self.sub_conn = Pipe()
            self.job_id_seed = 0
            self.func_dict = {}
            self.is_running = True
            self._thread = threading.Thread(target=self.recv_thread)
            self._thread.start()
        print("ProcessPool initialize end")

    def recv_thread(self):
        print("ProcessPool recv_thread start")
        while (self.is_running):
            try:
                obj = self.main_conn.recv()
                print("ProcessPool recv:", obj)
                id = obj["id"]
                data = obj["data"]
                if id in self.func_dict:
                    cb = self.func_dict[id]
                    del self.func_dict[id]
                    cb["func"](data)
            except:
                traceback.print_exc()
        print("ProcessPool recv_thread stop")

    def dispose(self):
        print("ProcessPool dispose")
        self.is_running = False
        self.pool.close()
        print("ProcessPool pool close")
        process_log.dispose()
        # self.pool.join()
        # print("ProcessPool pool join")

    def get_job_id(self):
        self.job_id_seed += 1
        return "job_" + str(self.job_id_seed)

    def sync_execute(self, mcp_object, method, args):
        f = getattr(mcp_object, method)
        data = f(*args)
        return data

    def execute_job(self, mcp_object, method, args, f):
        print("execute_job:", method)
        if not self.is_running:
            self.initialize()
        job_id = self.get_job_id()
        self.func_dict[job_id] = {
            "func": f,
        }
        wrapper = trace_args(mcp_object)
        print("execute_job:", method, job_id, wrapper)
        self.pool.apply_async(func=wrapper_process, kwds={
            "id": job_id,
            "wrapper": wrapper,
            "method": method,
            "args": args,
            "conn": self.sub_conn,
        })


process_pool = ProcessPool(6)
process_pool.is_sync_execute = True
