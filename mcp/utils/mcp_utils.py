import json
from datetime import datetime, timedelta
import re
import pandas as pd

debug_del_info = False
debug_args_info = False


class McpConst():
    Call_Option = 0
    Put_Option = 1

    Side_Buy = 1
    Side_Sell = -1

    Knock_Down_In = 2
    Knock_Down_Out = 3
    Knock_Up_In = 4
    Knock_Up_Out = 5


mcp_const = McpConst()

def excel_date_to_string(excel_date):
    if isinstance(excel_date, float):
        # Excel的日期从1900-01-01开始
        base_date = datetime(1899, 12, 30)
        # 将Excel日期转换为timedelta
        delta_days = timedelta(days=float(excel_date))
        # 计算日期
        date_obj = base_date + delta_days
        # 格式化日期字符串
        date_string = date_obj.strftime('%Y-%m-%d')
        return date_string
    else:
        return excel_date

def time_to(start, end, days=365):
    if days is None:
        days = 365
    td: timedelta = end - start
    return td.days / days


def pure_digit_date(date):
    return re.sub("\\D", "", date)


def parse_date(date):
    date = pure_digit_date(date)
    if len(date) < 8:
        return None
    dt = datetime.strptime(date[0:8], "%Y%m%d")
    return dt

## 返回excel日期格式
import pandas as pd
from datetime import datetime

def parse_excel_date(date_str):
    """
    解析 Excel 输入的日期字符串，支持多种格式和 Excel 日期数字（包括小数）。
    同时支持直接处理 datetime.datetime 对象。
    
    参数:
    date_str (str, float, int, datetime.datetime): 日期字符串或 Excel 日期数字。
    
    返回:
    pd.Timestamp: 解析后的日期对象，如果无法解析则返回 pd.NaT。
    """
    # 如果输入是 datetime.datetime 类型，直接转换为 pd.Timestamp
    if isinstance(date_str, datetime):
        return pd.Timestamp(date_str)
    
    # 尝试多种日期格式
    formats = [
        "%Y-%m-%d",  # 2024-11-29
        "%Y/%m/%d",  # 2024/11/29
        "%d-%m-%Y",  # 29-11-2024
        "%d/%m/%Y",  # 29/11/2024
        "%Y.%m.%d",  # 2024.11.29
        "%d.%m.%Y",  # 29.11.2024
        "%Y%m%d"     # 20241129 (新增的 YYYYMMDD 格式)
    ]
    
    # 首先检查是否为 YYYYMMDD 格式
    if isinstance(date_str, str) and date_str.isdigit() and len(date_str) == 8:
        try:
            # 尝试解析为 YYYYMMDD 格式
            return pd.to_datetime(date_str, format="%Y%m%d")
        except ValueError:
            pass  # 如果解析失败，继续尝试其他格式
    
    # 检查是否为 Excel 日期数字
    try:
        excel_date = float(date_str)  # 将输入转换为浮点数
        
        # 直接取整数部分
        excel_date_int = int(excel_date)
        
        # 将 Excel 日期转换为日期
        base_date = pd.Timestamp('1899-12-30')  # Excel 的基准日期
        date_part = base_date + pd.Timedelta(days=excel_date_int)  # 整数部分对应的日期
        
        return date_part

    except ValueError:
        pass  # 如果转换失败，继续尝试其他格式

    # 尝试其他日期格式
    for fmt in formats:
        try:
            # 尝试使用当前格式解析
            return pd.to_datetime(date_str, format=fmt)
        except ValueError:
            continue  # 如果解析失败，尝试下一个格式
    
    # 如果所有格式都无法解析，返回 pd.NaT
    return pd.NaT

def date_to_string(dt: datetime):
    return dt.strftime("%Y-%m-%d")


def date_to_string2(dt: datetime):
    return dt.strftime("%Y/%m/%d")


def date_to_pure_string(dt: datetime):
    return dt.strftime("%Y%m%d")


def call_put_internal(call_put):
    call_put = str(call_put).lower() == "call"
    if call_put:
        call_put = mcp_const.Call_Option
    else:
        call_put = mcp_const.Put_Option
    return call_put


def call_put_view(call_put):
    if call_put == mcp_const.Call_Option:
        return "Call"
    else:
        return "Put"


def buy_sell_view(buy_sell):
    if buy_sell == mcp_const.Side_Buy:
        return "Buy"
    else:
        return "Sell"


def buy_sell_internal(buy_sell):
    buy_sell = str(buy_sell).lower() == "buy"
    if buy_sell:
        buy_sell = mcp_const.Side_Buy
    else:
        buy_sell = mcp_const.Side_Sell
    return buy_sell


def lower_key_dict(src_dict):
    result = {}
    for key in src_dict:
        result[str(key).lower()] = src_dict[key]
    return result


class McpDateTime():
    Date_Format_Pure = "%Y%m%d"
    Date_Format_1 = "%Y-%m-%d"
    Date_Format_2 = "%Y/%m/%d"

    def __init__(self):
        pass

    def time_to(self, start, end, days=365):
        start = self.parse_date(start)
        end = self.parse_date(end)
        td: datetime.timedelta = end - start
        return td.days / days

    def pure_digit(self, s):
        return re.sub("\\D", "", s)

    def parse_date(self, s):
        # s = self.pure_digit(s)
        # if len(s) < 8:
        #     return None
        # dt = datetime.strptime(s[0:8], "%Y%m%d")
        # return dt
        return pd.to_datetime(s)

    def parse_date2(self, s):
        strs = re.split("\\D", s, 3)
        if len(strs[1]) == 1:
            strs[1] = "0" + strs[1]
        if len(strs[2]) == 1:
            strs[2] = "0" + strs[2]
        s = "".join(strs)
        if len(s) < 8:
            return None
        dt = datetime.strptime(s[0:8], "%Y%m%d")
        return dt

    def parse_excel_date(self, ordinal, _epoch0=datetime(1899, 12, 31)):
        if ordinal >= 60:
            ordinal -= 1  # Excel leap year bug, 1900 is not a leap year!
        return (_epoch0 + timedelta(days=ordinal)).replace(microsecond=0)

    def format(self, dt: datetime, fmt):
        return dt.strftime(fmt)

    def to_pure_date(self, dt: datetime):
        return self.format(dt, self.Date_Format_Pure)

    def to_date1(self, dt: datetime):
        return self.format(dt, self.Date_Format_1)

    def to_date2(self, dt: datetime):
        return self.format(dt, self.Date_Format_2)

    def to_date_list(self, dts, format_func):
        return [format_func(dt) for dt in dts]

    def today(self):
        return self.to_pure_date(datetime.now())

    def same_date(self, dt1, dt2):
        temp1 = self.to_pure_date(pd.to_datetime(dt1))
        temp2 = self.to_pure_date(pd.to_datetime(dt2))
        return temp1 == temp2

    def excel_date_to_string(self, excel_date):
        if isinstance(excel_date, float):
            # Excel的日期从1900-01-01开始
            base_date = datetime(1899, 12, 30)
            # 将Excel日期转换为timedelta
            delta_days = timedelta(days=float(excel_date))
            # 计算日期
            date_obj = base_date + delta_days
            # 格式化日期字符串
            date_string = date_obj.strftime('%Y-%m-%d')
            return date_string
        else:
            return excel_date

mcp_dt = McpDateTime()


def as_array(s, fmt, do_load=True):
    arr = s
    if isinstance(s, list):
        pass
    elif do_load or isinstance(s, str):
        arr = json.loads(s)
    if fmt == "H":
        return [arr]
    else:
        result = []
        for item in arr:
            result.append([item])
        return result


def as_2d_array(s, fmt, do_load=True):
    fmt = str(fmt).upper()
    arr = s
    if isinstance(s, list):
        pass
    elif do_load or isinstance(s, str):
        arr = json.loads(s)
    if fmt == "H":
        return arr
    else:
        result = []
        for j in range(len(arr[0])):
            sub_result = []
            for i in range(len(arr)):
                sub_result.append(arr[i][j])
            result.append(sub_result)
        return result


def trans_2d_array(arr):
    result = []
    if len(arr) >= 1:
        for j in range(len(arr[0])):
            sub_result = []
            for i in range(len(arr)):
                sub_result.append(arr[i][j])
            result.append(sub_result)
        return result
    else:
        return arr


def is_float(v):
    try:
        f = float(v)
        return True
    except:
        return False
