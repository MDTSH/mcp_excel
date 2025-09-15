import json

import mcp.forward.compound
import mcp.forward.custom
import mcp.wrapper
import numpy as np
import pandas as pd

from mcp.utils.excel_utils import pf_nd_arrary_or_list
import mcp.tool.args_parser as args_parser
import mcp.tool.args_def as args_def

from mcp.tool.tools_main import *


# for key in args_def.tool_def.item_dict:
#     item_def = args_def.tool_def.get_item(key)
#     init_func_name = item_def.key
#     fmt = item_def.get_fmt()
#     func_str = f"def {init_func_name}(*args):return args_def.tool_def.tool_create('{init_func_name}', args)"
#     # add_xls_init(init_func_name, init_args_str, item_def.get_pyxll_def())
#     exec(func_str)


def McpObject(*args, key=""):
    return args_def.tool_def.tool_create(key, args)


def McpDateRange(start, end, freq=None, periods=None):
    return pd.date_range(start, end, freq=freq, periods=periods).tolist()


# def McpDataFrame(data=None,
#                  index=None,
#                  columns=None,
#                  dtype=None,
#                  copy=False):
#     return pd.DataFrame(data, index, columns, dtype, copy)


# def LoadDataFrame(file, separator):
#     pass


def Pandas():
    return pd


def Numpy():
    return np


def McpToJson(obj):
    d = mcp.wrapper.trace_args(obj, args_def.tool_def)
    return json.dumps(d)


def McpFromJson(s):
    trace_args = json.loads(s)
    return mcp.wrapper.create_object(trace_args)


# def McpPortfolio(*args):
#     return pd.DataFrame({"Instrument": list(args)})


def InsFixedRateBond(value_date, maturity_date, coupon):
    return {
        "ValuationDate": value_date,
        "MaturityDate": maturity_date,
        "Coupon": coupon,
    }


class McpBondPricer:

    @staticmethod
    def parse_args(*args):
        if len(args) == 1:
            fields = ["ValuationDate", "MaturityDate", "Coupon"]
            vals = []
            d = args[0]
            for field in fields:
                field = field.lower()
                val = None
                for key in d:
                    if field == str(key).lower():
                        val = d[key]
                vals.append(val)
            value_date, maturity_date, coupon = vals
        elif len(args) == 3:
            value_date, maturity_date, coupon = args
        else:
            value_date, maturity_date, coupon = (None, None, None)
        return value_date, maturity_date, coupon

    @staticmethod
    def price(*args):
        # print("price: ",args)
        value_date, maturity_date, coupon = McpBondPricer.parse_args(*args)
        # print("price:",value_date, maturity_date, coupon )
        bond = McpFixedRateBond({
            "ValuationDate": value_date,
            "MaturityDate": maturity_date,
            "Coupon": coupon,
        })
        return bond.DirtyPriceFromYieldCHN(coupon, False)

    @staticmethod
    def duration(*args):
        value_date, maturity_date, coupon = McpBondPricer.parse_args(*args)
        bond = McpFixedRateBond({
            "ValuationDate": value_date,
            "MaturityDate": maturity_date,
            "Coupon": coupon,
        })
        return bond.DurationCHN(coupon)

    @staticmethod
    def dv01(*args):
        value_date, maturity_date, coupon = McpBondPricer.parse_args(*args)
        bond = McpFixedRateBond({
            "ValuationDate": value_date,
            "MaturityDate": maturity_date,
            "Coupon": coupon,
        })
        return bond.PVBPCHN(coupon)


# def to_plot_args(*args, fmt):
#     arr = []
#     for i in range(0, len(args), 2):
#         arr.append(args[i])
#         arr.append(args[i + 1])
#         arr.append(fmt)
#     return arr


def McpArgsTemplate(method, key_word=None):
    # args_def = args_parser.tool_parser.get_def(method)
    # kvs_list = args_def["kvs_list"]
    item_def = args_def.tool_def.get_item(method)
    if item_def is None:
        return None
    kvs_list = item_def.init_kv_list
    dest_kvs = None
    if key_word is not None:
        key_word = str(key_word).lower()
        for kvs in kvs_list:
            for kv in kvs:
                sub_key = str(kv[0]).lower()
                if sub_key.find(key_word) >= 0:
                    dest_kvs = kvs
                    break
            if dest_kvs is not None:
                break
    if dest_kvs is None:
        if len(kvs_list) > 0:
            dest_kvs = kvs_list[0]
        else:
            dest_kvs = []
    result = {}
    for kv in dest_kvs:
        has_default = False
        has_view_default = False
        if len(kv) >= 3:
            has_default = kv[2] is not None
        # if len(kv) == 3:
        #     needed = ""
        # else:
        #     needed = "*"
        if len(kv) >= 4:
            has_view_default = kv[3] is not None
        if has_view_default:
            dval = kv[3]
        else:
            dval = ""
        if has_default and not has_view_default:
            pass
        else:
            t = args_parser.mcp_args_type.get_type(kv[1])
            # to_list.append([kv[0], dval, t])
            result[kv[0]] = dval
    # return np.array(to_list)
    return result


def McpDataHelper(key):
    pass
    # return helper.data_helper.get(key)


def McpPayoff(obj, value_date, spot=None, rg=0.03):
    spots, payoffs = obj.payoff(value_date, spot, rg)
    df = pd.DataFrame({
        "Spot": spots,
        "Payoff": payoffs,
    })
    return df


def McpZeroRate(obj, dates, freq="D"):
    dates = McpDateRange(dates[0], dates[len(dates) - 1], freq)
    data = obj.ZeroRates(dates)
    return pd.DataFrame({
        "Date": dates,
        "ZeroRate": data,
    })


def McpDiscountFactor(obj, dates, freq="D"):
    dates = McpDateRange(dates[0], dates[len(dates) - 1], freq)
    data = obj.DiscountFactors(dates)
    return pd.DataFrame({
        "Date": dates,
        "DiscountFactor": data,
    })


# def McpYieldCurve(*args):
#     # mcp_args = args_parser.tool_parser.parse_args("McpYieldCurve", args)
#     # return mcp.wrapper.McpYieldCurve(*mcp_args)
#     return args_def.tool_def.tool_create("McpYieldCurve", args)


# def McpVanillaOption(*args):
#     mcp_args = args_parser.tool_parser.parse_args("McpVanillaOption", args)
#     return mcp.forward.compound.McpVanillaOption(*mcp_args)


# def McpAsianOption(*args):
#     mcp_args = args_parser.tool_parser.parse_args("McpAsianOption", args)
#     return mcp.forward.compound.McpAsianOption(*mcp_args)


# def McpFixedRateBond(*args):
#     mcp_args = args_parser.tool_parser.parse_args("McpFixedRateBond", args)
#     return mcp.wrapper.McpFixedRateBond(*mcp_args)
#
#
# def McpVanillaSwap(*args):
#     mcp_args = args_parser.tool_parser.parse_args("McpVanillaSwap", args)
#     return mcp.wrapper.McpVanillaSwap(*mcp_args)


def McpParseHoliday(df, header_ccy, header_dates, ccys):
    df_all = pd.DataFrame({"ccy": df[header_ccy].replace('\\W', '', regex=True),
                           "date": df[header_dates]})
    result = {}
    for ccy in ccys:
        df_temp = df_all[df_all["ccy"] == ccy]
        result[ccy] = df_temp["date"].tolist()
    return result


# def McpSchedule(*args):
#     mcp_args = args_parser.tool_parser.parse_args("McpSchedule", args)
#     return mcp.wrapper.McpSchedule(*mcp_args)


def McpCalendar(*args):
    if len(args) == 1:
        data = args[0]
        if isinstance(data, dict):
            ccys = list(data.keys())
            dates = [data[ccy] for ccy in ccys]
            mcp_args = [json.dumps(ccys), json.dumps(dates), False]
            return mcp.wrapper.McpCalendar(*mcp_args)
        else:
            return mcp.wrapper.McpCalendar("", "", "")
    elif len(args) >= 2:
        arg0 = args[0]
        arg1 = args[1]
        if isinstance(arg1, str):
            mcp_args = [json.dumps(arg0), arg1, True]
        else:
            if len(arg0) != len(arg1):
                raise Exception("Size not match: ccys=" + str(len(arg0)) + ", dates=" + str(len(arg1)))
            if arg1 is None:
                arg1 = [[] for ccy in arg0]
            else:
                arg1 = pf_nd_arrary_or_list(arg1)
            mcp_args = [json.dumps(arg0), json.dumps(arg1), False]
        # print(f"McpCalendar: {mcp_args}")
        return mcp.wrapper.McpCalendar(*mcp_args)
    else:
        return mcp.wrapper.McpCalendar("", "", "")


def McpPortfolio(*args):
    deals = []
    for item in args:
        deals.extend(pf_nd_arrary_or_list(item))
    return mcp.forward.custom.McpPortfolio(deals)

def McpVersion():
    return mcp.mcp.MMCP().McpVersion()
    
# def McpCustomForwardDefine(*args):
#     pass
