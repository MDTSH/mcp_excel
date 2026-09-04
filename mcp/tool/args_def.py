import json
from operator import truediv
import traceback

import mcp.tool.tool_utils as utils
import mcp.wrapper
from mcp.utils.enums import *
from mcp.utils.excel_utils import mcp_kv_wrapper, pf_nd_arrary_or_list, parse_dict_list
from mcp.forward.custom import general_fwd_register
from mcp.utils.mcp_utils import as_array, lower_key_dict
from mcp.wrapper import McpCalendar, McpCreditDefaultSwap, create_object_instance, McpRounder, to_mcp_args, McpAdjustmentTable, \
    mcp_wrapper_utils


def _format_vol_matrix_rows(val):
    vol_rows = []
    for row in val:
        if hasattr(row, "tolist"):
            row = row.tolist()
        if isinstance(row, (list, tuple)):
            items = row
        else:
            items = [row]
        vol_rows.append(",".join("" if item is None else str(item) for item in items))
    return ";".join(vol_rows)


def pf_dt_vol_matrix(val):
    if hasattr(val, "tolist"):
        val = val.tolist()
    if isinstance(val, str):
        raw = val.strip()
        if raw == "":
            return val
        try:
            parsed = json.loads(raw)
        except Exception:
            return val
        if isinstance(parsed, list) and parsed and isinstance(parsed[0], list):
            return _format_vol_matrix_rows(parsed)
        return val
    return _format_vol_matrix_rows(val)


class McpException(BaseException):

    def __init__(self, e):
        self.e: Exception = e

    def get_msg(self):
        try:
            msg = str(self.e.args[0])
            index = msg.rfind('(')
            if index >= 0:
                msg = msg[:index]
            return msg
        except:
            return str(self.e)


class McpArgsException(McpException):

    def __init__(self, key, lack_fields=[]):
        self.key = key
        self.lack_fields = lack_fields

    def get_msg(self):
        return f"{self.key} Missing fields: {self.lack_fields}"


class ItemDef:

    def __init__(self):
        self.init_data = {}
        self.init_kv_list = []
        self.methods_kv_list = {}
        self.key = self.__class__.__name__.replace("DefMcp", "Mcp")
        self.init_func = []
        self.custom_instance_func = None
        self.custom_instance_func_raw = None
        self.generate_xls_method = True
        self.generate_tools_method = True
        self.kv_const_dict = {}

        self.field_type_dict = None

    def find_match_kv_list(self, count, vals):
        for kv in self.init_kv_list:
            if len(kv) == count:
                return kv
        return []

    def get_const_field_enum(self, field):
        if field in self.kv_const_dict:
            return self.kv_const_dict[field]
        else:
            return field

    def is_valid_field(self, field_name):
        field_name = str(field_name).lower()
        return field_name in self.field_type_dict

    def is_list_field(self, field_name):
        if self.field_type_dict is None:
            self.field_type_dict = {}
            for kvs in self.init_kv_list:
                for kv in kvs:
                    self.field_type_dict[str(kv[0]).lower()] = str(kv[1])
        field_name = str(field_name).lower()
        if field_name in self.field_type_dict:
            t = self.field_type_dict[field_name]
            return t.count("list") >= 1 or t.count("array") >= 1
        return False

    def mcp_or_wrapper(self):
        is_wrapper = False
        if "is_wrapper" in self.init_data:
            is_wrapper = self.init_data["is_wrapper"]
        if is_wrapper:
            name = self.key
            if "pkg" in self.init_data:
                pkg = self.init_data["pkg"]
            else:
                pkg = "mcp.wrapper"
        else:
            name = self.key.replace("Mcp", "M")
            pkg = "mcp.mcp"
        return is_wrapper, name, pkg

    def get_fmt(self, d=None):
        if d is None:
            if "fmt" in self.init_data:
                return self.init_data["fmt"]
            else:
                return "VP"
        else:
            if "fmt" in d:
                return d["fmt"]
            else:
                return None

    def get_method_perifx(self):
        if "method_prefix" in self.init_data:
            return self.init_data["method_prefix"]
        else:
            return self.key.replace("Mcp", "")

    def add_method_def(self, method_def):
        method = str(method_def["method"]).lower()
        self.methods_kv_list[method] = method_def

    def add_method_range(self, methods, method_def):
        for method in methods:
            d = {}
            d.update(method_def)
            d["method"] = method
            self.add_method_def(d)

    def get_method_def(self, method):
        method = str(method).lower()
        if method in self.methods_kv_list:
            return self.methods_kv_list[method]
        else:
            return None

    def get_pyxll_def(self, d=None):
        if d is None:
            d = self.init_data
        if "pyxll_def" in d:
            return d["pyxll_def"]
        else:
            return {}

    def get_method_fmt(self, d):
        fmt = None
        has_fmt = False
        if "fmt" in d:
            has_fmt = True
            fmt = d["fmt"]
        return has_fmt, fmt

    def create_instance(self, args_list, fmt, data_fields):
        kvs_list = self.init_kv_list
        # kvs = kvs_list[0]
        # other_kvs = kvs_list[1:]
        # if data_fields is None:
        #     data_fields = self.init_data["data_fields"]
        # result, lack_keys = mcp_kv_wrapper.valid_parse_kv_list(self.key, args_list, fmt,
        #                                                        data_fields, kvs, other_kvs)
        if data_fields is None:
            data_fields = self.init_data["data_fields"]
        result, lack_keys = mcp_kv_wrapper.process_kv_list(args_list, fmt,
                                                           data_fields, kvs_list)
        if len(lack_keys) > 0:
            if len(self.init_func) > 0:
                for f in self.init_func:
                    args_dict = f(result["args_dict"])
                    result1, lack_keys1 = mcp_kv_wrapper.parse_args_dict(args_dict, kvs_list)
                    if len(lack_keys1) < len(lack_keys):
                        result, lack_keys = (result1, lack_keys1)
                    if len(lack_keys) == 0:
                        break
            if len(lack_keys) > 0:
                raise Exception("Missing fields: " + str(lack_keys))
        is_wrapper, name, pkg = self.mcp_or_wrapper()
        if tool_def.is_debug:
            print("create_instance:", self.key, pkg, name, result["vals"])
        # print("create_instance:", self.key, pkg, name, result["vals"])
        # print("create_instance dict:", self.key, result["dict"])
        if self.custom_instance_func is not None:
            return self.custom_instance_func(result["args_dict"])
        else:
            vals = result["vals"]
            if not is_wrapper:
                vals = to_mcp_args(result["vals"])
            try:
                return create_object_instance(pkg, name, vals)
            except Exception as e:
                if tool_def.raise_except:
                    raise McpException(e)
                else:
                    msg = str(e)
                    print(f"create_instance Exception: {self.key}, {msg}")
                    print(f"{self.key}, vals: {vals}")
                    print(f"{self.key}, args: {args_list}")
                    traceback.print_exc()
                    return msg


class ArgsDef:

    def __init__(self):
        self.item_dict = {}
        self.is_debug = False
        self.key_word_dict = {}
        self.raise_except = False

    def add_item(self, item):
        # key = str(item.key).lower()
        self.item_dict[item.key] = item

    def generate_key_word_dict(self):
        self.key_word_dict = utils.generate_key_word_dict(self.item_dict)
        # print("ArgsDef key_word_dict:", self.key_word_dict)

    def get_item(self, key) -> ItemDef:
        result = utils.find_key_word(key, self.key_word_dict, self.item_dict.keys())
        match_len = len(result)
        if match_len >= 1:
            if match_len > 1:
                print("Use:", result[0], "other:", ", ".join(result[1:]))
            return self.item_dict[result[0]]
        else:
            print("No match of:", key)
            return None
        # key = str(key).lower()
        # if key in self.item_dict:
        #     return self.item_dict[key]
        # else:
        #     method = str(key).lower()
        #     for item in self.item_dict:
        #         key = str(item).lower()
        #         if key.find(method) >= 0:
        #             return self.item_dict[item]
        #     # raise Exception(f"Not found {key}")
        #     return None

    def add_init_func(self, key, f):
        item_def = self.get_item(key)
        if item_def is None:
            raise Exception(f"Not found {key}")
        item_def.init_func.append(f)

    def get_init_def(self, key, index=0):
        item_def = self.get_item(key)
        if item_def is None:
            raise Exception(f"Not found {key}")
        kv_list = item_def.init_kv_list
        if index < len(kv_list):
            kvs = kv_list[index]
        else:
            kvs = kv_list[0]
        result = {}
        for kv in kvs:
            if len(kv) >= 3:
                result[kv[0]] = kv[2]
            else:
                result[kv[0]] = ""
        return result

    def merge_dicts(self, *args):
        temp = {}
        keys = {}
        for item in args:
            for key in item:
                lower_key = str(key).lower()
                temp[lower_key] = item[key]
                keys[lower_key] = key
        result = {}
        for key in temp:
            result[keys[key]] = temp[key]
        return result

    def xls_call(self, *args, key="", method=""):
        if tool_def.is_debug:
            print("xls_call:", key, method, args)
        item_def = self.get_item(key)
        if item_def is None:
            raise Exception(f"Invalid key: {key}.{method}")
        method_def = item_def.get_method_def(method)
        if method_def is None:
            raise Exception(f"Invalid method: {key}.{method}")
        has_fmt, fmt = item_def.get_method_fmt(method_def)
        if has_fmt:
            fmt = args[-1]
            args = args[:len(args) - 1]
        result, lack_keys = mcp_kv_wrapper.plain_parse(args, method_def["args"])
        # print(f'xls_call parse result:', method, result)
        if len(lack_keys) > 0:
            raise Exception("Missing fields: " + str(lack_keys))
        vals = result["vals"]
        if "func" in method_def:
            m = method_def["func"]
            result = m(*vals)
        else:
            vals = vals[1:]
            obj = args[0]
            m = getattr(obj, method_def["method"])
            # print(f'xls_call vals:', method, vals)
            result = m(*vals)
        if has_fmt:
            result = as_array(result, fmt, False)
        # print(f'xls_call result= ', result)
        return result

    def xls_create(self, *args, key=""):
        args_list = []
        # args = list(args)
        if tool_def.is_debug:
            print("xls_create:", key, args)
        for i in range(5):
            if args[i] is not None:
                args_list.append(args[i])
        fmt = args[5]
        return self.create_instance(key, args_list, fmt)

    def tool_create(self, key, args, fmt="VP", data_fields=[]):
        item_def = self.get_item(key)
        if item_def is not None and item_def.custom_instance_func_raw is not None:
            return item_def.custom_instance_func_raw(*args, key=key)
        args_list = args
        temp_list = pf_nd_arrary_or_list(args_list)
        args_list = [parse_dict_list(item) for item in temp_list]
        return self.create_instance(key, args_list, fmt, data_fields)

    def create_instance(self, key, args_list, fmt, data_fields=None):
        item_def = self.get_item(key)
        if item_def is None:
            raise Exception("Invalid key: " + str(key))
        return item_def.create_instance(args_list, fmt, data_fields)


def mcp_instance_list(*args, key=""):
    item_def = tool_def.get_item(key)
    if item_def is None:
        raise Exception("Invalid key: " + str(key))
    args_list = list(args)
    temp_list = pf_nd_arrary_or_list(args_list)
    single_args = []
    range_args = []
    for item in temp_list:
        arr = parse_dict_list(item)
        for kv in arr:
            if len(kv) < 2:
                continue
            if item_def.is_list_field(kv[0]):
                single_args.append([kv[0], kv[1]])
            else:
                if item_def.is_valid_field(kv[0]):
                    val = pf_nd_arrary_or_list(kv[1])
                    if isinstance(val, list):
                        range_args.append([kv[0], val])
                    else:
                        single_args.append([kv[0], val])
    if len(range_args) == 0:
        return tool_def.create_instance(key, [single_args], "VP", [])
    range_same = True
    range_info = {}
    for i in range(1, len(range_args)):
        prev = range_args[i - 1]
        cur = range_args[i]
        range_info[prev[0]] = len(prev[1])
        range_info[cur[0]] = len(cur[1])
        if len(prev[1]) != len(cur[1]):
            range_same = False
    if not range_same:
        raise Exception(key + " range args length not equals:" + str(range_info))
    obj_list = []
    for i in range(len(range_args[0][1])):
        range_item_args = [[item[0], item[1][i]] for item in range_args]
        obj_list.append(tool_def.create_instance(key, [single_args, range_item_args], "VP", []))
    return obj_list


class DefMcpYieldCurve(ItemDef):

    def __init__(self):
        super().__init__()
        self.custom_instance_func_raw = mcp_instance_list
        self.init_data = {
            "is_wrapper": True,
            "fmt": "VP|HD",
            "method_prefix": "YieldCurve",
            "data_fields": [
                ("Tenors", "str"),
                ("Dates", "date"),
                ("ZeroRates", "float"),
            ],
            "pyxll_def": {
            },
        }
        self.kv_const_dict = {
            'Variable': 'InterpolatedVariable',
            'Method': 'InterpolationMethod',
        }
        self.init_kv_list = [
            [
                ("ReferenceDate", "date"),
                ("Dates", "objectlist"),
                ("ZeroRates", "objectlist"),
                ("Frequency", "const", Frequency.NoFrequency, "NoFrequency"),
                ("Variable", "const", InterpolatedVariable.SIMPLERATES, "SIMPLERATES"),
                ("Method", "const", InterpolationMethod.LINEARINTERPOLATION, "LINEARINTERPOLATION"),
            ],
            [
                ("ReferenceDate", "date"),
                ("Tenors", "objectlist"),
                ("ZeroRates", "objectlist"),
                ("Method", "const", InterpolationMethod.LINEARINTERPOLATION, "LINEARINTERPOLATION"),
                ("Calendar", "object", McpCalendar("", "", "")),
                ("DayCounter", "const", DayCounter.ActActISDA),
                ("ValueDate", "date", ""),
            ],
            # C++ YieldCurve(FXForwardPointsCurve, YieldCurve, isCCY2, Calendar) — FX 隐含利率曲线
            [
                ("FXForwardPointsCurve", "object"),
                ("YieldCurve", "object"),
                ("IsCCY2", "bool"),
                ("Calendar", "object", McpCalendar("", "", "")),
            ],
        ]
        self.add_method_def({
            "method": "GetRefDate",
            "args": [
                ("curve", "object"),
            ],
        })
        self.add_method_def({
            "method": "ZeroRate",
            "args": [
                ("curve", "object"),
                ("date", "date"),
                ("dayCounter", "const", DayCounter.NONE, "NONE"),
                # compounding=True/frequency=366(Continuous) 与底层默认一致，不影响既有公式
                # frequency 可选 0(单利)/1(年复利)/2(半年复利 BEY)/4(季度复利)/366(连续复利)
                ("compounding", "bool", True, True),
                ("frequency", "const", Frequency.Continuous, "Continuous"),
            ],

        })
        self.add_method_def({
            "method": "ForwardRate",
            "args": [
                ("curve", "object"),
                ("StartDate", "date"),
                ("EndDate", "date"),
                ("DayCounter", "const", DayCounter.Act360, "Act360"),
                # 默认值由原来的 单利(False)/NoFrequency 改为 复利(True)/Continuous，
                # 与 MYieldCurve/MParametricCurve 底层 ForwardRate 默认保持一致。
                # 注意：不传参的旧 Excel 公式结果会从"单利"变为"连续复利"，
                # 如需保持旧行为请显式传 (Compounding=False, Frequency=NoFrequency)。
                ("Compounding", "bool", True),
                ("Frequency", "const", Frequency.Continuous, "Continuous"),
            ],
        })
        self.add_method_def({
            "method": "DiscountFactor",
            "args": [
                ("curve", "object"),
                ("date", "date"),
            ]
        })
        # 这个方法输入是double类型，excel日期也会被当作double类型，比较容易混淆
        # self.add_method_def({
        #     "method": "DiscountFactor",
        #     "args": [
        #         ("curve", "object"),
        #         ("time", "double"),
        #     ]
        # })
        self.add_method_def({
            "method": "MaturityDate",
            "args": [
                ("curve", "object"),
                ("tenor", "str"),
            ]
        })

        def ZeroRates(obj, dates):
            return [obj.ZeroRate(date) for date in dates]

        def DiscountFactors(obj, dates):
            return [obj.DiscountFactor(date) for date in dates]

        self.add_method_def({
            "method": "ZeroRates",
            "args": [
                ("curve", "object"),
                ("dates", "array_date"),
            ],
            "fmt": "V",
            "func": ZeroRates,
            "pyxll_def": {
                "auto_resize": True
            },
        })
        self.add_method_def({
            "method": "DiscountFactors",
            "args": [
                ("curve", "object"),
                ("dates", "array_date"),
            ],
            "fmt": "V",
            "func": DiscountFactors,
            "pyxll_def": {
                "auto_resize": True
            },
        })


class DefMcpYieldCurve2(ItemDef):

    def __init__(self):
        super().__init__()
        self.custom_instance_func_raw = mcp_instance_list
        self.init_data = {
            "is_wrapper": True,
            "fmt": "VP|HD",
            "method_prefix": "YieldCurve2",
            "data_fields": [
                ("Tenors", "str"),
                ("Dates", "date"),
                ("BidZeroRates", "float"),
                ("AskZeroRates", "float"),
            ],
            "pyxll_def": {
            },
        }
        self.kv_const_dict = {
            'Variable': 'InterpolatedVariable',
            'Method': 'InterpolationMethod',
        }
        self.init_kv_list = [
            [
                ("ReferenceDate", "date"),
                ("Tenors", "objectlist"),
                ("BidZeroRates", "objectlist"),
                ("AskZeroRates", "objectlist"),
                ("Frequency", "const", Frequency.NoFrequency, "NoFrequency"),
                ("Variable", "const", InterpolatedVariable.SIMPLERATES, "SIMPLERATES"),
                ("Method", "const", InterpolationMethod.LINEARINTERPOLATION, "LINEARINTERPOLATION"),
                ("Calendar", "object", McpCalendar("", "", "")),
                ("DayCounter", "const", DayCounter.Act360),
                ("ValueDate", "date", ""),
            ],
            [
                ("Method", "const", InterpolationMethod.LINEARINTERPOLATION, "LINEARINTERPOLATION"),
                ("ReferenceDate", "date"),
                ("Dates", "objectlist"),
                ("BidZeroRates", "objectlist"),
                ("AskZeroRates", "objectlist"),
                ("Frequency", "const", Frequency.NoFrequency, "NoFrequency"),
                ("Variable", "const", InterpolatedVariable.SIMPLERATES, "SIMPLERATES"),
                ("ValueDate", "date", ""),
            ],
            [
                ("BidYieldCurve", "object"),
                ("AskYieldCurve", "object"),
            ],
            [
                ("FxForwardPointsCurve2", "object"),
                ("YieldCurve2", "object"),
                ("CalculatedTarget", "const"),
                ("Calendar", "object", McpCalendar("", "", "")),
            ],
        ]
        self.add_method_def({
            "method": "GetRefDate",
            "args": [
                ("curve", "object"),
            ],

        })
        self.add_method_def({
            "method": "ZeroRate",
            "args": [
                ("curve", "object"),
                ("date", "date"),
                ("bidMidAsk", "str", 'MID'),
            ],

        })
        self.add_method_def({
            "method": "DiscountFactor",
            "args": [
                ("curve", "object"),
                ("date", "date"),
                ("bidMidAsk", "str", 'MID'),
            ]
        })
        self.add_method_def({
            "method": "MaturityDate",
            "args": [
                ("curve", "object"),
                ("tenor", "str"),
            ]
        })


class DefMcpVolSurface2(ItemDef):

    def __init__(self):
        super().__init__()
        self.custom_instance_func_raw = mcp_instance_list
        self.init_data = {
            "is_wrapper": True,
            "fmt": "VP|HD",
            "method_prefix": "VolSurface2",
            "data_fields": [
                ("ExpiryDates", "date"),
                ("BidStrikes", "float"),
                ("AskStrikes", "float"),
                ("BidPremiums", "float"),
                ("AskPremiums", "float"),
                ("BidImpVols", "float"),
                ("AskImpVols", "float"),
                ("BidOptionTypes", "const"),
                ("AskOptionTypes", "const"),
            ],
            "pyxll_def": {
            },
        }
        self.kv_const_dict = {
            'SmileInterp': 'SmileInterpolation',
        }
        self.init_kv_list = [
            [
                ("ReferenceDate", "date"),
                ("BidSpot", "float"),
                ("AskSpot", "float"),
                ("ExpiryDates", 'objectlist'),
                ("BidStrikes", "objectlist"),
                ("BidOptionTypes", "objectlist"),
                ("BidPremiums", "objectlist"),
                ("AskStrikes", "objectlist"),
                ("AskOptionTypes", "objectlist"),
                ("AskPremiums", "objectlist"),
                ("RiskFreeRateCurve2", "object"),
                ("Dividend", "float"),
                ("SmileInterp", "const"),
                ("Calendar", "object", McpCalendar("", "", "")),
                ("DateAdjusterRule", "const", DateAdjusterRule.ModifiedFollowing, "ModifiedFollowing"),
                ("BidImpVols", "objectlist"),
                ("AskImpVols", "objectlist"),
                ("SpotDate", "date"),
                ("MiniStrikeSize", "int")
            ],
            [
                ("ReferenceDate", "date"),
                ("ExpiryDates", 'objectlist'),
                ("BidStrikes", "objectlist"),
                ("BidOptionTypes", "objectlist"),
                ("BidPremiums", "objectlist"),
                ("AskStrikes", "objectlist"),
                ("AskOptionTypes", "objectlist"),
                ("AskPremiums", "objectlist"),
                ("RiskFreeRateCurve2", "object"),
                ("ForwardCurve2", "object"),
                ("SmileInterp", "const"),
                ("Calendar", "object", McpCalendar("", "", "")),
                ("DateAdjusterRule", "const", DateAdjusterRule.ModifiedFollowing, "ModifiedFollowing"),
                ("BidImpVols", "objectlist"),
                ("AskImpVols", "objectlist"),
                ("SpotDate", "date"),
                ("MiniStrikeSize", "int"),
                ("UsingImpVols", "bool", True)
            ],
            [
                ("ReferenceDate", "date"),
                ("ExpiryDates", 'objectlist'),
                ("BidStrikes", "objectlist"),
                ("BidOptionTypes", "objectlist"),
                ("BidPremiums", "objectlist"),
                ("AskStrikes", "objectlist"),
                ("AskOptionTypes", "objectlist"),
                ("AskPremiums", "objectlist"),
                ("RiskFreeRate", "float"),
                ("ForwardCurve2", "object"),
                ("SmileInterp", "const"),
                ("Calendar", "object", McpCalendar("", "", "")),
                ("DateAdjusterRule", "const", DateAdjusterRule.ModifiedFollowing, "ModifiedFollowing"),
                ("BidImpVols", "objectlist"),
                ("AskImpVols", "objectlist"),
                ("SpotDate", "date"),
                ("MiniStrikeSize", "int")
            ],
            [
                ("ReferenceDate", "date"),
                ("ExpiryDates", 'objectlist'),
                ("BidStrikes", "objectlist"),
                ("BidOptionTypes", "objectlist"),
                ("BidPremiums", "objectlist"),
                ("AskStrikes", "objectlist"),
                ("AskOptionTypes", "objectlist"),
                ("AskPremiums", "objectlist"),
                ("YieldCurve2", "object"),
                ("RiskFreeRateCurve2", "object"),
                ("SmileInterp", "const"),
                ("Calendar", "object", McpCalendar("", "", "")),
                ("DateAdjusterRule", "const", DateAdjusterRule.ModifiedFollowing, "ModifiedFollowing"),
                ("BidImpVols", "objectlist"),
                ("AskImpVols", "objectlist"),
                ("SpotDate", "date"),
                ("MiniStrikeSize", "int")
            ],
        ]
        self.add_method_def({
            "method": "GetVolatility",
            "args": [
                ("vs", "object"),
                ("interpVariable", "float"),
                ("maturityDate", "date"),
                ("bidMidAsk", "str", 'MID'),
                #                ("deltaOrStrike","int", "2"), # STRIKE_INTERPOLATION
                #                ("forward", "float", "0.0"),
            ],
        })
        self.add_method_def({
            "method": "GetSpotDate",
            "args": [
                ("vs", "object"),
            ],
        })
        self.add_method_def({
            "method": "GetReferenceDate",
            "args": [
                ("vs", "object"),
            ],
        })
        self.add_method_range(
            ["GetForward", "GetRiskFreeRate"],
            {
                "args": [
                    ("vs", "object"),
                    ("expiryOrDeliveryDate", "date"),
                    ("isDeliveryDate", "bool", False),
                    ("bidMidAsk", "str", 'MID'),
                ],
            }
        )
        self.add_method_range(
            ["GetForward", "GetRiskFreeRate"],
            {
                "args": [
                    ("vs", "object"),
                    ("expiryOrDeliveryDate", "date"),
                    ("isDeliveryDate", "bool", False),
                    ("bidMidAsk", "str", 'MID'),
                ],
            }
        )
        self.add_method_range(
            ["GetSpot"],
            {
                "args": [
                    ("vs", "object"),
                    ("bidMidAsk", "str", 'MID'),
                ],
            }
        )
        self.add_method_range(
            ["ExpiryDates", "ExpiryTimes", "GetForwards"],
            {
                "args": [
                    ("vs", "object"),
                    ("bidMidAsk", "str", 'MID'),
                ],
                "fmt": "V",
                "pyxll_def": {
                    "auto_resize": True
                },
            }
        )
        self.add_method_range(
            ["Strikes"],
            {
                "args": [
                    ("vs", "object"),
                    ("bidMidAsk", "str", 'MID'),
                ],
                "fmt": "H",
                "pyxll_def": {
                    "auto_resize": True
                },
            }
        )
        self.add_method_range(
            ["Volatilities"],
            {
                "args": [
                    ("vs", "object"),
                    ("bidMidAsk", "str", 'MID'),
                ],
                "fmt": "H",
                "pyxll_def": {
                    "auto_resize": True
                },
            }
        )


class DefMcpSwapCurve(ItemDef):

    def __init__(self):
        super().__init__()
        self.init_data = {
            "is_wrapper": True,
            "data_fields": [
                ("SettlementDates", "date"),
                ("MaturityDates", "date"),
                ("Coupons", "float"),
                ("FixedFrequencies", "const"),
                ("FloatingFrequencies", "const"),
                ("BumpAmounts", "float"),
                ("BUses", "intbool"),
            ]
        }
        self.kv_const_dict = {
            'AdjustRule': 'DateAdjusterRule',
        }
        self.init_kv_list = [
            [
                ("SettlementDate", "date"),
                ("CalibrationSet", "object"),
                ("InterpolatedVariable", "const"),
                ("InterpolationMethod", "const"),
                ("DayCounter", "const", DayCounter.Act365Fixed, "Act365Fixed"),
                ("UseGlobalSolver", "bool", True),  # 与 C++ testSOFRCurveBBGComparison 一致
                ("PillarEndDate", "int", 0, 0),
            ],
            [
                ("ReferenceDate", "date"),
                ("CalibrationSet", "mcphandler"),
                ("InterpolatedVariable", "const"),
                ("InterpolationMethod", "const"),
                ("DayCounter", "const"),
                ("UseGlobalSolver", "bool", True),
                ("PillarEndDate", "int", 0, 0),
            ],
            [
                ("ReferenceDate", "date"),
                ("InterpolatedVariable", "const"),
                ("InterpolationMethod", "const"),
                ("FixedDayCounter", "const", DayCounter.Act365Fixed, "Act365Fixed"),
                ("FloatDayCounter", "const", DayCounter.Act365Fixed, "Act365Fixed"),

                ("DayCounter", "const", DayCounter.Act365Fixed, "Act365Fixed"),
                ("Calendar", "object"),
                ("AdjustRule", "const"),

                ("SettlementDates", "plainlist"),
                ("MaturityDates", "plainlist"),
                ("Coupons", "plainlist"),
                ("FixedFrequencies", "plainlist"),
                ("FloatingFrequencies", "plainlist"),
                ("BumpAmounts", "plainlist"),
                ("BUses", "plainlist"),
            ],
        ]
        self.add_method_def({
            "method": "GetRefDate",
            "args": [
                ("curve", "object"),
            ],

        })
        self.add_method_def({
            "method": "ZeroRate",
            "args": [
                ("curve", "object"),
                ("endDate", "date"),
                ("dayCounter", "const", DayCounter.NONE, "NONE"),
                # compounding=True/frequency=366(Continuous) 与底层默认一致，不影响既有公式
                # frequency 可选 0(单利)/1(年复利)/2(半年复利 BEY)/4(季度复利)/366(连续复利)
                ("compounding", "bool", True, True),
                ("frequency", "const", Frequency.Continuous, "Continuous"),
            ],
        })
        self.add_method_def({
            "method": "DiscountFactor",
            "args": [
                ("curve", "object"),
                ("date", "date"),
            ]
        })
        self.add_method_def({
            "method": "Carry",
            "args": [
                ("curve", "object"),
                ("horizon", "str"),
                ("maturityPeriod", "str"),
            ]
        })
        self.add_method_def({
            "method": "Roll",
            "args": [
                ("curve", "object"),
                ("horizon", "str"),
                ("maturityPeriod", "str"),
            ]
        })
        self.add_method_def({
            "method": "ParSwapRate",
            "args": [
                ("curve", "object"),
                ("start", "str"),
                ("end", "str"),
            ]
        })

        def ZeroRates(obj, dates):
            return [obj.ZeroRate(date) for date in dates]

        def DiscountFactors(obj, dates):
            return [obj.DiscountFactor(date) for date in dates]

        self.add_method_def({
            "method": "ZeroRates",
            "args": [
                ("curve", "object"),
                ("dates", "array_date"),
            ],
            "fmt": "V",
            "pyxll_def": {
                "auto_resize": True
            },
            "func": ZeroRates,
        })
        self.add_method_def({
            "method": "DiscountFactors",
            "args": [
                ("curve", "object"),
                ("dates", "array_date"),
            ],
            "fmt": "V",
            "pyxll_def": {
                "auto_resize": True
            },
            "func": DiscountFactors,
        })


class DefMcpVolSurface(ItemDef):

    def __init__(self):
        super().__init__()
        self.init_data = {
            "is_wrapper": True,
            "fmt": "VP|HD",
            "data_fields": [
                ("ExpiryDates", "date"),
                ("SettlementDates", "date"),
                ("OptionTypes", "const"),
                ("Strikes", "float"),
                ("Premiums", "float"),
                ("ImpVols", "float"),
                ("ATM", "float"),
                ("25BF", "float"),
                ("10BF", "float"),
                ("25RR", "float"),
                ("10RR", "float"),
                ("DomRates", "float"),
                ("ForRates", "float"),
            ],
            "pyxll_def": {
            },
        }
        self.init_kv_list = [
            [
                ("ReferenceDate", "date"),
                ("SpotPx", "float"),
                ("ExpiryDates", "plainlist"),
                ("OptionTypes", "optiontypelist"),
                ("Strikes", "plainlist"),
                ("Premiums", "plainlist"),
                ("RiskFreeRateCurve", "object"),
                ("Dividend", "float"),
                ("SmileInterp", "const"),
                ("Calendar", "object"),
                ("DateAdjusterRule", "const"),
                ("SpotDate", "date"),
                ("ImpVols", "plainlist"),
                ("MiniStrikeSize", "int", 3),
                ("UsingImpVols", "bool", True)
            ],
            [
                ("ReferenceDate", "date"),
                ("ExpiryDates", "plainlist"),
                ("OptionTypes", "optiontypelist"),
                ("Strikes", "plainlist"),
                ("Premiums", "plainlist"),
                ("RiskFreeRateCurve", "object"),
                ("ForwardCurve", "object"),
                ("SmileInterp", "const"),
                ("Calendar", "object"),
                ("DateAdjusterRule", "const"),
                ("SpotDate", "date"),
                ("ImpVols", "plainlist"),
                ("MiniStrikeSize", "int", 3),
                ("UsingImpVols", "bool", True)
            ],
            [
                ("ReferenceDate", "date"),
                ("ExpiryDates", "plainlist"),
                ("OptionTypes", "optiontypelist"),
                ("Strikes", "plainlist"),
                ("Premiums", "plainlist"),
                ("RiskFreeRate", "float"),
                ("ForwardCurve", "object"),
                ("SmileInterp", "const"),
                ("Calendar", "object"),
                ("DateAdjusterRule", "const"),
                ("SpotDate", "date"),
                ("ImpVols", "plainlist"),
                ("MiniStrikeSize", "int", 3),
                ("UsingImpVols", "bool", True)
            ],
            [
                ("ReferenceDate", "date"),
                ("SpotDate", "date"),
                ("SpotPx", "float"),
                ("CallPut", "const"),
                ("DeltaRHS", "bool"),
                ("InterestRateType", "const"),
                ("FXVolatilitySurfaceType", "const"),
                ("FXVolatilityInterpolationType", "const"),
                ("ExpiryDates", "plainlist"),
                ("SettlementDates", "plainlist"),
                ("ATM", "plainlist"),
                ("25BF", "plainlist"),
                ("10BF", "plainlist"),
                ("25RR", "plainlist"),
                ("10RR", "plainlist"),
                ("DomRates", "plainlist"),
                ("ForRates", "plainlist"),
            ],
        ]
        self.add_method_def({
            "method": "GetVolatility",
            "args": [
                ("vs", "object"),
                ("strike", "float"),
                ("expiryDate", "date"),
                ("forward", "float", 0.0),
            ],
        })
        self.add_method_def({
            "method": "InterpolateRate",
            "args": [
                ("obj", "object"),
                ("expiryDate", "date"),
                ("foreignRate", "bool"),
                ("getDiscountFactor", "bool"),
            ],
        })
        self.add_method_def({
            "method": "GetSpotDate",
            "args": [
                ("vs", "object"),
            ],
        })
        self.add_method_def({
            "method": "GetReferenceDate",
            "args": [
                ("vs", "object"),
            ],
        })
        self.add_method_range(
            ["GetForward", "GetRiskFreeRate"],
            {
                "args": [
                    ("vs", "object"),
                    ("expiryOrDeliveryDate", "date"),
                    ("isDeliveryDate", "bool", False),
                ],
            }
        )
        self.add_method_range(
            ["GetSpot", "GetDividend"],
            {
                "args": [
                    ("vs", "object"),
                ],
            }
        )
        self.add_method_range(
            ["ExpiryDates", "ExpiryTimes", "GetForwards"],
            {
                "args": [
                    ("vs", "object"),
                ],
                "fmt": "V",
                "pyxll_def": {
                    "auto_resize": True
                },
            }
        )
        self.add_method_range(
            ["Strikes"],
            {
                "args": [
                    ("vs", "object"),
                ],
                "fmt": "H",
                "pyxll_def": {
                    "auto_resize": True
                },
            }
        )
        self.add_method_range(
            ["Volatilities"],
            {
                "args": [
                    ("vs", "object"),
                ],
                "fmt": "H",
                "pyxll_def": {
                    "auto_resize": True
                },
            }
        )


def _mcp_localvol_prepare_args(args_dict):
    """UsingImpVols=False 且 ImpVols 为空时去掉该键，使 ImpVols 默认值生效并匹配股指/期货重载。"""
    lower = {str(k).lower(): v for k, v in args_dict.items()}
    using_imp = lower.get("usingimpvols")
    if using_imp in (False, "FALSE", "false", 0, "0"):
        imp = lower.get("impvols")
        if imp is None or (isinstance(imp, str) and imp.strip() == ""):
            for k in list(args_dict.keys()):
                if str(k).lower() == "impvols":
                    del args_dict[k]
    return args_dict


class DefMcpLocalVol(ItemDef):

    def __init__(self):
        super().__init__()
        self.init_func.append(_mcp_localvol_prepare_args)
        self.init_data = {
            "is_wrapper": True,
            "fmt": "VP|HD",
            "data_fields": [
                ("ExpiryDates", "date"),
                ("Strikes", "float"),
                ("OptionTypes", "const"),
                ("Premiums", "float"),
                ("ImpVols", "float"),
                ("LowerGuessParams", "float"),
                ("UpperGuessParams", "float"),
            ],
            "pyxll_def": {
            },
        }
        self.init_kv_list = [
            [
                ("FXVolSurface", "object"),
                ("LocalVolModel", "const", 4),
                ("LogLevel", "const", 6),
                ("TraceFile", "str", ""),
                ("MiniStrikeSize", "int", 3),
                ("UseOtmOptionType", "bool", True),
            ],
            [
                ("FXVolSurface", "object"),
                ("LocalVolModel", "const", 4),
                ("LogLevel", "const", 6),
                ("TraceFile", "str", ""),
                ("MiniStrikeSize", "int", 3),
                ("UseOtmOptionType", "bool", True),
                ("DeltaStrings", "plainlist", ""),
                ("LowerGuessParams", "plainlist", ""),
                ("UpperGuessParams", "plainlist", ""),
            ],
            [
                ("ReferenceDate", "date"),
                ("Spot", "float"),
                ("ExpiryDates", "datelist"),
                ("OptionTypes", "optiontypelist"),
                ("Strikes", "plainlist"),
                ("Premiums", "plainlist"),
                ("PremiumAdjusted", "bool"),
                ("DomesticCurve", "object"),
                ("ForeignCurve", "object"),
                ("FXForwardCurve", "object"),
                ("CalculatedTarget", "const"),
                ("LocalVolModel", "const"),
                ("LogLevel", "const"),
                ("TraceFile", "str", ""),
                ("Calendar", "object"),
                ("DateAdjusterRule", "const"),
                ("SpotDate", "date"),
                ("ImpVols", "plainlist", "[]"),
                ("MiniStrikeSize", "int"),
                ("UsingImpVols", "bool", True),
                ("LowerGuessParams", "plainlist", ""),
                ("UpperGuessParams", "plainlist", ""),
            ],
            [
                ("ReferenceDate", "date"),
                ("Spot", "float"),
                ("ExpiryDates", "datelist"),
                ("OptionTypes", "optiontypelist"),
                ("Strikes", "plainlist"),
                ("Premiums", "plainlist"),
                ("RiskFreeRateCurve", "object"),
                ("Dividend", "float"),
                ("LocalVolModel", "const"),
                ("LogLevel", "const"),
                ("TraceFile", "str", ""),
                ("Calendar", "object"),
                ("DateAdjusterRule", "const"),
                ("SpotDate", "date"),
                ("ImpVols", "plainlist", "[]"),
                ("MiniStrikeSize", "int"),
                ("UsingImpVols", "bool", True),
                ("UsingImpDividend", "bool", False),
                ("LowerGuessParams", "plainlist", ""),
                ("UpperGuessParams", "plainlist", ""),
            ],
            [
                ("ReferenceDate", "date"),
                ("ExpiryDates", "datelist"),
                ("OptionTypes", "optiontypelist"),
                ("Strikes", "plainlist"),
                ("Premiums", "plainlist"),
                ("RiskFreeRateCurve", "object"),
                ("ForwardCurve", "object"),
                ("LocalVolModel", "const"),
                ("LogLevel", "const"),
                ("TraceFile", "str", ""),
                ("Calendar", "object"),
                ("DateAdjusterRule", "const"),
                ("SpotDate", "date"),
                ("ImpVols", "plainlist", '[0.0]'),
                ("MiniStrikeSize", "int"),
                ("UsingImpVols", "bool", True),
                ("LowerGuessParams", "plainlist", ""),
                ("UpperGuessParams", "plainlist", ""),
            ],
        ]
        self.add_method_def({
            "method": "GetVolatility",
            "args": [
                ("vs", "object"),
                ("strike", "float"),
                ("expiryDate", "date"),
            ],
        })
        self.add_method_def({
            "method": "GetSpot",
            "args": [
                ("vs", "object"),
            ],
        })


class DefMcpMktVolSurface(ItemDef):

    def __init__(self):
        super().__init__()

    def pf_dt_vol(val):
        """
        将波动率数据转换为字符串格式

        参数:
            val: 可以是二维列表或已格式化的字符串

        返回:
            str: 分号分隔行，逗号分隔列的波动率字符串
        """
        if isinstance(val, str):
            # 如果已经是字符串，直接返回
            return val
        # 处理二维列表的情况
        vol_rows = []
        for row in val:
            items = [str(item) for item in row]
            vol_rows.append(",".join(items))
        return ";".join(vol_rows)

        bd_type = "bd@McpMktVolSurface"
        mcp_kv_wrapper.parse_func_dict[bd_type] = pf_dt_vol

        self.init_data = {
            "is_wrapper": True,
            "fmt": "DT|VP|HD",
            "data_fields": [
                ("Tenors", "str"),
                ("DeltaStrings", "str"),
                ("MaturityDates", "date"),
                ("Strikes", "float"),
                ("Volatilities", "float"),
                ("DeltaTypes", "const"),
                ("AtmVolTypes", "const"),
                ("PutWingRatios", "float"),
                ("CallWingRatios", "float"),
            ],
            "pyxll_def": {
            },
        }
        self.kv_const_dict = {
            ("SmileInterpMethod", "const"),

        }
        self.init_kv_list = [
            [
                ("ReferenceDate", "date"),
                ("SpotPx", "float"),
                ("Tenors", "plainlist"),  # Tenors
                ("DeltaStrings", "plainlist"),  # DeltaStrings
                ("Strikes", "str"),
                ("Volatilities", "str"),
                ("ForeignCurve", "object"),
                ("DomesticCurve", "object"),
                ("Calendar", "object"),
                ("DateAdjusterRule", "const"),
                ("DeltaType", "const"),
                ("SmileInterpMethod", "const"),
                ("FxForwardPointsCurve", "object"),
                ("PremiumAdjusted", "bool", True),
                ("IsATMFwd", "bool", False),
                ("SpotDate", "date"),
                ("CalculatedTarget", "const", CalculateTarget.CCY1),
            ],
            [
                ("ReferenceDate", "date"),
                ("MaturityDates", "plainlist"),  # MaturityDates
                ("SpotPx", "float"),
                ("DeltaStrings", "plainlist"),  # DeltaStrings
                ("Strikes", "str"),
                ("Volatilities", "str"),
                ("ForeignCurve", "object"),
                ("DomesticCurve", "object"),
                ("Calendar", "object"),
                ("DateAdjusterRule", "const"),
                ("DeltaType", "const"),
                ("SmileInterpMethod", "const"),
                ("FxForwardPointsCurve", "object"),
                ("PremiumAdjusted", "bool", True),
                ("IsATMFwd", "bool", False),
                ("SpotDate", "date"),
                ("CalculatedTarget", "const", CalculateTarget.CCY1),
            ],
            [
                ("ReferenceDate", "date"),
                ("SpotPx", "float"),
                ("Tenors", "plainlist"),
                ("DeltaStrings", "plainlist"),
                ("Volatilities", bd_type),
                ("ForeignCurve", "object"),
                ("DomesticCurve", "object"),
                ("Calendar", "object"),
                ("DateAdjusterRule", "const"),
                ("DeltaType", "const"),
                ("SmileInterpMethod", "const"),
                ("FxForwardPointsCurve", "object"),
                ("PremiumAdjusted", "bool", True),
                ("IsATMFwd", "bool", False),
                ("SpotDate", "date"),
                ("CalculatedTarget", "const", CalculateTarget.CCY1),
                ("FXVolInterpType", "const", FXVolInterpType.SPLINE_VOLATILITY),
            ],
            [
                ("ReferenceDate", "date"),
                ("SpotPx", "float"),
                ("Tenors", "plainlist"),
                ("DeltaStrings", "plainlist"),
                ("@bd", bd_type),
                ("ForeignCurve", "object"),
                ("DomesticCurve", "object"),
                ("Calendar", "object"),
                ("DateAdjusterRule", "const"),
                ("DeltaType", "const"),
                ("SmileInterpMethod", "const"),
                ("FxForwardPointsCurve", "object"),
                ("PremiumAdjusted", "bool", True),
                ("IsATMFwd", "bool", False),
                ("SpotDate", "date"),
                ("CalculatedTarget", "const", CalculateTarget.CCY1),
                ("FXVolInterpType", "const", FXVolInterpType.SPLINE_VOLATILITY),
            ],
            [
                ("ReferenceDate", "date"),
                ("SpotPx", "float"),
                ("Tenors", "plainlist"),
                ("DeltaStrings", "plainlist"),
                ("@bd", bd_type),
                ("DeltaTypes", "plainlist"),
                ("AtmVolTypes", "plainlist"),
                ("PutWingRatio", "float"),
                ("CallWingRatio", "float"),
                ("PremiumAdjusted", "bool", True),
                ("ForeignCurve", "object"),
                ("DomesticCurve", "object"),
                ("Calendar", "object"),
                ("DateAdjusterRule", "const"),
                ("SmileInterpMethod", "const"),
                ("FxForwardPointsCurve", "object"),
                ("SpotDate", "date"),
                ("CalculatedTarget", "const", CalculateTarget.CCY1),
            ],
            [
                ("ReferenceDate", "date"),
                ("SpotPx", "float"),
                ("Tenors", "plainlist"),
                ("DeltaStrings", "plainlist"),
                ("@bd", bd_type),
                ("DeltaTypes", "plainlist"),
                ("AtmVolTypes", "plainlist"),
                ("PutWingRatios", "plainlist"),
                ("CallWingRatios", "plainlist"),
                ("PremiumAdjusted", "bool", True),
                ("ForeignCurve", "object"),
                ("DomesticCurve", "object"),
                ("Calendar", "object"),
                ("DateAdjusterRule", "const"),
                ("SmileInterpMethod", "const"),
                ("FxForwardPointsCurve", "object"),
                ("SpotDate", "date"),
                ("CalculatedTarget", "const", CalculateTarget.CCY1),
            ],
            [
                ("ReferenceDate", "date"),
                ("SpotPx", "float"),
                ("Tenors", "plainlist"),
                ("DeltaStrings", "plainlist"),
                ("@bd", bd_type),
                ("DeltaTypes", "plainlist"),
                ("AtmVolTypes", "plainlist"),
                ("ForeignCurve", "object"),
                ("DomesticCurve", "object"),
                ("Calendar", "object"),
                ("DateAdjusterRule", "const"),
                ("SmileInterpMethod", "const"),
                ("FxForwardPointsCurve", "object"),
                ("PremiumAdjusted", "bool", True),
                ("SpotDate", "date"),
                ("CalculatedTarget", "const", CalculateTarget.CCY1),
                ("FXVolInterpType", "const", FXVolInterpType.SPLINE_VOLATILITY),
            ],
            # [
            #     ("ReferenceDate", "date"),
            #     ("SpotPx", "float"),
            #     ("Tenors", "plainlist"),
            #     ("DeltaStrings", "plainlist"),
            #     ("@bd", bd_type),
            #     ("@bd", bd_type),
            #     ("ForeignCurve", "object"),
            #     ("DomesticCurve", "object"),
            #     ("Calendar", "object"),
            #     ("DateAdjusterRule", "const"),
            #     ("DeltaType", "const"),
            #     ("SmileInterpMethod", "const"),
            #     ("FxForwardPointsCurve", "object"),
            #     ("PremiumAdjusted", "bool", True),
            #     ("IsATMFwd", "bool", False),
            #     ("SpotDate", "date"),
            #
            # ],
            # [
            #     ("ReferenceDate", "date"),
            #     ("MaturityDates", "plainlist"),
            #     ("SpotPx", "float"),
            #     ("DeltaStrings", "plainlist"),
            #     ("Strikes",bd_type),
            #     ("Volatilities", bd_type),
            #     ("ForeignCurve", "object"),
            #     ("DomesticCurve", "object"),
            #     ("Calendar", "object"),
            #     ("DateAdjusterRule", "const"),
            #     ("DeltaType", "const"),
            #     ("SmileInterpMethod", "const"),
            #     ("FxForwardPointsCurve", "object"),
            #     ("PremiumAdjusted", "bool", True),
            #     ("IsATMFwd", "bool", False),
            #     ("SpotDate", "date"),

            # ],
        ]
        # self.add_method_def({
        #     "method": "GetVolatility",
        #     "args": [
        #         ("vs", "object"),
        #         ("spotPx", "float", 0),
        #         ("ForeignRate", "float"),
        #         ("DomesticRate", "float"),
        #         ("interpVariable", "float"),
        #         ("expiryDate", "date"),
        #         ("deltaOrStrike", "const"),
        #     ],
        # })
        self.add_method_def({
            "method": "GetVolatility",
            "args": [
                ("vs", "object"),
                ("strike", "float"),
                ("expiryDate", "date"),
                ("forward", "float", 0.0),
                ("InputDeltaVolPair", "str", ''),
            ],
        })
        self.add_method_def({
            "method": "GetVolatilityByDeltaStr",
            "args": [
                ("vs", "object"),
                ("deltaString", "str"),
                ("expiryDate", "date"),
                ("forward", "float", 0.0),
                ("InputDeltaVolPair", "str", ''),
            ],
        })
        self.add_method_def({
            "method": "GetDomesticRate",
            "args": [
                ("vs", "object"),
                ("expiryOrDeliveryDate", "date"),
                ("isDeliveryDate", "bool", True),
                ("isDirect", "bool", False),
            ],
        })
        self.add_method_def({
            "method": "GetForeignRate",
            "args": [
                ("vs", "object"),
                ("expiryOrDeliveryDate", "date"),
                ("isDeliveryDate", "bool", True),
                ("isDirect", "bool", False),
            ],
        })
        self.add_method_def({
            "method": "GetForwardPoint",
            "args": [
                ("vs", "object"),
                ("expiryOrDeliveryDate", "date"),
                ("isDeliveryDate", "bool", True),
                ("isDirect", "bool", False),
            ],
        })
        self.add_method_def({
            "method": "GetForward",
            "args": [
                ("vs", "object"),
                ("expiryOrDeliveryDate", "date"),
                ("isDeliveryDate", "bool", True),
                ("isDirect", "bool", False),
            ],
        })
        self.add_method_def({
            "method": "GetATMVol",
            "args": [
                ("vs", "object"),
                ("expiryDate", "date"),
            ],
        })


class DefMcpFXVolSurface(ItemDef):

    def __init__(self):
        super().__init__()

        bd_type = "bd@McpFXVolSurface"
        mcp_kv_wrapper.parse_func_dict[bd_type] = pf_dt_vol_matrix

        self.init_data = {
            "is_wrapper": True,
            "fmt": "DT|VP|HD",
            "data_fields": [
                ("Tenors", "str"),
                ("DeltaStrings", "str"),
                ("MaturityDates", "date"),
                ("Strikes", "float"),
                ("Volatilities", "float"),
                ("DeltaTypes", "const"),
                ("AtmVolTypes", "const"),
                ("PutWingRatios", "float"),
                ("CallWingRatios", "float"),
            ],
            "pyxll_def": {
            },
        }
        self.kv_const_dict = {
            ("SmileInterpMethod", "const"),

        }
        self.init_kv_list = [
            [
                ("ReferenceDate", "date"),
                ("SpotPx", "float"),
                ("Tenors", "plainlist"),  # Tenors
                ("DeltaStrings", "plainlist"),  # DeltaStrings
                ("Strikes", "str"),
                ("Volatilities", "str"),
                ("ForeignCurve", "object"),
                ("DomesticCurve", "object"),
                ("Calendar", "object"),
                ("DateAdjusterRule", "const"),
                ("DeltaType", "const"),
                ("SmileInterpMethod", "const"),
                ("FxForwardPointsCurve", "object"),
                ("PremiumAdjusted", "bool", True),
                ("IsATMFwd", "bool", False),
                ("SpotDate", "date"),
                ("CalculatedTarget", "const", CalculateTarget.CCY1),
                ("Pair", "str", "USD/CNY"),
            ],
            [
                ("ReferenceDate", "date"),
                ("MaturityDates", "plainlist"),  # MaturityDates
                ("SpotPx", "float"),
                ("DeltaStrings", "plainlist"),  # DeltaStrings
                ("Strikes", "str"),
                ("Volatilities", "str"),
                ("ForeignCurve", "object"),
                ("DomesticCurve", "object"),
                ("Calendar", "object"),
                ("DateAdjusterRule", "const"),
                ("DeltaType", "const"),
                ("SmileInterpMethod", "const"),
                ("FxForwardPointsCurve", "object"),
                ("PremiumAdjusted", "bool", True),
                ("IsATMFwd", "bool", False),
                ("SpotDate", "date"),
                ("CalculatedTarget", "const", CalculateTarget.CCY1),
                ("Pair", "str", "USD/CNY"),
            ],
            [
                ("ReferenceDate", "date"),
                ("SpotPx", "float"),
                ("Tenors", "plainlist"),
                ("DeltaStrings", "plainlist"),
                ("Volatilities", bd_type),
                ("ForeignCurve", "object"),
                ("DomesticCurve", "object"),
                ("Calendar", "object"),
                ("DateAdjusterRule", "const"),
                ("DeltaType", "const"),
                ("SmileInterpMethod", "const"),
                ("FxForwardPointsCurve", "object"),
                ("PremiumAdjusted", "bool", True),
                ("IsATMFwd", "bool", False),
                ("SpotDate", "date"),
                ("CalculatedTarget", "const", CalculateTarget.CCY1),
                ("Pair", "str", "USD/CNY"),
                ("FXVolInterpType", "const", FXVolInterpType.SPLINE_VOLATILITY),
            ],
            [
                ("ReferenceDate", "date"),
                ("SpotPx", "float"),
                ("Tenors", "plainlist"),
                ("DeltaStrings", "plainlist"),
                ("@bd", bd_type),
                ("ForeignCurve", "object"),
                ("DomesticCurve", "object"),
                ("Calendar", "object"),
                ("DateAdjusterRule", "const"),
                ("DeltaType", "const"),
                ("SmileInterpMethod", "const"),
                ("FxForwardPointsCurve", "object"),
                ("PremiumAdjusted", "bool", True),
                ("IsATMFwd", "bool", False),
                ("SpotDate", "date"),
                ("CalculatedTarget", "const", CalculateTarget.CCY1),
                ("Pair", "str", "USD/CNY"),
                ("FXVolInterpType", "const", FXVolInterpType.SPLINE_VOLATILITY),
            ],
            [
                ("ReferenceDate", "date"),
                ("SpotPx", "float"),
                ("Tenors", "plainlist"),
                ("DeltaStrings", "plainlist"),
                ("@bd", bd_type),
                ("DeltaTypes", "plainlist"),
                ("AtmVolTypes", "plainlist"),
                ("PutWingRatio", "float"),
                ("CallWingRatio", "float"),
                ("PremiumAdjusted", "bool", True),
                ("ForeignCurve", "object"),
                ("DomesticCurve", "object"),
                ("Calendar", "object"),
                ("DateAdjusterRule", "const"),
                ("SmileInterpMethod", "const"),
                ("FxForwardPointsCurve", "object"),
                ("SpotDate", "date"),
                ("CalculatedTarget", "const", CalculateTarget.CCY1),
                ("Pair", "str", "USD/CNY"),
            ],
            [
                ("ReferenceDate", "date"),
                ("SpotPx", "float"),
                ("Tenors", "plainlist"),
                ("DeltaStrings", "plainlist"),
                ("@bd", bd_type),
                ("DeltaTypes", "plainlist"),
                ("AtmVolTypes", "plainlist"),
                ("PutWingRatios", "plainlist"),
                ("CallWingRatios", "plainlist"),
                ("PremiumAdjusted", "bool", True),
                ("ForeignCurve", "object"),
                ("DomesticCurve", "object"),
                ("Calendar", "object"),
                ("DateAdjusterRule", "const"),
                ("SmileInterpMethod", "const"),
                ("FxForwardPointsCurve", "object"),
                ("SpotDate", "date"),
                ("CalculatedTarget", "const", CalculateTarget.CCY1),
                ("Pair", "str", "USD/CNY"),
            ],
            [
                ("ReferenceDate", "date"),
                ("SpotPx", "float"),
                ("Tenors", "plainlist"),
                ("DeltaStrings", "plainlist"),
                ("@bd", bd_type),
                ("DeltaTypes", "plainlist"),
                ("AtmVolTypes", "plainlist"),
                ("ForeignCurve", "object"),
                ("DomesticCurve", "object"),
                ("Calendar", "object"),
                ("DateAdjusterRule", "const"),
                ("SmileInterpMethod", "const"),
                ("FxForwardPointsCurve", "object"),
                ("PremiumAdjusted", "bool", True),
                ("SpotDate", "date"),
                ("CalculatedTarget", "const", CalculateTarget.CCY1),
                ("Pair", "str", "USD/CNY"),
                ("FXVolInterpType", "const", FXVolInterpType.SPLINE_VOLATILITY),
            ],
            # [
            #     ("ReferenceDate", "date"),
            #     ("SpotPx", "float"),
            #     ("Tenors", "plainlist"),
            #     ("DeltaStrings", "plainlist"),
            #     ("@bd", bd_type),
            #     ("@bd", bd_type),
            #     ("ForeignCurve", "object"),
            #     ("DomesticCurve", "object"),
            #     ("Calendar", "object"),
            #     ("DateAdjusterRule", "const"),
            #     ("DeltaType", "const"),
            #     ("SmileInterpMethod", "const"),
            #     ("FxForwardPointsCurve", "object"),
            #     ("PremiumAdjusted", "bool", True),
            #     ("IsATMFwd", "bool", False),
            #     ("SpotDate", "date"),
            #
            # ],
            # [
            #     ("ReferenceDate", "date"),
            #     ("MaturityDates", "plainlist"),
            #     ("SpotPx", "float"),
            #     ("DeltaStrings", "plainlist"),
            #     ("Strikes",bd_type),
            #     ("Volatilities", bd_type),
            #     ("ForeignCurve", "object"),
            #     ("DomesticCurve", "object"),
            #     ("Calendar", "object"),
            #     ("DateAdjusterRule", "const"),
            #     ("DeltaType", "const"),
            #     ("SmileInterpMethod", "const"),
            #     ("FxForwardPointsCurve", "object"),
            #     ("PremiumAdjusted", "bool", True),
            #     ("IsATMFwd", "bool", False),
            #     ("SpotDate", "date"),

            # ],
        ]
        # self.add_method_def({
        #     "method": "GetVolatility",
        #     "args": [
        #         ("vs", "object"),
        #         ("spotPx", "float", 0),
        #         ("ForeignRate", "float"),
        #         ("DomesticRate", "float"),
        #         ("interpVariable", "float"),
        #         ("expiryDate", "date"),
        #         ("deltaOrStrike", "const"),
        #     ],
        # })
        self.add_method_def({
            "method": "GetVolatility",
            "args": [
                ("vs", "object"),
                ("strike", "float"),
                ("expiryDate", "date"),
                ("forward", "float", 0.0),
                ("InputDeltaVolPair", "str", ''),
            ],
        })
        self.add_method_def({
            "method": "GetVolatilityByDeltaStr",
            "args": [
                ("vs", "object"),
                ("deltaString", "str"),
                ("expiryDate", "date"),
                ("forward", "float", 0.0),
                ("InputDeltaVolPair", "str", ''),
            ],
        })
        self.add_method_def({
            "method": "GetDomesticRate",
            "args": [
                ("vs", "object"),
                ("expiryOrDeliveryDate", "date"),
                ("isDeliveryDate", "bool", True),
                ("isDirect", "bool", False),
            ],
        })
        self.add_method_def({
            "method": "GetForeignRate",
            "args": [
                ("vs", "object"),
                ("expiryOrDeliveryDate", "date"),
                ("isDeliveryDate", "bool", True),
                ("isDirect", "bool", False),
            ],
        })
        self.add_method_def({
            "method": "GetForwardPoint",
            "args": [
                ("vs", "object"),
                ("expiryOrDeliveryDate", "date"),
                ("isDeliveryDate", "bool", True),
                ("isDirect", "bool", False),
            ],
        })
        self.add_method_def({
            "method": "GetForward",
            "args": [
                ("vs", "object"),
                ("expiryOrDeliveryDate", "date"),
                ("isDeliveryDate", "bool", True),
                ("isDirect", "bool", False),
            ],
        })
        self.add_method_def({
            "method": "GetATMVol",
            "args": [
                ("vs", "object"),
                ("expiryDate", "date"),
            ],
        })


class DefMcpMktVolSurface2(ItemDef):

    def __init__(self):
        super().__init__()

        bd_type = "bd@McpFXVolSurface2"
        mcp_kv_wrapper.parse_func_dict[bd_type] = pf_dt_vol_matrix

        self.init_data = {
            "is_wrapper": True,
            "fmt": "VP",
            "data_fields": [
                ("Tenors", "str"),
                ("DeltaStrings", "str"),
                ("BidVolatilities", "float"),
                ("AskVolatilities", "float"),
                ("DeltaTypes", "const"),
                ("AtmVolTypes", "const"),
                ("PutWingRatios", "float"),
                ("CallWingRatios", "float"),
            ],
            "pyxll_def": {
            },
        }
        self.kv_const_dict = {
            ("SmileInterpMethod", "const"),
        }
        self.init_kv_list = [
            [
                ("ReferenceDate", "date"),
                ("Tenors", "plainlist"),  # Tenors
                ("DeltaStrings", "plainlist"),  # DeltaStrings
                ("BidVolatilities", bd_type),
                ("AskVolatilities", bd_type),
                ("FxForwardPointsCurve2", "object"),
                ("ForeignCurve2", "object"),
                ("DomesticCurve2", "object"),
                ("CalculatedTarget", "const"),
                ("SmileInterpMethod", "const"),
                ("Calendar", "object", McpCalendar("", "", "")),
                ("DateAdjusterRule", "const"),
                ("DeltaType", "const"),
                ("PremiumAdjusted", "bool", True),
                ("IsATMFwd", "bool", False),
                ("SpotDate", "date", "1901-01-01"),
                ("FXVolInterpType", "const", FXVolInterpType.SPLINE_VOLATILITY),
            ],
            [
                ("ReferenceDate", "date"),
                ("Tenors", "plainlist"),  # Tenors
                ("DeltaStrings", "plainlist"),  # DeltaStrings
                ("BidVolatilities", bd_type),
                ("AskVolatilities", bd_type),
                ("FxForwardPointsCurve2", "object"),
                ("ForeignCurve2", "object"),
                ("DomesticCurve2", "object"),
                ("CalculatedTarget", "const"),
                ("SmileInterpMethod", "const"),
                ("DeltaTypes", "plainlist"),
                ("AtmVolTypes", "plainlist"),
                ("PutWingRatio", "float", 3.7),
                ("CallWingRatio", "float", 2.2),
                ("Calendar", "object", McpCalendar("", "", "")),
                ("DateAdjusterRule", "const"),
                ("PremiumAdjusted", "bool", True),
                ("SpotDate", "date", "1901-01-01"),
            ],
            [
                ("ReferenceDate", "date"),
                ("Tenors", "plainlist"),  # Tenors
                ("DeltaStrings", "plainlist"),  # DeltaStrings
                ("BidVolatilities", bd_type),
                ("AskVolatilities", bd_type),
                ("FxForwardPointsCurve2", "object"),
                ("ForeignCurve2", "object"),
                ("DomesticCurve2", "object"),
                ("CalculatedTarget", "const"),
                ("SmileInterpMethod", "const"),
                ("DeltaTypes", "plainlist"),
                ("AtmVolTypes", "plainlist"),
                ("PutWingRatios", "float"),
                ("CallWingRatios", "float"),
                ("Calendar", "object", McpCalendar("", "", "")),
                ("DateAdjusterRule", "const"),
                ("PremiumAdjusted", "bool", True),
                ("SpotDate", "date", "1901-01-01"),
            ],
            [
                ("ReferenceDate", "date"),
                ("Tenors", "plainlist"),  # Tenors
                ("DeltaStrings", "plainlist"),  # DeltaStrings
                ("BidVolatilities", bd_type),
                ("AskVolatilities", bd_type),
                ("FxForwardPointsCurve2", "object"),
                ("ForeignCurve2", "object"),
                ("DomesticCurve2", "object"),
                ("CalculatedTarget", "const"),
                ("SmileInterpMethod", "const"),
                ("DeltaTypes", "plainlist"),
                ("AtmVolTypes", "plainlist"),
                ("Calendar", "object", McpCalendar("", "", "")),
                ("DateAdjusterRule", "const"),
                ("PremiumAdjusted", "bool", True),
                ("SpotDate", "date", "1901-01-01"),
                ("FXVolInterpType", "const", FXVolInterpType.SPLINE_VOLATILITY),
            ],
            [
                ("ReferenceDate", "date"),
                ("MktVolSurface2_1", "object"),
                ("MktVolSurface2_2", "object"),
                ("Correlation", "float"),
                ("IsCur1Direct", "bool"),
                ("IsCur2Direct", "bool"),
                ("Calendar", "object", McpCalendar("", "", "")),
                ("DateAdjusterRule", "const"),
                ("CalculatedTarget", "const"),
                ("SmileInterpMethod", "const"),
                ("UsingExternalForwardPointCurve", "bool"),
                ("ExternalForwardPointCurve2", "object"),
                ("DeltaType", "const"),
                ("PremiumAdjusted", "bool", True),
                ("IsATMFwd", "bool", False),
                ("SpotDate", "date", "1901-01-01"),
                ("CrossFXSpot", "bool", True),
                ("BidFXSpotRate", "float", 0.0),
                ("AskFXSpotRate", "float", 0.0),
                ("SwapPointScaleFactor", "float", 10000.0),
                ("QuoteUnit", "float", 1.0),
            ],
        ]
        self.add_method_def({
            "method": "GetVolatility",
            "args": [
                ("vs", "object"),
                ("strike", "float"),
                ("expiryDate", "date"),
                ("bidMidAsk", "str", 'MID'),
                ("midForward", "float", 0.0),
                ("bidInputDeltaVolPair", "str", ''),
                ("askInputDeltaVolPair", "str", ''),
            ],
        })
        self.add_method_def({
            "method": "GetVolatilityByDeltaStr",
            "args": [
                ("vs", "object"),
                ("deltaString", "str"),
                ("expiryDate", "date"),
                ("bidMidAsk", "str", 'MID'),
                ("midForward", "float", 0.0),
                ("bidInputDeltaVolPair", "str", ''),
                ("askInputDeltaVolPair", "str", ''),
            ],
        })
        self.add_method_range(
            ["GetForward", "GetForwardPoint", "GetForeignRate", "GetDomesticRate"],
            {
                "args": [
                    ("vs", "object"),
                    ("expiryOrDeliveryDate", "date"),
                    ("isDeliveryDate", "bool", False),
                    ("bidMidAsk", "str", 'MID'),
                    ("isDirect", "bool", False),
                ],
            }
        )
        self.add_method_def({
            "method": "StrikeFromString",
            "args": [
                ("vs", "object"),
                ("s", "str"),
                ("bidMidAsk", "str", 'MID'),
                ("callPut", "const", CallPut.Call),
                ("expiryDate", "date"),
                ("spotPx", "float", 0.0),
                ("forwardPx", "float", 0.0),
            ],
        })
        self.add_method_def({
            "method": "GetStrike",
            "args": [
                ("vs", "object"),
                ("deltaString", "str"),
                ("tenor", "str"),
                ("bidMidAsk", "str", 'MID'),
            ],
        })
        self.add_method_def({
            "method": "GetATMVol",
            "args": [
                ("vs", "object"),
                ("expiryDate", "date"),
                ("bidMidAsk", "str", 'MID'),
            ],
        })
        self.add_method_def({
            "method": "GetSpot",
            "args": [
                ("vs", "object"),
                ("bidMidAsk", "str", 'MID'),
            ],
        })
        self.add_method_def({
            "method": "GetReferenceDate",
            "args": [
                ("vs", "object"),
            ],
        })
        self.add_method_def({
            "method": "GetSpotDate",
            "args": [
                ("vs", "object"),
            ],
        })
        self.add_method_def({
            "method": "GetParams",
            "args": [
                ("vs", "object"),
                ("expiryDate", "date"),
                ("bidMidAsk", "str", 'MID'),
            ],
            "fmt": "V",
            "pyxll_def": {
                "auto_resize": True
            },
        })
        self.add_method_def({
            "method": "GetDeltaStrings",
            "args": [
                ("vs", "object"),
            ],
            "fmt": "H",
            "pyxll_def": {
                "auto_resize": True
            },
        })
        self.add_method_def({
            "method": "GetTenors",
            "args": [
                ("vs", "object"),
            ],
            "fmt": "V",
            "pyxll_def": {
                "auto_resize": True
            },
        })


class DefMcpFXVolSurface2(ItemDef):

    def __init__(self):
        super().__init__()

        bd_type = "bd@McpFXVolSurface2"
        mcp_kv_wrapper.parse_func_dict[bd_type] = pf_dt_vol_matrix

        self.init_data = {
            "is_wrapper": True,
            "fmt": "VP",
            "data_fields": [
                ("Tenors", "str"),
                ("DeltaStrings", "str"),
                ("BidVolatilities", "float"),
                ("AskVolatilities", "float"),
                ("DeltaTypes", "const"),
                ("AtmVolTypes", "const"),
                ("PutWingRatios", "float"),
                ("CallWingRatios", "float"),
            ],
            "pyxll_def": {
            },
        }
        self.kv_const_dict = {
            ("SmileInterpMethod", "const"),
        }
        self.init_kv_list = [
            [
                ("ReferenceDate", "date"),
                ("Tenors", "plainlist"),  # Tenors
                ("DeltaStrings", "plainlist"),  # DeltaStrings
                ("BidVolatilities", bd_type),
                ("AskVolatilities", bd_type),
                ("FxForwardPointsCurve2", "object"),
                ("ForeignCurve2", "object"),
                ("DomesticCurve2", "object"),
                ("CalculatedTarget", "const"),
                ("SmileInterpMethod", "const"),
                ("Calendar", "object", McpCalendar("", "", "")),
                ("DateAdjusterRule", "const"),
                ("DeltaType", "const"),
                ("PremiumAdjusted", "bool", True),
                ("IsATMFwd", "bool", False),
                ("SpotDate", "date", "1901-01-01"),
                ("Pair", "str", "USD/CNY"),
                ("FXVolInterpType", "const", FXVolInterpType.SPLINE_VOLATILITY),
            ],
            [
                ("ReferenceDate", "date"),
                ("Tenors", "plainlist"),  # Tenors
                ("DeltaStrings", "plainlist"),  # DeltaStrings
                ("BidVolatilities", bd_type),
                ("AskVolatilities", bd_type),
                ("FxForwardPointsCurve2", "object"),
                ("ForeignCurve2", "object"),
                ("DomesticCurve2", "object"),
                ("CalculatedTarget", "const"),
                ("SmileInterpMethod", "const"),
                ("DeltaTypes", "plainlist"),
                ("AtmVolTypes", "plainlist"),
                ("PutWingRatio", "float", 3.7),
                ("CallWingRatio", "float", 2.2),
                ("Calendar", "object", McpCalendar("", "", "")),
                ("DateAdjusterRule", "const"),
                ("PremiumAdjusted", "bool", True),
                ("SpotDate", "date", "1901-01-01"),
                ("Pair", "str", "USD/CNY"),
            ],
            [
                ("ReferenceDate", "date"),
                ("Tenors", "plainlist"),  # Tenors
                ("DeltaStrings", "plainlist"),  # DeltaStrings
                ("BidVolatilities", bd_type),
                ("AskVolatilities", bd_type),
                ("FxForwardPointsCurve2", "object"),
                ("ForeignCurve2", "object"),
                ("DomesticCurve2", "object"),
                ("CalculatedTarget", "const"),
                ("SmileInterpMethod", "const"),
                ("DeltaTypes", "plainlist"),
                ("AtmVolTypes", "plainlist"),
                ("PutWingRatios", "float"),
                ("CallWingRatios", "float"),
                ("Calendar", "object", McpCalendar("", "", "")),
                ("DateAdjusterRule", "const"),
                ("PremiumAdjusted", "bool", True),
                ("SpotDate", "date", "1901-01-01"),
                ("Pair", "str", "USD/CNY"),
            ],
            [
                ("ReferenceDate", "date"),
                ("Tenors", "plainlist"),  # Tenors
                ("DeltaStrings", "plainlist"),  # DeltaStrings
                ("BidVolatilities", bd_type),
                ("AskVolatilities", bd_type),
                ("FxForwardPointsCurve2", "object"),
                ("ForeignCurve2", "object"),
                ("DomesticCurve2", "object"),
                ("CalculatedTarget", "const"),
                ("SmileInterpMethod", "const"),
                ("DeltaTypes", "plainlist"),
                ("AtmVolTypes", "plainlist"),
                ("Calendar", "object", McpCalendar("", "", "")),
                ("DateAdjusterRule", "const"),
                ("PremiumAdjusted", "bool", True),
                ("SpotDate", "date", "1901-01-01"),
                ("Pair", "str", "USD/CNY"),
                ("FXVolInterpType", "const", FXVolInterpType.SPLINE_VOLATILITY),
            ],
            [
                ("ReferenceDate", "date"),
                ("MktVolSurface2_1", "object"),
                ("MktVolSurface2_2", "object"),
                ("Correlation", "float"),
                ("IsCur1Direct", "bool"),
                ("IsCur2Direct", "bool"),
                ("Calendar", "object", McpCalendar("", "", "")),
                ("DateAdjusterRule", "const"),
                ("CalculatedTarget", "const"),
                ("SmileInterpMethod", "const"),
                ("UsingExternalForwardPointCurve", "bool"),
                ("ExternalForwardPointCurve2", "object"),
                ("DeltaType", "const"),
                ("PremiumAdjusted", "bool", True),
                ("IsATMFwd", "bool", False),
                ("SpotDate", "date", "1901-01-01"),
                ("CrossFXSpot", "bool", True),
                ("BidFXSpotRate", "float", 0.0),
                ("AskFXSpotRate", "float", 0.0),
                ("SwapPointScaleFactor", "float", 10000.0),
                ("QuoteUnit", "float", 1.0),
                ("Pair", "str", "USD/CNY"),
            ],
        ]
        self.add_method_def({
            "method": "GetVolatility",
            "args": [
                ("vs", "object"),
                ("strike", "float"),
                ("expiryDate", "date"),
                ("bidMidAsk", "str", 'MID'),
                ("midForward", "float", 0.0),
                ("bidInputDeltaVolPair", "str", ''),
                ("askInputDeltaVolPair", "str", ''),
            ],
        })
        self.add_method_def({
            "method": "GetVolatilityByDeltaStr",
            "args": [
                ("vs", "object"),
                ("deltaString", "str"),
                ("expiryDate", "date"),
                ("bidMidAsk", "str", 'MID'),
                ("midForward", "float", 0.0),
                ("bidInputDeltaVolPair", "str", ''),
                ("askInputDeltaVolPair", "str", ''),
            ],
        })
        self.add_method_range(
            ["GetForward", "GetForwardPoint", "GetForeignRate", "GetDomesticRate"],
            {
                "args": [
                    ("vs", "object"),
                    ("expiryOrDeliveryDate", "date"),
                    ("isDeliveryDate", "bool", False),
                    ("bidMidAsk", "str", 'MID'),
                    ("isDirect", "bool", False),
                ],
            }
        )
        self.add_method_def({
            "method": "StrikeFromString",
            "args": [
                ("vs", "object"),
                ("s", "str"),
                ("bidMidAsk", "str", 'MID'),
                ("callPut", "const", CallPut.Call),
                ("expiryDate", "date"),
                ("spotPx", "float", 0.0),
                ("forwardPx", "float", 0.0),
            ],
        })
        self.add_method_def({
            "method": "GetStrike",
            "args": [
                ("vs", "object"),
                ("deltaString", "str"),
                ("tenor", "str"),
                ("bidMidAsk", "str", 'MID'),
            ],
        })
        self.add_method_def({
            "method": "GetATMVol",
            "args": [
                ("vs", "object"),
                ("expiryDate", "date"),
                ("bidMidAsk", "str", 'MID'),
            ],
        })
        self.add_method_def({
            "method": "GetSpot",
            "args": [
                ("vs", "object"),
                ("bidMidAsk", "str", 'MID'),
            ],
        })
        self.add_method_def({
            "method": "GetReferenceDate",
            "args": [
                ("vs", "object"),
            ],
        })
        self.add_method_def({
            "method": "GetSpotDate",
            "args": [
                ("vs", "object"),
            ],
        })
        self.add_method_def({
            "method": "GetCalendar",
            "args": [
                ("vs", "object"),
            ],
        })
        self.add_method_def({
            "method": "GetParams",
            "args": [
                ("vs", "object"),
                ("expiryDate", "date"),
                ("bidMidAsk", "str", 'MID'),
            ],
            "fmt": "V",
            "pyxll_def": {
                "auto_resize": True
            },
        })
        self.add_method_def({
            "method": "GetDeltaStrings",
            "args": [
                ("vs", "object"),
            ],
            "fmt": "H",
            "pyxll_def": {
                "auto_resize": True
            },
        })
        self.add_method_def({
            "method": "GetTenors",
            "args": [
                ("vs", "object"),
            ],
            "fmt": "V",
            "pyxll_def": {
                "auto_resize": True
            },
        })


class DefMcpVanillaOption(ItemDef):

    def __init__(self):
        super().__init__()
        # self.custom_instance_func_raw = mcp_instance_list
        self.init_data = {
            "is_wrapper": True,
            "pkg": "mcp.forward.compound",
            "method_prefix": "VO",
            "data_fields": [
            ],
            "pyxll_def": {
            },
        }
        self.init_kv_list = [
            [
                ("CallPut", "const"),
                ("ReferenceDate", "date"),
                ("SpotPx", "float"),
                ("ExpiryDate", "date"),
                ("DeliveryDate", "date"),
                ("StrikePx", "float"),
                ("DomesticRate", "float"),
                ("ForeignRate", "float"),
                ("ForwardPx", "float", -1.0),
                ("Volatility", "float"),
                ("PremiumDate", "date"),
                ("Calendar", "object", McpCalendar("", "", ""), ""),
                ("DayCounter", "const", DayCounter.Act365Fixed, "Act365Fixed"),
                ("OptionExpiryNature", "const", OptionExpiryNature.EUROPEAN, "EUROPEAN"),
                ("PricingMethod", "const", PricingMethod.BLACKSCHOLES, "BLACKSCHOLES"),
                ("BuySell", "const"),
                ("FaceAmount", "float", 1),
                ("NumSimulation", "int", 10000),
                ("TimeToExpiryTime", "float", 0.0),
                ("CalculatedTarget", "const", CalculatedTarget.CCY1),
                ("Pair", "str", "USD/CNY"),

                ("PipsUnit", "float", 10000),
                ("VoType", "const", 1),
            ],
            [
                ("CallPut", "const"),
                ("ReferenceDate", "date"),
                ("SpotPx", "float"),
                ("ExpiryDate", "date"),
                ("DeliveryDate", "date"),
                ("StrikePx", "float"),
                ("ForwardPx", "float", -1.0),
                ("PremiumDate", "date"),
                ("Calendar", "object", McpCalendar("", "", ""), ""),
                ("DayCounter", "const", DayCounter.Act365Fixed, "Act365Fixed"),
                ("OptionExpiryNature", "const", OptionExpiryNature.EUROPEAN, "EUROPEAN"),
                ("PricingMethod", "const", PricingMethod.BLACKSCHOLES, "BLACKSCHOLES"),
                ("BuySell", "const"),
                ("FaceAmount", "float", 1),
                ("NumSimulation", "int", 10000),
                ("MktData", "object"),
                ("UndDayCounter", "const", DayCounter.Act360),
                ("Volatility", "str", 'None'),
                ("Side", "str", "Client"),
                ("TimeToExpiryTime", "float", 0.0),
                ("CalculatedTarget", "const", CalculatedTarget.CCY1),

                ("PipsUnit", "float", 10000),
                ("VoType", "const", 2),
            ],
            [
                ("CallPut", "const"),
                ("ReferenceDate", "date"),
                ("StrikePx", "float"),
                ("SpotPx", "float"),
                ("FaceAmount", "float", 1),
                ("ExpiryDate", "date"),
                ("DeliveryDate", "date"),
                ("PremiumDate", "date"),
                ("BuySell", "const"),
                ("OptionExpiryNature", "const", OptionExpiryNature.EUROPEAN, "EUROPEAN"),
                ("PricingMethod", "const", PricingMethod.BLACKSCHOLES, "BLACKSCHOLES"),
                ("DayCounter", "const", DayCounter.Act365Fixed, "Act365Fixed"),
                ("Calendar", "object", McpCalendar("", "", ""), ""),
                ("VolSurface", "object"),
                ("NumSimulation", "int", 1000),
                ("DomesticCurve", "object"),
                ("ForeignCurve", "object"),
                ("VoType", "const", 3),
            ],
            [
                ("CallPut", "const"),
                ("ReferenceDate", "date"),
                ("StrikePx", "float"),
                ("SpotPx", "float"),
                ("FaceAmount", "float"),
                ("ExpiryDate", "date"),
                ("DeliveryDate", "date"),
                ("PremiumDate", "date"),
                ("BuySell", "const"),
                ("OptionExpiryNature", "const", OptionExpiryNature.EUROPEAN, "EUROPEAN"),
                ("PricingMethod", "const", PricingMethod.BLACKSCHOLES, "BLACKSCHOLES"),
                ("DayCounter", "const", DayCounter.Act365Fixed, "Act365Fixed"),
                ("Calendar", "object", McpCalendar("", "", "")),
                ("VolSurface", "object"),
                ("NumSimulation", "int", 1000),
                ("VoType", "const", 4),
            ],
            [  # 股指期权
                ("CallPut", "const"),
                ("ReferenceDate", "date"),
                ("SpotPx", "float"),
                ("ExpiryDate", "date"),
                ("DeliveryDate", "date"),
                ("StrikePx", "float"),
                ("RiskFreeRate", "float"),
                ("Dividend", "float"),
                ("Volatility", "float"),
                ("PremiumDate", "date"),
                ("Calendar", "object", McpCalendar("", "", "")),
                ("DayCounter", "const", DayCounter.Act365Fixed, "Act365Fixed"),
                ("OptionExpiryNature", "const", OptionExpiryNature.EUROPEAN, "EUROPEAN"),
                ("PricingMethod", "const", PricingMethod.BLACKSCHOLES, "BLACKSCHOLES"),
                ("BuySell", "const"),
                ("FaceAmount", "float"),
                ("NumSimulation", "int", 500000),
                ("TimeToExpiryTime", "float", 0.0),
                ("VoType", "const", 5),
            ],
            [  # 商品期权（期货期权）
                ("CallPut", "const"),
                ("ReferenceDate", "date"),
                ("ExpiryDate", "date"),
                ("DeliveryDate", "date"),
                ("StrikePx", "float"),
                ("RiskFreeRate", "float"),
                ("CostOfCarry", "float", 0.0),
                ("Volatility", "float"),
                ("PremiumDate", "date"),
                ("ForwardPx", "float"),
                ("Calendar", "object", McpCalendar("", "", "")),
                ("DayCounter", "const", DayCounter.Act365Fixed, "Act365Fixed"),
                ("OptionExpiryNature", "const", OptionExpiryNature.EUROPEAN, "EUROPEAN"),
                ("PricingMethod", "const", PricingMethod.BLACKSCHOLES, "BLACKSCHOLES"),
                ("BuySell", "const"),
                ("FaceAmount", "float"),
                ("NumSimulation", "int", 500000),
                ("TimeToExpiryTime", "float", 0.0),
                ("VoType", "const", 6),
            ],
            [  # 用VolSurface2来对商品期权（期货期权）、和股指期权定价
                ("CallPut", "const"),
                ("ReferenceDate", "date"),
                ("ExpiryDate", "date"),
                ("DeliveryDate", "date"),
                ("StrikePx", "float"),
                ("volSurface2", "object"),
                ("PremiumDate", "date"),
                ("OptionExpiryNature", "const", OptionExpiryNature.EUROPEAN, "EUROPEAN"),
                ("PricingMethod", "const", PricingMethod.BLACKSCHOLES, "BLACKSCHOLES"),
                ("Side", "const", Side.Client, "Client"),
                ("BuySell", "const", BuySell.Buy, "Buy"),
                ("FaceAmount", "float"),
                ("NumSimulation", "int", 500000),
                ("TimeToExpiryTime", "float", 0.0),
                ("VoType", "const", 7),
            ],
            # 用LocalVol对美式期权定价（Aderson、LSMC）
            # [
            #     ("CallPut", "const"),
            #     ("ReferenceDate", "date"),
            #     ("SpotPx", "float"),
            #     ("ExpiryDate", "date"),
            #     ("SettlementDate", "date"),
            #     ("StrikePx", "float"),
            #     ("DomesticRate", "float"),
            #     ("ForeignRate", "float"),
            #     ("ForwardPx", "float", -1.0),
            #     ("LocalVol", "object"),
            #     ("PremiumDate", "date"),
            #     ("Calendar", "object", McpCalendar("", "", ""), ""),
            #     ("DayCounter", "const", DayCounter.Act365Fixed, "Act365Fixed"),
            #     ("OptionExpiryNature", "const", OptionExpiryNature.EUROPEAN, "EUROPEAN"),
            #     ("PricingMethod", "const", PricingMethod.BLACKSCHOLES, "BLACKSCHOLES"),
            #     ("BuySell", "const"),
            #     ("FaceAmount", "float", 1),
            #     ("NumSimulation", "int", 10000),
            #     ("CalculatedTarget", "const", CalculatedTarget.CCY1),
            #     ("Pair", "str", "USD/CNY"),
            #     ("ImpVol", "float", 0.0),
            #     ("PipsUnit", "float", 10000),
            #     ("VoType", "const", 8),
            # ],
            # 用FXVolSurface/strike对外汇期权定价
            [
                ("CallPut", "const"),
                ("ReferenceDate", "date"),
                ("ExpiryDate", "date"),
                ("DeliveryDate", "date"),
                ("StrikePx", "float"),
                ("FXVolSurface", "object"),
                ("PremiumDate", "date"),
                ("BuySell", "const"),
                ("SpotPx", "float", float('nan')),
                ("ForwardPx", "float", float('nan')),
                ("Volatility", "float", float('nan')),
                ("DomesticRate", "float", float('nan')),
                ("ForeignRate", "float", float('nan')),
                ("TimeToExpiryTime", "float", 0.0),
                ("Calendar", "object", McpCalendar("", "", ""), ""),
                ("DayCounter", "const", DayCounter.Act365Fixed, "Act365Fixed"),
                ("OptionExpiryNature", "const", OptionExpiryNature.EUROPEAN, "EUROPEAN"),
                ("PricingMethod", "const", PricingMethod.BLACKSCHOLES, "BLACKSCHOLES"),
                ("FaceAmount", "float", 1),
                ("NumSimulation", "int", 10000),
                # ("PipsUnit", "float", 10000),
                ("VoType", "const", 8),
            ],
            # 用FXVolSurface/deltastr对外汇期权定价
            [
                ("CallPut", "const"),
                ("ReferenceDate", "date"),
                ("ExpiryDate", "date"),
                ("DeliveryDate", "date"),
                ("DeltaStr", "str"),
                ("FXVolSurface", "object"),
                ("PremiumDate", "date"),
                ("BuySell", "const"),
                ("SpotPx", "float", float('nan')),
                ("ForwardPx", "float", float('nan')),
                ("Volatility", "float", float('nan')),
                ("DomesticRate", "float", float('nan')),
                ("ForeignRate", "float", float('nan')),
                ("TimeToExpiryTime", "float", 0.0),
                ("Calendar", "object", McpCalendar("", "", ""), ""),
                ("DayCounter", "const", DayCounter.Act365Fixed, "Act365Fixed"),
                ("OptionExpiryNature", "const", OptionExpiryNature.EUROPEAN, "EUROPEAN"),
                ("PricingMethod", "const", PricingMethod.BLACKSCHOLES, "BLACKSCHOLES"),
                ("FaceAmount", "float", 1),
                ("NumSimulation", "int", 10000),
                # ("PipsUnit", "float", 10000),
                ("VoType", "const", 9),
            ],
            # 用FXVolSurface2对外汇期权定价(Strike版本)
            [
                ("CallPut", "const"),
                ("ReferenceDate", "date"),
                ("ExpiryDate", "date"),
                ("DeliveryDate", "date"),
                ("StrikePx", "float"),
                ("FXVolSurface2", "object"),
                ("Side", "const", -1),
                ("BuySell", "const", 1),
                ("PremiumDate", "date", ""),
                ("TimeToExpiryTime", "float", 0.0),
                ("SpotPx", "float", float('nan')),
                ("ForwardPx", "float", float('nan')),
                ("Volatility", "float", float('nan')),
                ("DomesticRate", "float", float('nan')),
                ("ForeignRate", "float", float('nan')),
                ("OptionExpiryNature", "const", OptionExpiryNature.EUROPEAN, "EUROPEAN"),
                ("PricingMethod", "const", PricingMethod.BLACKSCHOLES, "BLACKSCHOLES"),
                ("FaceAmount", "float", 1.0),
                ("NumSimulation", "int", 500000),
                ("VoType", "const", 10),
            ],
            # 用FXVolSurface2对外汇期权定价(Delta版本)
            [
                ("CallPut", "const"),
                ("ReferenceDate", "date"),
                ("ExpiryDate", "date"),
                ("DeliveryDate", "date"),
                ("DeltaStr", "str"),  # 注意这里不同
                ("FXVolSurface2", "object"),
                ("Side", "const", -1),
                ("BuySell", "const", 1),
                ("PremiumDate", "date", ""),
                ("TimeToExpiryTime", "float", 0.0),
                ("SpotPx", "float", float('nan')),
                ("ForwardPx", "float", float('nan')),
                ("Volatility", "float", float('nan')),
                ("DomesticRate", "float", float('nan')),
                ("ForeignRate", "float", float('nan')),
                ("OptionExpiryNature", "const", OptionExpiryNature.EUROPEAN, "EUROPEAN"),
                ("PricingMethod", "const", PricingMethod.BLACKSCHOLES, "BLACKSCHOLES"),
                ("FaceAmount", "float", 1.0),
                ("NumSimulation", "int", 500000),
                ("VoType", "const", 11),
            ],
            # Forward, DeltaStr, FXOption
            [
                ("CallPut", "const"),
                ("ReferenceDate", "date"),
                ("SpotPx", "float"),
                ("ExpiryDate", "date"),
                ("DeliveryDate", "date"),
                ("DeltaStr", "str"),
                ("DomesticRate", "float"),
                ("ForeignRate", "float"),
                ("ForwardPx", "float"),
                ("Volatility", "float"),
                ("PremiumDate", "date"),
                ("Calendar", "object", McpCalendar("", "", ""), ""),
                ("DayCounter", "const", DayCounter.Act365Fixed, "Act365Fixed"),
                ("OptionExpiryNature", "const", OptionExpiryNature.EUROPEAN, "EUROPEAN"),
                ("PricingMethod", "const", PricingMethod.BLACKSCHOLES, "BLACKSCHOLES"),
                ("BuySell", "const"),
                ("FaceAmount", "float", 1),
                ("NumSimulation", "int", 10000),
                ("TimeToExpiryTime", "float", 0.0),
                ("CalculatedTarget", "const", CalculatedTarget.CCY1),
                ("Pair", "const", "USD/CNY"),
                ("PipsUnit", "float", 10000),
                ("VoType", "const", 12),
            ],
        ]
        self.add_method_range(
            ["VegaDigital", "VegaIDDigital", "DvegaDvol", "DvegaDvol2", "DvegaDspot", "Dd1Dvol", ],
            {
                "args": [
                    ("obj", "object"),
                ],

            }
        )
        self.add_method_range(
            ["GetSpot", "GetForward", "GetVol", "GetStrike", "GetUndRate", "GetAccRate", "GetCallPutType",
             "GetBuySell", ],
            {
                "args": [
                    ("obj", "object"),
                ],

            }
        )
        self.add_method_range(
            ["VolImpliedFromPrice", "StrikeImpliedFromPrice"],
            {
                "args": [
                    ("obj", "object"),
                    ("price", "float"),
                    ("isAmount", "bool"),
                ],
            }
        )

        self.add_method_def({
            "method": "DeltaImpliedFromStrike",
            "args": [
                ("obj", "object"),
                ("strike", "float"),
            ],
        })

        self.add_method_def({
            "method": "StrikeImpliedFromDelta",
            "args": [
                ("obj", "object"),
                ("delta", "float"),
                ("deltaRHS", "bool"),
                ("isAmount", "bool"),
            ],
        })

        self.add_method_def({
            "method": "StrikeImpliedFromForwardDelta",
            "args": [
                ("obj", "object"),
                ("delta", "float"),
                ("deltaRHS", "bool"),
                ("isAmount", "bool"),
            ],
        })


class DefMcpVanillaStrategy(ItemDef):

    def __init__(self):
        super().__init__()
        self.generate_xls_method = True
        self.custom_instance_func_raw = mcp_instance_list
        self.init_data = {
            "is_wrapper": True,
            "method_prefix": "VS",
            "data_fields": [
            ],
            "pyxll_def": {
            },
        }

        self.init_kv_list = [
            # tenor
            [
                ("DeltaStrategyStr", "str"),
                ("ReferenceDate", "date"),
                ("FxVolSurface", "object"),
                ("Tenor", "str"),
                ("SpotPx", "float", float('nan')),
                ("FwdPoints", "float", float('nan')),
                ("Volatility", "float", float('nan')),
                ("Volatility2", "float", float('nan')),
            ],
            [
                ("StrategyType", "const"),
                ("DeltaStr", "str"),
                ("ReferenceDate", "date"),
                ("FxVolSurface", "object"),
                ("Tenor", "str"),
                ("SpotPx", "float", float('nan')),
                ("FwdPoints", "float", float('nan')),
                ("Volatility", "float", float('nan')),
                ("Volatility2", "float", float('nan')),
            ],
            [
                ("Tenor", "str"),
                ("FxVolSurface2", "object"),
                ("DeltaStrategyStr", "str"),
                ("ReferenceDate", "date"),
                ("SpotPx", "float", float('nan')),
                ("FwdPoints", "float", float('nan')),
                ("Volatility", "float", float('nan')),
                ("Volatility2", "float", float('nan')),
            ],
            [
                ("Tenor", "str"),
                ("FxVolSurface2", "object"),
                ("StrategyType", "const"),
                ("DeltaStr", "str"),
                ("ReferenceDate", "date"),
                ("SpotPx", "float", float('nan')),
                ("FwdPoints", "float", float('nan')),
                ("Volatility", "float", float('nan')),
                ("Volatility2", "float", float('nan')),
            ],
            # expiryDate
            [
                ("DeltaStrategyStr", "str"),
                ("ReferenceDate", "date"),
                ("ExpiryDate", "date"),
                ("FxVolSurface", "object"),
                ("SpotPx", "float", float('nan')),
                ("FwdPoints", "float", float('nan')),
                ("Volatility", "float", float('nan')),
                ("Volatility2", "float", float('nan')),
            ],
            [
                ("StrategyType", "const"),
                ("DeltaStr", "str"),
                ("ReferenceDate", "date"),
                ("ExpiryDate", "date"),
                ("FxVolSurface", "object"),
                ("SpotPx", "float", float('nan')),
                ("FwdPoints", "float", float('nan')),
                ("Volatility", "float", float('nan')),
                ("Volatility2", "float", float('nan')),
            ],
            [
                ("FxVolSurface2", "object"),
                ("DeltaStrategyStr", "str"),
                ("ReferenceDate", "date"),
                ("ExpiryDate", "date"),
                ("SpotPx", "float", float('nan')),
                ("FwdPoints", "float", float('nan')),
                ("Volatility", "float", float('nan')),
                ("Volatility2", "float", float('nan')),
            ],
            [
                ("FxVolSurface2", "object"),
                ("StrategyType", "const"),
                ("DeltaStr", "str"),
                ("ReferenceDate", "date"),
                ("ExpiryDate", "date"),
                ("SpotPx", "float", float('nan')),
                ("FwdPoints", "float", float('nan')),
                ("Volatility", "float", float('nan')),
                ("Volatility2", "float", float('nan')),
            ],
        ]
        self.add_method_range(
            ["GetSpot", "GetForward", "GetFwdPoints", "Volatility", "Price", "GetLegNames", "GetStrategyType",
             "GetDeltaString", "GetReferenceDate", "GetExpiryDate", "GetDeliveryDate", ],
            {
                "args": [
                    ("obj", "object"),
                ],

            }
        )
        self.add_method_range(
            ["Delta", "ForwardDelta", "Gamma", "Vega", "Theta", "Rho", "Phi", "Vanna", "Volga"],
            {
                "args": [
                    ("obj", "object"),
                    ("isCcy2", "bool"),
                    ("isAmount", "bool"),
                ],

            }
        )

        self.add_method_def({
            "method": "GetLeg",
            "args": [
                ("obj", "object"),
                ("legName", "str"),
            ],
        })


class DefMcpFXForward(ItemDef):

    def __init__(self):
        super().__init__()
        # self.custom_instance_func_raw = mcp_instance_list
        self.init_data = {
            "is_wrapper": True,
            "pkg": "mcp.forward.compound",
            "method_prefix": "VO",
            "data_fields": [
            ],
            "pyxll_def": {
            },
        }
        self.init_kv_list = [
            [
                ("ReferenceDate", "date"),
                ("SpotDate", "date"),
                ("ExpiryDate", "date"),
                ("DeliveryDate", "date"),
                ("StrikePx", "float"),
                ("SpotPx", "float"),
                ("DomesticRate", "float"),
                ("ForeignRate", "float"),
                ("Forward", "float"),
                # ("Calendar", "object", McpCalendar("", "", ""), ""),
                ("DayCounter", "const", DayCounter.Act365Fixed, "Act365Fixed"),
                # ("PricingMethod", "const", FxFwdPricingMethod.MARKETFWD, "MARKETFWD"),
                ("BuySell", "const"),
                ("FaceAmount", "float", 1),
                ("CalculatedTarget", "const", CalculateTarget.CCY1),
                ("Pair", "str", "USD/CNY"),
            ],
            [
                ("StrikePx", "float"),
                ("SpotPx", "float"),
                ("DomesticRate", "float"),
                ("ForeignRate", "float"),
                ("Forward", "float"),
                ("ReferenceDate", "date"),
                ("SettlementDate", "date"),
                ("DeliveryDate", "date"),
                ("Calendar", "object", McpCalendar("", "", ""), ""),
                ("DayCounter", "const", DayCounter.Act365Fixed, "Act365Fixed"),
                ("PricingMethod", "const", FxFwdPricingMethod.MARKETFWD, "MARKETFWD"),
                ("BuySell", "const"),
                ("FaceAmount", "float", 1),
            ],
        ]


class DefMcpFXForward2(ItemDef):

    def __init__(self):
        super().__init__()
        # self.custom_instance_func_raw = mcp_instance_list
        self.init_data = {
            "is_wrapper": True,
            #            "pkg": "mcp.forward.compound",
            "method_prefix": "Fwd",
            "data_fields": [
            ],
            "pyxll_def": {
            },
        }
        self.init_kv_list = [
            [
                # ("ReferenceDate", "date"),
                # ("SpotPx", "float"),
                ("StrikePx", "float"),
                ("FXForwardPointsCurve2", "object"),
                ("DiscountCurve", "object"),
                ("SettlementDate", "date"),
                ("BuySell", "const"),
                ("FaceAmount", "float"),
                ("Side", "const"),
            ]
        ]


class DefMcpAsianOption(ItemDef):

    def __init__(self):
        super().__init__()
        self.custom_instance_func_raw = mcp_instance_list
        self.init_data = {
            "is_wrapper": True,
            "pkg": "mcp.forward.compound",
            "method_prefix": "AO",
            "data_fields": [
            ],
            "pyxll_def": {
            },
        }
        self.init_kv_list = [
            [
                ("CallPut", "const"),
                ("ReferenceDate", "date"),
                ("SpotPx", "float"),
                ("AveRate", "float"),
                ("FirstAverageDate", "date"),
                ("ExpiryDate", "date"),
                ("SettlementDate", "date"),
                ("StrikePx", "float"),
                ("ForwardPx", "float"),
                ("DomesticRate", "float"),
                ("ForeignRate", "float"),
                ("Volatility", "float"),
                ("PremiumDate", "date"),
                ("FixingFrequency", "const", Frequency.Monthly, "Monthly"),
                ("LastAverageDate", "date"),
                ("CalculatedTarget", "const", CalculatedTarget.CCY1),
                ("AverageMethod", "const", AverageMethod.Arithmetic, "Arithmetic"),
                ("StrikeType", "const", StrikeType.Fixed, "Fixed"),
                ("PricingMethod", "const", PricingMethod.BINOMIAL, "BINOMIAL"),
                ("BuySell", "const"),
                ("FaceAmount", "float", 1),
                ("NumSimulation", "int", 10000),
                ("FixingDateAdjuster", "const", DateAdjusterRule.ModifiedFollowing, "ModifiedFollowing"),
                ("KeepEndOfMonth", "bool", True),
                ("FixingLongStub", "bool", False),
                ("FixingEndStub", "bool", True),
                ("Calendar", "object", McpCalendar("", "", ""), ""),
                ("DayCounter", "const", DayCounter.Act365Fixed, "Act365Fixed"),
                ("TimeStep", "int", 10),

                ("PipsUnit", "float", 10000),
            ],
            [
                ("CallPut", "const"),
                ("ReferenceDate", "date"),
                ("SpotPx", "float"),
                ("AveRate", "float"),
                ("FirstAverageDate", "date"),
                ("ExpiryDate", "date"),
                ("SettlementDate", "date"),
                ("StrikePx", "float"),
                ("DomesticRate", "float"),
                ("ForeignRate", "float"),
                ("Volatility", "float"),
                ("PremiumDate", "date"),
                ("NumFixings", "int"),
                ("Calendar", "object", McpCalendar("", "", ""), ""),
                ("DayCounter", "const", DayCounter.Act365Fixed, "Act365Fixed"),
                ("AverageMethod", "const", AverageMethod.Arithmetic, "Arithmetic"),
                ("StrikeType", "const", StrikeType.Fixed, "Fixed"),
                ("PricingMethod", "const", PricingMethod.BINOMIAL, "BINOMIAL"),
                ("BuySell", "const"),
                ("FaceAmount", "float", 1),
                ("TimeStep", "int", 10),
                ("NumSimulation", "int", 10000),

                ("PipsUnit", "float", 10000),
            ],
        ]

        self.add_method_range(
            ["VolImpliedFromPrice", "StrikeImpliedFromPrice"],
            {
                "args": [
                    ("obj", "object"),
                    ("price", "float"),
                ],
            }
        )

        def AveRate(obj):
            return obj.GetAveRate()

        self.add_method_def({
            "method": "AveRate",
            "func": AveRate,
            "args": [
                ("obj", "object"),
            ],
        })

        def NumFixDone(obj):
            return obj.GetNumFixDone()

        self.add_method_def({
            "method": "NumFixDone",
            "func": NumFixDone,
            "args": [
                ("obj", "object"),
            ],
        })

        def NumFixings(obj):
            return obj.GetNumFixings()

        self.add_method_def({
            "method": "NumFixings",
            "func": NumFixings,
            "args": [
                ("obj", "object"),
            ],
        })

        def FixingSchedule(obj):
            s = obj.GetFixingSchedule()
            print("FixingSchedule:", s)
            return json.loads(s)

        self.add_method_def({
            "method": "FixingSchedule",
            "fmt": "V",
            "func": FixingSchedule,
            "args": [
                ("obj", "object"),
            ],
        })


class DefMcpFixedRateBond(ItemDef):

    def __init__(self):
        super().__init__()
        self.custom_instance_func_raw = mcp_instance_list
        self.init_data = {
            "is_wrapper": True,
            "method_prefix": "Frb",
            "data_fields": [
            ],
            "pyxll_def": {
            },
        }
        rounder = McpRounder(0, 8)
        self.init_kv_list = [
            [
                ("SettlementDate", "date"),
                ("MaturityDate", "date"),
                ("Frequency", "const"),
                ("Coupon", "float"),
                ("CouponType", "const"),
                ("ValueDate", "date"),
                ("IssuePrice", "float"),
                ("DayCounter", "const", DayCounter.ActActXTR)
            ],
            [
                ("Calendar", "object", McpCalendar("", "", "")),
                ("ValuationDate", "date"),
                ("MaturityDate", "date"),
                ("Frequency", "const", Frequency.Annual, "Annual"),
                ("Coupon", "float"),
                ("DayCounter", "const", DayCounter.Act365Fixed, "Act365Fixed"),
                ("ExInterestDays", "int", 0, 0),
                ("FaceValue", "float", 100, 100),
                ("PrevCpnDate", "date", ""),
                ("LastCpnDate", "date", ""),
                ("Issuer", "str", "", ""),
                ("DirtyPriceRounder", "object", rounder),
                ("CleanPriceRounder", "object", rounder),
                ("AccruedInterestRounder", "object", rounder),
                ("CashRounder", "object", rounder),
                ("RedempRounder", "object", rounder),
                ("IssueDate", "date", "", ""),
                ("FirstCouponDate", "date", "", ""),
                ("NextCallDate", "date", "", ""),
                ("EndToEnd", "bool", True),
                ("LongStub", "bool", False),
                ("EndStub", "bool", False),
                ("ApplyDayCount", "bool", False),
                ("DateAdjuster", "const", DateAdjusterRule.Actual, "Actual"),
            ],
        ]

        self.add_method_def({
            "method": "KeyRateDuration",
            "args": [
                ("bond", "object"),
                ("curve", "object"),
                ("tenors", "array"),
                ("adjustWithEffectiveDuration", "bool", True),
            ],
            "fmt": "V",
            "pyxll_def": {
                "auto_resize": True
            },
        })
        self.add_method_range(
            ["AmCost", "AmEIR", "AmERInstIncome", "AmAccuredIncome", "AmCashflow"],
            {
                "args": [
                    ("bond", "object"),
                    ("startDate", "date"),
                    ("endDate", "date"),
                    ("initCost", "float"),
                ],
            }
        )
        self.add_method_range(
            ["BondAcctAmCost", "BondAcctEIR"],
            {
                "args": [
                    ("bond", "object"),
                    ("prevDate", "date"),
                    ("currDate", "date"),
                    ("initCost", "float"),
                ],
            }
        )
        self.add_method_range(
            ["BondAcctPandlImpact", "BondAcctOciImpact", "BondAcctAccountingPnl"],
            {
                "args": [
                    ("bond", "object"),
                    ("classification", "str"),
                    ("prevDate", "date"),
                    ("currDate", "date"),
                    ("initCost", "float"),
                    ("prevClean", "float"),
                    ("currClean", "float"),
                    ("quantity", "float"),
                    ("dailyAccrual", "float"),
                    ("realizedPnl", "float"),
                ],
            }
        )


class DefMcpAmortizingBond(ItemDef):

    def __init__(self):
        super().__init__()
        self.init_data = {
            "is_wrapper": True,
            "method_prefix": "AmortBond",
            "data_fields": [
            ],
            "pyxll_def": {
            },
        }
        self.init_kv_list = [
            [
                ("SettlementDate", "date"),
                ("MaturityDate", "date"),
                ("IssueDate", "date"),
                ("Frequency", "const", Frequency.Annual, "Annual"),
                ("Coupon", "float"),
                ("DayCounter", "const", DayCounter.Act365Fixed, "Act365Fixed"),
                ("FaceValue", "float", 100, 100),
                ("PrincipalSchedule", "str"),
                ("CouponSchedule", "str", "", ""),
                ("PrincipalBasis", "int", 0, 0),
            ],
        ]
        self.add_method_range(
            ["AmCost", "AmEIR", "AmERInstIncome", "AmAccuredIncome", "AmCashflow"],
            {
                "args": [
                    ("bond", "object"),
                    ("startDate", "date"),
                    ("endDate", "date"),
                    ("initCost", "float"),
                ],
            }
        )
        self.add_method_range(
            ["RemainingPrincipal", "RemainingPrincipalFactor", "CouponRateOn"],
            {
                "args": [
                    ("bond", "object"),
                    ("asOf", "date"),
                ],
            }
        )


class DefMcpCommodityFuture(ItemDef):

    def __init__(self):
        super().__init__()
        self.custom_instance_func_raw = mcp_instance_list
        self.init_data = {
            "is_wrapper": True,
            "method_prefix": "CommodityFuture",
            "data_fields": [
            ],
            "pyxll_def": {
            },
        }
        # 定价方法常量: 1=MARKET_PRICE, 2=THEORETICAL, 3=FORWARD_CURVE
        PRICING_METHOD_MARKET_PRICE = 1
        PRICING_METHOD_THEORETICAL = 2
        PRICING_METHOD_FORWARD_CURVE = 3

        self.init_kv_list = [
            [
                ("Underlying", "str"),
                ("ContractSpec", "str"),
                ("ContractQuantity", "float"),
                ("ContractMultiplier", "float"),
                ("Direction", "int"),
                ("ReferenceDate", "date"),
                ("DeliveryDate", "date"),
                ("SettlementDate", "date"),
                ("SpotPrice", "float"),
                ("TradePrice", "float"),
                ("MarketPrice", "float"),
                ("PricingMethod", "int"),
                ("Calendar", "object", McpCalendar("", "", "")),
                ("DayCounter", "const", DayCounter.Act365Fixed, "Act365Fixed"),
            ],
            [
                ("Underlying", "str"),
                ("ContractSpec", "str", "", ""),
                ("ContractQuantity", "float"),
                ("ContractMultiplier", "float", 1.0, 1.0),
                ("Direction", "const", BuySell.Buy, "Buy"),
                ("ReferenceDate", "date"),
                ("DeliveryDate", "date"),
                ("SettlementDate", "date", "", ""),
                ("SpotPrice", "float"),
                ("TradePrice", "float", 0.0, 0.0),
                ("MarketPrice", "float", 0.0, 0.0),
                ("PricingMethod", "int", PRICING_METHOD_MARKET_PRICE, PRICING_METHOD_MARKET_PRICE),
                ("Calendar", "object", McpCalendar("", "", "")),
                ("DayCounter", "const", DayCounter.Act365Fixed, "Act365Fixed"),
            ],
        ]


class DefMcpBondFuture(ItemDef):

    def __init__(self):
        super().__init__()
        self.custom_instance_func_raw = mcp_instance_list
        self.init_data = {
            "is_wrapper": True,
            "method_prefix": "BondFuture",
            "data_fields": [
            ],
            "pyxll_def": {
            },
        }
        self.init_kv_list = [
            [
                ("Calendar", "object"),
                ("SettlementDate", "date"),
                ("Tenor", "str"),
                ("ContractMonth", "date"),
                ("StandardCoupon", "float"),
                ("Frequency", "int"),
                ("DayCounter", "int"),
                ("ContractSize", "float"),
            ],
            [
                ("Calendar", "object", McpCalendar("", "", "")),
                ("SettlementDate", "date"),
                ("Tenor", "str", "3Y", "3Y"),
                ("ContractMonth", "date"),
                ("StandardCoupon", "float", 0.03, 0.03),
                ("Frequency", "int", 1, 1),
                ("DayCounter", "const", DayCounter.Act365Fixed, "Act365Fixed"),
                ("ContractSize", "float", 10000000.0, 10000000.0),
            ],
        ]


class DefMcpEquityFuture(ItemDef):

    def __init__(self):
        super().__init__()
        self.custom_instance_func_raw = mcp_instance_list
        self.init_data = {
            "is_wrapper": True,
            "method_prefix": "EquityFuture",
            "data_fields": [
            ],
            "pyxll_def": {
            },
        }
        # 定价方法常量: 1=MARKET_PRICE, 2=THEORETICAL, 3=FORWARD_CURVE
        PRICING_METHOD_MARKET_PRICE = 1
        PRICING_METHOD_THEORETICAL = 2
        PRICING_METHOD_FORWARD_CURVE = 3

        self.init_kv_list = [
            [
                ("Underlying", "str"),
                ("ContractSpec", "str"),
                ("ContractQuantity", "float"),
                ("ContractMultiplier", "float"),
                ("Direction", "int"),
                ("ReferenceDate", "date"),
                ("DeliveryDate", "date"),
                ("SettlementDate", "date"),
                ("SpotPrice", "float"),
                ("TradePrice", "float"),
                ("MarketPrice", "float"),
                ("PricingMethod", "int"),
                ("Calendar", "object"),
                ("DayCounter", "int"),
            ],
            [
                ("Underlying", "str"),
                ("ContractSpec", "str", "", ""),
                ("ContractQuantity", "float"),
                ("ContractMultiplier", "float", 1.0, 1.0),
                ("Direction", "const", BuySell.Buy, "Buy"),
                ("ReferenceDate", "date"),
                ("DeliveryDate", "date"),
                ("SettlementDate", "date", "", ""),
                ("SpotPrice", "float"),
                ("TradePrice", "float", 0.0, 0.0),
                ("MarketPrice", "float", 0.0, 0.0),
                ("PricingMethod", "int", PRICING_METHOD_MARKET_PRICE, PRICING_METHOD_MARKET_PRICE),
                ("Calendar", "object", McpCalendar("", "", "")),
                ("DayCounter", "const", DayCounter.Act365Fixed, "Act365Fixed"),
            ],
        ]


class DefMcpEquitySpot(ItemDef):

    def __init__(self):
        super().__init__()
        self.custom_instance_func_raw = mcp_instance_list
        self.init_data = {
            "is_wrapper": True,
            "method_prefix": "EquitySpot",
            "data_fields": [
            ],
            "pyxll_def": {
            },
        }
        self.init_kv_list = [
            [
                ("Underlying", "str"),
                ("Notional", "float"),
                ("Direction", "int"),
                ("ReferenceDate", "date"),
                ("SpotPrice", "float"),
                ("TradePrice", "float"),
                ("Calendar", "object"),
                ("DayCounter", "int"),
            ],
            [
                ("Underlying", "str"),
                ("Notional", "float"),
                ("Direction", "const", BuySell.Buy, "Buy"),
                ("ReferenceDate", "date"),
                ("SpotPrice", "float"),
                ("TradePrice", "float", 0.0, 0.0),
                ("Calendar", "object", McpCalendar("", "", "")),
                ("DayCounter", "const", DayCounter.Act365Fixed, "Act365Fixed"),
            ],
        ]


class DefMcpFund(ItemDef):

    def __init__(self):
        super().__init__()
        self.custom_instance_func_raw = mcp_instance_list
        self.init_data = {
            "is_wrapper": True,
            "method_prefix": "Fund",
            "data_fields": [
            ],
            "pyxll_def": {
            },
        }
        # 基金类型: 1=ETF, 2=MUTUAL_FUND
        FUND_TYPE_ETF = 1
        FUND_TYPE_MUTUAL_FUND = 2
        # 定价方法: 1=NAV, 2=MARKET_PRICE
        PRICING_METHOD_NAV = 1
        PRICING_METHOD_MARKET_PRICE = 2

        self.init_kv_list = [
            [
                ("FundCode", "str"),
                ("FundType", "int"),
                ("Notional", "float"),
                ("Direction", "int"),
                ("ReferenceDate", "date"),
                ("NAV", "float"),
                ("TradePrice", "float"),
                ("MarketPrice", "float"),
                ("PricingMethod", "int"),
                ("Calendar", "object"),
                ("DayCounter", "int"),
            ],
            [
                ("FundCode", "str"),
                ("FundType", "int", FUND_TYPE_MUTUAL_FUND, FUND_TYPE_MUTUAL_FUND),
                ("Notional", "float"),
                ("Direction", "const", BuySell.Buy, "Buy"),
                ("ReferenceDate", "date"),
                ("NAV", "float"),
                ("TradePrice", "float", 0.0, 0.0),
                ("MarketPrice", "float", 0.0, 0.0),
                ("PricingMethod", "int", PRICING_METHOD_NAV, PRICING_METHOD_NAV),
                ("Calendar", "object", McpCalendar("", "", "")),
                ("DayCounter", "const", DayCounter.Act365Fixed, "Act365Fixed"),
            ],
        ]


class DefMcpFXNDF(ItemDef):

    def __init__(self):
        super().__init__()
        self.custom_instance_func_raw = mcp_instance_list
        self.init_data = {
            "is_wrapper": True,
            "method_prefix": "FXNDF",
            "data_fields": [
            ],
            "pyxll_def": {
            },
        }
        self.init_kv_list = [
            [
                ("ReferenceDate", "date"),
                ("FixingDate", "date"),
                ("SettlementDate", "date"),
                ("Strike", "float"),
                ("Notional", "float"),
                ("ReceiveBaseCurrency", "bool"),
                ("Pair", "str"),
                ("SettlementCcy", "str"),
            ],
            [
                ("ReferenceDate", "date"),
                ("FixingDate", "date"),
                ("SettlementDate", "date"),
                ("Strike", "float"),
                ("Notional", "float"),
                ("ReceiveBaseCurrency", "bool", True, True),
                ("Pair", "str", "USD/CNY", "USD/CNY"),
                ("SettlementCcy", "str", "", ""),
            ],
        ]


class DefMcpRepurchaseProduct(ItemDef):

    def __init__(self):
        super().__init__()
        self.custom_instance_func_raw = mcp_instance_list
        self.init_data = {
            "is_wrapper": True,
            "method_prefix": "RepurchaseProduct",
            "data_fields": [
            ],
            "pyxll_def": {
            },
        }
        self.init_kv_list = [
            [
                ("ValueDate", "date"),
                ("StartDate", "date"),
                ("EndDate", "date"),
                ("RepoRate", "float"),
                ("Coupon", "float"),
                ("DayCounter", "int"),
                ("CurrentCapital", "float"),
                ("HaircutType", "int"),
                ("Haircut", "float"),
                ("UnderlyingSecurity", "object"),
                ("UnderlyingDirty", "float"),
                ("RepoType", "int"),
                ("PaymentCalendar", "object"),
                ("RepoMaturity", "int"),
            ],
            [
                ("ValueDate", "date"),
                ("StartDate", "date"),
                ("EndDate", "date"),
                ("RepoRate", "float"),
                ("Coupon", "float"),
                ("DayCounter", "const", DayCounter.Act365Fixed, "Act365Fixed"),
                ("CurrentCapital", "float"),
                ("HaircutType", "int", 0, 0),
                ("Haircut", "float", 0.0, 0.0),
                ("UnderlyingSecurity", "object", None, None),
                ("UnderlyingDirty", "float"),
                ("RepoType", "int", 0, 0),
                ("PaymentCalendar", "object", McpCalendar("", "", "")),
                ("RepoMaturity", "int", 1, 1),
            ],
        ]


class DefMcpTotalReturnSwap(ItemDef):

    def __init__(self):
        super().__init__()
        self.init_data = {
            "is_wrapper": True,
            "method_prefix": "Trs",
            "data_fields": [],
            "pyxll_def": {},
        }
        # FundingLegType / FixedFundingRate 不作为 C++ 构造函数参数传入，
        # 而是在对象创建后通过 setFundingLegType() 方法设置（见 custom_instance_func）。
        self.init_kv_list = [
            [
                ("StartDate", "date"),
                ("MaturityDate", "date"),
                ("Notional", "float"),
                ("Currency", "str"),
                ("InitialPrice", "float"),
                ("FundingIndex", "str"),
                ("FundingSpread", "float"),
                ("Direction", "int"),
                ("ResetFrequency", "str"),
                ("PaymentCalendar", "object"),
                ("DayCounter", "int"),
                ("FundingLegType", "str", "FLOATING", "FLOATING"),
                ("FixedFundingRate", "float", 0.0, 0.0),
            ],
            [
                ("StartDate", "date"),
                ("MaturityDate", "date"),
                ("Notional", "float"),
                ("Currency", "str", "CNY", "CNY"),
                ("InitialPrice", "float"),
                ("FundingIndex", "str", "FR007", "FR007"),
                ("FundingSpread", "float", 50.0, 50.0),
                ("Direction", "int", 1, 1),
                ("ResetFrequency", "str", "1M", "1M"),
                ("PaymentCalendar", "object", McpCalendar("", "", ""), ""),
                ("DayCounter", "const", DayCounter.Act365Fixed, "Act365Fixed"),
                ("FundingLegType", "str", "FLOATING", "FLOATING"),
                ("FixedFundingRate", "float", 0.0, 0.0),
            ],
        ]

        def create_trs(args_dict):
            from mcp.wrapper import create_object_instance
            from mcp.utils.excel_utils import pf_date
            # 提取 11 个 C++ 构造函数参数（不含 FundingLegType / FixedFundingRate）
            start_date     = pf_date(args_dict.get('StartDate'))
            maturity_date  = pf_date(args_dict.get('MaturityDate'))
            notional       = float(args_dict.get('Notional', 0.0))
            currency       = str(args_dict.get('Currency', 'CNY'))
            initial_price  = float(args_dict.get('InitialPrice', 0.0))
            _fi = args_dict.get('FundingIndex')
            funding_index  = str(_fi) if _fi is not None else ''
            funding_spread = float(args_dict.get('FundingSpread', 0.0))
            direction      = int(float(args_dict.get('Direction', 1)))
            reset_freq     = str(args_dict.get('ResetFrequency', '3M'))
            cal            = args_dict.get('PaymentCalendar', McpCalendar('', '', ''))
            # args_dict 存储原始 Excel 值（float），须显式转 int；
            # SWIG 对重载函数匹配类型严格，float 无法匹配 int。
            _dc_raw = args_dict.get('DayCounter', DayCounter.Act365Fixed)
            try:
                day_counter = int(float(_dc_raw))
            except (TypeError, ValueError):
                day_counter = int(DayCounter.Act365Fixed)

            # mcp_trs.cpp 中 paymentCalendar 做 static_cast<mcp::Calendar*>，
            # 期望值是 MCalendar::getHandler() 返回的 mcp::Calendar*（即内部 m_qagCal）。
            # 直接传 Python wrapper 会使 SWIG 传入 MCalendar C++ 对象地址，类型不兼容导致 crash。
            if hasattr(cal, 'getHandler'):
                cal_ptr = cal.getHandler()
            else:
                cal_ptr = cal

            ctor_args = [
                start_date, maturity_date, notional, currency,
                initial_price, funding_index, funding_spread,
                direction, reset_freq, cal_ptr, day_counter,
            ]
            # 使用 mcp.wrapper.McpTotalReturnSwap（继承自 MTotalReturnSwap），
            # 确保 PyXLL 缓存 key 为 McpTotalReturnSwap@N 而非 MTotalReturnSwap@N。
            # McpTotalReturnSwap.__init__ 内部会再次调用 to_mcp_args，但 cal_ptr 已是
            # Python int（getHandler() 结果），不再是 wrapper，所以不会被二次处理。
            trs = create_object_instance("mcp.wrapper", "McpTotalReturnSwap", ctor_args)

            # 设置固定资金腿（构造后调用 setFundingLegType）
            leg_type_str = str(args_dict.get('FundingLegType', 'FLOATING')).strip().upper()
            try:
                fixed_rate = float(args_dict.get('FixedFundingRate', 0.0))
            except (TypeError, ValueError):
                fixed_rate = 0.0
            if leg_type_str == 'FIXED' and hasattr(trs, 'setFundingLegType'):
                trs.setFundingLegType(1, fixed_rate)

            return trs

        self.custom_instance_func = create_trs


class DefMcpBondTRSAdapter(ItemDef):
    """BondTotalReturnSwap - 固收TRS（债券总收益互换），适用于 SAC-0396TRS0018 等离岸债券TRS交易"""

    def __init__(self):
        super().__init__()
        self.init_data = {
            "is_wrapper": False,
            "method_prefix": "BondTrs",
            "data_fields": [],
            "pyxll_def": {},
        }
        self.init_kv_list = [
            [
                ("BondIsin", "str"),
                ("FaceValue", "float"),
                ("Currency", "str"),
                ("StartDate", "date"),
                ("MaturityDate", "date"),
                ("InitialCleanPrice", "float"),
                ("InitialAccrued", "float"),
                ("CouponRate", "float"),
                ("CouponFrequency", "str"),
                ("CouponStartDate", "date"),
                ("DayCounter", "int"),
                ("FixedFundingRate", "float"),
                ("Direction", "int"),
                ("PaymentCalendar", "object"),
                ("DiscountCurve", "object"),
                ("CurrentPrice", "float"),
                ("ValuationDate", "date"),
            ],
            [
                ("BondIsin", "str"),
                ("FaceValue", "float"),
                ("Currency", "str", "CNY", "CNY"),
                ("StartDate", "date"),
                ("MaturityDate", "date"),
                ("InitialCleanPrice", "float"),
                ("InitialAccrued", "float", 0.0, 0.0),
                ("CouponRate", "float"),
                ("CouponFrequency", "str", "SEMIANNUAL", "SEMIANNUAL"),
                ("CouponStartDate", "date"),
                ("DayCounter", "const", DayCounter.Act365Fixed, "Act365Fixed"),
                ("FixedFundingRate", "float"),
                ("Direction", "int", 1, 1),
                ("PaymentCalendar", "object", McpCalendar("", "", ""), ""),
                ("DiscountCurve", "object", None, ""),
                ("CurrentPrice", "float", None, ""),
                ("ValuationDate", "date", None, ""),
            ],
        ]

        def create_bond_trs_adapter(args_dict):
            """构造 McpBondTRSAdapter（SWIG 包装的 mcp::metrics::BondTRSAdapter）。

            约定：所有比例字段在 Excel 中均以小数输入（与 C++ 接口一致）：
              - InitialCleanPrice: 0.977879  表示 97.7879%
              - InitialAccrued:    0.031452  表示  3.1452%
              - CouponRate:        0.07      表示 7%
              - FixedFundingRate:  0.032     表示 3.2%

            可选字段（直接嵌入参数块，避免 BondTrsSetXxx 的计算顺序问题）：
              - DiscountCurve:  折现曲线对象（McpBondCurve / McpSwapCurve）
              - CurrentPrice:   估值日净价（小数，如 0.985 = 98.5%）
              - ValuationDate:  估值日（YYYY-MM-DD 字符串或 Excel 日期序号）
            """
            from mcp.wrapper import McpBondTRSAdapter
            from mcp.utils.excel_utils import pf_date
            data = {
                'BondIsin':          str(args_dict.get('BondIsin', '')),
                'FaceValue':         float(args_dict.get('FaceValue', 0.0)),
                'Currency':          str(args_dict.get('Currency', 'CNY')),
                'StartDate':         pf_date(args_dict.get('StartDate')),
                'MaturityDate':      pf_date(args_dict.get('MaturityDate')),
                'InitialCleanPrice': float(args_dict.get('InitialCleanPrice', 0.0)),
                'InitialAccrued':    float(args_dict.get('InitialAccrued', 0.0)),
                'CouponRate':        float(args_dict.get('CouponRate', 0.0)),
                'CouponFrequency':   args_dict.get('CouponFrequency', 'SEMIANNUAL'),
                'CouponStartDate':   pf_date(args_dict.get('CouponStartDate')),
                'DayCounter':        int(float(args_dict.get('DayCounter', 1))),
                'FixedFundingRate':  float(args_dict.get('FixedFundingRate', 0.0)),
                'Direction':         int(float(args_dict.get('Direction', 1))),
                'PaymentCalendar':   args_dict.get('PaymentCalendar'),
                'InstrumentId':      str(args_dict.get('InstrumentId', '')),
                'TradeId':           str(args_dict.get('TradeId', '')),
                'PortfolioKey':      str(args_dict.get('PortfolioKey', '')),
            }
            adapter = McpBondTRSAdapter(data)

            # 注入可选市场数据字段：直接嵌入参数块，避免 BondTrsSetXxx 的计算顺序问题。
            # adapter 单元格依赖这些输入单元格 → 任一变化都会触发 adapter 重算 → 所有下游
            # 函数（NPV/Cashflow/MarketParRate）自动联动。

            discount_curve = args_dict.get('DiscountCurve')
            if discount_curve is not None:
                try:
                    if hasattr(adapter, 'setDiscountCurve'):
                        adapter.setDiscountCurve(discount_curve)
                    setattr(adapter, '_mcp_bond_trs_discount_curve', discount_curve)
                except Exception:
                    pass

            current_price_raw = args_dict.get('CurrentPrice')
            if current_price_raw is not None and current_price_raw != '':
                try:
                    current_price = float(current_price_raw)
                    if hasattr(adapter, 'setCurrentCleanPrice'):
                        adapter.setCurrentCleanPrice(current_price)
                    setattr(adapter, '_mcp_bond_trs_current_clean', current_price)
                except Exception:
                    pass

            val_date_raw = args_dict.get('ValuationDate')
            if val_date_raw is not None and val_date_raw != '':
                try:
                    val_date = pf_date(val_date_raw)
                    if hasattr(adapter, 'setValuationDate'):
                        adapter.setValuationDate(val_date)
                    setattr(adapter, '_mcp_bond_trs_valuation_date', val_date)
                except Exception:
                    pass

            return adapter

        self.custom_instance_func = create_bond_trs_adapter


class DefMcpBondTRS(ItemDef):
    """BondTotalReturnSwap 合约对象（McpBondTRS），VP 参数块风格，供 BondTrsMarketParRate 等函数使用。"""

    def __init__(self):
        super().__init__()
        self.init_data = {
            "is_wrapper": True,
            "method_prefix": "BondTrs",
            "data_fields": [],
            "pyxll_def": {},
        }
        self.init_kv_list = [
            [
                ("BondIsin",         "str"),
                ("FaceValue",        "float"),
                ("Currency",         "str"),
                ("StartDate",        "date"),
                ("MaturityDate",     "date"),
                ("InitialClean",     "float"),
                ("CouponRate",       "float"),
                ("CouponStartDate",  "date"),
                ("FixedFundingRate", "float"),
                ("CouponFrequency",  "str"),
                ("Direction",        "int"),
                ("InitialAccrued",   "float"),
            ],
            [
                ("BondIsin",         "str"),
                ("FaceValue",        "float"),
                ("Currency",         "str", "CNY", "CNY"),
                ("StartDate",        "date"),
                ("MaturityDate",     "date"),
                ("InitialClean",     "float"),
                ("CouponRate",       "float"),
                ("CouponStartDate",  "date"),
                ("FixedFundingRate", "float"),
                ("CouponFrequency",  "str", "SEMIANNUAL", "SEMIANNUAL"),
                ("Direction",        "int", 1, 1),
                ("InitialAccrued",   "float", 0.0, 0.0),
            ],
        ]

        def create_bond_trs(args_dict):
            from mcp.wrapper import create_object_instance, McpBondTRS as _McpBondTRS
            from mcp.utils.excel_utils import pf_date
            # PaymentCalendar：若 VP 块中传入了 McpCalendar 对象则使用，否则用空日历
            cal_raw = args_dict.get('PaymentCalendar', McpCalendar('', '', ''))
            if cal_raw is None:
                cal_raw = McpCalendar('', '', '')
            cal_ptr = cal_raw.getHandler() if hasattr(cal_raw, 'getHandler') else cal_raw
            return _McpBondTRS(
                bondIsin=str(args_dict.get('BondIsin', '')),
                faceValue=float(args_dict.get('FaceValue', 0.0)),
                currency=str(args_dict.get('Currency', 'CNY')),
                startDate=pf_date(args_dict.get('StartDate')),
                maturityDate=pf_date(args_dict.get('MaturityDate')),
                initialCleanPrice=float(args_dict.get('InitialClean', 0.0)),
                initialAccrued=float(args_dict.get('InitialAccrued', 0.0)),
                couponRate=float(args_dict.get('CouponRate', 0.0)),
                couponFrequency=str(args_dict.get('CouponFrequency', 'SEMIANNUAL')),
                couponStartDate=pf_date(args_dict.get('CouponStartDate')),
                dayCounter=int(DayCounter.Act365Fixed),
                fixedFundingRate=float(args_dict.get('FixedFundingRate', 0.0)),
                direction=int(float(args_dict.get('Direction', 1))),
                paymentCalendar=cal_ptr,
            )

        self.custom_instance_func = create_bond_trs


class DefMcpCreditCurve(ItemDef):
    """MCreditCurve - 信用曲线，支持 CFETS CDS Index 构造。使用 McpCreditCurve 包装，Excel 显示 McpCreditCurve@0"""

    def __init__(self):
        super().__init__()
        self.init_data = {
            "is_wrapper": True,
            "method_prefix": "CreditCurve",
            "data_fields": [],
            "pyxll_def": {},
        }
        self.init_kv_list = [
            [
                ("ReferenceDate", "date"),
                ("CftsSpreads", "str"),
                ("YieldCurve", "object"),
                ("RecoveryRate", "float"),
                ("Variable", "const"),
                ("Method", "const"),
                ("Calendar", "object"),
                ("DayCounter", "const"),
                ("ValuationType", "const"),
            ],
            [
                ("ReferenceDate", "date"),
                ("CftsSpreads", "str", '{"3M": 62.15, "6M": 76.45, "1Y": 85.2, "2Y": 95.0, "3Y": 102.0, "5Y": 115.0}', ""),
                ("YieldCurve", "object"),
                ("RecoveryRate", "float", 0.40, 0.40),
                ("Variable", "const", InterpolatedVariable.HAZARDRATES, "HAZARDRATES"),
                ("Method", "const", InterpolationMethod.LINEARINTERPOLATION, "LINEARINTERPOLATION"),
                ("Calendar", "object", McpCalendar("", "", ""), ""),
                ("DayCounter", "const", DayCounter.Act365Fixed, "Act365Fixed"),
                ("ValuationType", "const", 1, "JPMISDA"),
            ],
        ]


def _cds_date_to_str(val, default):
    """将日期转为 C++ 可解析的 YYYY-MM-DD 字符串，避免 Excel 序列数等导致 crash。"""
    if val is None or val == "":
        return default
    try:
        from mcp.utils.excel_utils import pf_date
        s = pf_date(val)
        return s if s else default
    except Exception:
        return default


class DefMcpCreditDefaultSwap(ItemDef):

    def __init__(self):
        super().__init__()
        self.custom_instance_func_raw = mcp_instance_list
        self.init_data = {
            "is_wrapper": True,
            "method_prefix": "CreditDefaultSwap",
            "data_fields": [],
            "pyxll_def": {},
        }
        self.init_kv_list = [
            [
                ("Notional", "float"),
                ("TradeDate", "date"),
                ("MaturityDate", "date"),
                ("ValuationDate", "date"),
                ("Spread", "float"),
                ("RecoveryRate", "float"),
                ("PaymentCalendar", "object"),
                ("DayCounter", "int"),
                ("ValuationType", "int"),
                ("DefaultParty", "str"),
            ],
            [
                ("Notional", "float", 10000000.0, 10000000.0),
                ("TradeDate", "date"),
                ("MaturityDate", "date"),
                ("ValuationDate", "date"),
                ("Spread", "float", 0.01, 0.01),
                ("RecoveryRate", "float", 0.40, 0.40),
                ("PaymentCalendar", "object", McpCalendar("", "", ""), ""),
                ("DayCounter", "int", 1, 1),
                ("ValuationType", "int", 1, 1),
                ("DefaultParty", "str", "", ""),
            ],
        ]

        def _create_credit_default_swap(args_dict):
            """确保日期为 YYYY-MM-DD 字符串传入 C++，避免 SWIG/Excel 传错类型导致 CreditDefaultSwap 内部 legs 损坏。"""
            d = lower_key_dict(args_dict)
            notional = float(d.get("notional", d.get("Notional", 10000000.0)))
            trade_date = _cds_date_to_str(d.get("tradedate", d.get("TradeDate")), "2024-06-01")
            maturity_date = _cds_date_to_str(d.get("maturitydate", d.get("MaturityDate")), "2027-12-20")
            valuation_date = _cds_date_to_str(d.get("valuationdate", d.get("ValuationDate")), "2025-01-17")
            # C++ CDS 要求 ValuationDate <= MaturityDate，否则构造时抛错
            try:
                from datetime import datetime
                vd = datetime.strptime(valuation_date, "%Y-%m-%d")
                md = datetime.strptime(maturity_date, "%Y-%m-%d")
                if vd > md:
                    raise ValueError(
                        f"McpCreditDefaultSwap: ValuationDate ({valuation_date}) 不能晚于 MaturityDate ({maturity_date})"
                    )
            except ValueError as ve:
                if "ValuationDate" in str(ve):
                    raise
                pass  # 日期解析失败时继续，由 C++ 处理
            spread = float(d.get("spread", d.get("Spread", 0.01)))
            recovery_rate = float(d.get("recoveryrate", d.get("RecoveryRate", 0.40)))
            payment_calendar = d.get("paymentcalendar", d.get("PaymentCalendar"))
            # 空时传 None，C++ 会创建默认日历；有值时传 M 对象，to_mcp_args 会取 getHandler()
            if payment_calendar is None or payment_calendar == "":
                payment_calendar = None
            day_counter = int(d.get("daycounter", d.get("DayCounter", 1)))
            valuation_type = int(d.get("valuationtype", d.get("ValuationType", 1)))
            default_party = d.get("defaultparty", d.get("DefaultParty", ""))
            if default_party is None:
                default_party = ""
            vals = [notional, trade_date, maturity_date, valuation_date, spread, recovery_rate,
                    payment_calendar, day_counter, valuation_type, str(default_party)]
            return McpCreditDefaultSwap(*vals)

        self.custom_instance_func = _create_credit_default_swap


class DefMcpCdsAdapter(ItemDef):
    """
    MCdsAdapter 参数约定：
    - CreditCurve: 必须传入 MCreditCurve 对象（如 =McpCreditCurve(...) 的结果），不能传 getHandler()
    - YieldCurve: 必须传入 MYieldCurve/MBondCurve/MSwapCurve 对象
    - setCreditCurve(MCreditCurve) 期望 M 包装类，内部会调用 getHandler() 获取 mcp::CreditCurve*
    """

    def __init__(self):
        super().__init__()
        self.init_data = {
            "is_wrapper": False,
            "method_prefix": "CdsAdapter",
            "data_fields": [],
            "pyxll_def": {},
        }
        self.init_kv_list = [
            [
                ("CreditDefaultSwap", "object"),
                ("InstrumentId", "str"),
                ("TradeId", "str"),
                ("PortfolioKey", "str"),
                ("CreditCurve", "object"),
                ("YieldCurve", "object"),
                ("PrevYieldCurve", "object"),
                ("PrevCreditCurve", "object"),
                ("Notional", "float"),
                ("Currency", "str"),
            ],
        ]

        def create_cds_adapter(args_dict):
            import mcp.mcp as mcp_module
            from mcp.wrapper import create_object_instance, McpYieldCurve, McpSwapCurve, McpBondCurve, McpCreditCurve, McpCreditDefaultSwap, McpCdsAdapter

            cds = args_dict.get('CreditDefaultSwap', args_dict.get('creditDefaultSwap'))
            instrument_id = args_dict.get('InstrumentId', args_dict.get('instrumentId', 'CDS_001'))
            trade_id = args_dict.get('TradeId', args_dict.get('tradeId', 'TRADE_CDS_001'))
            portfolio_key = args_dict.get('PortfolioKey', args_dict.get('portfolioKey', ''))
            credit_curve = args_dict.get('CreditCurve', args_dict.get('creditCurve'))
            yield_curve = args_dict.get('YieldCurve', args_dict.get('yieldCurve'))
            prev_yield_curve = args_dict.get('PrevYieldCurve', args_dict.get('prevYieldCurve'))
            prev_credit_curve = args_dict.get('PrevCreditCurve', args_dict.get('prevCreditCurve'))
            notional = args_dict.get('Notional', args_dict.get('notional'))
            currency = args_dict.get('Currency', args_dict.get('currency', 'CNY'))

            # 必须传入 MCreditDefaultSwap/McpCreditDefaultSwap，不能误传 MCreditCurve 或其他类型
            if cds is None:
                raise TypeError("MCdsAdapter: CreditDefaultSwap is required")
            cds_types = (mcp_module.MCreditDefaultSwap, McpCreditDefaultSwap)
            if not isinstance(cds, cds_types):
                raise TypeError(
                    f"MCdsAdapter: CreditDefaultSwap must be McpCreditDefaultSwap, got {type(cds).__name__}. "
                    "Check Excel cell references - ensure the first parameter points to McpCreditDefaultSwap(...) result."
                )

            adapter = create_object_instance("mcp.mcp", "MCdsAdapter", [
                cds,
                instrument_id,
                trade_id,
                portfolio_key or ""
            ])

            # 【关键】MCdsAdapter.setCreditCurve 必须传入 MCreditCurve 对象本身，不能传 getHandler()
            # - 正确：adapter.setCreditCurve(credit_curve)  或  adapter.setCreditCurve(credit_curve.getInstance())
            # - 错误：adapter.setCreditCurve(credit_curve.getHandler())  # 会 crash
            # C++ 签名：void setCreditCurve(MCreditCurve* curve)，内部会调用 curve->getHandler() 获取 mcp::CreditCurve*
            # 必须使用 getInstance() 传入 M 包装类，不能传 getHandler()
            credit_curve_types = (mcp_module.MCreditCurve, McpCreditCurve)
            yield_curve_types = (mcp_module.MYieldCurve, mcp_module.MBondCurve, mcp_module.MSwapCurve,
                                 McpYieldCurve, McpSwapCurve, McpBondCurve)
            if credit_curve is not None:
                if not isinstance(credit_curve, credit_curve_types):
                    raise TypeError(
                        f"MCdsAdapter.setCreditCurve: CreditCurve must be MCreditCurve/McpCreditCurve, got {type(credit_curve).__name__}. "
                        "Use McpCreditCurve object (NOT getHandler()). Check Excel - CreditCurve cell should reference McpCreditCurve."
                    )
                _cc_arg = credit_curve.getInstance() if hasattr(credit_curve, 'getInstance') else credit_curve
                adapter.setCreditCurve(_cc_arg)
            if yield_curve is not None:
                if not isinstance(yield_curve, yield_curve_types):
                    raise TypeError(
                        f"MCdsAdapter.setYieldCurve: YieldCurve must be MYieldCurve/McpYieldCurve/MBondCurve/MSwapCurve, got {type(yield_curve).__name__}."
                    )
                _yc_arg = yield_curve.getInstance() if hasattr(yield_curve, 'getInstance') else yield_curve
                adapter.setYieldCurve(_yc_arg)
            # 归因阶梯：prev 曲线。MCdsAdapter 需有 setPrevYieldCurve/setPrevCreditCurve（mcpPortLib 已实现，需重建 mcp）
            def _do_set_prev_yield_cds(curve):
                _arg = curve.getInstance() if hasattr(curve, 'getInstance') else curve
                if hasattr(adapter, 'setPrevYieldCurve'):
                    adapter.setPrevYieldCurve(_arg)
                elif hasattr(adapter, 'getHandler'):
                    try:
                        h = adapter.getHandler()
                        if h is not None and hasattr(h, 'setPrevYieldCurve'):
                            h.setPrevYieldCurve(_arg)
                    except Exception:
                        pass
            def _do_set_prev_credit_cds(curve):
                _arg = curve.getInstance() if hasattr(curve, 'getInstance') else curve
                if hasattr(adapter, 'setPrevCreditCurve'):
                    adapter.setPrevCreditCurve(_arg)
                elif hasattr(adapter, 'getHandler'):
                    try:
                        h = adapter.getHandler()
                        if h is not None and hasattr(h, 'setPrevCreditCurve'):
                            h.setPrevCreditCurve(_arg)
                    except Exception:
                        pass
            if prev_yield_curve is not None and isinstance(prev_yield_curve, yield_curve_types):
                _do_set_prev_yield_cds(prev_yield_curve)
            if prev_credit_curve is not None and isinstance(prev_credit_curve, credit_curve_types):
                _do_set_prev_credit_cds(prev_credit_curve)
            if notional is not None:
                adapter.setNotional(float(notional))
            if currency is not None:
                adapter.setCurrency(str(currency))

            adapter._cds_ref = cds
            adapter._credit_curve_ref = credit_curve
            adapter._yield_curve_ref = yield_curve

            return McpCdsAdapter(adapter)

        self.custom_instance_func = create_cds_adapter


class DefMcpClnAdapter(ItemDef):
    """
    MClnAdapter 参数约定（信用联结票据：Bond + CDS 组合）：
    - Bond: 必须传入 MFixedRateBond 对象
    - CreditDefaultSwap: 必须传入 McpCreditDefaultSwap 对象
    - CreditCurve, YieldCurve: 必须传入对应曲线对象
    - 日期字段使用 pf_date() 解析
    """

    def __init__(self):
        super().__init__()
        self.init_data = {
            "is_wrapper": False,
            "method_prefix": "ClnAdapter",
            "data_fields": [],
            "pyxll_def": {},
        }
        self.init_kv_list = [
            [
                ("Bond", "object"),
                ("CreditDefaultSwap", "object"),
                ("InstrumentId", "str"),
                ("TradeId", "str"),
                ("PortfolioKey", "str"),
                ("CreditCurve", "object"),
                ("YieldCurve", "object"),
                ("Notional", "float"),
                ("Currency", "str"),
                ("PrevYieldCurve", "object"),
                ("PrevCreditCurve", "object"),
            ],
            # 支持 CDS 作为 CreditDefaultSwap 的别名（部分 Excel 布局使用）
            [
                ("Bond", "object"),
                ("CDS", "object"),
                ("InstrumentId", "str"),
                ("TradeId", "str"),
                ("PortfolioKey", "str"),
                ("CreditCurve", "object"),
                ("YieldCurve", "object"),
                ("Notional", "float"),
                ("Currency", "str"),
                ("PrevYieldCurve", "object"),
                ("PrevCreditCurve", "object"),
            ],
        ]

        def create_cln_adapter(args_dict):
            import mcp.mcp as mcp_module
            from mcp.wrapper import create_object_instance, McpYieldCurve, McpSwapCurve, McpBondCurve, McpCreditCurve, McpCreditDefaultSwap, McpClnAdapter, McpFixedRateBond

            bond = args_dict.get('Bond', args_dict.get('bond'))
            cds = args_dict.get('CreditDefaultSwap', args_dict.get('creditDefaultSwap',
                   args_dict.get('CDS', args_dict.get('cds'))))
            instrument_id = args_dict.get('InstrumentId', args_dict.get('instrumentId', 'CLN_001'))
            trade_id = args_dict.get('TradeId', args_dict.get('tradeId', 'TRADE_CLN_001'))
            portfolio_key = args_dict.get('PortfolioKey', args_dict.get('portfolioKey', ''))
            credit_curve = args_dict.get('CreditCurve', args_dict.get('creditCurve'))
            yield_curve = args_dict.get('YieldCurve', args_dict.get('yieldCurve'))
            prev_yield_curve = args_dict.get('PrevYieldCurve', args_dict.get('prevYieldCurve'))
            prev_credit_curve = args_dict.get('PrevCreditCurve', args_dict.get('prevCreditCurve'))
            notional = args_dict.get('Notional', args_dict.get('notional'))
            currency = args_dict.get('Currency', args_dict.get('currency', 'CNY'))

            if bond is None:
                raise TypeError("MClnAdapter: Bond is required")
            if cds is None:
                raise TypeError("MClnAdapter: CreditDefaultSwap is required")

            bond_types = (mcp_module.MFixedRateBond, McpFixedRateBond)
            cds_types = (mcp_module.MCreditDefaultSwap, McpCreditDefaultSwap)
            if not isinstance(bond, bond_types):
                raise TypeError(f"MClnAdapter: Bond must be MFixedRateBond, got {type(bond).__name__}")
            if not isinstance(cds, cds_types):
                raise TypeError(f"MClnAdapter: CreditDefaultSwap must be McpCreditDefaultSwap, got {type(cds).__name__}")

            m_bond = bond.getInstance() if hasattr(bond, 'getInstance') else bond
            m_cds = cds.getInstance() if hasattr(cds, 'getInstance') else cds
            try:
                adapter = create_object_instance("mcp.mcp", "MClnAdapter", [
                    m_bond,
                    m_cds,
                    instrument_id,
                    trade_id,
                    portfolio_key or ""
                ])
            except (AttributeError, TypeError) as e:
                if "MClnAdapter" in str(e) or "has no attribute" in str(e).lower():
                    raise TypeError(
                        "MClnAdapter is not available in the current mcp build. "
                        "Please ensure mcpPortLib includes MClnAdapter (ClnAdapter binding) and rebuild."
                    ) from e
                raise

            credit_curve_types = (mcp_module.MCreditCurve, McpCreditCurve)
            yield_curve_types = (mcp_module.MYieldCurve, mcp_module.MBondCurve, mcp_module.MSwapCurve,
                                McpYieldCurve, McpSwapCurve, McpBondCurve)
            if credit_curve is not None:
                if isinstance(credit_curve, credit_curve_types):
                    _cc_arg = credit_curve.getInstance() if hasattr(credit_curve, 'getInstance') else credit_curve
                    adapter.setCreditCurve(_cc_arg)
            if yield_curve is not None:
                if isinstance(yield_curve, yield_curve_types):
                    _yc_arg = yield_curve.getInstance() if hasattr(yield_curve, 'getInstance') else yield_curve
                    adapter.setYieldCurve(_yc_arg)
            if notional is not None:
                adapter.setNotional(float(notional))
            if currency is not None:
                adapter.setCurrency(str(currency))

            # 归因阶梯：prev 曲线。MClnAdapter 需有 setPrevYieldCurve/setPrevCreditCurve（mcpPortLib 已实现，需重建 mcp）
            def _do_set_prev_yield(curve):
                _arg = curve.getInstance() if hasattr(curve, 'getInstance') else curve
                if hasattr(adapter, 'setPrevYieldCurve'):
                    adapter.setPrevYieldCurve(_arg)
                elif hasattr(adapter, 'getHandler'):
                    try:
                        h = adapter.getHandler()
                        if h is not None and hasattr(h, 'setPrevYieldCurve'):
                            h.setPrevYieldCurve(_arg)
                    except Exception:
                        pass
            def _do_set_prev_credit(curve):
                _arg = curve.getInstance() if hasattr(curve, 'getInstance') else curve
                if hasattr(adapter, 'setPrevCreditCurve'):
                    adapter.setPrevCreditCurve(_arg)
                elif hasattr(adapter, 'getHandler'):
                    try:
                        h = adapter.getHandler()
                        if h is not None and hasattr(h, 'setPrevCreditCurve'):
                            h.setPrevCreditCurve(_arg)
                    except Exception:
                        pass
            if prev_yield_curve is not None and isinstance(prev_yield_curve, yield_curve_types):
                _do_set_prev_yield(prev_yield_curve)
            if prev_credit_curve is not None and isinstance(prev_credit_curve, credit_curve_types):
                _do_set_prev_credit(prev_credit_curve)

            adapter._bond_ref = bond
            adapter._cds_ref = cds
            adapter._credit_curve_ref = credit_curve
            adapter._yield_curve_ref = yield_curve

            return McpClnAdapter(adapter)

        self.custom_instance_func = create_cln_adapter

        def _normalize_cln_args(args_dict):
            """规范化键：去空格，CDS 映射为 CreditDefaultSwap，prev 曲线别名"""
            d = {str(k).strip(): v for k, v in args_dict.items() if str(k).strip()}
            if 'CreditDefaultSwap' not in d:
                for k in list(d.keys()):
                    if k.lower() == 'cds':
                        d['CreditDefaultSwap'] = d[k]
                        break
            if 'PrevYieldCurve' not in d and 'prevYieldCurve' in d:
                d['PrevYieldCurve'] = d['prevYieldCurve']
            if 'PrevCreditCurve' not in d and 'prevCreditCurve' in d:
                d['PrevCreditCurve'] = d['prevCreditCurve']
            return d

        self.init_func = [_normalize_cln_args]


class DefMcpFXForwardOutright(ItemDef):

    def __init__(self):
        super().__init__()
        self.custom_instance_func_raw = mcp_instance_list
        self.init_data = {
            "is_wrapper": True,
            "method_prefix": "FXForwardOutright",
            "data_fields": [
            ],
            "pyxll_def": {
            },
        }
        self.init_kv_list = [
            [
                ("ForwardOutright", "float"),
                ("Notional", "float"),
                ("ReferenceDate", "date"),
                ("SpotDate", "date"),
                ("EndDate", "date"),
                ("Pair", "str"),
            ],
            [
                ("ForwardOutright", "float"),
                ("Notional", "float", 1000000.0, 1000000.0),
                ("ReferenceDate", "date"),
                ("SpotDate", "date", "", ""),
                ("EndDate", "date"),
                ("Pair", "str", "", ""),
            ],
        ]


class DefMcpABSTranche(ItemDef):
    """ABS 档位（资产支持证券）：优先档、次级档、私募档"""
    def __init__(self):
        super().__init__()
        self.init_data = {
            "is_wrapper": False,
            "method_prefix": "Abs",
            "data_fields": [],
            "pyxll_def": {},
        }
        self.init_kv_list = [
            [
                ("UnderlyingBond", "object"),
                ("TrancheType", "const", ABSTrancheType.PRIORITY, "PRIORITY"),
                ("ABSMarket", "const", ABSMarket.INTERBANK, "INTERBANK"),
                ("SettlementDate", "date"),
                ("FaceValue", "float"),
                ("Currency", "str", "CNY", "CNY"),
                ("LiquidityDiscount", "float", 0.0, 0.0),
                ("DefaultRateMean", "float", 0.02, 0.02),
                ("DefaultRateStd", "float", 0.005, 0.005),
                ("RecoveryRateMean", "float", 0.4, 0.4),
                ("RecoveryRateStd", "float", 0.1, 0.1),
                ("MCSimulations", "int", 10000, 10000),
            ],
        ]
        self.kv_const_dict = {
            "TrancheType": "ABSTrancheType",
            "ABSMarket": "ABSMarket",
        }

        def create_abs_tranche(args_dict):
            from mcp.wrapper import create_object_instance
            from mcp.utils.excel_utils import pf_date

            def _date(val, default):
                try:
                    s = pf_date(val) if val is not None and val != '' else ''
                    return s if s else default
                except Exception:
                    return default

            bond = args_dict.get("UnderlyingBond", args_dict.get("underlyingBond"))
            if bond is None:
                raise ValueError("DefMcpABSTranche: UnderlyingBond is required")
            if hasattr(bond, "getInstance"):
                bond = bond.getInstance()
            tranche_type = args_dict.get("TrancheType", args_dict.get("trancheType", 0))
            if isinstance(tranche_type, str):
                tranche_type = getattr(ABSTrancheType, tranche_type.strip().upper(), ABSTrancheType.PRIORITY)
            abs_market = args_dict.get("ABSMarket", args_dict.get("absMarket", 0))
            if isinstance(abs_market, str):
                abs_market = getattr(ABSMarket, abs_market.strip().upper(), ABSMarket.INTERBANK)
            settlement = _date(args_dict.get("SettlementDate", args_dict.get("settlementDate")), "")
            face_value = args_dict.get("FaceValue", args_dict.get("faceValue", 1000000.0))
            currency = args_dict.get("Currency", args_dict.get("currency", "CNY"))
            currency_str = str(currency) if currency else "CNY"
            abs_tranche = create_object_instance("mcp.mcp", "MABSTranche", [
                bond, int(tranche_type), int(abs_market),
                str(settlement), float(face_value), currency_str
            ])
            tt = int(tranche_type)
            if tt == 2:  # PRIVATE_PLACEMENT
                liq = args_dict.get("LiquidityDiscount", args_dict.get("liquidityDiscount", 0.0))
                if liq:
                    abs_tranche.setLiquidityDiscount(float(liq))
            elif tt == 1:  # SUBORDINATED
                abs_tranche.setDefaultRateDistribution(
                    float(args_dict.get("DefaultRateMean", 0.02)),
                    float(args_dict.get("DefaultRateStd", 0.005))
                )
                abs_tranche.setRecoveryRateDistribution(
                    float(args_dict.get("RecoveryRateMean", 0.4)),
                    float(args_dict.get("RecoveryRateStd", 0.1))
                )
                abs_tranche.setMonteCarloSimulationCount(int(args_dict.get("MCSimulations", 10000)))
            return abs_tranche

        self.custom_instance_func = create_abs_tranche


# class DefMcpBond(ItemDef):
#
#     def __init__(self):
#         super().__init__()
#         self.custom_instance_func_raw = mcp_instance_list
#         self.init_data = {
#             "is_wrapper": True,
#             "method_prefix": "Bond",
#             "data_fields": [
#             ],
#             "pyxll_def": {
#             },
#         }
#         self.init_kv_list = [
#             [
#                 ("SettlementDate", "date"),
#                 ("MaturityDate", "date"),
#                 ("Frequency", "const"),
#                 ("Coupon", "float"),
#                 ("CouponType", "const"),
#                 ("ValueDate", "date"),
#                 ("IssuePrice", "float"),
#                 ("DayCounter", "const"),
#             ],
#             [
#                 ("SettlementDate", "date"),
#                 ("MaturityDate", "date"),
#                 ("Frequency", "const", Frequency.Annual, "Annual"),
#                 ("Coupon", "float"),
#                 ("CouponType", "const", CouponType.Fixed, "Fixed"),
#                 ("ValueDate", "date", "", ""),
#                 ("IssuePrice", "float", 100.0, 100.0),
#                 ("DayCounter", "const", DayCounter.Act365Fixed, "Act365Fixed"),
#             ],
#         ]


class DefMcpCallableBond(ItemDef):

    def __init__(self):
        super().__init__()
        self.custom_instance_func_raw = mcp_instance_list
        self.init_data = {
            "is_wrapper": True,
            "method_prefix": "CallableBond",
            "data_fields": [
                ("ExerciseDates", "date"),
                ("Strikes", "float"),
                ("VolDates", "date"),
                ("IrVols", "float"),
            ],
            "pyxll_def": {
            },
        }
        # MCallableBond(valuationDate, underlyingBond, optionType, exerciseDates, strikes, benchmarkCurve, volDates, irVols)
        # plainlist 类型会自动转换为 JSON 数组字符串
        self.init_kv_list = [
            [
                ("ReferenceDate", "date"),
                ("FixedRateBond", "object"),
                ("OptionType", "int"),
                ("ExerciseDates", "plainlist"),
                ("Strikes", "plainlist"),
                ("BenchmarkCurve", "object"),
                ("VolDates", "plainlist"),
                ("IrVols", "plainlist"),
                ("SpreadCurve", "object", None, None),
            ],
            [
                ("ReferenceDate", "date"),
                ("FixedRateBond", "object"),
                ("OptionType", "int", 1, 1),  # 1=CALL, 2=PUT
                ("ExerciseDates", "plainlist", [], []),
                ("Strikes", "plainlist", [], []),
                ("BenchmarkCurve", "object", None, None),
                ("VolDates", "plainlist", [], []),
                ("IrVols", "plainlist", [], []),
                ("SpreadCurve", "object", None, None),
            ],
        ]

        def create_callable_bond(args_dict):
            from mcp.wrapper import McpCallableBond
            from mcp.utils.mcp_utils import parse_excel_date
            import pandas as pd

            def _as_handler(obj):
                return obj.getHandler() if hasattr(obj, "getHandler") else obj

            def _normalize_date_string(x):
                if x is None:
                    return None
                if hasattr(x, "strftime"):
                    return x.strftime("%Y-%m-%d")
                try:
                    dt = parse_excel_date(x)
                    if str(dt) != "NaT":
                        return dt.strftime("%Y-%m-%d")
                except Exception:
                    pass
                try:
                    dt2 = pd.to_datetime(x, errors="coerce")
                    if str(dt2) != "NaT":
                        return dt2.strftime("%Y-%m-%d")
                except Exception:
                    pass
                s = str(x).strip()
                if not s:
                    return None
                # 常见 Excel/ISO 时间串兜底截断到日期
                if "T" in s:
                    s = s.split("T", 1)[0]
                if " " in s:
                    s = s.split(" ", 1)[0]
                return s

            def _to_json_array_string(v):
                # 统一转为 JSON 数组字符串，匹配 MCallableBond 的 char* 入参
                if v is None:
                    return "[]"
                if isinstance(v, str):
                    s = v.strip()
                    if not s:
                        return "[]"
                    # 已是 JSON 数组
                    if s.startswith("[") and s.endswith("]"):
                        return s
                    # 逗号分隔字符串 -> 数组
                    if "," in s:
                        arr = [x.strip() for x in s.split(",") if str(x).strip()]
                        return json.dumps(arr)
                    # 单值字符串
                    return json.dumps([s])
                if isinstance(v, (list, tuple)):
                    arr = []
                    for x in v:
                        if x is None:
                            continue
                        # 日期类统一转字符串
                        if hasattr(x, "strftime"):
                            arr.append(x.strftime("%Y-%m-%d"))
                        else:
                            arr.append(x)
                    return json.dumps(arr)
                # 标量兜底
                return json.dumps([v])

            def _to_json_date_array_string(v):
                if v is None:
                    return "[]"
                if isinstance(v, str):
                    s = v.strip()
                    if not s:
                        return "[]"
                    if s.startswith("[") and s.endswith("]"):
                        try:
                            arr = json.loads(s)
                        except Exception:
                            arr = [s]
                    elif "," in s:
                        arr = [x.strip() for x in s.split(",") if str(x).strip()]
                    else:
                        arr = [s]
                elif isinstance(v, (list, tuple)):
                    arr = list(v)
                else:
                    arr = [v]

                out = []
                for x in arr:
                    if x is None or (isinstance(x, str) and not x.strip()):
                        continue
                    ds = _normalize_date_string(x)
                    if ds is not None:
                        out.append(ds)
                return json.dumps(out)

            reference_date = args_dict.get("ReferenceDate", args_dict.get("referenceDate"))
            fixed_rate_bond = args_dict.get("FixedRateBond", args_dict.get("fixedRateBond"))
            option_type = args_dict.get("OptionType", args_dict.get("optionType", 1))
            exercise_dates = args_dict.get("ExerciseDates", args_dict.get("exerciseDates"))
            strikes = args_dict.get("Strikes", args_dict.get("strikes"))
            benchmark_curve = args_dict.get("BenchmarkCurve", args_dict.get("benchmarkCurve"))
            vol_dates = args_dict.get("VolDates", args_dict.get("volDates"))
            ir_vols = args_dict.get("IrVols", args_dict.get("irVols"))
            spread_curve = args_dict.get("SpreadCurve", args_dict.get("spreadCurve"))

            if reference_date is None or fixed_rate_bond is None or benchmark_curve is None:
                raise Exception("McpCallableBond Missing required fields: ReferenceDate/FixedRateBond/BenchmarkCurve")

            reference_date = _normalize_date_string(reference_date)
            if not reference_date:
                raise Exception("McpCallableBond Invalid ReferenceDate")

            m_bond = _as_handler(fixed_rate_bond)
            m_curve = _as_handler(benchmark_curve)
            m_option_type = int(option_type)
            exercise_dates_s = _to_json_date_array_string(exercise_dates)
            strikes_s = _to_json_array_string(strikes)
            vol_dates_s = _to_json_date_array_string(vol_dates)
            ir_vols_s = _to_json_array_string(ir_vols)

            try:
                if spread_curve is not None and spread_curve != "":
                    m_spread = _as_handler(spread_curve)
                    obj = McpCallableBond(
                        reference_date,
                        m_bond,
                        m_option_type,
                        exercise_dates_s,
                        strikes_s,
                        m_curve,
                        vol_dates_s,
                        ir_vols_s,
                        m_spread,
                    )
                else:
                    obj = McpCallableBond(
                        reference_date,
                        m_bond,
                        m_option_type,
                        exercise_dates_s,
                        strikes_s,
                        m_curve,
                        vol_dates_s,
                        ir_vols_s,
                    )
            except Exception as e:
                raise Exception(
                    f"McpCallableBond ctor failed: {e}; "
                    f"referenceDate={reference_date}, "
                    f"exerciseDates={exercise_dates_s}, "
                    f"volDates={vol_dates_s}"
                )
            return obj

        self.custom_instance_func = create_callable_bond


class DefMcpLoanAndDepos(ItemDef):

    def __init__(self):
        super().__init__()
        self.custom_instance_func_raw = mcp_instance_list
        self.init_data = {
            "is_wrapper": True,
            "method_prefix": "Lnd",
            "data_fields": [],
            "pyxll_def": {},
        }
        self.init_kv_list = [
            [
                ("ValueDate", "date"),
                ("Settlement", "date"),
                ("StartDate", "date"),
                ("EndDate", "date"),
                ("RateOrMargin", "float"),
                ("Notional", "float"),
                ("IsLoan", "bool"),
                ("IsFloatingRate", "bool"),
                ("DayCounter", "const"),
                ("Frequency", "const"),
                ("HasEndStub", "bool"),
                ("Calendar", "object"),
                ("FixingPeriods", "str", "", ""),
                ("FirstFixing", "float", 0.0, 0.0),
            ],
            [
                ("ValueDate", "date"),
                ("Settlement", "date"),
                ("StartDate", "date"),
                ("EndDate", "date"),
                ("RateOrMargin", "float"),
                ("Notional", "float"),
                ("IsLoan", "bool", True, True),
                ("IsFloatingRate", "bool", False, False),
                ("DayCounter", "const", DayCounter.Act360, "Act360"),
                ("Frequency", "const", Frequency.Quarterly, "Quarterly"),
                ("HasEndStub", "bool", False, False),
                ("Calendar", "object", McpCalendar("", "", "")),
                ("FixingPeriods", "str", "", ""),
                ("FirstFixing", "float", 0.0, 0.0),
            ],
        ]


class DefMcpVanillaSwap(ItemDef):

    def __init__(self):
        super().__init__()
        self.generate_xls_method = True
        self.custom_instance_func_raw = mcp_instance_list
        self.init_data = {
            "is_wrapper": True,
            "method_prefix": "Swap",
            "data_fields": [
            ],
            "pyxll_def": {
            },
        }
        self.init_kv_list = [
            [
                ("ReferenceDate", "date"),
                ("StartDate", "date"),
                ("EndDate", "date"),
                ("RollDate", "date"),
                ("FixedPayReceive", "const", PayReceive.Pay, "Pay"),
                ("Notional", "float", 1000000, 1000000),
                ("Coupon", "float"),
                ("Margin", "float", 0, 0),
                ("PaymentCalendar", "object", McpCalendar("", "", ""), ""),
                # ("FixedEstimationCurve", "object", "", ""),
                ("FixedDiscountCurve", "object", "", ""),
                ("FixedPaymentFrequency", "const", Frequency.Quarterly, "Quarterly"),
                ("FixedPaymentDateAdjuster", "const", DateAdjusterRule.Following, "Following"),
                ("FixedPaymentDayCounter", "const", DayCounter.Act365Fixed, "Act365Fixed"),
                ("FixedResetFrequency", "const", Frequency.Once, "Once"),
                ("FixedResetDateAdjuster", "const", DateAdjusterRule.LME, "LME"),  # 设置LME，代表缺省等于PaymentDateAdjuster
                ("FixedResetDayCounter", "const", DayCounter.Act252, "Act252"),  # 设置Act252，代表缺省等于PaymentDayCounter
                ("FloatPaymentFrequency", "const", Frequency.Quarterly, "Quarterly"),
                ("FloatPaymentDateAdjuster", "const", DateAdjusterRule.Following, "Following"),
                ("FloatPaymentDayCounter", "const", DayCounter.Act360, "Act360"),
                ("FloatResetFrequency", "const", Frequency.Quarterly, "Quarterly"),
                ("FloatResetDateAdjuster", "const", DateAdjusterRule.LME, "LME"),  # 设置LME，代表缺省等于PaymentDateAdjuster
                ("FloatResetDayCounter", "const", DayCounter.Act252, "Act252"),  # 设置Act252，代表缺省等于PaymentDayCounter
                ("FixingFrequency", "const", Frequency.Weekly),
                ("FixingIndex", "str", "7D", "7D"),
                ("FixingDateAdjuster", "const", DateAdjusterRule.LME, "LME"),  # 设置LME，代表缺省等于PaymentDateAdjuster
                ("FloatEstimationCurve", "object", "", ""),
                ("FloatDiscountCurve", "object", "", ""),
                ("FixingCalendar", "object", McpCalendar("", "", ""), ""),
                ("FixInAdvance", "bool", True, True),
                ("FixDaysBackward", "int", 2, 2),
                ("FixingRateMethod", "const", ResetRateMethod.RESETRATE_MAX),
                ("HistoryFixingDates", "objectlist", "[]"),
                ("HistoryFixingRates", "objectlist", "[]"),
                ("FixedExchangeNotional", "const", ExchangePrincipal.NOEXCHANGE),
                ("FixedResidual", "float", 0, 0),
                ("FixedResidualType", "const", ResidualType.AbsoluteValue),
                ("FixedFirstAmortDate", "date", ""),
                ("FixedAmortisationType", "const", AmortisationType.AMRT_NONE),
                ("FloatExchangeNotional", "const", ExchangePrincipal.NOEXCHANGE),
                ("FloatResidual", "float", 0, 0),
                ("FloatResidualType", "const", ResidualType.AbsoluteValue),
                ("FloatFirstAmortDate", "date", ""),
                ("FloatAmortisationType", "const", AmortisationType.AMRT_NONE),
                ("FixedResetPaymentDates", "objectlist", "[]"),
                ("FixedResetRates", "objectlist", "[]"),
                ("FixedResetAmortAmounts", "objectlist", "[]"),
                ("FloatResetPaymentDates", "objectlist", "[]"),
                ("FloatResetRates", "objectlist", "[]"),
                ("FloatResetAmortAmounts", "objectlist", "[]"),
                ("FixedKeepEndOfMonth", "bool", True),
                ("FixedLongStub", "bool", False),
                ("FixedEndStub", "bool", True),
                ("FixedAdjStartDate", "bool", True),
                ("FixedAdjEndDate", "bool", True),
                ("FloatKeepEndOfMonth", "bool", True),
                ("FloatLongStub", "bool", False),
                ("FloatEndStub", "bool", True),
                ("FloatAdjStartDate", "bool", True),
                ("FloatAdjEndDate", "bool", True),
                ("FixedPaymentLag", "int", 0),
                ("FloatPaymentLag", "int", 0),
                ("FixedCompounding", "bool", True),
                ("FixedCompoundingFrequency", "const", Frequency.Continuous),
                ("FloatCompounding", "bool", True),
                ("FloatCompoundingFrequency", "const", Frequency.Continuous),
                ("FixingDayCounter", "const", DayCounter.Act360),
            ],
            # [
            #     ("Curve", "object", "", ""),
            #     ("ValueDate", "date"),
            #     ("StartDate", "date", "", ""),
            #     ("EndDate", "date"),
            #     ("RollDate", "date", "", ""),
            #     ("FixedPayReceive", "const", PayReceive.Pay, "Pay"),
            #     ("Notional", "float", 1000000, 1000000),
            #     ("Coupon", "float"),
            #     ("Margin", "float", 0, 0),
            #     ("PaymentCalendar", "object", McpCalendar("", "", ""), ""),
            #     ("FixedEstimationCurve", "object", "", ""),
            #     ("FixedDiscountCurve", "object", "", ""),
            #     ("FixedPaymentFrequency", "const", Frequency.Quarterly, "Quarterly"),
            #     ("FixedPaymentDateAdjuster", "const", DateAdjusterRule.Following, "Following"),
            #     ("FixedPaymentDayCounter", "const", DayCounter.Act365Fixed, "Act365Fixed"),
            #     ("FixedResetFrequency", "const", Frequency.Once, "Once"),
            #     ("FixedResetDateAdjuster", "const", DateAdjusterRule.Actual, "Actual"),
            #     ("FixedResetDayCounter", "const", DayCounter.Act365Fixed, "Act365Fixed"),
            #     ("FloatPaymentFrequency", "const", Frequency.Quarterly, "Quarterly"),
            #     ("FloatPaymentDateAdjuster", "const", DateAdjusterRule.Following, "Following"),
            #     ("FloatPaymentDayCounter", "const", DayCounter.Act365Fixed, "Act365Fixed"),
            #     ("FloatResetFrequency", "const", Frequency.Quarterly, "Quarterly"),
            #     ("FloatResetDateAdjuster", "const", DateAdjusterRule.Actual, "Actual"),
            #     ("FloatResetDayCounter", "const", DayCounter.Act365Fixed, "Act365Fixed"),
            #     ("FixingFrequency", "const", Frequency.Weekly),
            #     ("FixingIndex", "str", "7D", "7D"),
            #     ("FixingDateAdjuster", "const", DateAdjusterRule.Following, "Following"),
            #     ("FloatEstimationCurve", "object", "", ""),
            #     ("FloatDiscountCurve", "object", "", ""),
            #     ("FixingCalendar", "object", McpCalendar("", "", ""), ""),
            #     ("FixInAdvance", "bool", True, True),
            #     ("FixDaysBackward", "int", 2, 2),
            #     ("FixingRateMethod", "const", ResetRateMethod.RESETRATE_MAX),
            #     ("HistoryFixingDates", "objectlist", "[]"),
            #     ("HistoryFixingRates", "objectlist", "[]"),
            # ],
            [
                ("SettlementDate", "date"),
                ("StartDate", "date"),
                ("EndDate", "date"),
                ("Coupon", "float"),
                ("PaymentCalendar", "object", McpCalendar("", "", ""), ""),
                ("FixedFrequency", "const"),
                ("FixedDayCounter", "const", DayCounter.Act365Fixed, "Act365Fixed"),
                ("UseIndexEstimation", "bool", False),
                ("FloatingFrequency", "const"),
                ("FloatingDayCounter", "const", DayCounter.Act365Fixed, "Act365Fixed"),
                ("FixedEstimationCurve", "object", "", ""),
                ("FixedDiscountCurve", "object", "", ""),
                ("FloatingEstimationCurve", "object", "", ""),
                ("FloatingDiscountCurve", "object", "", ""),
                ("FloatingCalendar", "object", McpCalendar("", "", ""), ""),
                ("FirstFixing", "float"),
                ("SecondFixing", "float"),
                ("EomRule", "int", 1),
                ("CompoundingFrequency", "int", 0),
                ("Notional", "float", 1000000, 1000000),
                ("CsaId", "str", ""),
                ("SwapStartLag", "int", 2),
                ("Margin", "float"),
                ("FixedAdjusterRule", "const", DateAdjusterRule.ModifiedFollowing, "ModifiedFollowing"),
                ("FloatAdjusterRule", "const", DateAdjusterRule.ModifiedFollowing, "ModifiedFollowing"),
                ("FixedLastOpenday", "bool", False),
                ("FloatLastOpenday", "bool", False),
                ("FixedLegPayReceive", "const", PayReceive.Pay, "Pay"),
                ("FixInAdvance", "bool", True),
                ("FixDaysBackward", "int", 2),
                ("FixDaysForward", "int", 2),
                ("EndStub", "bool", False),
                ("FixedPayType", "const", PaymentType.InArrears, "InArrears"),
                ("FloatPayType", "const", PaymentType.InArrears, "InArrears"),
            ],
            [
                ("ReferenceDate", "date"),
                ("StartDate", "date"),
                ("EndDate", "date"),
                ("FixedPayReceive", "const", PayReceive.Pay, "Pay"),
                ("RateConvention", "object"),
                ("Calendar", "object"),
                ("Coupon", "float"),
                ("Notional", "float"),
                ("FixedFrequency", "const", Frequency.Annual, "Annual"),
                ("FloatingFrequency", "const", Frequency.Annual, "Annual"),
                ("FixedDiscountCurve", "object", "", ""),
                ("FloatingEstimationCurve", "object", "", ""),
                ("FloatingDiscountCurve", "object", "", ""),
                ("HistoryFixingDates", "objectlist", "[]"),
                ("HistoryFixingRates", "objectlist", "[]"),
            ],
            [
                ("ReferenceDate", "date"),
                ("StartDate", "date"),
                ("EndDate", "date"),
                ("RollDate", "date"),
                ("FixedPayReceive", "const", PayReceive.Pay, "Pay"),
                ("RateConvention", "object"),
                ("Calendar", "object"),
                ("Coupon", "float"),
                ("Notional", "float"),
                ("FixedFrequency", "const", Frequency.Annual, "Annual"),
                ("FloatingFrequency", "const", Frequency.Annual, "Annual"),
                ("FixedDiscountCurve", "object", "", ""),
                ("FloatingEstimationCurve", "object", "", ""),
                ("FloatingDiscountCurve", "object", "", ""),
                ("HistoryFixingDates", "objectlist", "[]"),
                ("HistoryFixingRates", "objectlist", "[]"),
            ],
            [
                ("ReferenceDate", "date"),
                ("StartDate", "date"),
                ("Tenor", "str"),
                ("FixedPayReceive", "const", PayReceive.Pay, "Pay"),
                ("RateConvention", "object"),
                ("Coupon", "float"),
                ("Notional", "float"),
                ("FixedFrequency", "const", Frequency.Annual, "Annual"),
                ("FloatingFrequency", "const", Frequency.Annual, "Annual"),
                ("FixedDiscountCurve", "object", "", ""),
                ("FloatingEstimationCurve", "object", "", ""),
                ("FloatingDiscountCurve", "object", "", ""),
                ("Calendar", "object"),
                ("AdjustedStartDate", "bool", False),
                ("HistoryFixingDates", "objectlist", "[]"),
                ("HistoryFixingRates", "objectlist", "[]"),
            ],
            [
                ("ReferenceDate", "date"),
                ("StartDate", "date"),
                ("Tenor", "str"),
                ("RollDate", "date"),
                ("FixedPayReceive", "const", PayReceive.Pay, "Pay"),
                ("RateConvention", "object"),
                ("Coupon", "float"),
                ("Notional", "float"),
                ("FixedFrequency", "const", Frequency.Annual, "Annual"),
                ("FloatingFrequency", "const", Frequency.Annual, "Annual"),
                ("FixedDiscountCurve", "object", "", ""),
                ("FloatingEstimationCurve", "object", "", ""),
                ("FloatingDiscountCurve", "object", "", ""),
                ("Calendar", "object"),
                ("AdjustedStartDate", "bool", False),
                ("HistoryFixingDates", "objectlist", "[]"),
                ("HistoryFixingRates", "objectlist", "[]"),
            ],
        ]


class DefMcpBlack76Swaption(ItemDef):

    def __init__(self):
        super().__init__()
        self.generate_xls_method = True
        self.custom_instance_func_raw = mcp_instance_list
        self.init_data = {
            "is_wrapper": True,
            "method_prefix": "Swaption",
            "data_fields": [
            ],
            "pyxll_def": {
            },
        }
        self.init_kv_list = [
            [
                ("UnderlyingSwap", "object"),
                ("SwaptionExpiry", "date"),
                ("Vol", "float"),
                ("HaveVol", "bool"),
                ("PayReceiveType", "const"),
                ("SettlementDate", "date"),
                ("SettlementMethod", "const"),
            ],
            [
                ("UnderlyingSwap", "object"),
                ("SwaptionExpiry", "date"),
                ("Volatility", "float"),
                ("SettlementDate", "date"),
                ("BuySell", "int", BuySell.Buy),
                ("PayReceiveType", "const", PayReceive.Receive),
                ("Strike", "double"),
                ("SettlementMethod", "const"),
                ("Notional", 1.0),
                ("EstimationSwapCurve", "object", None),
                ("DiscountSwapCurve", "object", None),
            ],
        ]
        self.add_method_range(
            ["Price", "DV01", "Delta", "Gamma", "Vega", "Vomma", "Theta", "NPV"],
            {
                "args": [
                    ("curve", "object"),
                ],
            }
        )


class DefMcpCapFloor(ItemDef):

    def __init__(self):
        super().__init__()
        self.generate_xls_method = True
        self.custom_instance_func_raw = mcp_instance_list
        self.init_data = {
            "is_wrapper": True,
            "method_prefix": "capFloor",
            "data_fields": [
            ],
            "pyxll_def": {
            },
        }
        self.init_kv_list = [
            [
                ("IROptionType", "const"),
                ("ReferenceDate", "date"),
                ("StartDate", "date"),
                ("MaturityTenor", "str"),  # Date or Tenor
                ("PaymentFrequency", "const"),
                ("Strike", "float"),
                ("PaymentType", "const"),
                ("PriceVol", "bool", False),
                ("DiscountCurve", "object"),
                ("CapVolStripping", "object"),
                ("BuySell", "const"),
                ("DayCounter", "const"),
                ("Notional", "float"),
                ("Calendar", "object"),
            ],
            [
                ("ReferenceDate", "date"),
                ("StartDate", "date"),
                ("MaturityDate", "date"),  # Date or Tenor
                ("IROptionType", "const"),
                ("PaymentFrequency", "const"),
                ("Strike", "float"),
                ("PaymentType", "const"),
                ("PriceVol", "bool", False),
                ("DiscountCurve", "object"),
                ("CapVolStripping", "object"),
                ("BuySell", "const"),
                ("DayCounter", "const"),
                ("Notional", "float"),
                ("Calendar", "object"),
            ],
        ]
        self.add_method_range(
            ["Price", "GetCaplet", "GetNumCaplets", "ExpiryDates", "MaturityDates", "SpotDelta", "FrwdDelta",
             "SpotVega", "FwdVega", "SpotGamma", "FwdGamma"],
            {
                "args": [
                    ("obj", "object"),
                ],
            }
        )


class DefMcpCapLetFloorLet(ItemDef):

    def __init__(self):
        super().__init__()
        self.generate_xls_method = True
        self.custom_instance_func_raw = mcp_instance_list
        self.init_data = {
            "is_wrapper": True,
            "method_prefix": "capfloorlet",
            "data_fields": [
            ],
            "pyxll_def": {
            },
        }
        self.init_kv_list = [
            [
                ("ReferenceDate", "date"),
                ("YieldCurve", "object"),
                ("CapFloorType", "const"),  # Date or Tenor
                ("Strike", "float"),
                ("Volatility", "float"),
                ("ExpiryDate", "date"),
                ("MaturityDate", "date"),
                ("InAdvance", "bool"),
                ("PriceVol", "bool"),
                ("BuySellCap", "int"),
                ("DayCounter", "const"),
                ("Notional", "float"),
            ],
        ]
        self.add_method_range(
            ["Price", "ValueDate", "ExpiryDate", "MaturityDate", "SpotDelta", "FrwdDelta", "SpotVega", "FwdVega",
             "SpotGamma", "FwdGamma"],
            {
                "args": [
                    ("obj", "object"),
                ],
            }
        )


class DefMcpCurrencySwapLeg(ItemDef):

    def __init__(self):
        super().__init__()
        self.generate_xls_method = True
        self.custom_instance_func_raw = mcp_instance_list
        self.init_data = {
            "is_wrapper": True,
            "method_prefix": "SwapLeg",
            "data_fields": [
            ],
            "pyxll_def": {
            },
        }
        self.init_kv_list = [
            [
                ("ReferenceDate", "date"),
                ("StartDate", "date"),
                ("EndDate", "date"),
                ("RollDate", "date"),
                ("FixedPayReceive", "const", PayReceive.Pay, "Pay"),
                ("Notional", "float", 1000000, 1000000),
                ("Margin", "float"),
                ("PaymentFrequency", "const", Frequency.Quarterly, "Quarterly"),
                ("PaymentDateAdjuster", "const", DateAdjusterRule.Following, "Following"),
                ("PaymentDayCounter", "const", DayCounter.Act365Fixed, "Act365Fixed"),
                ("PaymentCalendar", "object", McpCalendar("", "", ""), ""),
                ("ResetFrequency", "const", Frequency.Once, "Once"),
                ("ResetDateAdjuster", "const", DateAdjusterRule.Actual, "Actual"),
                ("ResetDayCounter", "const", DayCounter.Act365Fixed, "Act365Fixed"),
                ("FixingFrequency", "const", Frequency.Weekly),
                ("FixingIndex", "str", "7D", "7D"),
                ("FixingDateAdjuster", "const", DateAdjusterRule.LME, "LME"),
                ("EstimationCurve", "object", "", ""),
                ("DiscountCurve", "object", "", ""),
                ("FixingCalendar", "object", McpCalendar("", "", ""), ""),
                ("FixInAdvance", "bool", True, True),
                ("FixDaysBackward", "int", 2, 2),
                ("FixingRateMethod", "const", ResetRateMethod.RESETRATE_MAX),
                ("HistoryFixingDates", "objectlist", "[]"),
                ("HistoryFixingRates", "objectlist", "[]"),
                ("HasInitialExchange", "bool", False, False),
                ("HasFinalExchange", "bool", False, False),
                ("FinalNotional", "float", 0.0, 0.0),
            ],
            [
                ("ReferenceDate", "date"),
                ("StartDate", "date"),
                ("EndDate", "date"),
                ("RollDate", "date"),
                ("FixedPayReceive", "const", PayReceive.Pay, "Pay"),
                ("Notional", "float", 1000000, 1000000),
                ("Coupon", "float"),
                ("EstimationCurve", "object", "", ""),
                ("DiscountCurve", "object", "", ""),
                ("PaymentCalendar", "object", McpCalendar("", "", ""), ""),
                ("PaymentFrequency", "const", Frequency.Quarterly, "Quarterly"),
                ("PaymentDateAdjuster", "const", DateAdjusterRule.Following, "Following"),
                ("PaymentDayCounter", "const", DayCounter.Act365Fixed, "Act365Fixed"),
                ("ResetFrequency", "const", Frequency.Once, "Once"),
                ("ResetDateAdjuster", "const", DateAdjusterRule.Actual, "Actual"),
                ("ResetDayCounter", "const", DayCounter.Act365Fixed, "Act365Fixed"),
                ("HasInitialExchange", "bool", False, False),
                ("HasFinalExchange", "bool", False, False),
                ("FinalNotional", "float", 0.0, 0.0), ],
            [
                ("Margin", "float"),
                ("PaymentFrequency", "const", Frequency.Quarterly, "Quarterly"),
                ("PaymentDateAdjuster", "const", DateAdjusterRule.Following, "Following"),
                ("PaymentDayCounter", "const", DayCounter.Act365Fixed, "Act365Fixed"),
                ("PaymentCalendar", "object", McpCalendar("", "", ""), ""),
                ("ResetFrequency", "const", Frequency.Once, "Once"),
                ("ResetDateAdjuster", "const", DateAdjusterRule.Actual, "Actual"),
                ("ResetDayCounter", "const", DayCounter.Act365Fixed, "Act365Fixed"),
                ("FixingFrequency", "const", Frequency.Weekly),
                ("FixingIndex", "str", "7D", "7D"),
                ("FixingDateAdjuster", "const", DateAdjusterRule.LME, "LME"),
                ("EstimationCurve", "object", "", ""),
                ("DiscountCurve", "object", "", ""),
                ("FixingCalendar", "object", McpCalendar("", "", ""), ""),
                ("FixInAdvance", "bool", True, True),
                ("FixDaysBackward", "int", 2, 2),
                ("FixingRateMethod", "const", ResetRateMethod.RESETRATE_MAX),
                ("HistoryFixingDates", "objectlist", "[]"),
                ("HistoryFixingRates", "objectlist", "[]"),
            ],
            [
                ("Coupon", "float"),
                ("DiscountCurve", "object"),
                ("PaymentCalendar", "object", McpCalendar("", "", ""), ""),
                ("PaymentFrequency", "const", Frequency.Quarterly, "Quarterly"),
                ("PaymentDateAdjuster", "const", DateAdjusterRule.Following, "Following"),
                ("PaymentDayCounter", "const", DayCounter.Act365Fixed, "Act365Fixed"),
                ("ResetFrequency", "const", Frequency.Once, "Once"),
                ("ResetDateAdjuster", "const", DateAdjusterRule.Actual, "Actual"),
                ("ResetDayCounter", "const", DayCounter.Act365Fixed, "Act365Fixed"),
                ("KeepEndOfMonth", "bool", True, True),
            ],
            # 4 constructors using RateConvention (C++ signatures from header)
            # MCurrencySwapLeg(double coupon, void* rateConvention, void* discountCurve, void* paymentCalendar, int paymentFrequencyOverride=-1);
            [
                ("Coupon", "float"),
                ("RateConvention", "object"),
                ("DiscountCurve", "object"),
                ("PaymentCalendar", "object"),
                ("PaymentFrequency", "const", Frequency.NoFrequency, "NoFrequency"),
                ("KeepEndOfMonth", "bool", True, True),
            ],
            # MCurrencySwapLeg(double coupon, char* conventionName, void* discountCurve, void* paymentCalendar, int paymentFrequencyOverride=-1);
            [
                ("Coupon", "float"),
                ("RateConvention", "str"),
                ("DiscountCurve", "object"),
                ("PaymentCalendar", "object"),
                ("PaymentFrequency", "const", Frequency.NoFrequency, "NoFrequency"),
                ("KeepEndOfMonth", "bool", True, True),
            ],
            # MCurrencySwapLeg(void* rateConvention, void*, void*, void* fixingCalendar, char* historyFixingDates="", char* historyFixingRates="", ...);
            # 改为与 VanillaSwap/BasisSwap 一致的 HistoryFixingDates + HistoryFixingRates 字符串配对方式，
            # 不再使用 MHistoricalRates 对象。
            # PaymentCalendar: 新增，可选。缺省不填时回退为 FixingCalendar（向后兼容）；
            # 显式提供时支付日历与定盘日历可独立设置（如跨境 index 支付地与定盘地日历不同）
            [
                ("RateConvention", "object"),
                ("EstimationCurve", "object"),
                ("DiscountCurve", "object"),
                ("FixingCalendar", "object"),
                ("HistoryFixingDates", "objectlist", "[]"),
                ("HistoryFixingRates", "objectlist", "[]"),
                ("PaymentFrequency", "const", Frequency.NoFrequency, "NoFrequency"),
                ("SpreadBps", "float", 0.0, 0.0),
                ("KeepEndOfMonth", "bool", True, True),
                ("CollateralFxForwardPointsCurve", "object", None, None),
                ("TargetLegIsTerm", "bool", True, True),
                ("PaymentCalendar", "object", None, None),
            ],
            # MCurrencySwapLeg(char* conventionName, void*, void*, void* fixingCalendar, char* historyFixingDates="", char* historyFixingRates="", ...);
            [
                ("RateConvention", "str"),
                ("EstimationCurve", "object"),
                ("DiscountCurve", "object"),
                ("FixingCalendar", "object"),
                ("HistoryFixingDates", "objectlist", "[]"),
                ("HistoryFixingRates", "objectlist", "[]"),
                ("PaymentFrequency", "const", Frequency.NoFrequency, "NoFrequency"),
                ("SpreadBps", "float", 0.0, 0.0),
                ("KeepEndOfMonth", "bool", True, True),
                ("CollateralFxForwardPointsCurve", "object", None, None),
                ("TargetLegIsTerm", "bool", True, True),
                ("PaymentCalendar", "object", None, None),
            ],
        ]


class DefMcpXCurrencySwap(ItemDef):

    def __init__(self):
        super().__init__()
        self.generate_xls_method = True
        self.custom_instance_func_raw = mcp_instance_list
        self.init_data = {
            "is_wrapper": True,
            "method_prefix": "XCcySwap",
            "data_fields": [
            ],
            "pyxll_def": {
            },
        }
        self.init_kv_list = [
            [
                ("ReferenceDate", "date"),
                ("StartDate", "date"),
                ("EndDate", "date"),
                ("RollDate", "date"),
                ("Notional", "float", 1000000, 1000000),
                ("BaseSwapLeg", "object", "", ""),
                ("TermSwapLeg", "object", "", ""),
                ("BasePayReceive", "const", PayReceive.Pay, "Pay"),
                ("FxRate", "float"),
                ("HasInitialExchange", "bool", False, False),
                ("HasFinalExchange", "bool", False, False),
                ("FinalFxRate", "float", 0.0, 0.0),
            ],
            [
                ("ReferenceDate", "date"),
                ("StartDate", "date"),
                ("EndDate", "date"),
                ("Notional", "float", 1000000, 1000000),
                ("BaseSwapLeg", "object", "", ""),
                ("TermSwapLeg", "object", "", ""),
                ("BasePayReceive", "const", PayReceive.Pay, "Pay"),
                ("FxRate", "float"),
                ("HasInitialExchange", "bool", False, False),
                ("HasFinalExchange", "bool", False, False),
                ("FinalFxRate", "float", 0.0, 0.0),
            ],
            [
                ("ReferenceDate", "date"),
                ("StartDate", "date"),
                ("EndDate", "date"),
                ("RollDate", "date"),
                ("Notional", "float", 1000000, 1000000),
                ("BaseSwapLeg", "object", "", ""),
                ("TermSwapLeg", "object", "", ""),
                ("BasePayReceive", "const", PayReceive.Pay, "Pay"),
                ("FxRate", "float"),
                ("FXForwardPointsCurve", "object", "", ""),
                ("HasInitialExchange", "bool", False, False),
                ("HasFinalExchange", "bool", False, False),
            ],
            [
                ("ReferenceDate", "date"),
                ("StartDate", "date"),
                ("EndDate", "date"),
                ("Notional", "float", 1000000, 1000000),
                ("BaseSwapLeg", "object", "", ""),
                ("TermSwapLeg", "object", "", ""),
                ("BasePayReceive", "const", PayReceive.Pay, "Pay"),
                ("FxRate", "float"),
                ("FXForwardPointsCurve", "object", "", ""),
                ("HasInitialExchange", "bool", False, False),
                ("HasFinalExchange", "bool", False, False),
            ],
        ]


class DefMcpBasisSwap(ItemDef):
    """同币种 float vs float basis swap（如 FR007 vs LPR1Y）。
    使用双 RateConvention 构造：Base/Term 两条浮动腿的 fixing index/frequency/day count/compounding 均可独立设置。
    仅支持同币种，无 FxRate 参数；跨币种场景请使用 McpXCcySwap。
    """

    def __init__(self):
        super().__init__()
        self.generate_xls_method = True
        self.custom_instance_func_raw = mcp_instance_list
        self.init_data = {
            "is_wrapper": True,
            "method_prefix": "BasisSwap",
            "data_fields": [
            ],
            "pyxll_def": {
            },
        }
        self.init_kv_list = [
            # EndDate 版
            [
                ("ReferenceDate", "date"),
                ("StartDate", "date"),
                ("EndDate", "date"),
                ("BaseRateConvention", "object"),
                ("TermRateConvention", "object"),
                ("BaseEstimationCurve", "object"),
                ("BaseDiscountCurve", "object"),
                ("TermEstimationCurve", "object"),
                ("TermDiscountCurve", "object"),
                ("PaymentCalendar", "object", McpCalendar("", "", ""), ""),
                ("Notional", "float", 1000000, 1000000),
                ("BaseMargin", "float", 0, 0),
                ("TermMargin", "float", 0, 0),
                ("BaseLegPayReceive", "const", PayReceive.Pay, "Pay"),
                ("TermFixingCalendar", "object", None, None),  # 可选，缺省=PaymentCalendar；仅两个 index 定盘日历不同时才需要
                ("BaseHistoryFixingDates", "objectlist", "[]"),
                ("BaseHistoryFixingRates", "objectlist", "[]"),
                ("TermHistoryFixingDates", "objectlist", "[]"),
                ("TermHistoryFixingRates", "objectlist", "[]"),
            ],
            # Tenor 版
            [
                ("ReferenceDate", "date"),
                ("StartDate", "date"),
                ("Tenor", "str"),
                ("BaseRateConvention", "object"),
                ("TermRateConvention", "object"),
                ("BaseEstimationCurve", "object"),
                ("BaseDiscountCurve", "object"),
                ("TermEstimationCurve", "object"),
                ("TermDiscountCurve", "object"),
                ("PaymentCalendar", "object", McpCalendar("", "", ""), ""),
                ("Notional", "float", 1000000, 1000000),
                ("BaseMargin", "float", 0, 0),
                ("TermMargin", "float", 0, 0),
                ("BaseLegPayReceive", "const", PayReceive.Pay, "Pay"),
                ("TermFixingCalendar", "object", None, None),
                ("BaseHistoryFixingDates", "objectlist", "[]"),
                ("BaseHistoryFixingRates", "objectlist", "[]"),
                ("TermHistoryFixingDates", "objectlist", "[]"),
                ("TermHistoryFixingRates", "objectlist", "[]"),
            ],
        ]


class DefMcpSchedule(ItemDef):

    def __init__(self):
        super().__init__()
        self.generate_xls_method = True
        self.init_data = {
            "is_wrapper": True,
            "method_prefix": "Schedule",
            "data_fields": [
            ],
            "pyxll_def": {
            },
        }
        self.init_kv_list = [
            [
                ("StartDate", "date"),
                ("EndDate", "date"),
                ("Frequency", "const", Frequency.Monthly, "Monthly"),
                ("Calendar", "object", McpCalendar("", "", "")),
                ("AdjusterRule", "const", DateAdjusterRule.ModifiedFollowing, "ModifiedFollowing"),
                ("KeepEndOfMonth", "bool", False, False),
                ("LongStub", "bool", False, False),
                ("EndStub", "bool", False, False),
                ("LastOpenday", "bool", False, False),
                ("AdjStartDate", "bool", True, True),
                ("AdjEndDate", "bool", True, True),
                ("StubDate", "date", "", ""),
                ("bothStub", "bool", False, False),
            ],
        ]


class DefMcpCustomForwardDefine(ItemDef):

    def __init__(self):
        super().__init__()
        self.generate_xls_method = False
        self.init_data = {
            "is_wrapper": True,
            "data_fields": [
            ],
            "pyxll_def": {
            },
        }
        self.init_kv_list = [
            [
                ("PackageName", "str"),
                ("BuySell", "str"),
                ("Strikes", "str"),
                ("StrikesStructure", "str"),
                ("ProductStructure", "str")
            ],
            [
                ("PackageName", "str"),
                ("BuySell", "str"),
                ("Strikes", "str"),
                ("Arguments", "str"),
                ("StrikesStructure", "str"),
                ("ProductStructure", "str")
            ],
        ]

        def custom_instance(*args, key=""):
            # result = []
            # # print(self.key, "args:", args)
            # for args_dict in args:
            #     # print(self.key, "args_dict:", args_dict)
            #     result.append(general_fwd_register.add(args_dict))
            result = general_fwd_register.add(list(args))
            # return f'{self.key} add: {result}'
            return result

        self.custom_instance_func_raw = custom_instance


class DefMcpCustomForward(ItemDef):

    def __init__(self):
        super().__init__()
        self.generate_xls_method = False
        self.custom_instance_func_raw = mcp_instance_list
        self.init_data = {
            "is_wrapper": True,
            "pkg": "mcp.forward.custom",
            "data_fields": [
            ],
            "pyxll_def": {
            },
        }
        self.init_kv_list = [
            [
                ("ReferenceDate", "date"),
                ("SpotPx", "str"),
                ("BuySell", "const"),
                ("ExpiryDate", "date"),
                ("MktData", "object"),
                ("SettlementDate", "date"),
                ("PremiumDate", "date"),
                ("Calendar", "object", McpCalendar("", "", "")),
                ("Notional", "float"),
                ("DayCounter", "const"),
                ("UndDayCounter", "const", DayCounter.Act360),
                ("LegsForwardPx", "str", 'None'),
                ("LegsAccRate", "str", 'None'),
                ("LegsUndRate", "str", 'None'),
                ("LegsVolatility", "str", 'None'),
                # ("DomesticCurve", "object"),
                # ("ForeignCurve", "object"),

                ("Package", "str"),
                ("StrikeDict", "object", {}),
                ("LegArgs", "object", {}),
            ],
            [
                ("ReferenceDate", "date"),
                ("SpotPx", "str"),
                ("BuySell", "const"),
                ("ExpiryDate", "date"),
                ("VolSurface", "object"),
                ("SettlementDate", "date"),
                ("PremiumDate", "date"),
                ("Calendar", "object", McpCalendar("", "", "")),
                ("Notional", "float"),

                ("Package", "str"),
                ("StrikeDict", "object", {}),
                ("LegArgs", "object", {}),
            ],
            [
                ("ReferenceDate", "date"),
                ("SpotPx", "str"),
                ("BuySell", "const"),
                ("ExpiryDate", "date"),
                ("VolSurface", "object"),
                ("SettlementDate", "date"),
                ("PremiumDate", "date"),
                ("Calendar", "object", McpCalendar("", "", "")),
                ("Notional", "float"),
                ("DayCounter", "const"),
                ("UndDayCounter", "const", DayCounter.Act360),
                ("DomesticCurve", "object"),
                ("ForeignCurve", "object"),

                ("Package", "str"),
                ("StrikeDict", "object", {}),
                ("LegArgs", "object", {}),
            ],

        ]


class DefMcpSwaptionCube(ItemDef):

    def __init__(self):
        super().__init__()
        self.generate_xls_method = False
        self.init_data = {
            "is_wrapper": True,
            "fmt": "VP",
            "data_fields": [
                ("ExpiryTenorPillars", "str"),
                ("StrikeOrSpreads", "float"),
                ("AtmExpiryPillars", "str"),
                ("AtmMaturityPillars", "str"),
            ],
            "pyxll_def": {
            },
        }
        self.init_kv_list = [
            [
                ("ReferenceDate", "date"),
                ("ExpiryTenorPillars", "objectlist"),
                ("StrikeOrSpreads", "objectlist"),
                ("VolSpreadOrVols", "objectlist"),
                ("AtmExpiryPillars", "objectlist"),
                ("AtmMaturityPillars", "objectlist"),
                ("AtmVols", "objectlist"),
                ("UsingSpread", "bool", True),
                ("StrikeInterpType", "const"),
                ("ExpiryMaturityInterpMethod", "const"),

                ("DayCounter", "const", DayCounter.Act365Fixed),
                ("Calendar", "object", McpCalendar("", "", "")),
                ("UnderlyingFixedPayFrequency", "const"),
                ("UnderlyingFloatFixingFrequency", "const"),
                ("UnderlyingFloatPayFrequency", "const"),
                ("UnderlyingYieldCurve", "object"),

                ("SABRApproxMethods", "const", 0),
                ("SABRSolverBump", "float", 0.01),
                ("SABRSolverTolerance", "float", 0.0001),
                ("SABRMaxIterations", "int", 200),
                ("SABRDirectionMethod", "int", 0),
                ("SABRSolverNRanShakes", "int", 100),
                ("SABRSolverShakeSize", "float", 0.001),
                ("MaxSpreadToATM", "float", 0.03),
                ("VolSpread", "bool", False),
            ],
            [
                ("ReferenceDate", "date"),
                ("ExpiryTenorPillars", "objectlist"),
                ("StrikeOrSpreads", "objectlist"),
                ("VolSpreadOrVols", "objectlist"),
                ("AtmExpiryPillars", "objectlist"),
                ("AtmMaturityPillars", "objectlist"),
                ("AtmVols", "objectlist"),
                ("UsingSpread", "bool", True),
                ("StrikeInterpType", "const", StrikeInterpType.SABR),
                ("ExpiryMaturityInterpMethod", "const", InterpolationMethod.LINEARINTERPOLATION),
                ("RateConvention", "object"),
                ("Calendar", "object"),
                ("FixedDiscountCurve", "object"),
                ("FloatEstimationCurve", "object"),
                ("FloatDiscountCurve", "object"),
                ("VolSpread", "bool", False),
            ],
        ]
        self.add_method_def({
            "method": "ZeroRate",
            "args": [
                ("curve", "object"),
                ("date", "date"),
            ],

        })


class DefMcpCapVolStripping(ItemDef):

    def __init__(self):
        super().__init__()
        self.generate_xls_method = False
        self.init_data = {
            "is_wrapper": True,
            "fmt": "VP",
            "data_fields": [
                ("Strikes", "float"),
                ("Terms", "str"),
            ],
            "pyxll_def": {
            },
        }
        self.init_kv_list = [
            [
                ("ReferenceDate", "date"),
                ("CapLagDay", "str"),
                ("RateLagDay", "str"),
                ("Tenor", "str"),
                ("Strikes", "objectlist"),
                ("Terms", "objectlist"),
                ("MarketQuotes", "objectlist"),
                ("EstimatingCurve", "object"),
                ("DiscountingCurve", "object"),
                ("Calendar", "object", McpCalendar("", "", "")),
                ("DayCounter", "const", DayCounter.Act365Fixed),
                ("CapVolPaymentType", "const", CapVolPaymentType.ARREARS),
                ("IROptionQuotation", "const", IROptionQuotation.PARYIELDVOL),
                ("InterpolationVariable", "const", InterpolationVariable.YIELDVOL),
                ("InterpolationMethod", "const", InterpolationMethod.LINEARINTERPOLATION),
                ("StrippingMethod", "const", StrippingMethod.METHOD2),
                ("NbrFuturesToUse", "int", 0)
            ],
        ]


class DefMcpCalendar(ItemDef):

    def __init__(self):
        super().__init__()
        self.generate_xls_method = False
        self.generate_tools_method = False
        self.init_data = {
            "is_wrapper": True,
            "fmt": "VP",
            "data_fields": [
                ("Strikes", "float"),
                ("Terms", "str"),
            ],
            "pyxll_def": {
            },
        }

        self.init_kv_list = [
            [
                ("Name", "str"),
                ("Codes", "str"),
                ("Dates", "str"),
            ],
            [
                ("Codes", "str"),
                ("Data", "str"),
                ("IsFile", "bool"),
            ],
        ]

    def find_match_kv_list(self, count, vals):
        if isinstance(vals[2], bool):
            return self.init_kv_list[1]
        else:
            return self.init_kv_list[0]


class DefMcpParametricCurve(ItemDef):

    def __init__(self):
        super().__init__()
        self.custom_instance_func_raw = mcp_instance_list
        self.init_data = {
            "is_wrapper": True,
            "fmt": "VP|HD",
            "method_prefix": "ParametricCurve",
            "data_fields": [
                ("MaturityDates", "date"),
                ("Rates", "float"),
                ("MaturityDate", "date"),
                ("Yield", "float"),
            ],
            "pyxll_def": {
            },
        }
        self.kv_const_dict = {
            'ParamCurveModel': 'ParametricCurveModel',
            'Method': 'InterpolationMethod',
        }
        self.init_kv_list = [
            [
                ("ReferenceDate", "date"),
                ("MaturityDates", "objectlist"),
                ("Rates", "objectlist"),
                ("ParamCurveModel", "const", ParametricCurveModel.NS, "NS"),
                ("DayCounter", "const", DayCounter.Act365Fixed, "Act365Fixed"),
            ],
            [
                ("ReferenceDate", "date"),
                ("MaturityDate", "objectlist"),
                ("Yield", "objectlist"),
                ("ParamCurveModel", "const", ParametricCurveModel.NS, "NS"),
                ("DayCounter", "const", DayCounter.Act365Fixed, "Act365Fixed"),
            ],
        ]
        self.add_method_def({
            "method": "ZeroRate",
            "args": [
                ("curve", "object"),
                ("date", "date"),
                ("dayCounter", "const", DayCounter.NONE, "NONE"),
                # compounding=True/frequency=366(Continuous) 与底层默认一致，不影响既有公式
                # frequency 可选 0(单利)/1(年复利)/2(半年复利 BEY)/4(季度复利)/366(连续复利)
                ("compounding", "bool", True, True),
                ("frequency", "const", Frequency.Continuous, "Continuous"),
            ],

        })
        self.add_method_def({
            "method": "DiscountFactor",
            "args": [
                ("curve", "object"),
                ("date", "date"),
            ]
        })
        self.add_method_def({
            "method": "ForwardRate",
            "args": [
                ("curve", "object"),
                ("StartDate", "date"),
                ("EndDate", "date"),
                ("DayCounter", "const", DayCounter.Act360, "Act360"),
                ("Compounding", "bool", True),
                ("Frequency", "const", Frequency.Continuous, "Continuous"),
            ],
        })
        self.add_method_def({
            "method": "Parameters",
            "args": [
                ("curve", "object"),
            ]
        })


class DefMcpBondCurve(ItemDef):

    def __init__(self):
        super().__init__()
        self.custom_instance_func_raw = mcp_instance_list
        self.init_data = {
            "is_wrapper": True,
            "fmt": "VP|HD",
            "method_prefix": "BondCurve",
            "data_fields": [
                ("MaturityDates", "date"),
                ("tenors", "str"),
                ("Frequencies", "int"),
                ("Coupons", "float"),
                ("YieldsOrDirtyPrice", "float"),
                ("BumpAmounts", "float"),
                ("BUses", "intbool"),
                ("TimeToMaturities", "float"),
                ("ZeroRates", "float"),
                ("DiscountFactors", "float"),
                ("ParYields", "float"),
            ],
            "pyxll_def": {
            },
        }
        self.kv_const_dict = {
        }
        self.init_kv_list = [
            [
                ("SettlementDate", "date"),
                # ("Mode", "str", 'frb'),
                ("InterpolatedVariable", "const", InterpolatedVariable.SIMPLERATES, 'SIMPLERATES'),
                ("InterpolationMethod", "const", InterpolationMethod.LINEARINTERPOLATION, 'LINEARINTERPOLATION'),
                # ("UseGlobalSolver", "bool", False, False),
                ("DayCounter", "const", DayCounter.Act365Fixed, "Act365Fixed"),

                # ("SettlementDate", "date"),
                ("MaturityDates", "objectlist"),
                ("Frequencies", "objectlist", '[]', '[]'),
                ("Coupons", "objectlist", '[]', '[]'),
                ("YieldsOrDirtyPrice", "objectlist"),
                # ("DayCounter", "const", DayCounter.Act365Fixed, "Act365Fixed"),
                ("IsYield", "bool", True, True),
                ("BumpAmounts", "objectlist", '[]', '[]'),
                ("BUses", "objectlist", '[]', '[]'),
                ("Calendar", "object", McpCalendar("", "", ""), ""),
            ],
            [
                ("SettlementDate", "date"),
                ("CalibrationSet", "object"),
                ("InterpolatedVariable", "const"),
                ("InterpolationMethod", "const"),
                ("DayCounter", "const"),
            ],
            [
                ("SettlementDate", "date"),
                ("TimeToMaturities", "objectlist"),
                ("InterpolatedVariable", "const"),
                ("InterpolationMethod", "const"),
                ("Calendar", "object", McpCalendar("", "", ""), ""),
                ("DayCounter", "const"),
                ("ZeroRates", "objectlist", '[]', '[]'),
                ("DiscountFactors", "objectlist", '[]', '[]'),
                ("ParYields", "objectlist", '[]', '[]'),
            ],
            [
                ("SettlementDate", "date"),
                ("InterpolatedVariable", "const"),
                ("InterpolationMethod", "const"),
                ("Calendar", "object"),
                ("DayCounter", "const"),
                ("tenors", "plainlist"),
                ("ZeroRates", "objectlist", '[]', '[]'),
                ("DiscountFactors", "objectlist", '[]', '[]'),
                ("ParYields", "objectlist", '[]', '[]'),
            ],
        ]

        self.add_method_def({
            "method": "ZeroRate",
            "args": [
                ("curve", "object"),
                ("date", "date"),
                ("dayCounter", "const", DayCounter.NONE, "NONE"),
                # compounding=True/frequency=366(Continuous) 与底层默认一致，不影响既有公式
                # frequency 可选 0(单利)/1(年复利)/2(半年复利 BEY)/4(季度复利)/366(连续复利)
                ("compounding", "bool", True, True),
                ("frequency", "const", Frequency.Continuous, "Continuous"),
            ],

        })
        self.add_method_def({
            "method": "DiscountFactor",
            "args": [
                ("curve", "object"),
                ("date", "date"),
            ]
        })
        self.add_method_def({
            "method": "ForwardRate",
            "args": [
                ("curve", "object"),
                ("StartDate", "date"),
                ("EndDate", "date"),
                ("DayCounter", "const", DayCounter.Act360, "Act360"),
                ("Compounding", "bool", True),
                ("Frequency", "const", Frequency.Continuous, "Continuous"),
            ],
        })

        self.add_method_def({
            "method": "ParRate",
            "args": [
                ("curve", "object"),
                ("date", "date"),
                # compounding=True/frequency=2(Semiannual) 与底层 BEY 口径一致, 不影响既有公式
                # frequency 可选 1(年复利)/2(半年复利 BEY)/4(季度复利)/366(连续复利); False 为单利口径
                ("compounding", "bool", True, True),
                ("frequency", "const", Frequency.Semiannual, "Semiannual"),
            ]
        })


class DefMcpBondSpreadCurve(ItemDef):

    def __init__(self):
        super().__init__()
        self.custom_instance_func_raw = mcp_instance_list
        self.init_data = {
            "is_wrapper": True,
            "fmt": "VP|HD",
            "method_prefix": "BondSpreadCurve",
            "data_fields": [],
            "pyxll_def": {},
        }
        # 说明：
        # 1) McpBondSpreadCurve(BenchmarkCurve, ReferenceDate, SpreadAdjustedCurve)
        # 2) McpBondSpreadCurve(ReferenceDate, CalibrationSet, BenchmarkCurve, ...)
        self.init_kv_list = [
            [
                ("BenchmarkCurve", "object"),
                ("ReferenceDate", "date"),
                ("SpreadAdjustedCurve", "object"),
            ],
            [
                ("ReferenceDate", "date"),
                ("CalibrationSet", "object"),
                ("BenchmarkCurve", "object"),
                ("InterpolatedVariable", "const", InterpolatedVariable.ZERORATES, "ZERORATES"),
                ("InterpolationMethod", "const", InterpolationMethod.LINEARINTERPOLATION, "LINEARINTERPOLATION"),
                ("DayCounter", "const", DayCounter.Act365Fixed, "Act365Fixed"),
                ("UseGlobalSolver", "bool", False, False),
                ("SpreadExtrapolation", "int", 0, 0),
            ],
            [
                ("ReferenceDate", "date"),
                ("CalibrationSet", "object"),
                ("BenchmarkCurve", "object"),
            ],
        ]

        self.add_method_def({
            "method": "zeroSpread",
            "args": [
                ("curve", "object"),
                ("date", "date"),
            ]
        })
        self.add_method_def({
            "method": "yieldSpread",
            "args": [
                ("curve", "object"),
                ("date", "date"),
            ]
        })
        self.add_method_def({
            "method": "ZeroRate",
            "args": [
                ("curve", "object"),
                ("date", "date"),
                ("dayCounter", "const", DayCounter.NONE, "NONE"),
                # compounding=True/frequency=366(Continuous) 与底层默认一致，不影响既有公式
                # frequency 可选 0(单利)/1(年复利)/2(半年复利 BEY)/4(季度复利)/366(连续复利)
                ("compounding", "bool", True, True),
                ("frequency", "const", Frequency.Continuous, "Continuous"),
            ]
        })
        self.add_method_def({
            "method": "DiscountFactor",
            "args": [
                ("curve", "object"),
                ("date", "date"),
            ]
        })
        self.add_method_def({
            "method": "ForwardRate",
            "args": [
                ("curve", "object"),
                ("StartDate", "date"),
                ("EndDate", "date"),
                ("DayCounter", "const", DayCounter.Act360, "Act360"),
                ("Compounding", "bool", True),
                ("Frequency", "const", Frequency.Continuous, "Continuous"),
            ],
        })
        self.add_method_def({
            "method": "ParRate",
            "args": [
                ("curve", "object"),
                ("date", "date"),
                # compounding=True/frequency=2(Semiannual) 与底层 BEY 口径一致, 不影响既有公式
                # frequency 可选 1(年复利)/2(半年复利 BEY)/4(季度复利)/366(连续复利); False 为单利口径
                ("compounding", "bool", True, True),
                ("frequency", "const", Frequency.Semiannual, "Semiannual"),
            ]
        })
        self.add_method_def({
            "method": "setBenchmarkCurve",
            "args": [
                ("curve", "object"),
                ("benchmarkCurve", "object"),
            ]
        })
        self.add_method_def({
            "method": "getBenchmarkCurve",
            "args": [
                ("curve", "object"),
            ]
        })


class DefMcpRounder(ItemDef):

    def __init__(self):
        super().__init__()
        self.generate_xls_method = False
        self.init_data = {
            "is_wrapper": True,
            "data_fields": [
            ],
            "pyxll_def": {
            },
        }
        self.init_kv_list = [
            [
            ]
        ]


class DefMcpHistoricalRates(ItemDef):

    def __init__(self):
        super().__init__()
        self.generate_xls_method = False
        self.custom_instance_func_raw = mcp_instance_list
        self.init_data = {
            "is_wrapper": False,
            "fmt": "HD",
            "data_fields": [
                ("date", "date"),
                ("rate", "float"),
            ],
            "pyxll_def": {},
        }
        self.init_kv_list = [
            [
                ("date", "plainlist"),
                ("rate", "plainlist"),
            ],
        ]


def _rate_convention_kv_to_dict(args):
    """
    Parse args to dict. Supports:
    - Single string: ("FR007",)
    - KV rows: ([["ConventionName","FR007"]],) or (row1, row2, ...) each row = [key, value]
    - Excel range: ([[k,v],[k,v]],) - nested list
    """
    if not args:
        return {}
    from mcp.utils.excel_utils import pf_nd_arrary_or_list
    result = {}
    # Single string: ("FR007",)
    if len(args) == 1 and isinstance(args[0], str):
        return {"ConventionName": args[0].strip()}
    # Collect all rows: args can be (row1, row2, ...) or ([[row1],[row2]],)
    rows = []
    flat = pf_nd_arrary_or_list(args)
    if isinstance(flat, (list, tuple)):
        for item in flat:
            item = pf_nd_arrary_or_list(item)
            if isinstance(item, (list, tuple)):
                # item is a row [k,v] or nested [[k,v],[k,v]]
                if len(item) >= 2 and not (isinstance(item[0], (list, tuple)) or isinstance(item[1], (list, tuple))):
                    rows.append(item)  # [k, v]
                else:
                    for row in item:
                        row = pf_nd_arrary_or_list(row)
                        if isinstance(row, (list, tuple)) and len(row) >= 2:
                            rows.append(row)
                        elif isinstance(row, str):
                            result["ConventionName"] = row
            elif isinstance(item, str):
                result["ConventionName"] = item
    for row in rows:
        if len(row) >= 2:
            result[str(row[0]).strip()] = row[1]
        elif len(row) == 1:
            result["ConventionName"] = row[0]
    # Alias: common typos/truncation for ConventionName (e.g. ConventionNan in narrow Excel cell)
    _cn_aliases = ("conventionnan", "conventionnme", "conventioname", "conventionna")
    for k in list(result.keys()):
        if str(k).lower().strip() in _cn_aliases:
            result["ConventionName"] = result.pop(k)
            break
    return result


# KV key -> (set_method, type_for_parse). type: 'int','float','bool','const:EnumName'
_RC_SET_MAP = {
    "swapstartlag": ("setSwapStartLag", "int"),
    "marginbps": ("setMarginBps", "float"),
    "margin": ("setMarginBps", "float"),
    "fixedpaymentfrequency": ("setFixedFrequency", "const:Frequency"),
    "fixedfrequency": ("setFixedFrequency", "const:Frequency"),
    "floatpaymentfrequency": ("setFloatFrequency", "const:Frequency"),
    "floatfrequency": ("setFloatFrequency", "const:Frequency"),
    "fixinadvance": ("setFixInAdvance", "bool"),
    "fixdaysbackward": ("setFixDaysBackward", "int"),
    "useindexestimation": ("setUseIndexEstimation", "bool"),
    "fixedpaymentdateadjuster": ("setFixedPaymentDateAdjuster", "const:DateAdjusterRule"),
    "fixedresetdateadjuster": ("setFixedResetDateAdjuster", "const:DateAdjusterRule"),
    "floatpaymentdateadjuster": ("setFloatPaymentDateAdjuster", "const:DateAdjusterRule"),
    "floatresetdateadjuster": ("setFloatResetDateAdjuster", "const:DateAdjusterRule"),
    "fixeddaycounter": ("setFixedDayCount", "const:DayCounter"),
    "fixeddaycount": ("setFixedDayCount", "const:DayCounter"),
    "floatdaycounter": ("setFloatDayCount", "const:DayCounter"),
    "floatdaycount": ("setFloatDayCount", "const:DayCounter"),
    "fixingfrequency": ("setFixingFrequency", "const:Frequency"),
    "fixingdateadjuster": ("setFixingDateAdjuster", "const:DateAdjusterRule"),
    "fixedpaymentlag": ("setFixedPaymentLag", "int"),
    "floatpaymentlag": ("setFloatPaymentLag", "int"),
}


def _rate_convention_create(*args, key=""):
    """
    Create McpRateConvention. Supports:
    1) Single param: ConventionName (e.g. FR007)
    2) KV: ConventionName only
    3) KV: ConventionName + set params (modify predefined)
    4) KV: New/temp convention: BaseConvention + params (e.g. BaseConvention|FR007, SwapStartLag|7)
    5) KV: New name + params: ConventionName|OH-NEW, BaseConvention|FR007, SwapStartLag|7
    """
    from mcp.wrapper import McpRateConvention
    d = _rate_convention_kv_to_dict(args)
    if not d:
        raise Exception("McpRateConvention: Missing ConventionName or BaseConvention")
    name = str(d.get("ConventionName", d.get("conventionname", ""))).strip()
    base_from_kv = str(d.get("BaseConvention", d.get("baseconvention", ""))).strip()
    # Derive base: 1) explicit BaseConvention, 2) from name (FR007-NEW->FR007)
    base_name = base_from_kv if base_from_kv else (name.split("-")[0].strip() if "-" in name else name)
    # Create: try name first, then base_name, then base_from_kv
    try_order = []
    if name:
        try_order.append(name)
    if base_name and base_name not in try_order:
        try_order.append(base_name)
    if base_from_kv and base_from_kv not in try_order:
        try_order.append(base_from_kv)
    if not try_order:
        raise Exception("McpRateConvention: ConventionName or BaseConvention is required")
    rc = None
    try_name_used = None
    last_err = None
    for try_name in try_order:
        try:
            rc = McpRateConvention(try_name)
            try_name_used = try_name
            break
        except Exception as e:
            last_err = e
            if "Unknown" in str(e) and len(try_order) > 1:
                continue
            if "Unknown" in str(e):
                raise Exception(
                    f"McpRateConvention: '{name}' 不在预定义列表中。"
                    f"请添加 BaseConvention 行指定基准（如 BaseConvention|FR007）以创建临时 convention。"
                ) from e
            raise
    if rc is None:
        raise Exception(
            f"McpRateConvention: 无法创建。已尝试: {try_order}。"
            f"请添加 BaseConvention（如 FR007）以创建临时 convention。"
        ) from last_err
    # Set custom name when ConventionName differs from base (C++ setName)
    if name and name != try_name_used and hasattr(rc, 'setName'):
        try:
            rc.setName(name)
        except Exception as ex:
            import logging
            logging.warning(f"McpRateConvention setName({name}): {ex}")
    # Apply set methods (skip ConventionName, BaseConvention)
    for k, v in d.items():
        k_lower = str(k).lower().strip()
        if k_lower in ("conventionname", "baseconvention"):
            continue
        if k_lower not in _RC_SET_MAP:
            continue
        set_method, vtype = _RC_SET_MAP[k_lower]
        try:
            if vtype == "int":
                val = int(float(v))
            elif vtype == "float":
                val = float(v)
            elif vtype == "bool":
                val = v in (True, "true", "True", "Y", "y", 1, "1")
            elif vtype.startswith("const:"):
                enum_name = vtype.split(":")[1]
                val = enum_wrapper.parse2(v, enum_name)
            else:
                val = v
            getattr(rc, set_method)(val)
        except Exception as ex:
            import logging
            logging.warning(f"McpRateConvention set {k}={v}: {ex}")
    return rc


class DefMcpRateConvention(ItemDef):

    def __init__(self):
        super().__init__()
        self.custom_instance_func_raw = _rate_convention_create
        self.generate_xls_method = False
        self.init_data = {
            "is_wrapper": True,
            "method_prefix": "rc",
            "data_fields": [],
            "pyxll_def": {},
        }
        self.init_kv_list = [
            [
                ("ConventionName", "str"),
            ],
        ]


class DefMcpEuropeanDigital(ItemDef):

    def __init__(self):
        super().__init__()
        self.custom_instance_func_raw = mcp_instance_list
        self.init_data = {
            "is_wrapper": True,
            "pkg": "mcp.forward.custom",
            "method_prefix": "EuropeanDigital",
            "data_fields": [
            ],
            "pyxll_def": {
            },
        }
        self.init_kv_list = [
            [
                ("ReferenceDate", "date"),
                ("DigitalType", "const"),
                ("BuySell", "const"),
                ("SpotPx", "float"),
                ("StrikePx", "float"),
                ("Volatility", "float"),
                ("ExpiryDate", "date"),
                ("DeliveryDate", "date"),
                ("DomesticRate", "float"),
                ("ForeignRate", "float"),
                ("PremiumDate", "date"),
                ("Payoff", "float", 100000),
                ("Calendar", "object", McpCalendar("", "", ""), ""),
                ("DayCounter", "const", DayCounter.Act365Fixed, "Act365Fixed"),
                ("PricingMethod", "const", PricingMethod.BLACKSCHOLES),
                ("ReplicateDelta", "float", 0.0001),
                ("RR25", "float", 0.0),
                ("BF25", "float", 0.0),
                ("ExerciseStyle", "const", 0, "EUROPEAN")
            ],
            # [
            #     ("ReferenceDate", "date"),
            #     ("DigitalType", "const"),
            #     ("BuySell", "const"),
            #     ("SpotPx", "float"),
            #     ("StrikePx", "float"),
            #     ("Volatility", "float"),
            #     ("ExpiryDate", "date"),
            #     ("SettlementDate", "date"),
            #     ("AccRate", "float"),
            #     ("UndRate", "float"),
            #     ("PremiumDate", "date"),
            #     ("FaceAmount", "float", 1),
            #     ("Payoff", "float", 1, 1),
            #     ("Calendar", "object", McpCalendar("", "", ""), ""),
            #     ("DayCounter", "const", DayCounter.Act365Fixed, "Act365Fixed"),
            #     ("Barrier", "float", 0.0),
            #     ("PricingMethod", "const"),
            #     # ("AdjTable", "object", McpAdjustmentTable()),
            #     ("AdjustmentOnly", "bool", False, False),
            # ],
        ]
        self.add_method_range(
            ["GetSpot", "GetForward", "GetVol", "GetStrike", "GetAccRate", "GetUndRate"],
            {
                "args": [
                    ("obj", "object"),
                ],
            }
        )


class DefMcpDoubleDigitalOption(ItemDef):
    """双障碍数字期权，三签名：1)FXVolSurface 2)VolSurface(EQ/COMM) 3)直接v,r,q,s。KV列表对应M类签名。

    使用 mcp.wrapper.McpDoubleDigitalOption（Python wrapper）以补齐 PV(isAmount)
    接口，让 Excel McpPV(...) 与估值引擎 PV = DiscMarketValue(true) 一致。
    """

    def __init__(self):
        super().__init__()
        self.init_data = {"is_wrapper": True, "pkg": "mcp.wrapper", "data_fields": [], "pyxll_def": {}}
        self.custom_instance_func_raw = mcp_instance_list
        self.kv_const_dict = {"DoubleType": "DoubleDigitalType", "BuySell": "BuySell", "ExerciseStyle": "ExerciseStyle"}
        self.init_kv_list = [
            # 签名1: FXVolSurface (FX)
            [
                ("ReferenceDate", "date"),
                ("PremiumDate", "date"),
                ("ExpiryDate", "date"),
                ("DeliveryDate", "date"),
                ("LowBarrier", "float"),
                ("HighBarrier", "float"),
                ("DoubleType", "const"),
                ("BuySell", "const"),
                ("FXVolSurface", "object"),
                ("Payoff", "float", 1000000, 1000000),
                ("LowRebate", "float", 0, 0),
                ("HighRebate", "float", 0, 0),
                ("ExerciseStyle", "const", 0, "EUROPEAN"),
            ],
            # 签名2: VolSurface (Equity/Commodity)
            [
                ("ReferenceDate", "date"),
                ("PremiumDate", "date"),
                ("ExpiryDate", "date"),
                ("DeliveryDate", "date"),
                ("LowBarrier", "float"),
                ("HighBarrier", "float"),
                ("DoubleType", "const"),
                ("BuySell", "const"),
                ("VolSurface", "object"),
                ("Payoff", "float", 1000000, 1000000),
                ("LowRebate", "float", 0, 0),
                ("HighRebate", "float", 0, 0),
                ("ExerciseStyle", "const", 0, "EUROPEAN"),
            ],
            # 签名3: 直接 v,r,q,s (spot, volatility, accRate, undRate)
            [
                ("ReferenceDate", "date"),
                ("PremiumDate", "date"),
                ("ExpiryDate", "date"),
                ("DeliveryDate", "date"),
                ("LowBarrier", "float"),
                ("HighBarrier", "float"),
                ("DoubleType", "const"),
                ("BuySell", "const"),
                ("SpotPx", "float"),
                ("Volatility", "float"),
                ("AccRate", "float"),
                ("UndRate", "float"),
                ("Payoff", "float", 1000000, 1000000),
                ("LowRebate", "float", 0, 0),
                ("HighRebate", "float", 0, 0),
                ("ExerciseStyle", "const", 0, "EUROPEAN"),
            ],
        ]


class DefMcpVanillaBarriers(ItemDef):

    def __init__(self):
        super().__init__()
        self.custom_instance_func_raw = mcp_instance_list
        self.init_data = {
            "is_wrapper": True,
            "pkg": "mcp.forward.custom",
            "method_prefix": "Vb",
            "data_fields": [
            ],
            "pyxll_def": {
            },
        }
        self.init_kv_list = [
            [
                ("OptionType", "const"),
                ("BarrierType", "const"),
                ("ReferenceDate", "date"),
                ("SpotPx", "float"),
                ("BuySell", "const"),
                ("ExpiryDate", "date"),
                ("DeliveryDate", "date"),
                ("StrikePx", "float"),
                ("Barrier", "float"),
                ("DomesticRate", "float"),
                ("ForeignRate", "float"),
                ("Volatility", "float"),
                ("FaceValue", "float", 1000000),
                ("Rebate", "float", 0.0),
                ("PricingMethod", "const", PricingMethod.BLACKSCHOLES),
                ("OptionExpiryNature", "const", OptionExpiryNature.EUROPEAN),
                ("BarrierLow", "float", 0.0),
                ("RR25", "float", 0.0),
                ("BF25", "float", 0.0),
                ("DiscreteFactor", "float", 0.5826),
                ("DiscreteAdjusted", "bool", False),
                ("Calendar", "object", McpCalendar("", "", ""), ""),
                ("DayCounter", "const", DayCounter.Act365Fixed, "Act365Fixed"),
                ("PremiumDate", "date"),
                ("NumSimulation", "int", 10000),
                # VV-only conventions (used when PricingMethod is VANNAVOLGA / VANNAVOLGACM).
                # Defaults match BBG OVML for FX tenor <=1Y (USDCNH/JPYCNH validated 2026-05).
                # 对应 C++ 入口签名 VanillaBarriers(..., DeltaType, bool, ATMVolType).
                ("DeltaType", "const", DeltaType.SPOT_DELTA, "SPOT_DELTA"),
                ("PremiumAdjusted", "bool", True),
                ("ATMVolType", "const", ATMVolType.DELTA_NEUTRAL_STRADDLE, "DELTA_NEUTRAL_STRADDLE"),
            ],
            # 用 FXVolSurface 作为市场数据来源（对应 mcplib.h 第 1263 行的 12 参构造）
            # 加入 PricingMethod（默认 BLACKSCHOLES），设为 VANNAVOLGA 时 RR25/BF25 自动从曲面提取
            [
                ("OptionType", "const"),
                ("BarrierType", "const"),
                ("BuySell", "const"),
                ("ReferenceDate", "date"),
                ("PremiumDate", "date"),
                ("ExpiryDate", "date"),
                ("DeliveryDate", "date"),
                ("StrikePx", "float"),
                ("Barrier", "float"),
                ("FXVolSurface", "object"),
                ("FaceValue", "float", 1000000.0),
                ("Rebate", "float", 0.0),
                ("PricingMethod", "const", PricingMethod.BLACKSCHOLES),
            ],
            # [
            #     ("CallPut", "const"),
            #     ("BarrierType", "const"),
            #     ("ReferenceDate", "date"),
            #     ("SpotPx", "float"),
            #     ("BuySell", "const"),
            #     ("ExpiryDate", "date"),
            #     ("DeliveryDate", "date"),
            #     ("StrikePx", "float"),
            #     ("Barrier", "float"),
            #     ("AccRate", "float"),
            #     ("UndRate", "float"),
            #     ("Volatility", "float"),
            #     ("FaceAmount", "float", 1),
            #     ("Rebate", "float", 0.0),
            #     ("PricingMethod", "const", PricingMethod.BLACKSCHOLES),
            #     ("AdjTable", "object", McpAdjustmentTable()),
            #     ("AdjustmentOnly", "bool", False),
            #     ("Calendar", "object", McpCalendar("", "", ""), ""),
            #     ("DayCounter", "const", DayCounter.Act365Fixed, "Act365Fixed"),
            #     ("PremiumDate", "date"),
            # ],
            # [
            #     ("OptionType", "const"),
            #     ("BarrierType", "const"),
            #     ("StrikePx", "float"),
            #     ("Barrier", "float"),
            #     ("Volatility", "float"),
            #     ("TimeToExpiry", "float"),
            #     ("TimeToSettlement", "float"),
            #     ("DomesticRate", "float"),
            #     ("ForeignRate", "float"),
            #     ("SpotPx", "float"),
            #     ("BuySell", "const", 0.0),
            #     ("Rebate", "float"),
            #     ("FaceValue", "float"),
            #     ("PricingMethod", "const", PricingMethod.BLACKSCHOLES),
            #     ("AdjTable", "object", MAdjustmentTable()),
            #     ("AdjustmentOnly", "bool", False),
            # ],
        ]
        self.add_method_range(
            ["GetSpot", "GetForward", "GetVol", "GetStrike", "GetAccRate", "GetUndRate"],
            {
                "args": [
                    ("obj", "object"),
                ],
            }
        )


class DefMcpFXForwardPointsCurve(ItemDef):

    def __init__(self):
        super().__init__()
        self.custom_instance_func_raw = mcp_instance_list
        self.generate_xls_method = False
        self.init_data = {
            "is_wrapper": True,
            "method_prefix": "Fxfpc",
            "data_fields": [
                ("Tenors", "str"),
                ("FXForwardPoints", "float"),
                ("FXOutright", "float"),
            ],
            "pyxll_def": {
            },
        }
        self.init_kv_list = [
            [
                ("ReferenceDate", "date"),
                ("Tenors", "plainlist"),
                ("FXForwardPoints", "plainlist"),
                ("FXSpotRate", "float"),
                ("Method", "const", InterpolationMethod.LINEARINTERPOLATION),
                ("Calendar", "object", McpCalendar("", "", "")),
                ("Pair", "str", "USD/CNY"),
                ("ScaleFactor", "float"),
            ],
            [
                ("ReferenceDate", "date"),
                ("Tenors", "plainlist"),
                ("FXForwardPoints", "plainlist"),
                ("FXSpotRate", "float"),
                ("Method", "const", InterpolationMethod.LINEARINTERPOLATION),
                ("Calendar", "object", McpCalendar("", "", "")),
                ("Pair", "str", "USD/CNY"),
            ],
            [
                ("ReferenceDate", "date"),
                ("Tenors", "plainlist"),
                ("FXForwardPoints", "plainlist"),
                ("FXSpotRate", "float"),
                ("Method", "const", InterpolationMethod.LINEARINTERPOLATION),
                ("Calendar", "object", McpCalendar("", "", "")),
                ("ScaleFactor", "float"),
            ],
            [
                ("ReferenceDate", "date"),
                ("FXOutright", "plainlist"),
                ("Tenors", "plainlist"),
                ("Method", "const", InterpolationMethod.LINEARINTERPOLATION),
                ("Calendar", "object", McpCalendar("", "", "")),
                ("FXSpotRate", "float"),
                ("ScaleFactor", "float"),
            ],
            [
                ("Leg1", "object"),
                ("Leg2", "object"),
                ("ScaleFactor", "float", 0.0),
                ("SpotRate", "float", 0.0),
            ],
            [
                ("Leg1", "object"),
                ("Leg2", "object"),
                ("Calendar", "object", None),
                ("CrossPair", "str", ""),
                ("ScaleFactor", "float", 0.0),
                ("SpotRate", "float", 0.0),
            ],
            [
                ("Leg1", "object"),
                ("Leg2", "object"),
                ("Calendar", "object", None),
                ("ReferenceDate", "date", None),
                ("CrossPair", "str", ""),
                ("ScaleFactor", "float", 0.0),
                ("SpotRate", "float", 0.0),
            ],
        ]
        self.add_method_range(
            ["TOForwardPoint", "TOForwardOutright", "TimeOptionDate"],
            {
                "args": [
                    ("curve", "object"),
                    ("startDate", "date"),
                    ("endDate", "date"),
                    ("findMax", "bool", True),
                ],
            }
        )
        self.add_method_def({
            "method": "GetPair",
            "args": [
                ("curve", "object"),
            ],
        })
        self.add_method_def({
            "method": "GetReferenceDate",
            "args": [
                ("curve", "object"),
            ],
        })
        self.add_method_def({
            "method": "GetSpotDate",
            "args": [
                ("curve", "object"),
            ],
        })


class DefMcpFXForwardPointsCurve2(ItemDef):

    def __init__(self):
        super().__init__()
        self.custom_instance_func_raw = mcp_instance_list
        self.generate_xls_method = True
        self.init_data = {
            "is_wrapper": True,
            "method_prefix": "Fxfpc2",
            "data_fields": [
                ("Tenors", "str"),
                ("BidForwardPoints", "float"),
                ("AskForwardPoints", "float"),
            ],
            "pyxll_def": {
            },
        }
        self.init_kv_list = [
            [
                ("ReferenceDate", "date"),
                ("BidFXSpotRate", "float"),
                ("BidForwardPoints", "plainlist"),
                ("AskFXSpotRate", "float"),
                ("AskForwardPoints", "plainlist"),
                ("Tenors", "plainlist"),
                ("Method", "const", InterpolationMethod.LINEARINTERPOLATION),
                ("Calendar", "object", McpCalendar("", "", "")),
                ("Pair", "str", "USD/CNY"),
                ("ScaleFactor", "float", 0.0),
                ("QuoteUnit", "float", 0.0),
            ],
            [
                ("ReferenceDate", "date"),
                ("BidFXSpotRate", "float"),
                ("BidForwardPoints", "plainlist"),
                ("AskFXSpotRate", "float"),
                ("AskForwardPoints", "plainlist"),
                ("Tenors", "plainlist"),
                ("Method", "const", InterpolationMethod.LINEARINTERPOLATION),
                ("Calendar", "object", McpCalendar("", "", "")),
                ("Pair", "str", "USD/CNY"),
            ],
            [
                ("ReferenceDate", "date"),
                ("BidFXSpotRate", "float"),
                ("BidForwardPoints", "plainlist"),
                ("AskFXSpotRate", "float"),
                ("AskForwardPoints", "plainlist"),
                ("Tenors", "plainlist"),
                ("Method", "const", InterpolationMethod.LINEARINTERPOLATION),
                ("Calendar", "object", McpCalendar("", "", "")),
                ("ScaleFactor", "float", 10000.0),
                ("QuoteUnit", "float", 1.0),
            ],
            [
                ("ReferenceDate", "date"),
                ("BidSpot", "float"),
                ("AskSpot", "float"),
                ("ForeignCurve2", "object"),
                ("DomesticCurve2", "object"),
                ("Calendar", "object", McpCalendar("", "", "")),
                ("ScaleFactor", "float", 10000.0),
                ("QuoteUnit", "float", 1.0),
            ],
            [
                ("ReferenceDate", "date"),
                ("FxForwardPointsCurve2_1", "object"),
                ("FxForwardPointsCurve2_2", "object"),
                ("IsCur1Direct", "bool"),
                ("IsCur2Direct", "bool"),
                ("BidFXSpotRate", "float"),
                ("AskFXSpotRate", "float"),
                ("CrossFXSpot", "bool"),
                ("Calendar", "object", McpCalendar("", "", "")),
                ("SpotDate", "date"),
                ("ScaleFactor", "float", 10000.0),
                ("QuoteUnit", "float", 1.0),
                ("QuoteUnit1", "float", 1.0),
                ("QuoteUnit2", "float", 1.0),
            ],
            [
                ("ReferenceDate", "date"),
                ("Leg1", "object"),
                ("Leg2", "object"),
                ("IsCur1Direct", "bool"),
                ("IsCur2Direct", "bool"),
                ("BidFXSpotRate", "float"),
                ("AskFXSpotRate", "float"),
                ("CrossFXSpot", "bool"),
                ("Calendar", "object", McpCalendar("", "", "")),
                ("SpotDate", "date"),
                ("ScaleFactor", "float", 10000.0),
                ("QuoteUnit", "float", 1.0),
                ("QuoteUnit1", "float", 1.0),
                ("QuoteUnit2", "float", 1.0),
            ],
        ]

        self.add_method_range(
            ["FXForwardPoints", "FXForwardOutright"],
            {
                "args": [
                    ("curve", "object"),
                    ("date", "date"),
                    ("bidMidAsk", "str", 'MID'),
                ],
            }
        )
        self.add_method_range(
            ["TOForwardPoint", "TOForwardOutright", "TimeOptionDate"],
            {
                "args": [
                    ("curve", "object"),
                    ("startDate", "date"),
                    ("endDate", "date"),
                    ("findMax", "bool", True),
                    ("bidMidAsk", "str", 'MID'),
                ],
            }
        )
        self.add_method_range(
            ["FXSpotRate", "ScaleFactor"],
            {
                "args": [
                    ("curve", "object"),
                    ("bidMidAsk", "str", 'MID'),
                ],
            }
        )

        self.add_method_def({
            "method": "SpotDate",
            "args": [
                ("curve", "object"),
            ],

        })


class DefMcpOvernightRateCurveData(ItemDef):

    def __init__(self):
        super().__init__()
        self.custom_instance_func_raw = mcp_instance_list
        self.generate_xls_method = False
        self.init_data = {
            "is_wrapper": True,
            "data_fields": [
                ("MaturityTenors", "str"),
                ("MaturityDates", "date"),
                ("Yields", "float"),
                ("BumpAmounts", "float"),
                ("BUses", "intbool")
            ],
            "pyxll_def": {
            },
        }
        self.init_kv_list = [
            [
                ("DayCounter", "const"),
                ("StartDate", "date"),
                ("MaturityDates", "plainlist"),
                ("Yields", "plainlist"),
                ("BumpAmounts", "plainlist"),
                ("BUses", "plainlist"),
                ("Calendar", "object", McpCalendar("", "", "")),
            ],
            [
                ("DayCounter", "const"),
                ("StartDate", "date"),
                ("MaturityTenors", "plainlist"),
                ("Yields", "plainlist"),
                ("BumpAmounts", "plainlist"),
                ("BUses", "plainlist"),
                ("Calendar", "object", McpCalendar("", "", "")),
            ],
        ]


def _curve_data_dates_tenors_nmode(result_keys):
    """Bill/BillFuture 等：VP 含 MaturityTenors → nmode=2，否则 nmode=1（MaturityDates）。"""
    keys = {str(k).lower() for k in result_keys}
    if "maturitytenors" in keys:
        return 2
    return 1


def _create_curve_data_with_nmode(args_dict, init_kv_list, class_name):
    from mcp.wrapper import create_object_instance

    lower_args = {str(k).lower(): v for k, v in args_dict.items()}
    result, lack_keys = mcp_kv_wrapper.parse_args_dict(lower_args, init_kv_list)
    if len(lack_keys) > 0:
        raise Exception("Missing fields: " + str(lack_keys))
    vals = [_curve_data_dates_tenors_nmode(result["keys"])] + list(result["vals"])
    return create_object_instance("mcp.wrapper", class_name, vals)


def create_bill_curve_data(args_dict, init_kv_list):
    """创建 McpBillCurveData：nmode 由 MaturityDates / MaturityTenors 内部推断。"""
    return _create_curve_data_with_nmode(args_dict, init_kv_list, "McpBillCurveData")


def create_bill_future_curve_data(args_dict, init_kv_list):
    """创建 McpBillFutureCurveData：nmode 由 MaturityDates / MaturityTenors 内部推断。"""
    return _create_curve_data_with_nmode(args_dict, init_kv_list, "McpBillFutureCurveData")


class DefMcpBillCurveData(ItemDef):

    def __init__(self):
        super().__init__()
        self.custom_instance_func_raw = mcp_instance_list
        self.generate_xls_method = False
        self.init_data = {
            "is_wrapper": True,
            "data_fields": [
                ("MaturityTenors", "str"),
                ("MaturityDates", "date"),
                ("Yields", "float"),
                ("BumpAmounts", "float"),
                ("BUses", "intbool")
            ],
            "pyxll_def": {
            },
        }
        self.init_kv_list = [
            [
                ("DayCounter", "const"),
                ("StartDate", "date"),
                ("MaturityDates", "plainlist"),
                ("Yields", "plainlist"),
                ("BumpAmounts", "plainlist"),
                ("BUses", "plainlist"),
                ("Calendar", "object", McpCalendar("", "", "")),
            ],
            [
                ("DayCounter", "const"),
                ("StartDate", "date"),
                ("MaturityTenors", "plainlist"),
                ("Yields", "plainlist"),
                ("BumpAmounts", "plainlist"),
                ("BUses", "plainlist"),
                ("Calendar", "object", McpCalendar("", "", "")),
            ],
        ]
        self.custom_instance_func = (
            lambda args_dict: create_bill_curve_data(args_dict, self.init_kv_list)
        )


class DefMcpBillFutureCurveData(ItemDef):

    def __init__(self):
        super().__init__()
        self.custom_instance_func_raw = mcp_instance_list
        self.generate_xls_method = False
        self.init_data = {
            "is_wrapper": True,
            "data_fields": [
                ("MaturityTenors", "str"),
                ("SettlementDates", "date"),
                ("MaturityDates", "date"),
                ("Yields", "float"),
                ("Convexities", "float"),
                ("BumpAmounts", "float"),
                ("BUses", "intbool")
            ],
            "pyxll_def": {
            },
        }
        self.init_kv_list = [
            [
                ("DayCounter", "const"),
                ("SettlementDates", "plainlist"),
                ("MaturityDates", "plainlist"),
                ("Yields", "plainlist"),
                ("Convexities", "plainlist"),
                ("BumpAmounts", "plainlist"),
                ("BUses", "plainlist")
            ],
            [
                ("DayCounter", "const"),
                ("SettlementDates", "plainlist"),
                ("MaturityTenors", "plainlist"),
                ("Yields", "plainlist"),
                ("Convexities", "plainlist"),
                ("BumpAmounts", "plainlist"),
                ("BUses", "plainlist")
            ],
        ]
        self.custom_instance_func = (
            lambda args_dict: create_bill_future_curve_data(args_dict, self.init_kv_list)
        )


class DefMcpFRACurveData(ItemDef):

    def __init__(self):
        super().__init__()
        self.custom_instance_func_raw = mcp_instance_list
        self.generate_xls_method = False
        self.init_data = {
            "is_wrapper": True,
            "data_fields": [
                ("Labels", "str"),
                ("Yields", "float"),
                ("BumpAmounts", "float"),
                ("BUses", "intbool"),
            ],
            "pyxll_def": {
            },
        }
        self.init_kv_list = [
            [
                ("SettlementDate", "date"),
                ("Labels", "plainlist"),
                ("Yields", "plainlist"),
                ("DayCounter", "const", DayCounter.Act365Fixed),
                ("BumpAmounts", "plainlist"),
                ("BUses", "plainlist"),
                ("Calendar", "object", McpCalendar("", "", "")),
                ("EomRule", "int", 1),
                ("MaturityFromSpotDate", "bool", False),
                ("AdjustRule", "const", DateAdjusterRule.ModifiedFollowing),
                ("LastOpenday", "bool", False),
                ("IsUpfrontPayment", "bool", False),
                ("Notional", "float", 1000000.0),
            ],
        ]


def _vanilla_swap_curve_nmode(result_keys):
    """根据匹配到的 VP 字段推断 C++ nmode；RateConvention 重载无 nmode。"""
    keys = {str(k).lower() for k in result_keys}
    if "rateconvention" in keys:
        return None
    if "paymentdateadjuster" in keys:
        return VanillaSwapCurveDataMode.IndexSwap
    if "maturitytenors" in keys and "startdate" in keys:
        return VanillaSwapCurveDataMode.MaturityTenors
    return VanillaSwapCurveDataMode.MaturityDates


def create_vanilla_swap_curve_data(args_dict, init_kv_list):
    """创建 McpVanillaSwapCurveData：Mode/nmode 由字段组合内部推断，不要求 Excel 填写。"""
    from mcp.wrapper import create_object_instance

    lower_args = {str(k).lower(): v for k, v in args_dict.items()}
    result, lack_keys = mcp_kv_wrapper.parse_args_dict(lower_args, init_kv_list)
    if len(lack_keys) > 0:
        raise Exception("Missing fields: " + str(lack_keys))
    vals = list(result["vals"])
    nmode = _vanilla_swap_curve_nmode(result["keys"])
    if nmode is not None:
        vals.insert(0, nmode)
    return create_object_instance("mcp.wrapper", "McpVanillaSwapCurveData", vals)


class DefMcpVanillaSwapCurveData(ItemDef):

    def __init__(self):
        super().__init__()
        self.custom_instance_func_raw = mcp_instance_list
        self.generate_xls_method = False
        self.init_data = {
            "is_wrapper": True,
            "data_fields": [
                ("MaturityTenors", "str"),
                ("MaturityDates", "date"),
                ("Frequencies", "const"),
                ("Coupons", "float"),
                ("BumpAmounts", "float"),
                ("BUses", "intbool"),
            ],
            "pyxll_def": {
            },
        }
        self.init_kv_list = [
            [
                ("SettlementDate", "date"),
                ("StartDate", "date"),
                ("MaturityDates", "plainlist"),
                ("Frequencies", "plainlist"),
                ("Coupons", "plainlist"),
                ("FixedDayCounter", "const", DayCounter.Act365Fixed),
                ("FloatDayCounter", "const", DayCounter.Act365Fixed),
                ("BumpAmounts", "plainlist"),
                ("BUses", "plainlist"),
                ("Calendar", "object", McpCalendar("", "", "")),
                ("AdjustRule", "const", DateAdjusterRule.ModifiedFollowing),
            ],
            [
                ("ReferenceDate", "date"),
                ("StartDate", "date"),
                ("MaturityDates", "plainlist"),
                ("Frequencies", "plainlist"),
                ("Coupons", "plainlist"),
                ("FixedDayCounter", "const", DayCounter.Act365Fixed),
                ("FloatDayCounter", "const", DayCounter.Act365Fixed),
                ("BumpAmounts", "plainlist"),
                ("BUses", "plainlist"),
                ("Calendar", "object", McpCalendar("", "", "")),
                ("AdjustRule", "const", DateAdjusterRule.ModifiedFollowing),
                ("UseIndexEstimation", "bool", True),
                ("SwapStartLag", "int", 1),
                ("CompoundingFrequency", "int", 0),
                ("FixInAdvance", "bool", True),
                ("FixDaysBackward", "int", 1),
                ("EndStub", "bool", False),
            ],
            [
                ("ReferenceDate", "date"),
                ("StartDate", "date"),
                ("MaturityTenors", "plainlist"),
                ("Frequencies", "plainlist"),
                ("Coupons", "plainlist"),
                ("FixedDayCounter", "const", DayCounter.Act365Fixed),
                ("FloatDayCounter", "const", DayCounter.Act365Fixed),
                ("BumpAmounts", "plainlist"),
                ("BUses", "plainlist"),
                ("Calendar", "object", McpCalendar("", "", "")),
                ("AdjustRule", "const", DateAdjusterRule.ModifiedFollowing),
            ],
            [
                ("ReferenceDate", "date"),
                ("SwapStartLag", "int", 2),
                ("MaturityTenors", "plainlist"),  # Tenors
                ("Calendar", "object", McpCalendar("", "", "")),
                ("PaymentDateAdjuster", "const"),
                ("AccrDateAdjuster", "const", DateAdjusterRule.Actual),
                ("Coupons", "plainlist"),
                ("FixedFrequency", "const"),
                ("FloatFrequency", "const"),
                ("FixedDayCounter", "const"),
                ("FloatDayCounter", "const"),
                ("UseIndexEstimation", "bool", True),
                ("FixingIndex", "str"),
                ("FixingRateMethod", "const"),
                ("FixInAdvance", "bool", True),
                ("FixDaysBackward", "int", 1),
                ("Margin", "float", 0.0),
                ("BumpAmounts", "plainlist"),
                ("BUses", "plainlist"),
                ("FixingDayCounter", "const", DayCounter.Act365Fixed),
                ("FloatCompounding", "bool", False),
                ("FloatCompoundingFrequency", "const", Frequency.Annual),
                ("FixedCompounding", "bool", False),
                ("FixedCompoundingFrequency", "const", Frequency.Annual),
            ],
            [
                ("ReferenceDate", "date"),
                ("SwapStartLag", "int", 2),
                ("MaturityDates", "plainlist"),  # Dates
                ("Calendar", "object", McpCalendar("", "", "")),
                ("PaymentDateAdjuster", "const"),
                ("AccrDateAdjuster", "const", DateAdjusterRule.Actual),
                ("Coupons", "plainlist"),
                ("FixedFrequency", "const"),
                ("FloatFrequency", "const"),
                ("FixedDayCounter", "const"),
                ("FloatDayCounter", "const"),
                ("UseIndexEstimation", "bool", True),
                ("FixingIndex", "str"),
                ("FixingRateMethod", "const"),
                ("FixInAdvance", "bool", True),
                ("FixDaysBackward", "int", 1),
                ("Margin", "float", 0.0),
                ("BumpAmounts", "plainlist"),
                ("BUses", "plainlist"),
                ("FixingDayCounter", "const", DayCounter.Act365Fixed),
                ("FloatCompounding", "bool", False),
                ("FloatCompoundingFrequency", "const", Frequency.Annual),
                ("FixedCompounding", "bool", False),
                ("FixedCompoundingFrequency", "const", Frequency.Annual),
            ],
            [
                ("ReferenceDate", "date"),
                ("RateConvention", "str"),
                ("MaturityDates", "plainlist"),  # Dates
                ("Coupons", "plainlist"),
                ("BumpAmounts", "plainlist"),
                ("BUses", "plainlist"),
                ("Calendar", "object", McpCalendar("", "", "")),
            ],
            [
                ("ReferenceDate", "date"),
                ("RateConvention", "str"),
                ("MaturityTenors", "plainlist"),  # Tenors
                ("Coupons", "plainlist"),
                ("BumpAmounts", "plainlist"),
                ("BUses", "plainlist"),
                ("Calendar", "object", McpCalendar("", "", "")),
            ],
        ]
        self.custom_instance_func = (
            lambda args_dict: create_vanilla_swap_curve_data(args_dict, self.init_kv_list)
        )


class DefMcpFixedRateBondCurveData(ItemDef):

    def __init__(self):
        super().__init__()
        self.custom_instance_func_raw = mcp_instance_list
        self.generate_xls_method = True
        self.init_data = {
            "is_wrapper": True,
            "fmt": "VP|HD",
            "data_fields": [
                ("MaturityTenors", "str"),
                ("MaturityDates", "date"),
                ("Frequencies", "int"),
                ("Coupons", "float"),
                ("YieldsOrDirtyPrice", "float"),
                ("BumpAmounts", "float"),
                ("BUses", "intbool"),
            ],
            "pyxll_def": {
            },
        }
        self.init_kv_list = [
            [
                ("SettlementDate", "date"),
                ("MaturityDates", "plainlist"),
                ("Frequencies", "plainlist"),
                ("Coupons", "plainlist"),
                ("YieldsOrDirtyPrice", "plainlist"),
                ("DayCounter", "const"),
                ("IsYield", "bool"),
                ("BumpAmounts", "plainlist"),
                ("BUses", "plainlist"),
                ("Calendar", "object"),
            ],
            # [
            #     ("SettlementDate", "date"),
            #     ("MaturityTenors", "plainlist"),
            #     ("Frequencies", "plainlist"),
            #     ("Coupons", "plainlist"),
            #     ("YieldsOrDirtyPrice", "plainlist"),
            #     ("DayCounter", "const"),
            #     ("IsYield", "bool"),
            #     ("BumpAmounts", "plainlist"),
            #     ("BUses", "plainlist"),
            #     ("Calendar", "object"),
            # ],
        ]


class DefMcpHestonModel(ItemDef):

    def __init__(self):
        super().__init__()
        self.custom_instance_func_raw = mcp_instance_list
        self.generate_xls_method = True
        self.init_data = {
            "is_wrapper": True,
            "pkg": "mcp.xscript.structure",
            "method_prefix": "Hm",
            "fmt": "VP|HD",
            "data_fields": [
                ("ExpiryDates", "date"),
                ("Strikes", "float"),
                ("OptionType", "const"),
                ("Bid", "float"),
                ("Ask", "float"),
            ],
            "pyxll_def": {
            },
        }
        self.init_kv_list = [
            [
                ("MktVol2", "object"),
                ("LogLevel", "const", LogLevel.Off),
                # ("UniqueID", "str", ""),
                # ("TraceDirectory", "str", "data/xScript"),
            ],
            [
                ("Spot", "float"),
                ("ReferenceDate", "date"),
                ("DomesticRateCurve", "object"),
                ("ForeignRateCurve", "object"),

                ("ExpiryDates", "plainlist"),
                ("Strikes", "plainlist"),
                ("OptionType", "plainlist"),
                ("Bid", "plainlist"),
                ("Ask", "plainlist"),

                ("LogLevel", "const", LogLevel.Off),
                # ("UniqueID", "str", ""),
                # ("TraceDirectory", "str", "data/xScript"),
            ],
            [
                ("Spot", "float"),
                ("ReferenceDate", "date"),
                ("RiskFreeRateCurve", "object"),
                ("Dividend", "float"),

                ("ExpiryDates", "plainlist"),
                ("Strikes", "plainlist"),
                ("OptionType", "plainlist"),
                ("Bid", "plainlist"),
                ("Ask", "plainlist"),

                ("LogLevel", "const", LogLevel.Off),
                # ("UniqueID", "str", ""),
                # ("TraceDirectory", "str", "data/xScript"),
            ],
        ]
        self.add_method_def({
            "method": "HestonCalibration",
            "args": [
                ("curve", "object"),
                ("initParams", "array"),
            ],
            "fmt": "V",
            "pyxll_def": {
                "auto_resize": True
            },
        })


class DefMcpOptionData(ItemDef):

    def __init__(self):
        super().__init__()
        self.custom_instance_func_raw = mcp_instance_list
        self.generate_xls_method = True
        self.init_data = {
            "is_wrapper": True,
            "fmt": "VP|HD",
            "data_fields": [
                ("ExpiryDates", "date"),
                ("Strikes", "float"),
                ("OptionTypes", "const"),
                ("Mid", "float"),
                ("Bid", "float"),
                ("Ask", "float"),
            ],
            "pyxll_def": {
            },
        }
        self.init_kv_list = [
            [
                ("AssetClass", "const"),
                ("Spot", "float"),
                ("ExpiryDates", "plainlist"),
                ("Strikes", "plainlist"),
                ("OptionTypes", "optiontypelist"),
                ("Mid", "plainlist"),
                ("Bid", "plainlist"),
                ("Ask", "plainlist"),

                ("RiskFreeRateCurve", "object", mcp.wrapper.McpYieldCurve()),
                ("UnderlyingCurve", "object", mcp.wrapper.McpYieldCurve()),
                ("RiskFreeRateCurve2", "object", mcp.wrapper.McpYieldCurve2()),
                ("UnderlyingCurve2", "object", mcp.wrapper.McpYieldCurve2()),

                ("RiskFreeRate", "float", 0.0),
                ("UnderlyingRate", "float", 0.0),
            ],
        ]


class DefMcpForwardCurve2(ItemDef):

    def __init__(self):
        super().__init__()
        self.custom_instance_func_raw = mcp_instance_list
        self.init_data = {
            "is_wrapper": True,
            "fmt": "VP|HD",
            "method_prefix": "ForwardCurve2",
            "data_fields": [
                ("ExpiryDates", "date"),
                ("BidUnderlyingRates", "float"),
                ("AskUnderlyingRates", "float"),
            ],
            "pyxll_def": {
            },
        }
        self.kv_const_dict = {
            'InterpolationMethod': 'InterpolationMethod',
        }
        self.init_kv_list = [
            [
                ("ReferenceDate", "date"),
                ("ExpiryDates", "plainlist"),
                ("BidUnderlyingRates", "plainlist"),
                ("AskUnderlyingRates", "plainlist"),
                ("InterpolationMethod", "const", InterpolationMethod.LINEARINTERPOLATION, "LINEARINTERPOLATION")
            ],
        ]
        self.add_method_def({
            "method": "ForwardRate",
            "args": [
                ("curve", "object"),
                ("endDate", "date"),
                ("bidMidAsk", "str", 'MID'),
            ],
        })


class DefMcpForwardCurve(ItemDef):

    def __init__(self):
        super().__init__()
        self.custom_instance_func_raw = mcp_instance_list
        self.init_data = {
            "is_wrapper": True,
            "fmt": "VP|HD",
            "method_prefix": "ForwardCurve",
            "data_fields": [
                ("ExpiryDates", "date"),
                ("UnderlyingRates", "float"),
            ],
            "pyxll_def": {
            },
        }
        self.kv_const_dict = {
            'InterpolationMethod': 'InterpolationMethod',
        }
        self.init_kv_list = [
            [
                ("ReferenceDate", "date"),
                ("ExpiryDates", "plainlist"),
                ("UnderlyingRates", "plainlist"),
                ("InterpolationMethod", "const", InterpolationMethod.LINEARINTERPOLATION, "LINEARINTERPOLATION")
            ],
        ]
        self.add_method_def({
            "method": "ForwardRate",
            "args": [
                ("curve", "object"),
                ("endDate", "date"),
            ],
        })


class DefMcpSingleCumulative(ItemDef):

    def __init__(self):
        super().__init__()
        # 这里模仿你的自定义逻辑
        self.custom_instance_func_raw = mcp_instance_list

        # 包装类的一些基本元数据
        self.init_data = {
            "is_wrapper": True,
            # "pkg": "mcp.forward.custom",            # 你项目中的包名
            "method_prefix": "SingleCumulative",  # 生成的前缀，比如 create / price / ...
            "data_fields": [
                # 如果有额外自定义字段，可在此扩充
            ],
            "pyxll_def": {
                # 若有 PyXLL 相关配置，可在此添加
            },
        }

        # 定义两组字段 (对应 SingleCumulative 的两种构造函数)
        # 按照 [ (字段名, 字段类型, 默认值, 其他说明), ... ] 的模式
        self.init_kv_list = [
            # --- (A) 通过日期计算 timeToExpiry 的构造方式 ---
            [
                ("ReferenceDate", "date"),  # 如 "20230301"
                ("Barrier", "float"),
                ("BuySell", "const"),  # 枚举: BuySell.BUY / SELL
                ("SpotPx", "float"),
                ("Volatility", "float"),
                ("ExpiryDate", "date"),  # "20230601"
                ("SettlementDate", "date"),  # "20230602"
                ("AccRate", "float"),
                ("UndRate", "float"),
                ("PremiumDate", "date"),  # "20230315"
                ("Notional", "float"),  # 名义本金
                ("CumFactor", "float", 0.05),  # 日/年累积因子
                ("Calendar", "object", McpCalendar("", "", ""), ""),
                ("DayCounter", "const", DayCounter.Act365Fixed, "Act365Fixed"),
                ("PricingMethod", "const", PricingMethod.PDE),
                ("OptionType", "const", CallPut.Call),
                ("OptionExpiryNature", "const", OptionExpiryNature.EUROPEAN)
            ],
            # --- (B) 直接传入 double timeToExpiry, timeToSettlement 的构造方式 ---
            [
                ("Barrier", "float"),
                ("TimeToExpiry", "float"),
                ("TimeToSettlement", "float"),
                ("BuySell", "const"),
                ("SpotPx", "float"),
                ("Volatility", "float"),
                ("AccRate", "float"),
                ("UndRate", "float"),
                ("Notional", "float"),
                ("CumFactor", "float", 0.05),
                ("PricingMethod", "const", PricingMethod.PDE),
                ("OptionType", "const", CallPut.Call),
                ("OptionExpiryNature", "const", OptionExpiryNature.EUROPEAN)
            ],
        ]


class DefMcpDoubleCumulative(ItemDef):

    def __init__(self):
        super().__init__()
        # 如果你的项目需要使用自定义 raw 函数，可同样传入
        self.custom_instance_func_raw = mcp_instance_list

        # 供封装器识别的一些元数据
        self.init_data = {
            "is_wrapper": True,
            # "pkg": "mcp.forward.custom",           # 你的项目包名，可自定义
            "method_prefix": "DoubleCumulative",  # 生成接口的方法前缀
            "data_fields": [
                # 如需其他自定义数据字段，可在此添加
            ],
            "pyxll_def": {
                # 若使用 PyXLL，可以在这里定义相关映射
            },
        }

        # init_kv_list: 两组字段，分别对应日期构造 & 直接年化时间构造
        # 每个字段的定义形如:
        #   (字段名, 字段类型, [可选:默认值], [可选:其他描述或枚举值])
        self.init_kv_list = [
            # --- (A) 通过日期计算到期时间的构造 ---
            [
                ("ReferenceDate", "date"),  # 譬如 "20230301"
                ("LowerBarrier", "float"),
                ("UpperBarrier", "float"),
                ("BuySell", "const"),  # 枚举( BuySell.BUY / SELL )
                ("SpotPx", "float"),
                ("Volatility", "float"),
                ("ExpiryDate", "date"),  # 如 "20230601"
                ("SettlementDate", "date"),  # "20230602"
                ("AccRate", "float"),  # r
                ("UndRate", "float"),  # q
                ("PremiumDate", "date"),  # "20230315"
                ("Notional", "float"),
                ("R1", "float"),  # 区间内收益率
                ("R2", "float"),  # 区间外收益率
                ("Calendar", "object", McpCalendar("", "", ""), ""),
                ("DayCounter", "const", DayCounter.Act365Fixed, "Act365Fixed"),
                ("PricingMethod", "const", PricingMethod.PDE),
                ("OptionType", "const", CallPut.Call),
                ("OptionExpiryNature", "const", OptionExpiryNature.EUROPEAN)
            ],
            # --- (B) 直接传入 TimeToExpiry, TimeToSettlement 的构造 ---
            [
                ("LowerBarrier", "float"),
                ("UpperBarrier", "float"),
                ("TimeToExpiry", "float"),
                ("TimeToSettlement", "float"),
                ("BuySell", "const"),
                ("SpotPx", "float"),
                ("Volatility", "float"),
                ("AccRate", "float"),
                ("UndRate", "float"),
                ("Notional", "float"),
                ("R1", "float"),
                ("R2", "float"),
                ("PricingMethod", "const", PricingMethod.PDE),
                ("OptionType", "const", CallPut.Call),
                ("OptionExpiryNature", "const", OptionExpiryNature.EUROPEAN)
            ],
        ]


class DefMcpEFXForward(ItemDef):
    def __init__(self):
        super().__init__()
        self.generate_xls_method = True
        self.custom_instance_func_raw = "mcp_instance_list"  # 假设使用相同的实例生成函数
        self.init_data = {
            "is_wrapper": True,
            "method_prefix": "FXForward",
            "data_fields": [],
            "pyxll_def": {},
        }
        self.init_kv_list = [
            [
                ("SpotPx", "float"),
                ("ForwardPoints", "float"),
                ("TradeForwardPx", "float"),
                ("ReferenceDate", "date"),
                ("DeliveryDate", "date"),
                ("BuySell", "const", BuySell.Buy, "Buy"),
                ("Notional", "float", 1000000.0, 1000000),
                ("Calendar", "object", McpCalendar("", "", ""), ""),
                ("DayCounter", "const", DayCounter.Act365Fixed, "Act365Fixed"),
                ("DomesticRate", "float"),
                ("ForeignRate", "float"),
                ("Pair", "str", "USDCNY", "USDCNY"),
            ],
            [
                ("FXForwardPointsCurve", "object"),
                ("TradeForwardPx", "float"),
                ("ReferenceDate", "date"),
                ("DeliveryDate", "date"),
                ("BuySell", "const", BuySell.Buy, "Buy"),
                ("Notional", "float", 1000000.0, 1000000),
                ("Calendar", "object", McpCalendar("", "", ""), ""),
                ("DayCounter", "const", DayCounter.Act365Fixed, "Act365Fixed"),
                ("DomesticCurve", "object"),
                ("ForeignCurve", "object"),
                ("Pair", "str", "USDCNY", "USDCNY"),
            ],
            [
                ("ReferenceDate", "date"),
                ("DeliveryDate", "date"),
                ("FXForwardPointsCurve2", "object"),
                ("TradeForwardPx", "float"),
                ("BuySell", "const", BuySell.Buy, "Buy"),
                ("Notional", "float", 1000000.0, 1000000),
                ("Calendar", "object", McpCalendar("", "", ""), ""),
                ("DayCounter", "const", DayCounter.Act365Fixed, "Act365Fixed"),
                ("DomesticCurve", "object"),
                ("ForeignCurve", "object"),
                ("Pair", "str", "USDCNY", "USDCNY"),
            ],
        ]


class DefMcpEFXSwap(ItemDef):
    def __init__(self):
        super().__init__()
        self.generate_xls_method = True
        self.custom_instance_func_raw = "mcp_instance_list"  # 假设使用相同的实例生成函数
        self.init_data = {
            "is_wrapper": True,
            "method_prefix": "FXSwap",
            "data_fields": [],
            "pyxll_def": {},
        }
        self.init_kv_list = [
            [
                ("SpotPx", "float"),
                ("ForwardPoints", "float"),
                ("TradeSpotPx", "float"),
                ("TradeFwdPoints", "float"),
                ("ReferenceDate", "date"),
                ("NearDate", "date"),
                ("FarDate", "date"),
                ("BuySell", "const", BuySell.Buy, "Buy"),
                ("Notional", "float", 1000000.0, 1000000),
                ("Calendar", "object", McpCalendar("", "", ""), ""),
                ("DayCounter", "const", DayCounter.Act365Fixed, "Act365Fixed"),
                ("DomesticRate", "float", 0.0, 0.0),
                ("ForeignRate", "float", 0.0, 0.0),
                ("Pair", "str", "USDCNY", "USDCNY"),
                ("NearFwdPoints", "float", 0.0, 0.0),
                ("TradeNearFwdPoints", "float", 0.0, 0.0),
            ],
            [
                ("FXForwardPointsCurve", "object"),
                ("TradeSpotPx", "float"),
                ("TradeFwdPoints", "float"),
                ("ReferenceDate", "date"),
                ("NearDate", "date"),
                ("FarDate", "date"),
                ("BuySell", "const", BuySell.Buy, "Buy"),
                ("Notional", "float", 1000000.0, 1000000),
                ("Calendar", "object", McpCalendar("", "", ""), ""),
                ("DayCounter", "const", DayCounter.Act365Fixed, "Act365Fixed"),
                ("DomesticCurve", "object", "", ""),
                ("ForeignCurve", "object", "", ""),
                ("Pair", "str", "USDCNY", "USDCNY"),
                ("TradeNearFwdPoints", "float", 0.0, 0.0),
            ],
            [
                ("ReferenceDate", "date"),
                ("NearDate", "date"),
                ("FarDate", "date"),
                ("FXForwardPointsCurve2", "object"),
                ("TradeSpotPx", "float"),
                ("TradeFwdPoints", "float"),
                ("BuySell", "const", BuySell.Buy, "Buy"),
                ("Notional", "float", 1000000.0, 1000000),
                ("Calendar", "object", McpCalendar("", "", ""), ""),
                ("DayCounter", "const", DayCounter.Act365Fixed, "Act365Fixed"),
                ("DomesticCurve", "object", "", ""),
                ("ForeignCurve", "object", "", ""),
                ("Pair", "str", "USDCNY", "USDCNY"),
                ("TradeNearFwdPoints", "float", 0.0, 0.0),
            ],
        ]


class DefMcpCommodityFutureAdapter(ItemDef):

    def __init__(self):
        super().__init__()
        self.init_data = {
            "is_wrapper": False,  # Adapter 不是 wrapper 类
            "method_prefix": "CommodityFutureAdapter",
            "data_fields": [],
            "pyxll_def": {},
        }
        self.init_kv_list = [
            [
                ("CommodityFuture", "object"),
                ("InstrumentId", "str"),
                ("TradeId", "str"),
                ("PortfolioKey", "str", "", ""),
                # 可选字段（DiscountCurve）在 custom_instance_func 中处理
            ],
        ]

        # 自定义实例函数：创建 adapter 并调用 set 方法
        def create_commodity_future_adapter(args_dict):
            import mcp.mcp as mcp_module
            from mcp.wrapper import create_object_instance

            commodity_future = args_dict.get('CommodityFuture', args_dict.get('commodityFuture'))
            instrument_id = args_dict.get('InstrumentId', args_dict.get('instrumentId', 'CommodityFuture_001'))
            trade_id = args_dict.get('TradeId', args_dict.get('tradeId', 'TRADE_CommodityFuture_001'))
            portfolio_key = args_dict.get('PortfolioKey', args_dict.get('portfolioKey', ''))
            discount_curve = args_dict.get('DiscountCurve', args_dict.get('discountCurve'))

            # 创建 adapter
            adapter = create_object_instance("mcp.mcp", "MCommodityFutureAdapter", [
                commodity_future,
                instrument_id,
                trade_id,
                portfolio_key
            ])

            # 调用 set 方法
            if discount_curve is not None:
                adapter.setDiscountCurve(discount_curve)

            return adapter

        self.custom_instance_func = create_commodity_future_adapter


class DefMcpVanillaSwapAdapter(ItemDef):

    def __init__(self):
        super().__init__()
        self.init_data = {
            "is_wrapper": False,
            "method_prefix": "VanillaSwapAdapter",
            "data_fields": [],
            "pyxll_def": {},
        }
        self.init_kv_list = [
            [
                ("VanillaSwap", "object"),
                ("InstrumentId", "str"),
                ("TradeId", "str"),
                # 可选字段（ValuationCurve）在 custom_instance_func 中处理
            ],
        ]

        def create_vanilla_swap_adapter(args_dict):
            import mcp.mcp as mcp_module
            from mcp.wrapper import create_object_instance, McpYieldCurve, McpSwapCurve, McpBondCurve

            vanilla_swap = args_dict.get('VanillaSwap', args_dict.get('vanillaSwap'))
            instrument_id = args_dict.get('InstrumentId', args_dict.get('instrumentId', 'VanillaSwap_001'))
            trade_id = args_dict.get('TradeId', args_dict.get('tradeId', 'TRADE_VanillaSwap_001'))
            valuation_curve = args_dict.get('ValuationCurve', args_dict.get('valuationCurve'))
            credit_curve = args_dict.get('CreditCurve', args_dict.get('creditCurve'))
            recovery_rate = args_dict.get('RecoveryRate', args_dict.get('recoveryRate'))

            adapter = create_object_instance("mcp.mcp", "MVanillaSwapAdapter", [
                vanilla_swap,
                instrument_id,
                trade_id
            ])

            # 仅当 valuation_curve 为曲线类型时设置（McpYieldCurve/McpSwapCurve/McpBondCurve 或 M 基类）
            if valuation_curve is not None and isinstance(
                valuation_curve,
                (mcp_module.MYieldCurve, mcp_module.MBondCurve, mcp_module.MSwapCurve,
                 McpYieldCurve, McpSwapCurve, McpBondCurve)
            ):
                adapter.setValuationCurve(valuation_curve)

            # 可选：信用曲线与回收率（用于 CVA/DFE）
            if credit_curve is not None and hasattr(adapter, 'SetCreditCurve'):
                try:
                    adapter.SetCreditCurve(credit_curve)
                except Exception:
                    pass
            if recovery_rate is not None and hasattr(adapter, 'SetRecoveryRate'):
                try:
                    adapter.SetRecoveryRate(float(recovery_rate))
                except Exception:
                    pass

            # 设置 PFE 计算器（VaR/ES/EE/PFE/DFE 依赖）
            has_pfe = hasattr(adapter, 'setPFECalculator')
            SwapPFECalc = getattr(getattr(mcp_module, 'metrics', None), 'SwapPFECalculator', None) or getattr(mcp_module, 'SwapPFECalculator', None)
            pfe_set_ok = False
            if SwapPFECalc is not None and has_pfe:
                try:
                    PFEConfig = getattr(SwapPFECalc, 'PFEConfig', None)
                    if PFEConfig is not None:
                        cfg = PFEConfig()
                        cfg.num_simulations = 1000
                        cfg.confidence_level = 0.95
                        pfe_calc = SwapPFECalc(cfg)
                    else:
                        pfe_calc = SwapPFECalc()
                    adapter.setPFECalculator(pfe_calc)
                    adapter._pfe_calc_ref = pfe_calc
                    pfe_set_ok = True
                except Exception as e:
                    pfe_set_ok = False

            # 回退：MVanillaSwapAdapter 无 setPFECalculator 时，改用 VanillaSwapAdapter（有 setPFECalculator）
            fallback_ok = False
            fallback_err = None
            fallback_steps = []
            has_vs = hasattr(mcp_module, 'VanillaSwapAdapter')
            curve_ok = valuation_curve is not None and isinstance(
                valuation_curve,
                (mcp_module.MYieldCurve, mcp_module.MBondCurve, mcp_module.MSwapCurve,
                 McpYieldCurve, McpSwapCurve, McpBondCurve)
            )
            def _dbg(msg, **kw):
                fallback_steps.append({"step": msg, **{k: str(v)[:150] if isinstance(v, (str, Exception)) else v for k, v in kw.items()}})

            if not pfe_set_ok and curve_ok and has_vs:
                try:
                    _dbg("fallback_start", swap_type=type(vanilla_swap).__name__)
                    if hasattr(mcp_module, 'GetUnderlyingVanillaSwap') and hasattr(mcp_module, 'CreateVanillaSwapAdapter'):
                        _dbg("try_GetUnderlying")
                        underlying = mcp_module.GetUnderlyingVanillaSwap(vanilla_swap)
                        _dbg("GetUnderlying_ok", underlying_type=type(underlying).__name__ if underlying else None)
                        adapter = mcp_module.CreateVanillaSwapAdapter(underlying, instrument_id, trade_id)
                        _dbg("CreateVanillaSwapAdapter_ok")
                    elif hasattr(mcp_module, 'CreateVanillaSwapAdapter'):
                        _dbg("try_handler")
                        handler = vanilla_swap.getHandler() if hasattr(vanilla_swap, 'getHandler') else vanilla_swap
                        adapter = mcp_module.CreateVanillaSwapAdapter(handler, instrument_id, trade_id)
                        _dbg("CreateVanillaSwapAdapter_ok")
                    else:
                        _dbg("try_VanillaSwapAdapter")
                        adapter = mcp_module.VanillaSwapAdapter(vanilla_swap, instrument_id, trade_id)
                        _dbg("VanillaSwapAdapter_ok")
                    curve_arg = valuation_curve.getHandler() if hasattr(valuation_curve, 'getHandler') else valuation_curve
                    if curve_arg is not None:
                        adapter.setValuationCurve(curve_arg)
                        _dbg("setValuationCurve_ok")
                    if credit_curve is not None and hasattr(adapter, 'SetCreditCurve'):
                        cc_arg = credit_curve.getHandler() if hasattr(credit_curve, 'getHandler') else credit_curve
                        adapter.SetCreditCurve(cc_arg)
                        _dbg("SetCreditCurve_ok")
                    if recovery_rate is not None and hasattr(adapter, 'SetRecoveryRate'):
                        adapter.SetRecoveryRate(float(recovery_rate))
                    _has_pfe = hasattr(adapter, 'setPFECalculator') or hasattr(adapter, 'SetPFECalculator')
                    _pfe_method = getattr(adapter, 'setPFECalculator', None) or getattr(adapter, 'SetPFECalculator', None)
                    _dbg("before_pfe", has_pfe=_has_pfe, SwapPFECalc=SwapPFECalc is not None, PFEConfig=getattr(SwapPFECalc, 'PFEConfig', None) is not None if SwapPFECalc else False)
                    if SwapPFECalc is not None and _pfe_method is not None:
                        PFEConfig = getattr(SwapPFECalc, 'PFEConfig', None)
                        if PFEConfig:
                            cfg = PFEConfig()
                            cfg.num_simulations = 1000
                            cfg.confidence_level = 0.95
                            pfe_calc = SwapPFECalc(cfg)
                        else:
                            pfe_calc = SwapPFECalc()
                        _pfe_method(pfe_calc)
                        adapter._pfe_calc_ref = pfe_calc
                        _dbg("setPFECalculator_ok")
                        pfe_set_ok = True
                        fallback_ok = True
                except Exception as ex:
                    fallback_err = str(ex)[:300]
                    _dbg("exception", err=fallback_err, exc_type=type(ex).__name__)

            return adapter

        self.custom_instance_func = create_vanilla_swap_adapter


class DefMcpXCurrencySwapAdapter(ItemDef):

    def __init__(self):
        super().__init__()
        self.init_data = {
            "is_wrapper": False,
            "method_prefix": "XCurrencySwapAdapter",
            "data_fields": [],
            "pyxll_def": {},
        }
        self.init_kv_list = [
            [
                ("XCurrencySwap", "object"),
                ("InstrumentId", "str"),
                ("TradeId", "str"),
                # 可选字段（CreditCurve, RecoveryRate）在 custom_instance_func 中处理
            ],
        ]

        def create_xcurrency_swap_adapter(args_dict):
            import mcp.mcp as mcp_module
            from mcp.wrapper import create_object_instance

            xccy_swap = args_dict.get('XCurrencySwap', args_dict.get('xcurrencySwap'))
            instrument_id = args_dict.get('InstrumentId', args_dict.get('instrumentId', 'XCCY_001'))
            trade_id = args_dict.get('TradeId', args_dict.get('tradeId', 'TRADE_XCCY_001'))
            portfolio_key = args_dict.get('PortfolioKey', args_dict.get('portfolioKey', ''))
            credit_curve = args_dict.get('CreditCurve', args_dict.get('creditCurve'))
            recovery_rate = args_dict.get('RecoveryRate', args_dict.get('recoveryRate'))

            adapter = create_object_instance("mcp.mcp", "MXCurrencySwapAdapter", [
                xccy_swap,
                instrument_id,
                trade_id,
                portfolio_key or ""
            ])

            if credit_curve is not None:
                adapter.SetCreditCurve(credit_curve)
            if recovery_rate is not None:
                adapter.SetRecoveryRate(recovery_rate)

            # 设置 PFE 计算器（VaR/ES/EE/PFE/DFE 依赖）
            has_pfe = hasattr(adapter, 'setPFECalculator')
            XCCYPFECalc = getattr(getattr(mcp_module, 'metrics', None), 'XCCYPFECalculator', None) or getattr(mcp_module, 'XCCYPFECalculator', None)
            pfe_set_ok = False
            if XCCYPFECalc is not None and has_pfe:
                try:
                    PFEConfig = getattr(XCCYPFECalc, 'PFEConfig', None)
                    if PFEConfig is not None:
                        cfg = PFEConfig()
                        cfg.num_simulations = 1000
                        cfg.confidence_level = 0.95
                        pfe_calc = XCCYPFECalc(cfg)
                    else:
                        pfe_calc = XCCYPFECalc()
                    adapter.setPFECalculator(pfe_calc)
                    adapter._pfe_calc_ref = pfe_calc
                    pfe_set_ok = True
                except Exception:
                    pass

            # 回退：MXCurrencySwapAdapter 无 setPFECalculator 时，改用 XCurrencySwapAdapter
            if not pfe_set_ok and (hasattr(mcp_module, 'XCurrencySwapAdapter') or hasattr(mcp_module, 'CreateXCurrencySwapAdapter')):
                try:
                    if hasattr(mcp_module, 'CreateXCurrencySwapAdapter'):
                        handler = xccy_swap.getHandler() if hasattr(xccy_swap, 'getHandler') else xccy_swap
                        adapter = mcp_module.CreateXCurrencySwapAdapter(handler, instrument_id, trade_id, portfolio_key or "")
                    else:
                        adapter = mcp_module.XCurrencySwapAdapter(xccy_swap, instrument_id, trade_id, portfolio_key or "")
                    if credit_curve is not None:
                        cc_arg = credit_curve.getHandler() if hasattr(credit_curve, 'getHandler') else credit_curve
                        adapter.SetCreditCurve(cc_arg)
                    if recovery_rate is not None:
                        adapter.SetRecoveryRate(float(recovery_rate))
                    if hasattr(adapter, 'setResultTermCurrency'):
                        adapter.setResultTermCurrency(True)
                    if XCCYPFECalc is not None and hasattr(adapter, 'setPFECalculator'):
                        PFEConfig = getattr(XCCYPFECalc, 'PFEConfig', None)
                        if PFEConfig:
                            cfg = PFEConfig()
                            cfg.num_simulations = 1000
                            cfg.confidence_level = 0.95
                            pfe_calc = XCCYPFECalc(cfg)
                        else:
                            pfe_calc = XCCYPFECalc()
                        adapter.setPFECalculator(pfe_calc)
                        adapter._pfe_calc_ref = pfe_calc
                        pfe_set_ok = True
                except Exception:
                    pass

            return adapter

        self.custom_instance_func = create_xcurrency_swap_adapter


class DefMcpRepoAdapter(ItemDef):

    def __init__(self):
        super().__init__()
        self.init_data = {
            "is_wrapper": False,
            "method_prefix": "RepoAdapter",
            "data_fields": [],
            "pyxll_def": {},
        }
        self.init_kv_list = [
            [
                ("RepurchaseProduct", "object"),
                ("InstrumentId", "str"),
                ("TradeId", "str"),
                # 可选字段（ValuationCurve, CollateralCurve）在 custom_instance_func 中处理
            ],
        ]

        def create_repo_adapter(args_dict):
            import mcp.mcp as mcp_module
            from mcp.wrapper import create_object_instance

            repurchase_product = args_dict.get('RepurchaseProduct', args_dict.get('repurchaseProduct'))
            instrument_id = args_dict.get('InstrumentId', args_dict.get('instrumentId', 'Repo_001'))
            trade_id = args_dict.get('TradeId', args_dict.get('tradeId', 'TRADE_Repo_001'))
            valuation_curve = args_dict.get('ValuationCurve', args_dict.get('valuationCurve'))
            collateral_curve = args_dict.get('CollateralCurve', args_dict.get('collateralCurve'))

            adapter = create_object_instance("mcp.mcp", "MRepoAdapter", [
                repurchase_product,
                instrument_id,
                trade_id
            ])

            if valuation_curve is not None:
                adapter.setValuationCurve(valuation_curve)
            if collateral_curve is not None:
                adapter.SetCollateralCurve(collateral_curve)

            return adapter

        self.custom_instance_func = create_repo_adapter


class DefMcpLoanAndDeposAdapter(ItemDef):

    def __init__(self):
        super().__init__()
        self.init_data = {
            "is_wrapper": False,
            "method_prefix": "LoanAndDeposAdapter",
            "data_fields": [],
            "pyxll_def": {},
        }
        self.init_kv_list = [
            [
                ("LoanAndDepos", "object"),
                ("InstrumentId", "str"),
                ("TradeId", "str"),
                ("PortfolioKey", "str"),
                ("Currency", "str"),
                ("ValuationCurve", "object"),
            ],
        ]

        def create_loan_and_depos_adapter(args_dict):
            from mcp.wrapper import create_object_instance

            loan_and_depos = args_dict.get('LoanAndDepos', args_dict.get('loanAndDepos'))
            instrument_id = args_dict.get('InstrumentId', args_dict.get('instrumentId', 'DEPO_001'))
            trade_id = args_dict.get('TradeId', args_dict.get('tradeId', 'TRADE_DEPO_001'))
            portfolio_key = args_dict.get('PortfolioKey', args_dict.get('portfolioKey', ''))
            currency = args_dict.get('Currency', args_dict.get('currency', 'CNY'))
            valuation_curve = args_dict.get('ValuationCurve', args_dict.get('valuationCurve'))

            adapter = create_object_instance("mcp.mcp", "MLoanAndDeposAdapter", [
                loan_and_depos,
                instrument_id,
                trade_id,
                portfolio_key or "",
                currency or "CNY"
            ])

            if valuation_curve is not None:
                try:
                    adapter.setValuationCurve(valuation_curve)
                except Exception:
                    pass

            # 保持引用，防止 GC 回收导致 C++ 层悬空指针
            adapter._loan_and_depos_ref = loan_and_depos
            adapter._valuation_curve_ref = valuation_curve

            return adapter

        self.custom_instance_func = create_loan_and_depos_adapter


class DefMcpFRAAdapter(ItemDef):

    def __init__(self):
        super().__init__()
        self.init_data = {
            "is_wrapper": False,
            "method_prefix": "FRAAdapter",
            "data_fields": [],
            "pyxll_def": {},
        }
        self.init_kv_list = [
            [
                ("SettlementDate", "date"),
                ("StartDate", "date"),
                ("EndDate", "date"),
                ("Notional", "float"),
                ("FixedRate", "float"),
                ("InstrumentId", "str"),
                ("TradeId", "str"),
                ("PortfolioKey", "str"),
                ("Currency", "str"),
                ("ValuationCurve", "object"),
                ("DayCounter", "str"),
                ("RateTenor", "str"),
                ("Calendar", "object"),
            ],
        ]

        def create_fra_adapter(args_dict):
            from mcp.wrapper import create_object_instance
            from mcp.utils.excel_utils import pf_date

            def _date(val, default):
                try:
                    s = pf_date(val) if val is not None and val != '' else ''
                    return s if s else default
                except Exception:
                    return default

            settlement_date = _date(args_dict.get('SettlementDate', args_dict.get('settlementDate')), '2025-06-30')
            start_date = _date(args_dict.get('StartDate', args_dict.get('startDate')), '2025-09-30')
            end_date = _date(args_dict.get('EndDate', args_dict.get('endDate')), '2025-12-30')
            notional = args_dict.get('Notional', args_dict.get('notional', 10000000))
            fixed_rate = args_dict.get('FixedRate', args_dict.get('fixedRate', 0.025))
            instrument_id = args_dict.get('InstrumentId', args_dict.get('instrumentId', 'FRA_001'))
            trade_id = args_dict.get('TradeId', args_dict.get('tradeId', 'TRADE_FRA_001'))
            portfolio_key = args_dict.get('PortfolioKey', args_dict.get('portfolioKey', ''))
            currency = args_dict.get('Currency', args_dict.get('currency', 'CNY'))
            valuation_curve = args_dict.get('ValuationCurve', args_dict.get('valuationCurve'))
            day_counter = args_dict.get('DayCounter', args_dict.get('dayCounter', 'Act365Fixed'))
            rate_tenor = args_dict.get('RateTenor', args_dict.get('rateTenor', '3M'))
            calendar = args_dict.get('Calendar', args_dict.get('calendar'))

            adapter = create_object_instance("mcp.mcp", "MFRAAdapter", [
                str(settlement_date),
                str(start_date),
                str(end_date),
                float(notional),
                float(fixed_rate),
                str(instrument_id),
                str(trade_id),
                portfolio_key or "",
                currency or "CNY",
                str(day_counter),
                str(rate_tenor),
                calendar if calendar is not None else None
            ])

            if valuation_curve is not None:
                try:
                    adapter.setValuationCurve(valuation_curve)
                except Exception:
                    pass

            # 保持引用，防止 GC 回收导致 C++ 层悬空指针
            adapter._valuation_curve_ref = valuation_curve

            return adapter

        self.custom_instance_func = create_fra_adapter


class DefMcpBondLendingAdapter(ItemDef):

    def __init__(self):
        super().__init__()
        self.init_data = {
            "is_wrapper": False,
            "method_prefix": "BondLendingAdapter",
            "data_fields": [],
            "pyxll_def": {},
        }
        self.init_kv_list = [
            [
                ("ReferenceDate", "date"),
                ("StartDate", "date"),
                ("EndDate", "date"),
                ("BondMaturityDate", "date"),
                ("BondCouponRate", "float"),
                ("BondFrequency", "int"),
                ("Notional", "float"),
                ("LendingFeeRate", "float"),
                ("UnderlyingDirtyPrice", "float"),
                ("InstrumentId", "str"),
                ("TradeId", "str"),
                ("PortfolioKey", "str"),
                ("Currency", "str"),
                ("ValuationCurve", "object"),
                ("DiscountCurve", "object"),
            ],
        ]

        def create_bond_lending_adapter(args_dict):
            from mcp.wrapper import create_object_instance
            from mcp.utils.excel_utils import pf_date

            def _date(val, default):
                try:
                    s = pf_date(val) if val is not None and val != '' else ''
                    return s if s else default
                except Exception:
                    return default

            ref_date = _date(args_dict.get('ReferenceDate', args_dict.get('referenceDate')), '2025-01-17')
            start_date = _date(args_dict.get('StartDate', args_dict.get('startDate')), '2025-01-17')
            end_date = _date(args_dict.get('EndDate', args_dict.get('endDate')), '2025-07-17')
            bond_mat = _date(args_dict.get('BondMaturityDate', args_dict.get('bondMaturityDate')), '2027-01-17')
            bond_coupon = args_dict.get('BondCouponRate', args_dict.get('bondCouponRate', 0.03))
            bond_freq = args_dict.get('BondFrequency', args_dict.get('bondFrequency', 2))
            notional = args_dict.get('Notional', args_dict.get('notional', 10000000))
            lending_fee = args_dict.get('LendingFeeRate', args_dict.get('lendingFeeRate', 0.001))
            dirty_price = args_dict.get('UnderlyingDirtyPrice', args_dict.get('underlyingDirtyPrice', 100.0))
            instrument_id = args_dict.get('InstrumentId', args_dict.get('instrumentId', 'BL_001'))
            trade_id = args_dict.get('TradeId', args_dict.get('tradeId', 'TRADE_BL_001'))
            portfolio_key = args_dict.get('PortfolioKey', args_dict.get('portfolioKey', ''))
            currency = args_dict.get('Currency', args_dict.get('currency', 'CNY'))
            valuation_curve = args_dict.get('ValuationCurve', args_dict.get('valuationCurve'))
            discount_curve = args_dict.get('DiscountCurve', args_dict.get('discountCurve'))

            adapter = create_object_instance("mcp.mcp", "MBondLendingAdapter", [
                str(ref_date),
                str(start_date),
                str(end_date),
                str(bond_mat),
                float(bond_coupon),
                int(bond_freq),
                float(notional),
                float(lending_fee),
                float(dirty_price),
                str(instrument_id),
                str(trade_id),
                portfolio_key or "",
                currency or "CNY",
            ])

            if valuation_curve is not None:
                try:
                    adapter.setValuationCurve(valuation_curve)
                except Exception:
                    pass
            if discount_curve is not None:
                try:
                    adapter.setDiscountCurve(discount_curve)
                except Exception:
                    pass

            adapter._valuation_curve_ref = valuation_curve
            adapter._discount_curve_ref = discount_curve
            return adapter

        self.custom_instance_func = create_bond_lending_adapter


class DefMcpCommodityLendingAdapter(ItemDef):

    def __init__(self):
        super().__init__()
        self.init_data = {
            "is_wrapper": False,
            "method_prefix": "CommodityLendingAdapter",
            "data_fields": [],
            "pyxll_def": {},
        }
        self.init_kv_list = [
            [
                ("Underlying", "str"),
                ("ReferenceDate", "date"),
                ("StartDate", "date"),
                ("EndDate", "date"),
                ("Notional", "float"),
                ("LendingFeeRate", "float"),
                ("CommodityPrice", "float"),
                ("InstrumentId", "str"),
                ("TradeId", "str"),
                ("PortfolioKey", "str"),
                ("Currency", "str"),
                ("DiscountCurve", "object"),
            ],
        ]

        def create_commodity_lending_adapter(args_dict):
            from mcp.wrapper import create_object_instance
            from mcp.utils.excel_utils import pf_date

            def _date(val, default):
                try:
                    s = pf_date(val) if val is not None and val != '' else ''
                    return s if s else default
                except Exception:
                    return default

            underlying = args_dict.get('Underlying', args_dict.get('underlying', 'AU'))
            ref_date = _date(args_dict.get('ReferenceDate', args_dict.get('referenceDate')), '2025-01-17')
            start_date = _date(args_dict.get('StartDate', args_dict.get('startDate')), '2025-01-17')
            end_date = _date(args_dict.get('EndDate', args_dict.get('endDate')), '2025-07-17')
            notional = args_dict.get('Notional', args_dict.get('notional', 1000))
            lending_fee = args_dict.get('LendingFeeRate', args_dict.get('lendingFeeRate', 0.003))
            commodity_price = args_dict.get('CommodityPrice', args_dict.get('commodityPrice', 450.0))
            instrument_id = args_dict.get('InstrumentId', args_dict.get('instrumentId', 'CL_001'))
            trade_id = args_dict.get('TradeId', args_dict.get('tradeId', 'TRADE_CL_001'))
            portfolio_key = args_dict.get('PortfolioKey', args_dict.get('portfolioKey', ''))
            currency = args_dict.get('Currency', args_dict.get('currency', 'CNY'))
            discount_curve = args_dict.get('DiscountCurve', args_dict.get('discountCurve'))

            adapter = create_object_instance("mcp.mcp", "MCommodityLendingAdapter", [
                str(underlying),
                str(ref_date),
                str(start_date),
                str(end_date),
                float(notional),
                float(lending_fee),
                float(commodity_price),
                str(instrument_id),
                str(trade_id),
                portfolio_key or "",
                currency or "CNY",
            ])

            if discount_curve is not None:
                try:
                    adapter.setDiscountCurve(discount_curve)
                except Exception:
                    pass

            adapter._discount_curve_ref = discount_curve
            return adapter

        self.custom_instance_func = create_commodity_lending_adapter


class DefMcpBillDiscountAdapter(ItemDef):

    def __init__(self):
        super().__init__()
        self.init_data = {
            "is_wrapper": False,
            "method_prefix": "BillDiscountAdapter",
            "data_fields": [],
            "pyxll_def": {},
        }
        self.init_kv_list = [
            [
                ("ValuationDate", "date"),
                ("StartDate", "date"),
                ("MaturityDate", "date"),
                ("Notional", "float"),
                ("InstrumentId", "str"),
                ("TradeId", "str"),
                ("PortfolioKey", "str"),
                ("Currency", "str"),
                ("ValuationCurve", "object"),
            ],
        ]

        def create_bill_discount_adapter(args_dict):
            from mcp.wrapper import create_object_instance
            from mcp.utils.excel_utils import pf_date

            def _date(val, default):
                try:
                    s = pf_date(val) if val is not None and val != '' else ''
                    return s if s else default
                except Exception:
                    return default

            valuation_date = _date(args_dict.get('ValuationDate', args_dict.get('valuationDate')), '2025-06-30')
            start_date = _date(args_dict.get('StartDate', args_dict.get('startDate')), valuation_date)
            maturity_date = _date(args_dict.get('MaturityDate', args_dict.get('maturityDate')), '2025-12-31')
            notional = args_dict.get('Notional', args_dict.get('notional', 5000000))
            instrument_id = args_dict.get('InstrumentId', args_dict.get('instrumentId', 'BILL_001'))
            trade_id = args_dict.get('TradeId', args_dict.get('tradeId', 'TRADE_BILL_001'))
            portfolio_key = args_dict.get('PortfolioKey', args_dict.get('portfolioKey', ''))
            currency = args_dict.get('Currency', args_dict.get('currency', 'CNY'))
            valuation_curve = args_dict.get('ValuationCurve', args_dict.get('valuationCurve'))

            adapter = create_object_instance("mcp.mcp", "MBillDiscountAdapter", [
                str(valuation_date),
                str(start_date),
                str(maturity_date),
                float(notional),
                str(instrument_id),
                str(trade_id),
                portfolio_key or "",
                currency or "CNY",
            ])

            if valuation_curve is not None:
                try:
                    adapter.setValuationCurve(valuation_curve)
                except Exception:
                    pass

            adapter._valuation_curve_ref = valuation_curve
            return adapter

        self.custom_instance_func = create_bill_discount_adapter


class DefMcpBillRepoAdapter(ItemDef):

    def __init__(self):
        super().__init__()
        self.init_data = {
            "is_wrapper": False,
            "method_prefix": "BillRepoAdapter",
            "data_fields": [],
            "pyxll_def": {},
        }
        self.init_kv_list = [
            [
                ("ValuationDate", "date"),
                ("StartDate", "date"),
                ("EndDate", "date"),
                ("Notional", "float"),
                ("RepoRate", "float"),
                ("BillMaturityDate", "date"),
                ("BillFaceValue", "float"),
                ("InstrumentId", "str"),
                ("TradeId", "str"),
                ("PortfolioKey", "str"),
                ("Currency", "str"),
                ("RepoType", "str"),
                ("DiscountCurve", "object"),
                ("BillCurve", "object"),
            ],
        ]

        def create_bill_repo_adapter(args_dict):
            from mcp.wrapper import create_object_instance
            from mcp.utils.excel_utils import pf_date

            def _date(val, default):
                try:
                    s = pf_date(val) if val is not None and val != '' else ''
                    return s if s else default
                except Exception:
                    return default

            valuation_date = _date(args_dict.get('ValuationDate', args_dict.get('valuationDate')), '2025-06-30')
            start_date = _date(args_dict.get('StartDate', args_dict.get('startDate')), '2025-01-17')
            end_date = _date(args_dict.get('EndDate', args_dict.get('endDate')), '2025-04-17')
            notional = args_dict.get('Notional', args_dict.get('notional', 5000000))
            repo_rate = args_dict.get('RepoRate', args_dict.get('repoRate', 0.025))
            bill_maturity_date = _date(args_dict.get('BillMaturityDate', args_dict.get('billMaturityDate')), end_date)
            bill_face_value = args_dict.get('BillFaceValue', args_dict.get('billFaceValue', 0))
            if bill_face_value <= 0:
                bill_face_value = notional
            instrument_id = args_dict.get('InstrumentId', args_dict.get('instrumentId', 'BILL_REPO_001'))
            trade_id = args_dict.get('TradeId', args_dict.get('tradeId', 'TRADE_BILL_REPO_001'))
            portfolio_key = args_dict.get('PortfolioKey', args_dict.get('portfolioKey', ''))
            currency = args_dict.get('Currency', args_dict.get('currency', 'CNY'))
            repo_type = args_dict.get('RepoType', args_dict.get('repoType', 'Repo'))
            discount_curve = args_dict.get('DiscountCurve', args_dict.get('discountCurve'))
            bill_curve = args_dict.get('BillCurve', args_dict.get('billCurve'))

            adapter = create_object_instance("mcp.mcp", "MBillRepoAdapter", [
                str(valuation_date),
                str(start_date),
                str(end_date),
                float(notional),
                float(repo_rate),
                str(bill_maturity_date),
                float(bill_face_value),
                str(instrument_id),
                str(trade_id),
                portfolio_key or "",
                currency or "CNY",
                str(repo_type),
            ])

            if discount_curve is not None:
                try:
                    adapter.setDiscountCurve(discount_curve)
                except Exception:
                    pass
            if bill_curve is not None:
                try:
                    adapter.setBillCurve(bill_curve)
                except Exception:
                    pass

            adapter._discount_curve_ref = discount_curve
            adapter._bill_curve_ref = bill_curve
            return adapter

        self.custom_instance_func = create_bill_repo_adapter


class DefMcpBasisSwapAdapter(ItemDef):

    def __init__(self):
        super().__init__()
        self.init_data = {
            "is_wrapper": False,
            "method_prefix": "BasisSwapAdapter",
            "data_fields": [],
            "pyxll_def": {},
        }
        self.init_kv_list = [
            [
                ("SettlementDate", "date"),
                ("StartDate", "date"),
                ("EndDate", "date"),
                ("Notional", "float"),
                ("BaseMargin", "float"),
                ("TermMargin", "float"),
                ("InstrumentId", "str"),
                ("TradeId", "str"),
                ("PortfolioKey", "str"),
                ("Currency", "str"),
                ("BaseLegEstimationCurve", "object"),
                ("BaseLegDiscountCurve", "object"),
                ("TermLegEstimationCurve", "object"),
                ("TermLegDiscountCurve", "object"),
                ("DayCounter", "str"),
                ("BaseFrequency", "str"),
                ("TermFrequency", "str"),
                ("Calendar", "object"),
            ],
        ]

        def create_basis_swap_adapter(args_dict):
            from mcp.wrapper import create_object_instance
            from mcp.utils.excel_utils import pf_date

            def _date(val, default):
                try:
                    s = pf_date(val) if val is not None and val != '' else ''
                    return s if s else default
                except Exception:
                    return default

            settlement_date = _date(args_dict.get('SettlementDate', args_dict.get('settlementDate')), '2025-06-30')
            start_date = _date(args_dict.get('StartDate', args_dict.get('startDate')), '2025-06-30')
            end_date = _date(args_dict.get('EndDate', args_dict.get('endDate')), '2028-06-30')
            notional = args_dict.get('Notional', args_dict.get('notional', 100000000))
            base_margin = args_dict.get('BaseMargin', args_dict.get('baseMargin', 0.0))
            term_margin = args_dict.get('TermMargin', args_dict.get('termMargin', 0.0))
            instrument_id = args_dict.get('InstrumentId', args_dict.get('instrumentId', 'BS_001'))
            trade_id = args_dict.get('TradeId', args_dict.get('tradeId', 'TRADE_BS_001'))
            portfolio_key = args_dict.get('PortfolioKey', args_dict.get('portfolioKey', ''))
            currency = args_dict.get('Currency', args_dict.get('currency', 'CNY'))
            base_est_curve = args_dict.get('BaseLegEstimationCurve', args_dict.get('baseLegEstimationCurve'))
            base_disc_curve = args_dict.get('BaseLegDiscountCurve', args_dict.get('baseLegDiscountCurve'))
            term_est_curve = args_dict.get('TermLegEstimationCurve', args_dict.get('termLegEstimationCurve'))
            term_disc_curve = args_dict.get('TermLegDiscountCurve', args_dict.get('termLegDiscountCurve'))
            day_counter = args_dict.get('DayCounter', args_dict.get('dayCounter', 'Act365Fixed'))
            base_frequency = args_dict.get('BaseFrequency', args_dict.get('baseFrequency', 'Quarterly'))
            term_frequency = args_dict.get('TermFrequency', args_dict.get('termFrequency', 'Quarterly'))
            calendar = args_dict.get('Calendar', args_dict.get('calendar'))

            adapter = create_object_instance("mcp.mcp", "MBasisSwapAdapter", [
                str(settlement_date),
                str(start_date),
                str(end_date),
                float(notional),
                float(base_margin),
                float(term_margin),
                str(instrument_id),
                str(trade_id),
                portfolio_key or "",
                currency or "CNY",
                str(day_counter),
                str(base_frequency),
                str(term_frequency),
                calendar if calendar is not None else None
            ])

            for curve, setter in [
                (base_est_curve, 'setBaseLegEstimationCurve'),
                (base_disc_curve, 'setBaseLegDiscountCurve'),
                (term_est_curve, 'setTermLegEstimationCurve'),
                (term_disc_curve, 'setTermLegDiscountCurve'),
            ]:
                if curve is not None:
                    try:
                        getattr(adapter, setter)(curve)
                    except Exception:
                        pass

            # 保持引用，防止 GC 回收导致 C++ 层悬空指针
            adapter._base_est_curve_ref = base_est_curve
            adapter._base_disc_curve_ref = base_disc_curve
            adapter._term_est_curve_ref = term_est_curve
            adapter._term_disc_curve_ref = term_disc_curve

            return adapter

        self.custom_instance_func = create_basis_swap_adapter


class DefMcpBondForwardAdapter(ItemDef):

    def __init__(self):
        super().__init__()
        self.init_data = {
            "is_wrapper": False,
            "method_prefix": "BondForwardAdapter",
            "data_fields": [],
            "pyxll_def": {},
        }
        self.init_kv_list = [
            [
                ("Underlying", "str"),
                ("MaturityDate", "date"),
                ("Coupon", "float"),
                ("Frequency", "int"),
                ("ValueDate", "date"),
                ("IssuePrice", "float"),
                ("Notional", "float"),
                ("ForwardSettlementDate", "date"),
                ("InstrumentId", "str"),
                ("TradeId", "str"),
                ("PortfolioKey", "str"),
                ("Currency", "str"),
                ("DiscountCurve", "object"),
                ("DayCounter", "str"),
                ("Calendar", "object"),
            ],
        ]

        def create_bond_forward_adapter(args_dict):
            from mcp.wrapper import create_object_instance
            from mcp.utils.excel_utils import pf_date

            def _date(val, default):
                try:
                    s = pf_date(val) if val is not None and val != '' else ''
                    return s if s else default
                except Exception:
                    return default

            value_date = _date(args_dict.get('ValueDate', args_dict.get('valueDate')), '2025-01-15')
            maturity_date = _date(args_dict.get('MaturityDate', args_dict.get('maturityDate')), '2027-12-13')
            coupon = args_dict.get('Coupon', args_dict.get('coupon', 0.035))
            frequency = args_dict.get('Frequency', args_dict.get('frequency', 2))
            issue_price = args_dict.get('IssuePrice', args_dict.get('issuePrice', 100))
            notional = args_dict.get('Notional', args_dict.get('notional', 10000000))
            forward_date = _date(args_dict.get('ForwardSettlementDate', args_dict.get('forwardSettlementDate')), '2025-06-30')
            instrument_id = args_dict.get('InstrumentId', args_dict.get('instrumentId', 'BF_001'))
            trade_id = args_dict.get('TradeId', args_dict.get('tradeId', 'TRADE_BF_001'))
            portfolio_key = args_dict.get('PortfolioKey', args_dict.get('portfolioKey', ''))
            currency = args_dict.get('Currency', args_dict.get('currency', 'CNY'))
            discount_curve = args_dict.get('DiscountCurve', args_dict.get('discountCurve'))
            day_counter = args_dict.get('DayCounter', args_dict.get('dayCounter', 'Act365Fixed'))
            calendar = args_dict.get('Calendar', args_dict.get('calendar'))

            adapter = create_object_instance("mcp.mcp", "MBondForwardAdapter", [
                str(value_date),
                str(maturity_date),
                float(coupon),
                int(frequency),
                float(issue_price),
                str(forward_date),
                float(notional),
                str(instrument_id),
                str(trade_id),
                portfolio_key or "",
                currency or "CNY",
                str(day_counter),
                calendar if calendar is not None else None
            ])

            if discount_curve is not None:
                try:
                    adapter.setDiscountCurve(discount_curve)
                except Exception:
                    pass

            adapter._discount_curve_ref = discount_curve

            return adapter

        self.custom_instance_func = create_bond_forward_adapter


class DefMcpTRSAdapter(ItemDef):

    def __init__(self):
        super().__init__()
        self.init_data = {
            "is_wrapper": False,
            "method_prefix": "TrsAdapter",
            "data_fields": [],
            "pyxll_def": {},
        }
        self.init_kv_list = [
            [
                ("TotalReturnSwap", "object"),
                ("InstrumentId", "str"),
                ("TradeId", "str"),
                ("PortfolioKey", "str"),
                ("DiscountCurve", "object"),
                ("FundingCurve", "object"),
                ("UnderlyingPrice", "float"),
            ],
        ]

        def create_trs_adapter(args_dict):
            import mcp.mcp as mcp_module
            from mcp.wrapper import create_object_instance, McpYieldCurve, McpSwapCurve, McpBondCurve, McpTRSAdapter

            trs = args_dict.get('TotalReturnSwap', args_dict.get('totalReturnSwap'))
            instrument_id = args_dict.get('InstrumentId', args_dict.get('instrumentId', 'TRS_001'))
            trade_id = args_dict.get('TradeId', args_dict.get('tradeId', 'TRADE_TRS_001'))
            portfolio_key = args_dict.get('PortfolioKey', args_dict.get('portfolioKey', ''))
            discount_curve = args_dict.get('DiscountCurve', args_dict.get('discountCurve'))
            funding_curve = args_dict.get('FundingCurve', args_dict.get('fundingCurve'))
            underlying_price = args_dict.get('UnderlyingPrice', args_dict.get('underlyingPrice'))

            raw_adapter = create_object_instance("mcp.mcp", "MTRSAdapter", [
                trs,
                instrument_id,
                trade_id,
                portfolio_key or ""
            ])

            # 与 VanillaSwapAdapter/FXNDFAdapter 一致：仅当曲线为 M 类型时设置
            curve_types = (mcp_module.MYieldCurve, mcp_module.MBondCurve, mcp_module.MSwapCurve,
                          McpYieldCurve, McpSwapCurve, McpBondCurve)
            if discount_curve is not None and isinstance(discount_curve, curve_types):
                raw_adapter.setDiscountCurve(discount_curve)
            if funding_curve is not None and isinstance(funding_curve, curve_types):
                raw_adapter.setFundingCurve(funding_curve)
            if underlying_price is not None:
                raw_adapter.setUnderlyingPrice(float(underlying_price))

            # 用 McpTRSAdapter 代理包装，确保 PyXLL 缓存 key 为 McpTRSAdapter@N
            adapter = McpTRSAdapter(raw_adapter)
            # 保持引用，防止 GC 回收导致 C++ 层悬空指针
            adapter._trs_ref = trs
            adapter._discount_curve_ref = discount_curve
            adapter._funding_curve_ref = funding_curve
            adapter._underlying_price_ref = underlying_price  # 供 MarketParRate 委托使用

            return adapter

        self.custom_instance_func = create_trs_adapter


class DefMcpFundAdapter(ItemDef):

    def __init__(self):
        super().__init__()
        self.init_data = {
            "is_wrapper": False,
            "method_prefix": "FundAdapter",
            "data_fields": [],
            "pyxll_def": {},
        }
        self.init_kv_list = [
            [
                ("Fund", "object"),
                ("InstrumentId", "str"),
                ("TradeId", "str"),
                ("PortfolioKey", "str", "", ""),
                # 可选字段（DiscountCurve, PreviousNAV, PreviousPrice, PreviousPV）在 custom_instance_func 中处理
            ],
        ]

        def create_fund_adapter(args_dict):
            import mcp.mcp as mcp_module
            from mcp.wrapper import create_object_instance

            fund = args_dict.get('Fund', args_dict.get('fund'))
            instrument_id = args_dict.get('InstrumentId', args_dict.get('instrumentId', 'Fund_001'))
            trade_id = args_dict.get('TradeId', args_dict.get('tradeId', 'TRADE_Fund_001'))
            portfolio_key = args_dict.get('PortfolioKey', args_dict.get('portfolioKey', ''))
            discount_curve = args_dict.get('DiscountCurve', args_dict.get('discountCurve'))
            previous_nav = args_dict.get('PreviousNAV', args_dict.get('previousNAV'))
            previous_price = args_dict.get('PreviousPrice', args_dict.get('previousPrice'))
            previous_pv = args_dict.get('PreviousPV', args_dict.get('previousPV'))

            adapter = create_object_instance("mcp.mcp", "MFundAdapter", [
                fund,
                instrument_id,
                trade_id,
                portfolio_key
            ])

            if discount_curve is not None:
                adapter.setDiscountCurve(discount_curve)

            if previous_nav is not None and previous_price is not None and previous_pv is not None:
                adapter.setPreviousState(previous_nav, previous_price, previous_pv)

            return adapter

        self.custom_instance_func = create_fund_adapter


class DefMcpWMProductAdapter(ItemDef):

    def __init__(self):
        super().__init__()
        self.init_data = {
            "is_wrapper": False,
            "method_prefix": "WMProductAdapter",
            "data_fields": [],
            "pyxll_def": {},
        }
        self.init_kv_list = [
            [
                ("FundAdapter", "object"),
            ],
        ]

        def create_wm_product_adapter(args_dict):
            from mcp.wrapper import create_object_instance

            fund_adapter = args_dict.get('FundAdapter', args_dict.get('fundAdapter'))
            if fund_adapter is None:
                raise ValueError("DefMcpWMProductAdapter: FundAdapter is required")

            adapter = create_object_instance("mcp.mcp", "MWMProductAdapter", [fund_adapter])
            return adapter

        self.custom_instance_func = create_wm_product_adapter


class DefMcpFXNDFAdapter(ItemDef):

    def __init__(self):
        super().__init__()
        self.init_data = {
            "is_wrapper": False,
            "method_prefix": "FXNDFAdapter",
            "data_fields": [],
            "pyxll_def": {},
        }
        self.init_kv_list = [
            [
                ("FXNDF", "object"),
                ("InstrumentId", "str"),
                ("TradeId", "str"),
                ("PortfolioKey", "str", "", ""),
                # 可选字段（ForwardPointsCurve, DiscountCurve, FxRate, PreviousPV）在 custom_instance_func 中处理
            ],
        ]

        def create_fxndf_adapter(args_dict):
            import mcp.mcp as mcp_module
            from mcp.wrapper import create_object_instance

            fxndf = args_dict.get('FXNDF', args_dict.get('fxndf'))
            instrument_id = args_dict.get('InstrumentId', args_dict.get('instrumentId', 'FXNDF_001'))
            trade_id = args_dict.get('TradeId', args_dict.get('tradeId', 'TRADE_FXNDF_001'))
            portfolio_key = args_dict.get('PortfolioKey', args_dict.get('portfolioKey', ''))
            forward_points_curve = args_dict.get('ForwardPointsCurve', args_dict.get('forwardPointsCurve'))
            discount_curve = args_dict.get('DiscountCurve', args_dict.get('discountCurve'))
            fx_rate = args_dict.get('FxRate', args_dict.get('fxRate'))
            previous_pv = args_dict.get('PreviousPV', args_dict.get('previousPV'))

            adapter = create_object_instance("mcp.mcp", "MFXNDFAdapter", [
                fxndf,
                instrument_id,
                trade_id,
                portfolio_key
            ])

            if forward_points_curve is not None:
                adapter.setForwardPointsCurve(forward_points_curve)
            if discount_curve is not None:
                adapter.setDiscountCurve(discount_curve)

            if fx_rate is not None and previous_pv is not None:
                adapter.setFxRate(fx_rate)
                adapter.setPreviousState(fx_rate, previous_pv)

            return adapter

        self.custom_instance_func = create_fxndf_adapter


class DefMcpFXForwardSwapAdapter(ItemDef):

    def __init__(self):
        super().__init__()
        self.init_data = {
            "is_wrapper": False,
            "method_prefix": "FXForwardSwapAdapter",
            "data_fields": [],
            "pyxll_def": {},
        }
        self.init_kv_list = [
            [
                ("ForwardOutright", "object"),
                ("InstrumentId", "str"),
                ("TradeId", "str"),
                # 可选字段（ForwardPointsCurve, DiscountCurve, FxSpot, PreviousPV）在 custom_instance_func 中处理
            ],
        ]

        def create_fx_forward_swap_adapter(args_dict):
            import mcp.mcp as mcp_module
            from mcp.wrapper import create_object_instance

            forward_outright = args_dict.get('ForwardOutright', args_dict.get('forwardOutright'))
            instrument_id = args_dict.get('InstrumentId', args_dict.get('instrumentId', 'FXForwardSwap_001'))
            trade_id = args_dict.get('TradeId', args_dict.get('tradeId', 'TRADE_FXForwardSwap_001'))
            forward_points_curve = args_dict.get('ForwardPointsCurve', args_dict.get('forwardPointsCurve'))
            discount_curve = args_dict.get('DiscountCurve', args_dict.get('discountCurve'))
            fx_spot = args_dict.get('FxSpot', args_dict.get('fxSpot'))
            previous_pv = args_dict.get('PreviousPV', args_dict.get('previousPV'))

            adapter = create_object_instance("mcp.mcp", "MFXForwardSwapAdapter", [
                forward_outright,
                instrument_id,
                trade_id
            ])

            if forward_points_curve is not None:
                adapter.setForwardPointsCurve(forward_points_curve)
            if discount_curve is not None:
                adapter.setDiscountCurve(discount_curve)

            if fx_spot is not None and previous_pv is not None:
                adapter.setPreviousState(fx_spot, previous_pv)

            return adapter

        self.custom_instance_func = create_fx_forward_swap_adapter


class DefMcpFXOptionsAdapter(ItemDef):

    def __init__(self):
        super().__init__()
        self.init_data = {
            "is_wrapper": False,
            "method_prefix": "FXOptionsAdapter",
            "data_fields": [],
            "pyxll_def": {},
        }
        self.init_kv_list = [
            [
                ("Options", "object"),
                ("InstrumentId", "str"),
                ("TradeId", "str"),
                ("PortfolioKey", "str"),
            ],
        ]

        def create_fx_options_adapter(args_dict):
            import mcp.mcp as mcp_module
            from mcp.wrapper import create_object_instance

            options = args_dict.get('Options', args_dict.get('options'))
            instrument_id = args_dict.get('InstrumentId', args_dict.get('instrumentId', 'FXOption_001'))
            trade_id = args_dict.get('TradeId', args_dict.get('tradeId', 'TRADE_FXOption_001'))
            portfolio_key = args_dict.get('PortfolioKey', args_dict.get('portfolioKey', 'PORTFOLIO_001'))

            adapter = create_object_instance("mcp.mcp", "MFXOptionsAdapter", [
                options,
                instrument_id,
                trade_id,
                portfolio_key
            ])

            return adapter

        self.custom_instance_func = create_fx_options_adapter


class DefMcpEquityOptionAdapter(ItemDef):

    def __init__(self):
        super().__init__()
        self.init_data = {
            "is_wrapper": False,
            "method_prefix": "EquityOptionAdapter",
            "data_fields": [],
            "pyxll_def": {},
        }
        self.init_kv_list = [
            [
                ("Options", "object"),
                ("Underlying", "str", "", ""),
                ("InstrumentId", "str"),
                ("TradeId", "str"),
                ("PortfolioKey", "str", "", ""),
            ],
        ]

        def create_equity_option_adapter(args_dict):
            import mcp.mcp as mcp_module
            from mcp.wrapper import create_object_instance

            options = args_dict.get('Options', args_dict.get('options'))
            instrument_id = args_dict.get('InstrumentId', args_dict.get('instrumentId', 'EquityOption_001'))
            trade_id = args_dict.get('TradeId', args_dict.get('tradeId', 'TRADE_EquityOption_001'))
            portfolio_key = args_dict.get('PortfolioKey', args_dict.get('portfolioKey', 'PORTFOLIO_001'))
            underlying = args_dict.get('Underlying', args_dict.get('underlying', 'SHFE_COPPER'))

            adapter = create_object_instance("mcp.mcp", "MEquityOptionAdapter", [
                options,
                underlying,
                instrument_id,
                trade_id,
                portfolio_key
            ])

            return adapter

        self.custom_instance_func = create_equity_option_adapter


class DefMcpCommodityOptionAdapter(ItemDef):

    def __init__(self):
        super().__init__()
        self.init_data = {
            "is_wrapper": False,
            "method_prefix": "CommodityOptionAdapter",
            "data_fields": [],
            "pyxll_def": {},
        }
        self.init_kv_list = [
            [
                ("Options", "object"),
                ("InstrumentId", "str"),
                ("TradeId", "str"),
                ("Underlying", "str", "", ""),
            ],
        ]

        def create_commodity_option_adapter(args_dict):
            import mcp.mcp as mcp_module
            from mcp.wrapper import create_object_instance

            options = args_dict.get('Options', args_dict.get('options'))
            instrument_id = args_dict.get('InstrumentId', args_dict.get('instrumentId', 'CommodityOption_001'))
            trade_id = args_dict.get('TradeId', args_dict.get('tradeId', 'TRADE_CommodityOption_001'))
            underlying = args_dict.get('Underlying', args_dict.get('underlying', 'SHFE_COPPER'))

            adapter = create_object_instance("mcp.mcp", "MCommodityOptionAdapter", [
                options,
                underlying,
                instrument_id,
                trade_id,
                ""
            ])

            return adapter

        self.custom_instance_func = create_commodity_option_adapter


class DefMcpStructuredDerivativeProductAdapter(ItemDef):

    def __init__(self):
        super().__init__()
        self.init_data = {
            "is_wrapper": False,
            "method_prefix": "StructuredDerivativeProductAdapter",
            "data_fields": [],
            "pyxll_def": {},
        }
        self.init_kv_list = [
            [
                ("StructuredProduct", "object"),
                ("AssetClass", "int"),
                ("Underlying", "str"),
                ("InstrumentId", "str"),
                ("TradeId", "str"),
                ("PortfolioKey", "str"),
            ],
        ]

        def create_structured_product_adapter(args_dict):
            import mcp.mcp as mcp_module
            from mcp.wrapper import create_object_instance

            structured_product = args_dict.get('StructuredProduct', args_dict.get('structuredProduct'))
            asset_class = args_dict.get('AssetClass', args_dict.get('assetClass', 1))
            underlying = args_dict.get('Underlying', args_dict.get('underlying', ''))
            instrument_id = args_dict.get('InstrumentId', args_dict.get('instrumentId', 'StructuredProduct_001'))
            trade_id = args_dict.get('TradeId', args_dict.get('tradeId', 'TRADE_StructuredProduct_001'))
            portfolio_key = args_dict.get('PortfolioKey', args_dict.get('portfolioKey', 'PORTFOLIO_001'))

            adapter = create_object_instance("mcp.mcp", "MStructuredDerivativeProductAdapter", [
                structured_product,
                int(asset_class),
                underlying,
                instrument_id,
                trade_id,
                portfolio_key
            ])

            return adapter

        self.custom_instance_func = create_structured_product_adapter


class DefMcpEquitySpotAdapter(ItemDef):

    def __init__(self):
        super().__init__()
        self.init_data = {
            "is_wrapper": False,
            "method_prefix": "EquitySpotAdapter",
            "data_fields": [],
            "pyxll_def": {},
        }
        self.init_kv_list = [
            [
                ("EquitySpot", "object"),
                ("InstrumentId", "str"),
                ("TradeId", "str"),
                # 可选字段（DiscountCurve, PreviousSpot, PreviousPrice, PreviousPV）在 custom_instance_func 中处理
            ],
        ]

        def create_equity_spot_adapter(args_dict):
            import mcp.mcp as mcp_module
            from mcp.wrapper import create_object_instance

            equity_spot = args_dict.get('EquitySpot', args_dict.get('equitySpot'))
            instrument_id = args_dict.get('InstrumentId', args_dict.get('instrumentId', 'EquitySpot_001'))
            trade_id = args_dict.get('TradeId', args_dict.get('tradeId', 'TRADE_EquitySpot_001'))
            discount_curve = args_dict.get('DiscountCurve', args_dict.get('discountCurve'))
            previous_spot = args_dict.get('PreviousSpot', args_dict.get('previousSpot'))
            previous_price = args_dict.get('PreviousPrice', args_dict.get('previousPrice'))
            previous_pv = args_dict.get('PreviousPV', args_dict.get('previousPV'))

            adapter = create_object_instance("mcp.mcp", "MEquitySpotAdapter", [
                equity_spot,
                instrument_id,
                trade_id
            ])

            if discount_curve is not None:
                adapter.setDiscountCurve(discount_curve)

            if previous_spot is not None and previous_price is not None and previous_pv is not None:
                adapter.setPreviousState(previous_spot, previous_price, previous_pv)

            return adapter

        self.custom_instance_func = create_equity_spot_adapter


class DefMcpEquityFutureAdapter(ItemDef):

    def __init__(self):
        super().__init__()
        self.init_data = {
            "is_wrapper": False,
            "method_prefix": "EquityFutureAdapter",
            "data_fields": [],
            "pyxll_def": {},
        }
        self.init_kv_list = [
            [
                ("EquityFuture", "object"),
                ("InstrumentId", "str"),
                ("TradeId", "str"),
                ("PortfolioKey", "str", "", ""),
                # 可选字段（DiscountCurve, PreviousSpot, PreviousPrice, PreviousPV）在 custom_instance_func 中处理
            ],
        ]

        def create_equity_future_adapter(args_dict):
            import mcp.mcp as mcp_module
            from mcp.wrapper import create_object_instance

            equity_future = args_dict.get('EquityFuture', args_dict.get('equityFuture'))
            instrument_id = args_dict.get('InstrumentId', args_dict.get('instrumentId', 'EquityFuture_001'))
            trade_id = args_dict.get('TradeId', args_dict.get('tradeId', 'TRADE_EquityFuture_001'))
            portfolio_key = args_dict.get('PortfolioKey', args_dict.get('portfolioKey', ''))
            discount_curve = args_dict.get('DiscountCurve', args_dict.get('discountCurve'))
            previous_spot = args_dict.get('PreviousSpot', args_dict.get('previousSpot'))
            previous_price = args_dict.get('PreviousPrice', args_dict.get('previousPrice'))
            previous_pv = args_dict.get('PreviousPV', args_dict.get('previousPV'))

            adapter = create_object_instance("mcp.mcp", "MEquityFutureAdapter", [
                equity_future,
                instrument_id,
                trade_id,
                portfolio_key
            ])

            if discount_curve is not None:
                adapter.setDiscountCurve(discount_curve)

            if previous_spot is not None and previous_price is not None and previous_pv is not None:
                adapter.setPreviousState(previous_spot, previous_price, previous_pv)

            return adapter

        self.custom_instance_func = create_equity_future_adapter


class DefMcpBondFutureAdapter(ItemDef):

    def __init__(self):
        super().__init__()
        self.init_data = {
            "is_wrapper": False,
            "method_prefix": "BondFutureAdapter",
            "data_fields": [],
            "pyxll_def": {},
        }
        self.init_kv_list = [
            [
                ("BondFuture", "object"),
                ("InstrumentId", "str"),
                ("TradeId", "str"),
                ("ProductType", "int", 2, 2),  # 2 = BOND_FUTURE
                # 可选字段（ValuationCurve, Bond）在 custom_instance_func 中处理
            ],
        ]

        def create_bond_future_adapter(args_dict):
            import mcp.mcp as mcp_module
            from mcp.wrapper import create_object_instance, is_mcp_wrapper

            bond_future = args_dict.get('BondFuture', args_dict.get('bondFuture'))
            instrument_id = args_dict.get('InstrumentId', args_dict.get('instrumentId', 'BOND_FUTURE_001'))
            trade_id = args_dict.get('TradeId', args_dict.get('tradeId', 'TRADE_BOND_FUTURE_001'))
            product_type = args_dict.get('ProductType', args_dict.get('productType', 2))
            valuation_curve = args_dict.get('ValuationCurve', args_dict.get('valuationCurve'))
            bond = args_dict.get('Bond', args_dict.get('bond'))

            if bond_future is None:
                return 'not found bond_future object'

            # 如果提供了 Bond，设置可交割债券列表
            if bond is not None:
                ctd_bond_handler = bond.getHandler() if hasattr(bond, 'getHandler') else bond
                if isinstance(ctd_bond_handler, int):
                    deliverable_bonds_str = str(ctd_bond_handler)
                elif isinstance(ctd_bond_handler, str):
                    if ctd_bond_handler.startswith('0x') or ctd_bond_handler.startswith('0X'):
                        deliverable_bonds_str = str(int(ctd_bond_handler, 16))
                    else:
                        deliverable_bonds_str = ctd_bond_handler
                else:
                    deliverable_bonds_str = str(int(ctd_bond_handler))
                bond_future.SetDeliverableBonds(deliverable_bonds_str)

            adapter = create_object_instance("mcp.mcp", "MBondFutureAdapter", [
                bond_future,
                instrument_id,
                trade_id,
                product_type
            ])

            if valuation_curve is not None:
                adapter.setValuationCurve(valuation_curve)

            return adapter

        self.custom_instance_func = create_bond_future_adapter


class DefMcpBondAdapter(ItemDef):

    def __init__(self):
        super().__init__()
        self.init_data = {
            "is_wrapper": False,
            "method_prefix": "BondAdapter",
            "data_fields": [],
            "pyxll_def": {},
        }
        self.init_kv_list = [
            [
                ("Bond", "object"),
                ("InstrumentId", "str"),
                ("TradeId", "str"),
                ("ProductType", "int", 1, 1),  # 1 = CASH_RATES
                # 以下为可选（第三元为 None 时缺省不报 Missing fields；实际取值仍以 parse 得到的 args_dict 为准）
                ("ValuationCurve", "object", None),
                ("BenchmarkCurve", "object", None),
                ("SwapCurve", "object", None),
                ("SpreadCurve", "object", None),
                ("BondSpreadCurve", "object", None),
                ("BondCurve", "object", None),
                ("PreviousBenchmarkCurve", "object", None),
                ("PreviousBondSpreadCurve", "object", None),
                ("PreviousSpreadCurve", "object", None),
                ("CreditCurve", "object", None),
                ("PreviousCurve", "object", None),
                ("PreviousCreditCurve", "object", None),
                # 交易输入（一次性在 McpBondAdapter(...) 传入）
                ("MarketYield", "object", None),            # 市场收益率（小数，优先级最高）
                ("MarketYieldFromTrade", "object", None),   # 兼容别名
                ("MarketPrice", "object", None),            # 市场净价（次优先）
                ("TradeYield", "object", None),             # 开仓收益率（用于 MTM）
                ("OpeningYield", "object", None),           # 兼容别名
                ("TradePrice", "object", None),             # 开仓价格（用于 MTM）
                ("OpeningTradePrice", "object", None),      # 兼容别名
                ("ReinvestmentRate", "float", None),
                ("FundingRate", "float", None),
                ("RecoveryRate", "float", None),
            ],
            # 与常见 8 列 VP 一致，供 find_match_kv_list(8) / trace_args；多出的键仍留在 args_dict
            [
                ("Bond", "object"),
                ("InstrumentId", "str"),
                ("TradeId", "str"),
                ("ProductType", "int", 1, 1),
                ("ValuationCurve", "object", None),
                ("BenchmarkCurve", "object", None),
                ("BondSpreadCurve", "object", None),
                ("CreditCurve", "object", None),
            ],
            # 仅四必填，供 find_match_kv_list(4)
            [
                ("Bond", "object"),
                ("InstrumentId", "str"),
                ("TradeId", "str"),
                ("ProductType", "int", 1, 1),
            ],
        ]

        def create_bond_adapter(args_dict):
            import mcp.mcp as mcp_module
            from mcp.wrapper import create_object_instance

            def _optional_float(v):
                if v is None:
                    return None
                if isinstance(v, str):
                    s = v.strip()
                    if s == "":
                        return None
                    v = s
                return float(v)

            # args_dict 经 KeyValueWrapper.parse_args_dict 已合并小写键与 init_kv 中的 PascalCase 名
            bond = args_dict.get('Bond', args_dict.get('bond'))
            instrument_id = str(args_dict.get('InstrumentId') or args_dict.get('instrumentId') or 'BOND_001')
            trade_id = str(args_dict.get('TradeId') or args_dict.get('tradeId') or 'TRADE_BOND_001')
            product_type = int(args_dict.get('ProductType') or args_dict.get('productType') or 1)
            valuation_curve = args_dict.get('ValuationCurve', args_dict.get('valuationCurve'))
            benchmark_curve = args_dict.get('BenchmarkCurve', args_dict.get('benchmarkCurve'))
            swap_curve = args_dict.get('SwapCurve', args_dict.get('swapCurve'))
            # 前一日 Campisi：基准+利差。BondCurve 与 PreviousBenchmarkCurve 等价；利差可用 BondSpreadCurve / PreviousBondSpreadCurve / PreviousSpreadCurve
            bond_curve = (
                args_dict.get('BondCurve', args_dict.get('bondCurve'))
                or args_dict.get('PreviousBenchmarkCurve', args_dict.get('previousBenchmarkCurve'))
            )
            bond_spread_curve = (
                args_dict.get('BondSpreadCurve', args_dict.get('bondSpreadCurve'))
                or args_dict.get('PreviousBondSpreadCurve', args_dict.get('previousBondSpreadCurve'))
                or args_dict.get('PreviousSpreadCurve', args_dict.get('previousSpreadCurve'))
            )
            spread_curve = args_dict.get('SpreadCurve', args_dict.get('spreadCurve'))
            credit_curve = args_dict.get('CreditCurve', args_dict.get('creditCurve'))
            previous_curve = args_dict.get('PreviousCurve', args_dict.get('previousCurve'))
            reinvestment_rate = args_dict.get('ReinvestmentRate', args_dict.get('reinvestmentRate'))
            funding_rate = args_dict.get('FundingRate', args_dict.get('fundingRate'))
            recovery_rate = args_dict.get('RecoveryRate', args_dict.get('recoveryRate'))
            previous_credit_curve = args_dict.get('PreviousCreditCurve', args_dict.get('previousCreditCurve'))
            # 交易输入（支持多别名）
            market_yield = args_dict.get('MarketYield', args_dict.get('marketYield'))
            if market_yield is None:
                market_yield = args_dict.get('MarketYieldFromTrade', args_dict.get('marketYieldFromTrade'))
            market_price = args_dict.get('MarketPrice', args_dict.get('marketPrice'))
            trade_yield = args_dict.get('TradeYield', args_dict.get('tradeYield'))
            if trade_yield is None:
                trade_yield = args_dict.get('OpeningYield', args_dict.get('openingYield'))
            trade_price = args_dict.get('TradePrice', args_dict.get('tradePrice'))
            if trade_price is None:
                trade_price = args_dict.get('OpeningTradePrice', args_dict.get('openingTradePrice'))
            # bond 转为底层对象：getInstance() 返回 MBond*，与 MBondAdapter(MBond*,...) 匹配
            m_bond = bond.getInstance() if hasattr(bond, 'getInstance') else bond
            # MBondAdapter 构造：先试 4 参数，product_type 为 float 时回退到 3 参数
            try:
                adapter = mcp_module.MBondAdapter(m_bond, instrument_id, trade_id, product_type)
            except TypeError:
                adapter = mcp_module.MBondAdapter(m_bond, instrument_id, trade_id)

            if valuation_curve is not None:
                valuation_curve_type = type(valuation_curve).__name__
                if "BondSpreadCurve" in valuation_curve_type:
                    adapter.SetSpreadCurve(valuation_curve)
                    # ValuationCurve 仅支持 Yield/Bond/Swap；若传入 BondSpreadCurve，优先回退到 benchmark 作为估值曲线
                    if benchmark_curve is not None:
                        adapter.setValuationCurve(benchmark_curve)
                    elif hasattr(valuation_curve, "getBenchmarkCurve"):
                        try:
                            vc_bench = valuation_curve.getBenchmarkCurve()
                            if vc_bench is not None:
                                adapter.setValuationCurve(vc_bench)
                        except Exception as e:
                            pass
                else:
                    adapter.setValuationCurve(valuation_curve)
            if benchmark_curve is not None:
                adapter.SetBenchmarkCurve(benchmark_curve)
            if swap_curve is not None:
                adapter.SetSwapCurve(swap_curve)
            # SetSpreadCurve：显式 SpreadCurve，或仅有利差曲线键（无 bond_curve/PreviousBenchmarkCurve 时视为当前利差）
            if spread_curve is not None:
                adapter.SetSpreadCurve(spread_curve)
            elif bond_spread_curve is not None and bond_curve is None:
                adapter.SetSpreadCurve(bond_spread_curve)
            if credit_curve is not None:
                adapter.SetCreditCurve(credit_curve)
            if reinvestment_rate is not None:
                adapter.SetReinvestmentRate(float(reinvestment_rate))
            if funding_rate is not None:
                adapter.SetFundingRate(float(funding_rate))
            if recovery_rate is not None:
                adapter.SetRecoveryRate(float(recovery_rate))
            # 市场输入优先级：MarketYield > MarketPrice
            # （具体定价顺序由 C++ BondAdapter.calculateValuationMetrics 控制）
            if market_yield is not None:
                market_yield = _optional_float(market_yield)
            if market_price is not None:
                market_price = _optional_float(market_price)
            if trade_yield is not None:
                trade_yield = _optional_float(trade_yield)
            if trade_price is not None:
                trade_price = _optional_float(trade_price)

            # SWIG 的 MBondAdapter 在 mcp.py 里可能有 Python 方法，但 _mcp.pyd 未必导出对应 C 符号；
            # hasattr(adapter, ...) 会为 True，调用时才会报 module '_mcp' has no attribute 'MBondAdapter_set...'
            _swig = getattr(mcp_module, "_mcp", None)

            def _mbond_swig_has(name):
                return _swig is not None and hasattr(_swig, name)

            if market_yield is not None:
                if _mbond_swig_has("MBondAdapter_setMarketYieldFromTrade"):
                    adapter.setMarketYieldFromTrade(market_yield)
                else:
                    print(
                        "[WARN] _mcp.pyd 缺少 MBondAdapter_setMarketYieldFromTrade，MarketYield 未生效；请用 mathema-git 重新编译并替换 _mcp.pyd"
                    )
            if market_price is not None:
                if _mbond_swig_has("MBondAdapter_setMarketPrice"):
                    adapter.setMarketPrice(market_price)
                else:
                    print(
                        "[WARN] _mcp.pyd 缺少 MBondAdapter_setMarketPrice，MarketPrice 未生效；请重新编译并替换 _mcp.pyd"
                    )
            # 开仓输入优先级：TradeYield > TradePrice
            if trade_yield is not None:
                if _mbond_swig_has("MBondAdapter_setOpeningYield"):
                    adapter.setOpeningYield(trade_yield)
                else:
                    print(
                        "[WARN] _mcp.pyd 缺少 MBondAdapter_setOpeningYield，TradeYield/OpeningYield 未生效；请重新编译并替换 _mcp.pyd"
                    )
            if trade_price is not None:
                if _mbond_swig_has("MBondAdapter_setOpeningTradePrice"):
                    adapter.setOpeningTradePrice(trade_price)
                else:
                    print(
                        "[WARN] _mcp.pyd 缺少 MBondAdapter_setOpeningTradePrice，TradePrice 未生效；请重新编译并替换 _mcp.pyd"
                    )
            from mcp.wrapper import McpBondAdapter
            out = McpBondAdapter(adapter)
            # SetPreviousCurve 必须在 SWIG 包装类上调用（与 MYieldCurve/MBondCurve 重载匹配）；勿用 getHandler()。
            if previous_curve is not None:
                out.SetPreviousCurve(previous_curve)
            if bond_curve is not None and bond_spread_curve is not None:
                if hasattr(adapter, 'setPreviousMarketData'):
                    if previous_credit_curve is not None:
                        adapter.setPreviousMarketData(
                            bond_curve, bond_spread_curve, previous_credit_curve
                        )
                    else:
                        adapter.setPreviousMarketData(bond_curve, bond_spread_curve)
            return out

        self.custom_instance_func = create_bond_adapter


class DefMcpHistVols(ItemDef):
    def __init__(self):
        super().__init__()
        self.generate_xls_method = True
        self.init_data = {
            "is_wrapper": True,
            "data_fields": [],
            "pyxll_def": {},
        }
        self.init_kv_list = [
            [
                ("Label", "str"),
                ("ReferenceDate", "date"),
                ("Dates", "plainlist"),
                ("Quotes", "plainlist"),
                ("Periods", "int"),
                ("Model", "const"),
                ("ReturnMethod", "const"),
                ("AnnualFactor", "float"),
                ("Lamda", "float"),
                ("InterpolationMethod", "const"),
                ("DayCounter", "const"),
            ]
        ]


tool_def = ArgsDef()
tool_def.add_item(DefMcpYieldCurve())
tool_def.add_item(DefMcpYieldCurve2())
tool_def.add_item(DefMcpSwapCurve())
tool_def.add_item(DefMcpVolSurface())
tool_def.add_item(DefMcpMktVolSurface())
tool_def.add_item(DefMcpMktVolSurface2())
class DefMcpXccyBasisCurve(ItemDef):
    """交叉货币基差曲线（CrossCurrencySpreadCurve）。

    三种构造签名（init_kv_list 顺序即 C++ MXccyBasisCurve 构造器参数顺序）：
      1) Path A  ：FX 远期点直接报价（EndDates + ForwardPoints）
      2) Path A2 ：直接引用既有 FX 远期点曲线对象（FXForwardPointsCurve=McpFXForwardPointsCurve），
                  ref/spot/FXSpot/ScaleFactor 均取自该曲线，spot 后节点为 pillar
      3) Path B  ：基差互换报价（EndDates + BasisSpreads，decimal，spread 加在 CNY/base 腿）
    """

    def __init__(self):
        super().__init__()
        self.custom_instance_func_raw = mcp_instance_list
        self.init_data = {
            "is_wrapper": True,
            "fmt": "VP",
            "method_prefix": "XccyBasisCurve",
            "data_fields": [
                ("EndDates", "str"),
                ("ForwardPoints", "float"),
                ("BasisSpreads", "float"),
            ],
            "pyxll_def": {
            },
        }
        self.kv_const_dict = {
            'Variable': 'InterpolatedVariable',
            'Method': 'InterpolationMethod',
        }
        self.init_kv_list = [
            # Path A：FX 远期点报价
            [
                ("ReferenceDate", "date"),
                ("SpotDate", "date"),
                ("EndDates", "plainlist"),
                ("ForwardPoints", "plainlist"),
                ("USDDiscountCurve", "object"),
                ("CNYCleanCurve", "object"),
                ("FXSpotRate", "float"),
                ("ScaleFactor", "float", 10000.0),
                ("Variable", "const", InterpolatedVariable.SPREADS, "SPREADS"),
                ("Method", "const", InterpolationMethod.LINEARINTERPOLATION, "LINEARINTERPOLATION"),
                ("UseGlobalSolver", "bool", False),
            ],
            # Path A2：引用既有 FXFP 曲线对象（报价零重复）
            [
                ("FXForwardPointsCurve", "object"),
                ("USDDiscountCurve", "object"),
                ("CNYCleanCurve", "object"),
                ("Variable", "const", InterpolatedVariable.SPREADS, "SPREADS"),
                ("Method", "const", InterpolationMethod.LINEARINTERPOLATION, "LINEARINTERPOLATION"),
                ("UseGlobalSolver", "bool", False),
            ],
            # Path B：基差互换报价（spread 在 CNY/base 腿，decimal）
            [
                ("ReferenceDate", "date"),
                ("SpotDate", "date"),
                ("EndDates", "plainlist"),
                ("BasisSpreads", "plainlist"),
                ("CNYEstimationCurve", "object"),
                ("USDEstimationCurve", "object"),
                ("USDDiscountCurve", "object"),
                ("CNYCleanCurve", "object"),
                ("FXSpotRate", "float"),
                ("Variable", "const", InterpolatedVariable.SPREADS, "SPREADS"),
                ("Method", "const", InterpolationMethod.LINEARINTERPOLATION, "LINEARINTERPOLATION"),
                ("UseGlobalSolver", "bool", False),
            ],
        ]
        self.add_method_def({
            "method": "DiscountFactor2",
            "args": [
                ("curve", "object"),
                ("startDate", "date"),
                ("endDate", "date"),
            ],
        })
        self.add_method_def({
            "method": "ZeroRate",
            "args": [
                ("curve", "object"),
                ("date", "date"),
            ],
        })
        self.add_method_def({
            "method": "Spread",
            "args": [
                ("curve", "object"),
                ("date", "date"),
            ],
        })

        def Spreads(obj, dates):
            return [obj.Spread(d) for d in dates]

        self.add_method_def({
            "method": "Spreads",
            "args": [
                ("curve", "object"),
                ("dates", "array_date"),
            ],
            "fmt": "V",
            "func": Spreads,
            "pyxll_def": {
                "auto_resize": True
            },
        })
        for m in ("GetRefDate", "GetSpotDate", "GetFXSpot"):
            self.add_method_def({
                "method": m,
                "args": [
                    ("curve", "object"),
                ],
            })


tool_def.add_item(DefMcpFXVolSurface())
tool_def.add_item(DefMcpFXVolSurface2())
tool_def.add_item(DefMcpVanillaOption())
tool_def.add_item(DefMcpVanillaStrategy())
tool_def.add_item(DefMcpFXForward())
tool_def.add_item(DefMcpFXForward2())
tool_def.add_item(DefMcpAsianOption())
tool_def.add_item(DefMcpFixedRateBond())
tool_def.add_item(DefMcpAmortizingBond())
tool_def.add_item(DefMcpCommodityFuture())
tool_def.add_item(DefMcpVanillaSwap())
tool_def.add_item(DefMcpLoanAndDepos())
tool_def.add_item(DefMcpSchedule())
tool_def.add_item(DefMcpCustomForwardDefine())
tool_def.add_item(DefMcpCustomForward())
tool_def.add_item(DefMcpSwaptionCube())
tool_def.add_item(DefMcpBlack76Swaption())
tool_def.add_item(DefMcpCapVolStripping())
tool_def.add_item(DefMcpCapFloor())
tool_def.add_item(DefMcpCalendar())
tool_def.add_item(DefMcpParametricCurve())
tool_def.add_item(DefMcpBondCurve())
tool_def.add_item(DefMcpBondSpreadCurve())
tool_def.add_item(DefMcpRounder())
tool_def.add_item(DefMcpHistoricalRates())
tool_def.add_item(DefMcpRateConvention())
tool_def.add_item(DefMcpEuropeanDigital())
tool_def.add_item(DefMcpDoubleDigitalOption())
tool_def.add_item(DefMcpVanillaBarriers())
tool_def.add_item(DefMcpFXForwardPointsCurve())
tool_def.add_item(DefMcpFXForwardPointsCurve2())
tool_def.add_item(DefMcpXccyBasisCurve())
tool_def.add_item(DefMcpOvernightRateCurveData())
tool_def.add_item(DefMcpBillCurveData())
tool_def.add_item(DefMcpBillFutureCurveData())
tool_def.add_item(DefMcpFRACurveData())
tool_def.add_item(DefMcpVanillaSwapCurveData())
tool_def.add_item(DefMcpFixedRateBondCurveData())
tool_def.add_item(DefMcpHestonModel())
tool_def.add_item(DefMcpOptionData())
tool_def.add_item(DefMcpVolSurface2())
tool_def.add_item(DefMcpForwardCurve2())
tool_def.add_item(DefMcpForwardCurve())
tool_def.add_item(DefMcpLocalVol())
tool_def.add_item(DefMcpCurrencySwapLeg())
tool_def.add_item(DefMcpXCurrencySwap())
tool_def.add_item(DefMcpBasisSwap())
tool_def.add_item(DefMcpSingleCumulative())
tool_def.add_item(DefMcpDoubleCumulative())
tool_def.add_item(DefMcpEFXForward())
tool_def.add_item(DefMcpEFXSwap())
tool_def.add_item(DefMcpHistVols())
tool_def.add_item(DefMcpBondFuture())
tool_def.add_item(DefMcpEquityFuture())
tool_def.add_item(DefMcpEquitySpot())
tool_def.add_item(DefMcpFund())
tool_def.add_item(DefMcpFXNDF())
tool_def.add_item(DefMcpRepurchaseProduct())
tool_def.add_item(DefMcpTotalReturnSwap())
tool_def.add_item(DefMcpBondTRSAdapter())
tool_def.add_item(DefMcpBondTRS())
tool_def.add_item(DefMcpCreditCurve())
tool_def.add_item(DefMcpCreditDefaultSwap())
tool_def.add_item(DefMcpCdsAdapter())
tool_def.add_item(DefMcpClnAdapter())
tool_def.add_item(DefMcpFXForwardOutright())
# tool_def.add_item(DefMcpBond())
tool_def.add_item(DefMcpABSTranche())
tool_def.add_item(DefMcpCallableBond())
tool_def.add_item(DefMcpCommodityFutureAdapter())
tool_def.add_item(DefMcpVanillaSwapAdapter())
tool_def.add_item(DefMcpTRSAdapter())
tool_def.add_item(DefMcpXCurrencySwapAdapter())
tool_def.add_item(DefMcpRepoAdapter())
tool_def.add_item(DefMcpLoanAndDeposAdapter())
tool_def.add_item(DefMcpFRAAdapter())
tool_def.add_item(DefMcpBondLendingAdapter())
tool_def.add_item(DefMcpCommodityLendingAdapter())
tool_def.add_item(DefMcpBillDiscountAdapter())
tool_def.add_item(DefMcpBillRepoAdapter())
tool_def.add_item(DefMcpBasisSwapAdapter())
tool_def.add_item(DefMcpBondForwardAdapter())
tool_def.add_item(DefMcpFundAdapter())
tool_def.add_item(DefMcpWMProductAdapter())
tool_def.add_item(DefMcpFXNDFAdapter())
tool_def.add_item(DefMcpFXForwardSwapAdapter())
tool_def.add_item(DefMcpFXOptionsAdapter())
tool_def.add_item(DefMcpEquityOptionAdapter())
tool_def.add_item(DefMcpCommodityOptionAdapter())
tool_def.add_item(DefMcpStructuredDerivativeProductAdapter())
tool_def.add_item(DefMcpEquitySpotAdapter())
tool_def.add_item(DefMcpEquityFutureAdapter())
tool_def.add_item(DefMcpBondFutureAdapter())
tool_def.add_item(DefMcpBondAdapter())
tool_def.generate_key_word_dict()

mcp_wrapper_utils.tool_def = tool_def
