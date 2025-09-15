import logging
import os
import random
import re
from datetime import datetime


class XssConst:
    Base_Html_Folder = './data/xscript/'


class XssUtils:

    def __init__(self):
        self.id_seed = 1
        self.html_folder = './data/xscript'

    def set_folder(self, folder):
        self.html_folder = folder

    def gen_id(self):
        ri = random.randint(1, 100000)
        id = self.id_seed
        self.id_seed += 1
        dt = datetime.now().strftime('%Y_%m_%d')
        return f"{dt}_{ri}_{id}"

    def get_folder(self, id, create=False):
        folder = f"{self.html_folder}/{id}"
        if create and not os.path.exists(folder):
            os.makedirs(folder, exist_ok=True)
        return folder
    
    def extract_folder(self, fileName):
        folder = os.path.dirname(fileName)
        return folder

xss_utils = XssUtils()


class SttUtils:
    @staticmethod
    def format_code(code: str):
        if code is None:
            s = ''
        else:
            s = code
        s = s.replace('\n', ' ')
        s = s.replace('\t', ' ')
        s = re.sub(r'\s+', ' ', s)
        s = s.strip(' ')
        return s

    @staticmethod
    def replace_func(code, t, dt):
        arr = [
            (r'(\W)(dt\(\))', '\g<1>' + str(dt)),
            (r'(\W)(t\(\))', '\g<1>' + str(t)),
        ]
        s = code
        for rg, rp in arr:
            s = re.sub(rg, rp, s)
        return s

    @staticmethod
    def to_lower_key(d):
        result = {}
        for key in d:
            result[str(key).lower()] = d[key]
        return result

    @staticmethod
    def get_value(key, d, val_default=None):
        key = str(key).lower()
        if key in d:
            val = d[key]
            if val is None:
                val = val_default
        else:
            val = val_default
        return val

    @staticmethod
    def parse_excel_kv(item):
        if len(item) >= 2:
            key = item[0]
            val = item[1]
            return str(key).lower(), key, val
        else:
            logging.info(f'parse_excel_kv fail: {item}')
            return None, None, None

    @staticmethod
    def parse_excel_kv_array(arr):
        result = []
        d_raw = {}
        for item in arr:
            key_lower, key, val = SttUtils.parse_excel_kv(item)
            if key_lower is None:
                continue
            result.append((key_lower, val))
            d_raw[key_lower] = {
                'key_lower': key_lower,
                'key': key,
                'value': val,
            }
        return result, d_raw

    @staticmethod
    def parse_excel_kv_dict(arr):
        d = {}
        d_raw = {}
        for item in arr:
            key_lower, key, val = SttUtils.parse_excel_kv(item)
            if key_lower is None:
                continue
            d[key_lower] = val
            d_raw[key_lower] = {
                'key_lower': key_lower,
                'key': key,
                'value': val,
            }
        d['raw_keys'] = d_raw
        return d

    @staticmethod
    def get_dict_values(fields, d):
        result = []
        for key in fields:
            key_lower = str(key).lower()
            if key_lower in d:
                result.append(d[key_lower])
            else:
                result.append(None)
        return result

    @staticmethod
    def excel_args(arr, fields):
        d = SttUtils.parse_excel_kv_array(arr)
        result = SttUtils.get_dict_values(fields, d)
        return result, d
