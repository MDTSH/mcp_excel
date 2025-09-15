import json
import traceback

import mcp.tool.tool_utils as utils
import mcp.wrapper
from mcp.utils.enums import *
from mcp.utils.excel_utils import mcp_kv_wrapper, pf_nd_arrary_or_list, parse_dict_list
from mcp.forward.custom import general_fwd_register
from mcp.utils.mcp_utils import as_array
from mcp.wrapper import McpCalendar, create_object_instance, McpRounder, to_mcp_args, McpAdjustmentTable, \
    mcp_wrapper_utils


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
            ]
        ]
        self.add_method_def({
            "method": "ZeroRate",
            "args": [
                ("curve", "object"),
                ("date", "date"),
            ],

        })
        self.add_method_def({
            "method": "ForwardRate",
            "args": [
                ("curve", "object"),
                ("StartDate", "date"),
                ("EndDate", "date"),
                ("DayCounter", "const", DayCounter.ActActISDA, "ActActISDA"),
                ("Compounding", "bool", False),
                ("Frequency", "const", Frequency.NoFrequency, "NoFrequency"),
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
                ("UsingImpVols","bool",True)
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
                ("UseGlobalSolver", "bool", False),
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
                ("date", "date"),
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
                ("maturityPeriod","str"),
            ]
        })
        self.add_method_def({
            "method": "Roll",
            "args": [
                ("curve", "object"),
                ("horizon", "str"),
                ("maturityPeriod","str"),
            ]
        })
        self.add_method_def({
            "method": "ParSwapRate",
            "args": [
                ("curve", "object"),
                ("start", "str"),
                ("end","str"),
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
                ("OptionTypes", "plainlist"),
                ("Strikes", "plainlist"),
                ("Premiums", "plainlist"),
                ("RiskFreeRateCurve","object"),
                ("Dividend","float"),
                ("SmileInterp","const"),
                ("Calendar", "object"),
                ("DateAdjusterRule", "const"),
                ("SpotDate", "date"),
                ("ImpVols", "plainlist"),
                ("MiniStrikeSize", "int",3),
                ("UsingImpVols","bool",True)
            ],
            [
                ("ReferenceDate", "date"),
                ("ExpiryDates", "plainlist"),
                ("OptionTypes", "plainlist"),
                ("Strikes", "plainlist"),
                ("Premiums", "plainlist"),
                ("RiskFreeRateCurve","object"),
                ("ForwardCurve","object"),
                ("SmileInterp","const"),
                ("Calendar", "object"),
                ("DateAdjusterRule", "const"),
                ("SpotDate", "date"),
                ("ImpVols", "plainlist"),
                ("MiniStrikeSize", "int",3),
                ("UsingImpVols","bool",True)
            ],
            [
                ("ReferenceDate", "date"),
                ("ExpiryDates", "plainlist"),
                ("OptionTypes", "plainlist"),
                ("Strikes", "plainlist"),
                ("Premiums", "plainlist"),
                ("RiskFreeRate","float"),
                ("ForwardCurve","object"),
                ("SmileInterp","const"),
                ("Calendar", "object"),
                ("DateAdjusterRule", "const"),
                ("SpotDate", "date"),
                ("ImpVols", "plainlist"),
                ("MiniStrikeSize", "int",3),
                ("UsingImpVols","bool",True)
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
            ["GetSpot"],
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


class DefMcpLocalVol(ItemDef):

    def __init__(self):
        super().__init__()
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
                ("ReferenceDate", "date"),
                ("Spot", "float"),
                ("ExpiryDates", "plainlist"),
                ("OptionTypes", "plainlist"),
                ("Strikes", "plainlist"),
                ("Premiums", "plainlist"),
                ("PremiumAdjusted", "bool"),
                ("DomesticCurve", "object"),
                ("ForeignCurve", "object"),
                ("FXForwardCurve", "object"),
                ("CalculatedTarget", "const"),
                ("LocalVolModel", "const"),
                ("LogLevel", "const"),
                ("TraceFile", "str"),
                ("Calendar", "object"),
                ("DateAdjusterRule", "const"),
                ("SpotDate", "date"),
                ("ImpVols", "plainlist"),
                ("MiniStrikeSize", "int"),
                ("UsingImpVols", "bool", True),
                ("LowerGuessParams", "plainlist", ""),
                ("UpperGuessParams", "plainlist", ""),
            ],
            [
                ("ReferenceDate", "date"),
                ("Spot", "float"),
                ("ExpiryDates", "plainlist"),
                ("OptionTypes", "plainlist"),
                ("Strikes", "plainlist"),
                ("Premiums", "plainlist"),
                ("RiskFreeRateCurve", "object"),
                ("Dividend", "float"),
                ("LocalVolModel", "const"),
                ("LogLevel", "const"),
                ("TraceFile", "str"),
                ("Calendar", "object"),
                ("DateAdjusterRule", "const"),
                ("SpotDate", "date"),
                ("ImpVols", "plainlist"),
                ("MiniStrikeSize", "int"),
                ("UsingImpVols", "bool", True),
                ("LowerGuessParams", "plainlist", ""),
                ("UpperGuessParams", "plainlist", ""),
            ],
            [
                ("ReferenceDate", "date"),
                ("ExpiryDates", "plainlist"),
                ("OptionTypes", "plainlist"),
                ("Strikes", "plainlist"),
                ("Premiums", "plainlist"),
                ("RiskFreeRateCurve", "object"),
                ("ForwardCurve", "object"),
                ("LocalVolModel", "const"),
                ("LogLevel", "const"),
                ("TraceFile", "str"),
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

        def pf_dt_vol(val):
            if isinstance(val, str):
                return val
            vol_rows = []
            for row in val:
                items = [str(item) for item in row]
                vol_rows.append(",".join(items))
            return ";".join(vol_rows)

        bd_type = "bd@McpFXVolSurface"
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
                ("Pair","str","USD/CNY"),
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
                ("Pair","str","USD/CNY"),
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
                ("Pair","str","USD/CNY"),
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
                ("Pair","str","USD/CNY"),
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
                ("Pair","str","USD/CNY"),
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
                ("Pair","str","USD/CNY"),
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
                ("Pair","str","USD/CNY"),
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

        def pf_dt_vol(val):
            if isinstance(val, str):
                return val
            vol_rows = []
            for row in val:
                items = [str(item) for item in row]
                vol_rows.append(",".join(items))
            return ";".join(vol_rows)

        bd_type = "bd@McpFXVolSurface2"
        mcp_kv_wrapper.parse_func_dict[bd_type] = pf_dt_vol


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

        def pf_dt_vol(val):
            if isinstance(val, str):
                return val
            vol_rows = []
            for row in val:
                items = [str(item) for item in row]
                vol_rows.append(",".join(items))
            return ";".join(vol_rows)

        bd_type = "bd@McpFXVolSurface2"
        mcp_kv_wrapper.parse_func_dict[bd_type] = pf_dt_vol

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
                ("Pair","str","USD/CNY"),
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
                ("Pair","str","USD/CNY"),
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
                ("Pair","str","USD/CNY"),
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
                ("Pair","str","USD/CNY"),
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
                ("Pair","str","USD/CNY"),
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
                ("ReferenceDate", "str"),
                ("StrikePx", "float"),
                ("SpotPx", "float"),
                ("FaceAmount", "float"),
                ("ExpiryDate", "str"),
                ("DeliveryDate", "str"),
                ("PremiumDate", "str"),
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
            ["GetSpot", "GetForward", "GetVol", "GetStrike", "GetUndRate", "GetAccRate",  "GetCallPutType",  "GetBuySell",],
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
                ("FwdPoints", "float" , float('nan')),
                ("Volatility", "float", float('nan')),
                ("Volatility2", "float", float('nan')),
            ],
            [
                ("StrategyType", "const"),
                ("DeltaStr","str"),
                ("ReferenceDate", "date"),
                ("FxVolSurface", "object"),
                ("Tenor", "str"),
                ("SpotPx", "float", float('nan')),
                ("FwdPoints", "float" , float('nan')),
                ("Volatility", "float", float('nan')),
                ("Volatility2", "float", float('nan')),
            ],
            [
                ("Tenor", "str"),
                ("FxVolSurface2", "object"),
                ("DeltaStrategyStr", "str"),
                ("ReferenceDate", "date"),
                ("SpotPx", "float", float('nan')),
                ("FwdPoints", "float" , float('nan')),
                ("Volatility", "float", float('nan')),
                ("Volatility2", "float", float('nan')),
            ],
            [
                ("Tenor", "str"),
                ("FxVolSurface2", "object"),
                ("StrategyType", "const"),
                ("DeltaStr","str"),
                ("ReferenceDate", "date"),
                ("SpotPx", "float", float('nan')),
                ("FwdPoints", "float" , float('nan')),
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
                ("FwdPoints", "float" , float('nan')),
                ("Volatility", "float", float('nan')),
                ("Volatility2", "float", float('nan')),
            ],
            [
                ("StrategyType", "const"),
                ("DeltaStr","str"),
                ("ReferenceDate", "date"),
                ("ExpiryDate", "date"),
                ("FxVolSurface", "object"),
                ("SpotPx", "float", float('nan')),
                ("FwdPoints", "float" , float('nan')),
                ("Volatility", "float", float('nan')),
                ("Volatility2", "float", float('nan')),
            ],
            [
                ("FxVolSurface2", "object"),
                ("DeltaStrategyStr", "str"),
                ("ReferenceDate", "date"),
                ("ExpiryDate", "date"),
                ("SpotPx", "float", float('nan')),
                ("FwdPoints", "float" , float('nan')),
                ("Volatility", "float", float('nan')),
                ("Volatility2", "float", float('nan')),
            ],
            [
                ("FxVolSurface2", "object"),
                ("StrategyType", "const"),
                ("DeltaStr","str"),
                ("ReferenceDate", "date"),
                ("ExpiryDate", "date"),
                ("SpotPx", "float", float('nan')),
                ("FwdPoints", "float" , float('nan')),
                ("Volatility", "float", float('nan')),
                ("Volatility2", "float", float('nan')),
            ],
        ]
        self.add_method_range(
            ["GetSpot", "GetForward", "GetFwdPoints", "Volatility", "Price",  "GetLegNames","GetStrategyType", "GetDeltaString", "GetReferenceDate", "GetExpiryDate", "GetDeliveryDate",  ],
            {
                "args": [
                    ("obj", "object"),
                ],

            }
        )
        self.add_method_range(
            [ "Delta", "ForwardDelta", "Gamma", "Vega", "Theta", "Rho", "Phi", "Vanna", "Volga" ],
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
                ("SpotDate","date"),
                ("ExpiryDate", "date"),
                ("DeliveryDate", "date"),
                ("StrikePx", "float"),
                ("SpotPx", "float"),
                ("DomesticRate", "float"),
                ("ForeignRate", "float"),
                ("Forward", "float"),
                #("Calendar", "object", McpCalendar("", "", ""), ""),
                ("DayCounter", "const", DayCounter.Act365Fixed, "Act365Fixed"),
                #("PricingMethod", "const", FxFwdPricingMethod.MARKETFWD, "MARKETFWD"),
                ("BuySell", "const"),
                ("FaceAmount", "float", 1),
                ("CalculatedTarget", "const", CalculateTarget.CCY1),
                ("Pair","str","USD/CNY"),
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
                ("DayCounter","const",DayCounter.ActActXTR)
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
            ["AmCost","AmEIR","AmERInstIncome","AmAccuredIncome","AmCashflow"],
            {
                "args": [
                    ("bond", "object"),
                    ("startDate", "date"),
                    ("endDate", "date"),
                    ("initCost", "float"),
                ],
            }
        )

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
                ("RateConvention","object"),
                ("Calendar","object"),
                ("Coupon", "float"),
                ("Notional", "float"),
                ("FixedDiscountCurve", "object", "", ""),
                ("FloatingEstimationCurve", "object", "", ""),
                ("FloatingDiscountCurve", "object", "", ""),
            ],
            [
                ("ReferenceDate", "date"),
                ("StartDate", "date"),
                ("Tenor", "str"),
                ("FixedPayReceive", "const", PayReceive.Pay, "Pay"),
                ("RateConvention","object"),
                ("Coupon", "float"),
                ("Notional", "float"),
                ("FixedDiscountCurve", "object", "", ""),
                ("FloatingEstimationCurve", "object", "", ""),
                ("FloatingDiscountCurve", "object", "", ""),
                ("Calendar", "object"),
                ("AdjustedStartDate", "bool", False),
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
                ("BuySell","int", BuySell.Buy),
                ("PayReceiveType", "const", PayReceive.Receive),
                ("Strike", "double"),
                ("SettlementMethod", "const"),
                ("Notional",1.0),
                ("EstimationSwapCurve", "object", None),
                ("DiscountSwapCurve", "object", None),
            ],
        ]
        self.add_method_range(
            ["Price", "DV01", "Delta", "Gamma","Vega", "Vomma", "Theta", "NPV"],
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
                ("MaturityTenor", "str"),        # Date or Tenor
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
                ("MaturityDate", "date"),        # Date or Tenor
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
            ["Price", "GetCaplet", "GetNumCaplets", "ExpiryDates","MaturityDates", "SpotDelta", "FrwdDelta", "SpotVega", "FwdVega", "SpotGamma", "FwdGamma"],
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
                ("CapFloorType", "const"),        # Date or Tenor
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
            ["Price", "ValueDate", "ExpiryDate", "MaturityDate", "SpotDelta", "FrwdDelta", "SpotVega", "FwdVega", "SpotGamma", "FwdGamma"],
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
                ("HistoryFixingRates", "objectlist", "[]"),
            ],
            [
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
                ("VolSpread","bool", False),
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
                ("VolSpread","bool", False),
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
                ("Frequencies", "int"),
                ("Coupons", "float"),
                ("YieldsOrDirtyPrice", "float"),
                ("BumpAmounts", "float"),
                ("BUses","intbool"),
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
                #("Mode", "str", 'frb'),
                ("InterpolatedVariable", "const", InterpolatedVariable.SIMPLERATES, 'SIMPLERATES'),
                ("InterpolationMethod", "const", InterpolationMethod.LINEARINTERPOLATION, 'LINEARINTERPOLATION'),
                # ("UseGlobalSolver", "bool", False, False),
                ("DayCounter", "const", DayCounter.Act365Fixed, "Act365Fixed"),

                # ("SettlementDate", "date"),
                ("MaturityDates", "objectlist"),
                ("Frequencies", "objectlist", '[]', '[]'),
                ("Coupons", "objectlist", '[]', '[]'),
                ("YieldsOrDirtyPrice", "objectlist"),
                #("DayCounter", "const", DayCounter.Act365Fixed, "Act365Fixed"),
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
        ]

        self.add_method_def({
            "method": "ZeroRate",
            "args": [
                ("curve", "object"),
                ("date", "date"),
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
            "method": "ZeroRate",
            "args": [
                ("curve", "object"),
                ("date", "date"),
            ],

        })
        self.add_method_def({
            "method": "ParRate",
            "args": [
                ("curve", "object"),
                ("date", "date"),
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
                ("BF25", "float", 0.0)
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
                ("Mode", "int", 1),
                ("DayCounter", "const"),
                ("StartDate", "date"),
                ("MaturityDates", "plainlist"),
                ("Yields", "plainlist"),
                ("BumpAmounts", "plainlist"),
                ("BUses", "plainlist")
            ],
            [
                ("Mode", "int", 2),
                ("DayCounter", "const"),
                ("StartDate", "date"),
                ("MaturityTenors", "plainlist"),
                ("Yields", "plainlist"),
                ("BumpAmounts", "plainlist"),
                ("BUses", "plainlist")
            ],
        ]


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
                ("Frequencies", "float"),
                ("Coupons", "float"),
                ("BumpAmounts", "float"),
                ("BUses", "intbool"),
            ],
            "pyxll_def": {
            },
        }
        self.init_kv_list = [
            [
                ("Mode", "int", 1),
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
                ("Mode", "int", 1),
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
                ("Mode", "int", 2),
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
                ("Mode", "int", 3),
                ("ReferenceDate", "date"),
                ("SwapStartLag", "int", 2),
                ("MaturityTenors", "plainlist"), # Tenors
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
            ],
            [
                ("Mode", "int", 3),
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
            ],
            [
                ("ReferenceDate", "date"),
                ("RateConvention", "str"),
                ("MaturityDates", "plainlist"),  # Dates
                ("Coupons", "plainlist"),
                ("BumpAmounts", "plainlist"),
                ("BUses", "plainlist"),
                ("Calendar", "object", McpCalendar("","", "")),
            ],
            [
                ("ReferenceDate", "date"),
                ("RateConvention", "str"),
                ("MaturityTenors", "plainlist"),  # Tenors  
                ("Coupons", "plainlist"),
                ("BumpAmounts", "plainlist"),
                ("BUses", "plainlist"),
                ("Calendar", "object", McpCalendar("","", "")),
            ],
        ]


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
                ("OptionTypes", "plainlist"),
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
tool_def.add_item(DefMcpFXVolSurface())
tool_def.add_item(DefMcpFXVolSurface2())
tool_def.add_item(DefMcpVanillaOption())
tool_def.add_item(DefMcpVanillaStrategy())
tool_def.add_item(DefMcpFXForward())
tool_def.add_item(DefMcpFXForward2())
tool_def.add_item(DefMcpAsianOption())
tool_def.add_item(DefMcpFixedRateBond())
tool_def.add_item(DefMcpVanillaSwap())
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
tool_def.add_item(DefMcpRounder())
tool_def.add_item(DefMcpEuropeanDigital())
tool_def.add_item(DefMcpVanillaBarriers())
tool_def.add_item(DefMcpFXForwardPointsCurve())
tool_def.add_item(DefMcpFXForwardPointsCurve2())
tool_def.add_item(DefMcpOvernightRateCurveData())
tool_def.add_item(DefMcpBillCurveData())
tool_def.add_item(DefMcpBillFutureCurveData())
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
tool_def.add_item(DefMcpSingleCumulative())
tool_def.add_item(DefMcpDoubleCumulative())
tool_def.add_item(DefMcpEFXForward())
tool_def.add_item(DefMcpEFXSwap())
tool_def.add_item(DefMcpHistVols())
tool_def.generate_key_word_dict()

mcp_wrapper_utils.tool_def = tool_def
