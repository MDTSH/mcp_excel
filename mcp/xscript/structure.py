import json
import logging
import re
import traceback
from datetime import datetime

import pandas as pd
import seaborn

from mcp.utils.enums import *
from mcp.utils.excel_utils import pf_date, to_excel_ordinal, pf_array, pf_array_json,pf_array_date_json
from mcp.mcp import MDayCounter, MxScript, MXScriptStructure
from mcp.tool.args_def import McpArgsException
from mcp.tools import *
from mcp.wrapper import to_mcp_args
from mcp.xscript.asset import McpAsset, McpAssetFactory
from mcp.xscript.utils import SttUtils, xss_utils
from mcp.utils.mcp_utils import *

from scipy.optimize import root_scalar, minimize_scalar
import sys


class SttArgsTemplate:

    def __init__(self, mcp_field, field, val, req, val_default):
        self.mcp_field = mcp_field
        self.field = field
        self.req = req
        self.val_default = val_default
        self.is_template = False
        if val is not None:
            if isinstance(val, str):
                s = val.strip(' ')
                self.is_template = s[0] == '@'
        if self.is_template:
            self.args = val[1:]
        else:
            if val is not None:
                self.args = val
            else:
                self.args = val_default

    def get_value(self, d, prefix):
        if self.is_template and 'Frequency' != self.field:
            val = self.get_value_spec(self.args, prefix, d)
            return val
        else:
            val = self.get_value_spec(self.field, prefix, d)
            if val is not None:
                return val
            else:
                return self.args

    def get_value_spec(self, field, prefix, d):
        f1_lower = f'{prefix}/{field}'.lower()
        val = None
        if f1_lower in d:
            val = d[f1_lower]
        if val is None:
            f2_lower = field.lower()
            if f2_lower in d:
                val = d[f2_lower]
        return val


# class SttModel:
#
#     def __init__(self, name, fields_require, fields_asset):
#         self.name = name
#         self.fields_require = fields_require
#         self.fields_asset = fields_asset
#         self.fields = []
#         for item in [self.fields_require, self.fields_asset]:
#             self.fields.extend(item)


# class SttModelDefine:
#
#     def __init__(self, name, fields_require, fields_asset):
#         self.name = name
#         self.fields_require = fields_require
#         self.fields_asset = fields_asset
#         self.fields = []
#         for item in [self.fields_require, self.fields_asset]:
#             self.fields.extend(item)
#         stt_def_manager.model().add(name, self)


class McpModelDef:

    def __init__(self, arr, caller=''):
        d = SttUtils.parse_excel_kv_dict(arr)
        d = SttUtils.to_lower_key(d)
        fields_require = [
            ('ReferenceDate', pf_date),
            # ('BuySell', None),
            ("Spot", None),
            ('Vol', None),
            ("Underlying", None),
            ("ModelType", lambda x: enum_wrapper.parse2(x, "XsModelType"), False),
            ("ModelParam", lambda x: json.dumps(x), False),
            ("RunMode", lambda x: enum_wrapper.parse2(x, "XScriptRunMode"), False),
        ]
        self.name = SttUtils.get_value('ModelName', d)
        if self.name is None:
            raise Exception(f"Missing field: ModelName")
        is_exist, cur_caller = stt_def_manager.model().is_exist(self.name, caller)
        if is_exist:
            raise Exception(f"Duplicate ModelName: {self.name}, define in {cur_caller}")
        asset_name = SttUtils.get_value('AssetClass', d)
        self.asset: McpAsset = McpAssetFactory.gen_asset(asset_name)
        self.model = SttUtils.get_value('Model', d)

        fields = []
        for item in [fields_require, self.asset.fields]:
            fields.extend(item)
        self.fields = fields
        stt_def_manager.model().add(self.name, self, caller)
        self.delay_fields = {'rd', 'rf', 'vol'}

    def parse_args(self, d, result, key_map, lack_keys):
        for tp in self.fields:
            if len(tp) == 3:
                field, pf, require = tp
            else:
                field, pf = tp
                require = True
            field_lower = field.lower()
            if field_lower in self.delay_fields:
                continue
            key_map[field_lower] = field
            if field_lower in d:
                val = d[field_lower]
                if pf is not None:
                    val = pf(val)
                result[field_lower] = val
            else:
                if require:
                    lack_keys.append(field_lower)

    def parse_delay_args(self, d, result, key_map, lack_keys):
        for tp in self.fields:
            if len(tp) == 3:
                field, pf, require = tp
            else:
                field, pf = tp
                require = True
            field_lower = field.lower()
            if field_lower not in self.delay_fields:
                continue
            key_map[field_lower] = field
            if field_lower in d:
                val = d[field_lower]
                if pf is not None:
                    val = pf(val)
                result[field_lower] = val
            else:
                if require:
                    lack_keys.append(field_lower)


class SttStructure:

    def __init__(self, d):
        self.dates = SttUtils.get_value('Dates', d, '').split(',')
        self.strikes = SttUtils.get_value('Strikes', d, '').split(',')
        self.arguments = SttUtils.get_value('Arguments', d, '').split(',')
        self.calendars = SttUtils.get_value('Calendar', d, '').split(',')

        if 'basis' in d:
            self.basis = MDayCounter(d['basis'])
        else:
            self.basis = MDayCounter(DayCounter.Act360)

        temp = []
        for item in [self.dates, self.strikes, self.arguments, self.calendars]:
            temp.extend(item)
        fields = []
        for item in temp:
            if len(item) > 0:
                fields.append(item)
        self.fields = fields

    def parse_args(self, d, result, key_map, lack_keys):
        for field in self.dates:
            if len(field) > 0:
                field_lower = field.lower()
                key_map[field_lower] = field
                if field_lower in d:
                    result[field_lower] = pf_date(d[field_lower])
                else:
                    lack_keys.append(field_lower)
        for field in self.calendars:
            if len(field) > 0:
                field_lower = field.lower()
                key_map[field_lower] = field
                if field_lower in d:
                    result[field_lower] = d[field_lower]
                else:
                    lack_keys.append(field_lower)
        init_arr = []
        for arr in [self.strikes, self.arguments]:
            for field in arr:
                if len(field) > 0:
                    field_lower = field.lower()
                    key_map[field_lower] = field
                    if field_lower in d:
                        val = d[field_lower]
                        val_lower = str(val).lower()
                        if val_lower == 'yes':
                            val = 1
                        elif val_lower == 'no':
                            val = 0
                        # if isinstance(val, bool):
                        #     if val:
                        #         val = 1
                        #     else:
                        #         val = 0
                        result[field_lower] = val
                        init_arr.append(f"{field}={val}")
                    else:
                        lack_keys.append(field_lower)
        result['init'] = ' '.join(init_arr)
        result['basis'] = self.basis


class SttSchedule:
    # Fields = ['StartDate', 'EndDate', 'Frequency', 'Calendar', 'DateAdjuster', 'Basis',  #
    #           'EndToEnd', 'LongStub', 'EndStub']

    def __init__(self, d):
        self.name = SttUtils.get_value('ScheduleName', d)

        self.args_def = [
            ('StartDate', 'StartDate', True, None),
            ('EndDate', 'EndDate', True, None),
            ('Frequency', 'Frequency', True, None),
            ('Calendar', 'Calendar', True, None),
            ('AdjusterRule', 'DateAdjuster', False, DateAdjusterRule.Following),
            ('KeepEndOfMonth', 'EndToEnd', False, True),
            ('LongStub', 'LongStub', False, False),
            ('EndStub', 'EndStub', False, False),
        ]
        fields = []
        for mcp_field, field, req, val in self.args_def:
            fields.append(SttArgsTemplate(mcp_field, field, SttUtils.get_value(field, d), req, val))
        self.fields = fields

    def parse_args(self, d, result, key_map, lack_keys):
        args = {}
        temp_lack = []
        for item in self.fields:
            if item.is_template:
                if 'Frequency' == item.field:
                    field = f"{self.name}/{item.field}"
                else:
                    field = f"{self.name}/{item.args}"
                field_lower = field.lower()
                key_map[field_lower] = field
                # val = None
                # if field_lower in result:
                #     val = result[field_lower]
                # elif field_lower in d:
                #     val = d[field_lower]
                # if val is None:
                #     # field = f"{self.name}/{field}"
                #     # field_lower = field.lower()
                #     field = item.args
                #     field_lower = field.lower()
                #     key_map[field_lower] = field
                #     if field_lower in result:
                #         val = result[field_lower]
                #     elif field_lower in d:
                #         val = d[field_lower]
                val = item.get_value(d, self.name)
                if val is None and item.is_template and item.req:
                    temp_lack.append(field_lower)
                else:
                    mcp_val = item.get_value_spec(item.mcp_field, self.name, d)
                    if mcp_val is None:
                        args[item.mcp_field] = val
                    else:
                        args[item.mcp_field] = mcp_val
            else:
                args[item.mcp_field] = item.get_value(d, self.name)
        # print(f"McpSchedule args: {args}")
        name_lower = self.name.lower()
        key_map[name_lower] = self.name
        if len(temp_lack) == 0:
            # day_counter = MDayCounter(DayCounter.Act365Fixed)
            day_counter = result['basis']
            mcp_schedule = McpSchedule(args)
            # dates = mcp_schedule.dates()
            # arr = []
            # for i in range(1, len(dates)):
            #     t: float = day_counter.YearFraction(result['ReferenceDate'.lower()], dates[i])
            #     dt: float = day_counter.YearFraction(dates[i - 1], dates[i])
            #     arr.append((dates[i], round(t, 2), round(dt, 2)))
            result[name_lower] = mcp_schedule
        else:
            lack_keys.extend(temp_lack)


class SttPayoff:

    def __init__(self, kv_list, d_raw):
        self.kv_list = kv_list
        self.raw_dict = d_raw


    def parse_args(self, d, result, key_map, lack_keys):
        events = []
        # day_counter = MDayCounter(DayCounter.Act365Fixed)
        day_counter = result['basis']

        # ref_date = result['ReferenceDate'.lower()]
        # changed to StartDate
        ref_date = result['StartDate'.lower()]
        ref_date_dt = pd.to_datetime(ref_date)
        start_date = ref_date
        for i, (lower_key, code) in enumerate(self.kv_list):
            # if code is None:
            #     code = ''
            code = SttUtils.format_code(code)
            val_key = None
            if lower_key in result:
                val_key = result[lower_key]
                # 修改前，会取events第一个作为startdate
                #if i == 0:
                #    start_date = val_key
            elif lower_key in d:
                val_key = d[lower_key]
            if val_key is None:
                lack_keys.append(lower_key)
            else:
                # if isinstance(val_key, list):
                #     for date, t, dt in val_key:
                #         # code_temp = str(code).replace(' t()', f" {t}")
                #         if pd.to_datetime(date) < ref_date_dt:
                #             continue
                #         code_temp = SttUtils.replace_func(code, t, dt)
                #         events.append(
                #             (date, code_temp, lower_key)
                #         )
                if isinstance(val_key, mcp.wrapper.McpSchedule):
                    if any('schedule1' in event for event in events):
                        if any('schedule2' in event for event in events):
                            events.append(
                                ("schedule3", code, lower_key)
                            )
                        else:
                            events.append(
                                ("schedule2", code, lower_key)
                            )
                    else:
                        events.append(
                            ("schedule1", code, lower_key)
                        )                        
                else:
                    code_temp = code
                    # ref_date_key = 'ReferenceDate'.lower()
                    try:
                        # if ref_date_key in result:
                        #     ref_date = result[ref_date_key]
                        # t = round(day_counter.YearFraction(ref_date, val_key), 2)
                        if isinstance(val_key, (int, float)):
                            val_key = convert_excel_date_to_string(val_key)
                        t = round(day_counter.YearFraction(start_date, val_key), 3)
                        dt = t
                        code_temp = SttUtils.replace_func(code, t, dt)
                    except(NotImplementedError, ValueError, OverflowError) as e:
                        traceback.print_exc()
                        raise type(e)(str(e)) from e
                    events.append(
                        (val_key, code_temp, lower_key)
                    )
        if 'init' in result:
            init_str = result['init']
            if len(events) > 0:
                key, val, name = events[0]
                events[0] = (key, f"{init_str} {val}", name)
        #evn, evn_view = self.merge_events(events, key_map)

        result['events'] = json.dumps([{row[0]: row[1]}  for row in events])
        result['eventsview'] = events

    def merge_events(self, events, key_map):
        dates = []
        temp = {}
        temp_name = {}
        for key, val, name in events:
            if key not in temp:
                temp[key] = []
                temp_name[key] = []
                dates.append(key)
            temp[key].append(val)
            if name is not None:
                if name in key_map:
                    name = key_map[name]
                temp_name[key].append(name)
        # result = [{f"{int(to_excel_ordinal(item))}": " ".join(temp[item])} for item in dates]
        dates.sort()
        codes = [" ".join(temp[item]) for item in dates]
        names = [",".join(temp_name[item]) for item in dates]
        result = [{key: val} for key, val in zip(dates, codes)]
        result_view = [[item1, pd.to_datetime(item2), item3] for item1, item2, item3 in zip(names, dates, codes)]
        # result = [{item: " ".join(temp[item])} for item in dates]
        return result, result_view


class McpStructureDef:

    def __init__(self, pkg_name, structure, schedules, payoff, caller=''):
        is_exist, cur_caller = stt_def_manager.stt().is_exist(pkg_name, caller)
        if is_exist:
            raise Exception(f"Duplicate PackageName:  {pkg_name}, define in {cur_caller}")
        self.pkg_name = pkg_name
        self.structure = SttStructure(SttUtils.parse_excel_kv_dict(structure))
        self.schedules = []
        for item in schedules:
            schedule = SttSchedule(SttUtils.parse_excel_kv_dict(item))
            if schedule.name is not None:
                self.schedules.append(schedule)
        result, d_raw = SttUtils.parse_excel_kv_array(payoff)
        self.payoff = SttPayoff(result, d_raw)
        stt_def_manager.stt().add(pkg_name, self, caller)

    def parse_args(self, d, result, key_map, lack_keys):
        self.structure.parse_args(d, result, key_map, lack_keys)
        for item in self.schedules:
            item.parse_args(d, result, key_map, lack_keys)
        self.payoff.parse_args(d, result, key_map, lack_keys)


class SttDefDict:

    def __init__(self):
        self.data = {}

    def clear(self, caller):
        arr = []
        for key in self.data:
            cur_caller = self.data[key][1]
            if cur_caller == caller:
                arr.append(key)
        for key in arr:
            del self.data[key]
        #print(f'{caller} clear: {arr}')
        return arr

    def is_exist(self, name, caller):
        key = name.lower()
        result = False
        cur_caller = None
        if key in self.data:
            cur_caller = self.data[key][1]
            result = cur_caller != caller
        return result, cur_caller

    def add(self, name, dfn, caller):
        key = name.lower()
        can_add = True
        if key in self.data:
            cur_caller = self.data[key][1]
            can_add = cur_caller == caller
        if can_add:
            self.data[key] = [dfn, caller]

    def get(self, name):
        key = name.lower()
        if key in self.data:
            return self.data[key][0]
        else:
            return None


class SttDefineManager:

    def __init__(self):
        self.stt_dict = SttDefDict()
        self.model_dict = SttDefDict()

    def stt(self):
        return self.stt_dict

    def model(self):
        return self.model_dict


class McpHestonModel(mcp.mcp.MHestonModel):

    def __init__(self, *args):
        self.raw_args = args
        self.is_mcp_wrapper = True
        # logging.info(f"McpFixedRateBondCurveData args: {args}")
        self.hm_id = ''
        args = self.std_args(args)
        mcp_args = to_mcp_args(args)
        super().__init__(*mcp_args)

    def std_args(self, args):
        arr_default = [LogLevel.Off, "", "data/xscript"]
        if 1 <= len(args) <= 4:
            len_static = 1
        elif len(args) >= 9:
            len_static = 9
        else:
            raise Exception(f"Wrong args of McpHestonModel: len={len(args)}")
        arr = [None for _ in range(len_static)]
        arr.extend(arr_default)
        for i in range(len(args)):
            arr[i] = args[i]
        if arr[-3] == LogLevel.Trace:
            id = arr[-2]
            if id == '':
                id = xss_utils.gen_id()
            folder = xss_utils.get_folder(id, True)
            arr[-2] = id
            arr[-1] = folder
            self.hm_id = id
        return arr

    def HestonCalibration(self, initParams):
        if isinstance(initParams, str):
            js = initParams
        else:
            js = json.dumps(initParams)
        rjs = super().HestonCalibration(js)
        return json.loads(rjs)


def convert_excel_date_to_string(excel_date):
    """
    将 Excel 格式日期转换为字符串 "YYYYMMDD" 格式。
    输入必须是合法的 Excel 格式日期,否则会抛出异常。

    Args:
        excel_date (float): Excel 格式的日期。

    Returns:
        str: 转换后的日期字符串,格式为 "YYYYMMDD"。
    """
    try:
        #date = pd.Timestamp(excel_date, unit='D', origin='1900-01-01').strftime('%Y%m%d')
        date = pd.Timestamp('1900-01-01') + pd.Timedelta(days=excel_date)
        return date.strftime('%Y%m%d')
    except (ValueError, TypeError) as e:
        raise ValueError(f"Error converting Excel date: {e}")
        

class McpXScriptStructure(MXScriptStructure):

    def __init__(self, *args):
        self.raw_args = args
        d = {}
        for item in args:
            if isinstance(item, dict):
                d.update(item)
        d = SttUtils.to_lower_key(d)
        
        fixingdates = pf_array_date_json(d.get("fixingdates",[]))
        fixingrates = pf_array_json(d.get("fixingrates",[]))

        self.structure: McpStructureDef = self.get_def('PackageName', d, stt_def_manager.stt(), McpStructureDef)
        # self.model: McpModelDef = self.get_def('ModelName', d, stt_def_manager.model(), McpModelDef)
        self.value_dict, self.lack_keys = self.parse_args(d)

        dayCounter = self.structure.structure.basis

        # 目前支持两种构造方法，采用localvol来构造，或者时采用参数来构造
        if 'localvol' in d and d['localvol'] is not None:
            fields = [
                ('ReferenceDate', None),
                ('Spot', None),
                ('StartDate', None),
                ('EndDate', None),
                ('LocalVol', None),
                ('LogLevel', LogLevel.Off),
                ('Notional', 1000000),
                #('Init', None),
                ('Events', None),
                ('PremiumDate', None),
                ('NumSimulation', 10000),
                ('BuySell', BuySell.Sell),
                ('DiscountRateCurve', None),
                # ('Schedule1', None),
                # ('Schedule2', None),
                # ('Schedule3', None),
            ]
            self.key_parse_func = {
                'NumSimulation': lambda x: int(float(x)),
                'LocalVol': lambda x: x.getHandler(),
                'LogLevel': lambda x: enum_wrapper.parse2(x, 'LogLevel'),
                'BuySell': lambda x: enum_wrapper.parse2(x, 'BuySell'),
            }
        else:
            fields = [
                ('ReferenceDate', None),
                ('Spot', None),
                ('StartDate', None),
                ('EndDate', None),
                ('ModelType', None),
                ('RiskFreeRate', 0.0),
                ('UnderlyingRate', 0.0),
                ('Notional', 1000000),
                ('Events', None),
                ('NumSimulation', 10000),
                ('Volatility', 0.0),
                ('InitParams', ""),
                ('LogLevel', LogLevel.Off),
                ('PremiumDate', None),
                ('BuySell', BuySell.Sell),
                ('DiscountRate', 0.0),
            ]
            self.key_parse_func = {
                'ModelType':lambda x: enum_wrapper.parse2(x, 'ModelType'),
                'NumSimulation': lambda x: int(float(x)),
                'LocalVol': lambda x: x.getHandler(),
                'LogLevel': lambda x: enum_wrapper.parse2(x, 'LogLevel'),
                'BuySell': lambda x: enum_wrapper.parse2(x, 'BuySell'),
            }

        args = []
        keys_none = []
        self.hm_id = None
        for key, val in fields:
            raw = SttUtils.get_value(key, self.value_dict, val)
            if raw is None:
                keys_none.append(key)
            if key in self.key_parse_func:
                raw = self.key_parse_func[key](raw)
            args.append(raw)
        # logging.debug(f"MXScriptStructure args: {args}")
        if len(keys_none) > 0:
            self.lack_keys.extend(keys_none)
            # self.xss = None
            raise McpArgsException("McpXScriptStructure", self.lack_keys)
        else:
            # # self.xss: MXScriptStructure = MXScriptStructure(*args)
            # mkt_vol = SttUtils.get_value('MktVol2', self.value_dict, None)
            # if mkt_vol is not None:
            #     log_level = args[-4]
            #     if log_level == LogLevel.Trace:
            #         id = xss_utils.gen_id()
            #         self.hm_id = id
            #         folder = xss_utils.get_folder(id, True)
            #         args_hm = [mkt_vol, log_level, id, folder]
            #     else:
            #         args_hm = [mkt_vol, log_level]
            #     hm: mcp.wrapper.McpHestonModel = mcp.wrapper.McpHestonModel(*args_hm)
            #     hc = hm.HestonCalibration([0.52139, 0.0463869, 0.00206347, -0.00126779, 0.0511969])
            #     logging.info(f"HestonCalibration: {log_level},{self.hm_id}, {hc}")
            #     args[-2] = json.dumps(hc)
            # 定义一个字典来存储结果
            nullSchedule = None
            result = {
                'schedule1': nullSchedule,
                'schedule2': nullSchedule,
                'schedule3': nullSchedule,
            }

            # 遍历 eventview 列表
            for event in self.value_dict['eventsview']:
                # 检查是否包含 'schedule1'、'schedule2' 或 'schedule3'
                if 'schedule1' in event:
                    result['schedule1'] = self.value_dict[event[2]]
                elif 'schedule2' in event:
                    result['schedule2'] =  self.value_dict[event[2]]
                elif 'schedule3' in event:
                    result['schedule3'] =  self.value_dict[event[2]]

            if 'localvol' in d and d['localvol'] is not None:
                if d['discountratecurve'] is not None:
                    expiryDate = d['enddate']
                    if not isinstance(expiryDate, str):
                        expiryDate = convert_excel_date_to_string(d['enddate'])
                    result['DiscountRate'] =  d['discountratecurve'].ZeroRate(expiryDate)
                else:
                    result['DiscountRate'] = 0.0
                # 去掉 args['riskfreeratecurve ']    
                del args[-1]

            result['DayCounter'] = dayCounter.ToString()
            args.extend(result.values())
            

            args.append(fixingdates)
            args.append(fixingrates)

            self.spot_px = args[1]
            self.pips_unit = SttUtils.get_value('PipsUnit', d, 10000)
            logging.debug(f"MXScriptStructure args: {args}")
            super().__init__(*args)
        # logging.debug(f"McpXScriptStructure init end")
    
    def get_rawargs(self):
        args = self.raw_args[0]
        return dict(args)
    
    def parse_args(self, d):
        # print(f"parse_args d={d}")
        result = {}
        result.update(d)
        lack_keys = []
        key_map = {}

        self.parse_base_data(d, result, key_map, lack_keys)
        self.structure.parse_args(d, result, key_map, lack_keys)
        # print(f'parse_args result: {result}')
        # for key in result:
        #     print(f"{key}: {result[key]}")
        lack_keys_view = []
        for item in lack_keys:
            if item in key_map:
                lack_keys_view.append(key_map[item])
            else:
                print(f"no lack_keys {item} in key_map")
        # if len(lack_keys_view) > 0:
        #     print(f"lack_keys: {lack_keys_view}")
        # raise Exception(f"Missing fields: {lack_keys_view}")
        return result, lack_keys_view

    def parse_base_data(self, d, result, key_map, lack_keys):
        # fields = ['ReferenceDate', 'ExpiryDate', 'SpotPx', 'MktVol2', 'Notional', 'HestonParams']
        fields = [
            ('ReferenceDate', pf_date),
            ('Spot', lambda x: float(x)),
            ('StartDate', pf_date),
            ('ExpiryDate', pf_date),
            ('PremiumDate', pf_date),
            ('LocalVol', None),
            ('Notional', lambda x: float(x)),
            ('LogLevel', None),
        ]
        for field, f in fields:
            field_lower = field.lower()
            if field_lower in d:
                val = d[field_lower]
                if f is not None:
                    val = f(val)
                result[field_lower] = val
            else:
                # lack_keys.append(field_lower)
                key_map[field_lower] = field

    def get_def(self, name, d, dd: SttDefDict, cls):
        nv = SttUtils.get_value(name, d)
        if nv is None:
            raise Exception(f"{name} is None")
        dfn = None
        if isinstance(nv, str):
            dfn = dd.get(nv)
        elif isinstance(dfn, cls):
            dfn = nv
        if dfn is None:
            raise Exception(f"No define of {name}")
        return dfn

    def get_events(self):
        key = 'eventsview'
        if key in self.value_dict:
            return self.value_dict[key]
        else:
            return []

    def AnnualizedPrice(self):
        price = super().AnnualizedPrice()
        return price
    
    def price(self, price_method=None):
        price = super().Price()
        return price

    def ResultByVariable(self, variable):
        result = super().ResultByVariable(variable)
        return result
    
    def Premium(self, is_ccy2, is_amount):
        if (self.spot_px == 0.0):
            raise Exception("spot is zero!")

        if is_amount:
            amt = self.Price(True)
            if not is_ccy2:
                amt = amt / self.spot_px
            return amt
        else:
            p = self.Price(False)
            if is_ccy2:
                p = p * self.pips_unit
            else:
                p = p / self.spot_px
            return p
    
    def MarketValue(self, isAmount=True):
        return super().MarketValue(isAmount)
    
    def PV(self, isAmount=True):
        return super().PV(isAmount)
    
    def Delta(self, isCcy2=True, isAmount=True, pricingMethod=1):
        return super().Delta(isCcy2, isAmount)

    def Rho(self, isCcy2=True, isAmount=True, pricingMethod=1):
        return super().Rho(isCcy2, isAmount)

    def Gamma(self, isCcy2=True, isAmount=True, pricingMethod=1):
        return super().Gamma(isCcy2, isAmount)

    def Vega(self, isCcy2=True, isAmount=True, pricingMethod=1):
        return super().Vega(isCcy2, isAmount)

    def Theta(self, isCcy2=True, isAmount=True, pricingMethod=1):
        return super().Theta(isCcy2, isAmount)

    def Volga(self, isCcy2=True, isAmount=True, pricingMethod=1):
        return super().Volga(isCcy2, isAmount)

    def Vanna(self, isCcy2=True, isAmount=True, pricingMethod=1):
        return super().Vanna(isCcy2, isAmount)

    def ForwardDelta(self, isCcy2=True, isAmount=True, pricingMethod=1):
        return super().ForwardDelta(isCcy2, isAmount)

    def Events(self):
        return super().Events()
    
    def EventDates(self):
        return super().EventDates()
    
class McpStructuredProd:

    def __init__(self, d):
        d = SttUtils.to_lower_key(d)
        self.structure: McpStructureDef = self.get_def('PackageName', d, stt_def_manager.stt(), McpStructureDef)
        self.model: McpModelDef = self.get_def('ModelName', d, stt_def_manager.model(), McpModelDef)
        self.value_dict, self.lack_keys = self.parse_args(d)

    def parse_args(self, d):
        #print(f"parse_args d={d}")
        result = {}
        result.update(d)
        lack_keys = []
        key_map = {}

        self.model.parse_args(d, result, key_map, lack_keys)
        self.structure.parse_args(d, result, key_map, lack_keys)
        self.handle_mkt_data(d, result, key_map, lack_keys)
        self.model.parse_delay_args(d, result, key_map, lack_keys)
        # print(f'parse_args result: {result}')
        # for key in result:
        #     print(f"{key}: {result[key]}")
        lack_keys_view = []
        for item in lack_keys:
            if item in key_map:
                lack_keys_view.append(key_map[item])
            else:
                print(f"no lack_keys {item} in key_map")
        # if len(lack_keys_view) > 0:
        #     print(f"lack_keys: {lack_keys_view}")
        # raise Exception(f"Missing fields: {lack_keys_view}")
        return result, lack_keys_view

    def handle_mkt_data(self, d, result, key_map, lack_keys):
        # if 'mktdata' in d:
        #     dt = self.get_event_last_data()
        #     vs = d['mktdata']
        #     d['vol'] = vs.get_strike_vol(dt, )
        #     d['rd'] = vs.get_acc_rate(dt)
        #     d['rf'] = vs.get_und_rate(dt)
        pass

    def exec_script(self):
        xscript = MxScript()
        s = self.model.asset.execute(self.value_dict, xscript)
        # print(f"exec_script result: {s}")
        return json.loads(s)

    def get_event_last_data(self):
        evnts = self.get_events()
        if len(evnts) > 0:
            dt = evnts[-1][1]
        else:
            dt = datetime.now()
        return dt.strftime('%Y-%m-%d')

    def get_events(self):
        key = 'eventsview'
        if key in self.value_dict:
            return self.value_dict[key]
        else:
            return []

    def get_def(self, name, d, dd: SttDefDict, cls):
        nv = SttUtils.get_value(name, d)
        if nv is None:
            raise Exception(f"{name} is None")
        dfn = None
        if isinstance(nv, str):
            dfn = dd.get(nv)
        elif isinstance(dfn, cls):
            dfn = nv
        if dfn is None:
            raise Exception(f"No define of {name}")
        return dfn


stt_def_manager = SttDefineManager()

import copy

def find_root(func, target, bracket, tol=1e-6, max_iter=20):
    a, b = bracket
    fa, fb = func(a) - target, func(b) - target
    if fa * fb >= 0.0:
        raise ValueError("Bracket does not contain a root")

    for i in range(max_iter):
        c = (a + b) / 2
        fc = func(c) - target
        print(f"Iteration {i}: a={a}, b={b}, c={c}, fc={fc}")
        if abs(fc) < tol or (b - a) / 2 < tol:
            return c
        if fa * fc < 0.0:
            b, fb = c, fc
        else:
            a, fa = c, fc
    raise ValueError("Failed to converge")

class Solver:
    def __init__(self, priceObj):
        self.rawargs = priceObj.get_rawargs()
        # 用于求解目标为Upper/Lower Barriers
        self.midX = self.rawargs['Spot']
        #self.priceObj = priceObj

    def objFunc_Premium(self, targetFields, x, isAnnualized = False):
        _args = dict(self.rawargs)

        if len(targetFields) == 2:
            if targetFields[0] in _args:
                _args[targetFields[0]] = self.midX - x
            else:
                raise Exception(f"Error: {targetFields} is not a key in args.")
            if targetFields[1] in _args:
                _args[targetFields[1]] = self.midX + x
            else:
                raise Exception(f"Error: {targetFields} is not a key in args.")
        else:
            if targetFields[0] in _args:
                _args[targetFields[0]] = x
            else:
                raise Exception(f"Error: {targetFields} is not a key in args.")
        
        new_obj = McpXScriptStructure(_args)
        #print(_args)
        if (isAnnualized):
            premium = new_obj.AnnualizedPrice()
        else:
            premium = new_obj.Premium(True,True)
        return premium

 
    def SoverFromPremium(self, premium, targetField, x0=1.0, bracket=(-100, 100), method='bisect', options={'maxiter': 10, 'xtol': 1e-5}, isAnnualized=False):
        # 通过逗号分割字符串，并去除空格
        fields = targetField.split(',')
        self.midX = x0
        # 需要支持如果有两个strikes作为计算目标时，则从指定的x0开始同时向两边寻找求解。所以需要计算新的x0作为起点，以及新的bracket
        # 如果分割后的列表长度为2，则说明有两个字段
        if len(fields) == 2:
            # 计算 x0 到 bracket 两个边界的距离
            dist_to_lower = abs(x0 - bracket[0])
            dist_to_upper = abs(x0 - bracket[1])

            # 选择最小的距离
            min_distance = min(dist_to_lower, dist_to_upper)
            x0 = min_distance / 2.0
            # 设置一个合理的比0大一点的值
            bracket = (0.01 / x0, min_distance)

        elif len(fields) > 2:
            raise ValueError("Support two fields only!")
        
        # 将'maxiter'键对应的值转换为整数类型
        options['maxiter'] = int(options['maxiter'])
        # 设置最大迭代次数为 10,初始猜测值为 1.0,区间为 (-100, 100)
        result = root_scalar(lambda x: self.objFunc_Premium(fields, x, isAnnualized) - premium, x0=x0, bracket=bracket, method=method, options=options)
        #result = find_root(lambda x: self.objFunc_Premium(fields, x), premium, bracket)

        if result.converged:
            return result.root
        else:
            raise Exception(f"Target {targetField} root finding failed.")

    def objFunc_Delta(self, targetFields, x, isCCY2=False, isAmount=True):
        _args = dict(self.rawargs)

        if len(targetFields) == 2:
            if targetFields[0] in _args:
                _args[targetFields[0]] = self.midX - x
            else:
                raise Exception(f"Error: {targetFields} is not a key in args.")
            if targetFields[1] in _args:
                _args[targetFields[1]] = self.midX + x
            else:
                raise Exception(f"Error: {targetFields} is not a key in args.")
        else:
            if targetFields[0] in _args:
                _args[targetFields[0]] = x
            else:
                raise Exception(f"Error: {targetFields} is not a key in args.")
        
        new_obj = McpXScriptStructure(_args)
        #print(_args)
        premium = new_obj.Delta(isCCY2, isAmount)
        return premium

 
#   def SoverFromDelta(self, delta, targetField, x0=1.0, bracket=(-100, 100), method='bisect', options={'maxiter': 10, 'xtol': 1e-5}, isCCY2=False, isAmount=True):
    def SimpleSolverFromDelta(
        self,
        delta,
        targetField,
        x0=1.0,
        bracket=(-100, 100),
        method='bisect',
        options={'maxiter': 10, 'xtol': 1e-5},
        isCCY2=False,
        isAmount=True,
        curve_type='monotonic'  # 新增参数：'monotonic'（默认，单解）或 'v_shape'（V型多解）
    ):
        """
        通过 Delta 反解目标字段（支持单调曲线和 V 型曲线多解）
        
        参数:
            delta: 目标 Delta 值
            targetField: 需要求解的字段名（如 'UpperBarrier'），支持逗号分隔多字段
            x0: 初始猜测值（默认 1.0）
            bracket: 搜索区间（默认 (-100, 100)）
            method: 求根方法（'bisect'、'secant' 等，默认 'bisect'）
            options: 求解器选项（如最大迭代次数、容差）
            isCCY2: 是否计算 CCY2 的 Delta
            isAmount: 是否返回金额形式
            curve_type: 曲线类型，'monotonic'（单调）或 'v_shape'（V型多解）

        返回:
            List[float]: 解的列表（可能 0/1/2 个解），保持接口统一
        异常:
            ValueError: 输入参数不合法
            Exception: 求根失败
        """
        # --- 1. 解析目标字段 ---
        # 通过逗号分割字符串，并去除空格
        fields = targetField.split(',')
        self.midX = x0  # 记录初始猜测值

        # --- 2. 多字段逻辑（如双障碍期权需同时求解两个 Strike）---
        # 如果分割后的列表长度为2，则说明有两个字段
        if len(fields) == 2:
            if curve_type == 'v_shape':
                raise ValueError("这个结构由于会出现多解的场景，所以Delta仅支持一个目标字段的反算！")
            # 计算 x0 到 bracket 两个边界的距离
            dist_to_lower = abs(x0 - bracket[0])
            dist_to_upper = abs(x0 - bracket[1])

            # 选择最小的距离，调整初始猜测值和区间
            min_distance = min(dist_to_lower, dist_to_upper)
            x0 = min_distance / 2.0  # 新的初始值取中间
            bracket = (0.01 / x0, min_distance)  # 避免除零，设置合理区间

        elif len(fields) > 2:
            raise ValueError("仅支持两个字段！")

        # --- 3. 配置求解器选项 ---
        # 确保 maxiter 为整数（兼容字符串输入）
        options['maxiter'] = int(options['maxiter'])

        # --- 4. 定义目标函数 ---
        # 目标：计算当前 x 对应的 Delta 与目标 Delta 的差值
        def delta_obj_func(x):
            return self.objFunc_Delta(fields, x, isCCY2, isAmount) - delta

        # --- 5. 分曲线类型求解 ---
        # Case 1: V 型曲线（可能多解）
        if curve_type == 'v_shape' or  curve_type == 'rv_shape':
            try:
                # 5.1 寻找 Delta 的极值点（V 型最低点、RV型最高点）
                min_result = 0
                if (curve_type == 'v_shape'):
                    min_result = minimize_scalar(
                        lambda x: self.objFunc_Delta(fields, x, isCCY2, isAmount),
                        bounds=bracket,
                        method='bounded'  # 有界优化方法
                    )
                else:
                    min_result = minimize_scalar(
                        lambda x: -self.objFunc_Delta(fields, x, isCCY2, isAmount),
                        bounds=bracket,
                        method='bounded'  # 有界优化方法
                    )
            
                min_barrier = min_result.x  # 极值点对应的 UpperBarrier
                min_delta = min_result.fun  # 最小 Delta 值

                # 5.2 检查目标 Delta 是否可解
                if delta < min_delta:
                    raise ValueError(f"无解：目标 Delta ({delta}) 小于最小值 ({min_delta})")

                # 5.3 在左右子区间分别求根
                roots = []
                # 确定x0所在的子区间
                if bracket[0] <= x0 < min_barrier:
                    priority_bracket = (bracket[0], min_barrier)
                    other_bracket = (min_barrier, bracket[1])
                elif min_barrier <= x0 < bracket[1]:
                    priority_bracket = (min_barrier, bracket[1])
                    other_bracket = (bracket[0], min_barrier)
                else:
                    # x0不在总区间内，按原顺序搜索
                    priority_bracket = (bracket[0], min_barrier)
                    other_bracket = (min_barrier, bracket[1])
                
                # 按照优先级顺序搜索子区间
                for sub_bracket in [priority_bracket, other_bracket]:
                    try:
                        result = root_scalar(
                            delta_obj_func,
                            bracket=sub_bracket,
                            method=method,
                            options=options
                        )
                        if result.converged:
                            roots.append(result.root)
                    except ValueError:
                        continue  # 当前区间无解则跳过

                return roots if roots else None  # 返回所有解（可能空列表）

            except Exception as e:
                print(f"[警告] V 型曲线求解失败: {str(e)}")
                return None

        # Case 2: 单调曲线（单解）
        else:
            # 5.1 配置初始值（割线法需两个点）
            x1 = 0
            if method == 'secant':
                x0, x1 = bracket[0], bracket[1]

            # 5.2 调用求根器
            result = root_scalar(
                delta_obj_func,
                x0=x0,
                x1=x1,
                bracket=bracket,
                method=method,
                options=options
            )

            # 5.3 返回结果
            if result.converged:
                return [result.root]  # 封装为列表以统一接口
            else:
                raise Exception(f"目标 {targetField} 求根失败，请检查区间或初始值")
            

    def SolverFromDelta(
        self,
        delta,
        targetField,
        x0=1.0,
        bracket=(-100, 100),
        method='bisect',
        options={'maxiter': 10, 'xtol': 1e-5},
        isCCY2=True,
        isAmount=True,
        curve_type='monotonic' , # 新增参数：'monotonic'（默认，单解）或 'v_shape'（V型多解）
        inter_method = None
    ):
        """
        计算插值Delta的完整流程
        
        参数:
            delta: 目标Delta值
            targetField: 目标字段
            x0: 初始猜测值
            bracket: 搜索范围元组
            inter_method: 插值方法('linear'或'cubic')
            options: 求解器选项
            isCCY2: 是否使用CCY2
            isAmount: 是否使用金额
            curveType: 曲线类型
            
        返回:
            插值结果或错误信息
        """
        try:
            # 1. 检查插值方法是None否
            try:
                return self.SimpleSolverFromDelta(delta, targetField, x0, tuple(bracket),method, options, isCCY2, isAmount, curve_type)
            except ValueError as e:
                if inter_method == None:
                    raise

            if inter_method not in ['linear', 'cubic']:
                raise ValueError(f"不支持的插值方法: {inter_method}，只支持'linear'或'cubic'")

            # 2. 调用DeltaPlot获取原始数据
            x_values, y_values = self.DeltaPlot(
                targetField=targetField,
                bracket=bracket,
                isCCY2=isCCY2,
                isAmount=isAmount
            )

            # 3. 数据转置处理 (x和y交换)
            # 因为InterpolationHelper要求x是Delta值
            y_values_arr = np.array(y_values)
            x_values_arr = np.array(x_values)
            
            # 4. 创建插值器
            interpolator = InterpolationHelper(
                x_values=y_values_arr,  # 注意这里交换了x和y
                y_values=x_values_arr
            )

            # 5. 执行插值
            interpolated_results = interpolator.interp(
                x=delta, 
                method=inter_method
            )

            # 6. 处理插值结果
            if not interpolated_results:  # 空列表表示无解
                raise ValueError(f"无法在给定数据范围内找到delta={delta}对应的解")
                
            if len(interpolated_results) > 1:  # 多解情况
                warnings.warn(f"发现多个解({len(interpolated_results)})，返回第一个解")
                return interpolated_results
                
            return interpolated_results

        except ValueError as ve:
            print(f"参数错误: {str(ve)}")
            return None
        except TypeError as te:
            print(f"类型错误: {str(te)}")
            return None
        except Exception as e:
            print(f"计算过程中发生意外错误: {str(e)}")
            return None

    def DeltaPlot(
                self,
                targetField,
                bracket=(-100, 100),
                num_points=20,
                isCCY2=False,
                isAmount=True
            ):
            """
            生成Delta值的绘图数据
            
            参数:
                targetField: 目标字段
                bracket: 取值范围元组，默认为(-100, 100)
                num_points: 数据点数量，默认为20
                isCCY2: 是否使用CCY2，默认为False
                isAmount: 是否使用金额，默认为True
                
            返回:
                包含两个数组的元组: (x_values, y_values)
                x_values: 自变量数组
                y_values: 对应的Delta值数组
            """
            try:
                # 1. 确保num_points是整数
                num_points = int(num_points)
                if num_points <= 0:
                    raise ValueError("num_points必须为正整数")
                    
                # 2. 确保bracket是有效的数值范围
                start, end = map(float, bracket)
                if start >= end:
                    raise ValueError("bracket范围无效，第一个值必须小于第二个值")
                
                # 3. 计算步长(使用浮点数运算)
                step = (end - start) / (num_points - 1) if num_points > 1 else 0
                
                x_values = []
                y_values = []
                
                _args = dict(self.rawargs)

                # 4. 生成数据点(使用range的整数迭代)
                for i in range(num_points):
                    x = start + i * step
                    x_values.append(x)
                    
                    _args[targetField] = x
                    new_obj = McpXScriptStructure(_args)
                    delta = new_obj.Delta(isCCY2, isAmount)
                    y_values.append(delta)
                
                return x_values, y_values
                
            except TypeError as te:
                print(f"类型错误: {str(te)}")
                raise
            except ValueError as ve:
                print(f"数值错误: {str(ve)}")
                raise
            except Exception as e:
                print(f"计算过程中发生意外错误: {str(e)}")
                raise



from scipy import interpolate
import warnings
import numpy as np
class InterpolationHelper:
    def __init__(self, x_values, y_values):
        """
        初始化插值器（基于XToYInterpolator逻辑修改）
        参数:
            x_values: 自变量X数组
            y_values: 因变量Y数组
        """
        self.x_values = np.array(x_values, dtype=np.float64)
        self.y_values = np.array(y_values, dtype=np.float64)
        self._validate_input()
        self.tol = 1e-8  # 浮点数比较容差
        
    def _validate_input(self):
        """验证输入数据有效性"""
        if len(self.x_values) != len(self.y_values):
            raise ValueError("x_values和y_values长度必须相同")
        if len(self.x_values) < 2:
            raise ValueError("至少需要2个数据点才能插值")
            
    def interp(self, x, method='linear', tol=1e-6):
        """
        插值方法（基于XToYInterpolator逻辑）
        参数:
            x: 要插值的x值(可以是标量或数组)
            method: 仅支持'linear'（保持兼容性）
            tol: 判断重复x值的容差
            
        返回:
            成功时返回Y值列表，失败时返回错误信息字符串
        """
        if method != 'linear':
            warnings.warn("仅支持linear方法，已自动切换", RuntimeWarning)
            
        x = np.asarray(x, dtype=np.float64)
        scalar_input = x.ndim == 0
        if scalar_input:
            x = x[None]
            
        results = []
        for xi in x:
            try:
                y_values = self._get_y_values(xi)
                if y_values.size == 0:
                    results.append("Cannot find target value with input delta!")
                else:
                    results.append(y_values.tolist())  # 转换为列表保持兼容
            except ValueError:
                results.append("Cannot find target value with input delta!")
                
        return results[0] if scalar_input else results
        
    def _get_y_values(self, xi):
        """
        核心查询逻辑（来自XToYInterpolator）
        参数:
            xi: 要查询的X值
        返回:
            匹配的Y值数组
        """
        xi = float(xi)
        tol = self.tol

        # 1. 精确匹配
        exact_matches = np.isclose(self.x_values, xi, atol=tol)
        if np.any(exact_matches):
            return np.sort(np.unique(self.y_values[exact_matches]))
        
        # 2. 检查数据范围
        global_min = np.min(self.x_values)
        global_max = np.max(self.x_values)
        if xi < global_min - tol or xi > global_max + tol:
            raise ValueError("Extrapolation not supported")
        
        # 3. 遍历相邻点对
        results = []
        n = len(self.x_values)
        for i in range(n - 1):
            if np.isclose(self.x_values[i], self.x_values[i+1], atol=tol):
                continue
                
            x1, x2 = self.x_values[i], self.x_values[i+1]
            y1, y2 = self.y_values[i], self.y_values[i+1]
            interval_low = min(x1, x2)
            interval_high = max(x1, x2)
            
            if xi >= interval_low - tol and xi <= interval_high + tol:
                if xi < interval_low or xi > interval_high:
                    continue
                frac = (xi - x1) / (x2 - x1)
                interp_val = y1 + frac * (y2 - y1)
                results.append(interp_val)
        
        return np.array(results) if results else np.array([])

    # 保持原有方法兼容性
    def _safe_linear_interp(self, xi):
        """兼容方法（实际调用_get_y_values）"""
        try:
            result = self._get_y_values(xi)
            return result[0] if result.size > 0 else np.nan
        except ValueError:
            return np.nan
            
    def _robust_cubic_interp(self, xi):
        """兼容方法（降级为线性）"""
        warnings.warn("Cubic interpolation not supported, using linear instead")
        return self._safe_linear_interp(xi)