# -*- coding: utf-8 -*-

"""
General Utilities & Calendar-related PyXLL UDF Module

Contains:
- Version and date utility functions: McpVersion/McpToday/McpTimeTo
- Calendar object construction: McpCalendar/McpNCalendar/McpFCalendar
- Calendar operations: AddBusinessDays/Adjust/AddPeriod/.../IsBusinessDay/FXO date helpers
- Day count conventions & period calculations: McpDayCounter/DayCounterYearFraction/McpCalTerm
- Schedule object construction & export: McpSchedule/ScheduleDates/ScheduleAsTimes
"""

# =========================
# Standard Library
# =========================
import datetime
import json
import logging
import os
import re
from typing import Any, List, Tuple

# tkinter only needed for local popup input of username/password; usually server environments don't have GUI, use with caution
try:
    import tkinter as tk  # noqa: F401
except Exception:
    tk = None  # Disable in non-GUI environments

# =========================
# Third Party
# =========================
import pandas as pd
from pyxll import RTD, xl_arg, xl_app, xl_func, xl_return, xlfCaller  # noqa: F401

# =========================
# Project Internal
# =========================
import mcp.mcp
import mcp.wrapper
import mcp.xscript.utils as xsutils  # noqa: F401 May be called externally/indirectly used
from mcp.forward.compound import payoff_generate_spots  # noqa: F401 Reserved
from mcp.mcp import MDateFuntion  # noqa: F401 Reserved (if MDateFunction needs to be exposed)
from mcp.tool.args_def import tool_def
from mcp.utils.enums import DateAdjusterRule, enum_wrapper
from mcp.utils.excel_utils import pf_date
from mcp.utils.mcp_utils import mcp_dt, parse_excel_date


# =========================
# Global Logger
# =========================
root_logger = logging.getLogger()
print(f"root_logger.level={root_logger.level}")


# =========================
# Utility Functions
# =========================
def is_valid_datetime(dt: datetime.datetime) -> bool:
    """Check if time is within Excel/commonly representable range"""
    min_date = datetime.datetime(1900, 1, 1)
    max_date = datetime.datetime(9999, 12, 31)
    return min_date <= dt <= max_date


def format_date(dt: datetime.datetime, fmt: str) -> str:
    return dt.strftime(fmt)


def plain_date(dt: datetime.datetime) -> str:
    return format_date(dt, "%Y%m%d")


def date_to_string(dt: datetime.datetime) -> str:
    return format_date(dt, "%Y-%m-%d")


def string_to_date(date: str) -> datetime.datetime:
    return datetime.datetime.strptime(date, "%Y-%m-%d")


def date_list_to_string(dates):
    if dates is None:
        dates = []
    str_list = []
    for dt in dates:
        str_list.append(date_to_string(dt))
    return str_list



# =========================
# Version & Time
# =========================
@xl_func(macro=False, recalc_on_open=True)
def McpVersion():
    """Return MCP version number"""
    return mcp.mcp.MMCP().McpVersion()


@xl_func(macro=False, recalc_on_open=True)
def McpToday():
    """Return current time (Excel recognizable datetime)"""
    root_logger = logging.getLogger()
    print(f"root_logger.level={root_logger.level}")
    return datetime.datetime.now()


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("start", "datetime")
@xl_arg("end", "datetime")
@xl_arg("days", "int")
def McpTimeTo(start, end, days):
    """Return (end - start) annualized time length based on days, e.g. days=365"""
    if days is None or days == 0:
        days = 365
    td: datetime.timedelta = end - start
    return td.days / days


@xl_func(macro=False, recalc_on_open=True)
def McpAdjustmentTable():
    """Return table object for business day adjustment rules"""
    return mcp.mcp.MAdjustmentTable()


# =========================
# Calendar Object Construction
# =========================
@xl_func("str code, datetime[] dates: object", macro=False, recalc_on_open=True)
def McpCalendar(code, dates):
    """
    Construct calendar object based on code and additional holidays.
    dates:
      - None or only one 1899-12-31 is treated as no additional holidays
    """
    if dates is None:
        date_str = ""
    elif len(dates) == 1 and mcp_dt.to_pure_date(dates[0]) == "18991231":
        date_str = ""
    else:
        date_str = json.dumps(date_list_to_string(dates))

    try:
        if date_str == "":
            # load holiday from Holiday.txt in the same directory with pyd or dll file
            cal = mcp.wrapper.McpCalendar(code)
        else:
            cal = mcp.wrapper.McpCalendar(code, code, date_str)
    except Exception as e:
        errMsg = str(e)
        if "Credentials:-1" in errMsg:
            # 简化：直接用 admin/123 尝试登录；如需 GUI，请使用 GetUserCredentials 并确认 tk 可用
            user, pwd = "admin", "123"
            checker = mcp.wrapper.MCredentialsChecker()
            if checker.CheckLogin(user, pwd):
                cal = mcp.wrapper.McpCalendar(code, code, date_str)
            else:
                s = "McpCredentials error!"
                logging.warning(s, exc_info=True)
                return s
        else:
            logging.warning(f"McpCalendar exception: {e}", exc_info=True)
            return str(e)

    return cal


@xl_func("str[] ccys, datetime[][] holidays: object", macro=False, recalc_on_open=True)
def McpNCalendar(ccys, holidays):
    """
    批量构造多币种节假日日历，holidays 为二维数组，按列对应每个 ccy 的日期列表。
    """
    dts: List[List[str]] = []
    for i in range(len(ccys)):
        dts.append([])
        for arr in holidays:
            d = mcp_dt.to_pure_date(arr[i])
            if d != "18991231":
                dts[i].append(d)
    dt_str = json.dumps(dts)

    try:
        cal = mcp.wrapper.McpCalendar(json.dumps(ccys), dt_str, False)
    except Exception as e:
        errMsg = str(e)
        if "Credentials:-1" in errMsg:
            user, pwd = "admin", "123"
            checker = mcp.wrapper.MCredentialsChecker()
            if checker.CheckLogin(user, pwd):
                cal = mcp.wrapper.McpCalendar(json.dumps(ccys), dt_str, False)
            else:
                s = "McpCredentials error!"
                logging.warning(s, exc_info=True)
                return s
        else:
            logging.warning(f"McpNCalendar exception: {e}", exc_info=True)
            return str(e)
    return cal


@xl_func("str[] ccys, var path: object", macro=False, recalc_on_open=True)
def McpFCalendar(ccys, path=None):
    """
    从文件 Holidays.txt 构造多币种日历。
    path:
      - 未提供时，按当前文件路径向上定位到 'control/Holidays.txt'
    """
    if path is None:
        path = os.path.realpath(__file__)
        base = path[: path.rfind("calendar")]
        path = f"{base}/control/Holidays.txt"
    cal = mcp.wrapper.McpCalendar(json.dumps(ccys), path, True)
    return cal


# =========================
# 日历计算 UDF
# =========================
@xl_func("object cal, datetime date, var count, str calendarCodes: datetime", macro=False, recalc_on_open=False)
def CalendarAddBusinessDays(cal, date, count, calendarCodes=""):
    """加工作日，按指定日历组合调整"""
    sdate = date_to_string(date)
    cnt = int(count)
    result = cal.AddBusinessDays(sdate, cnt, calendarCodes)
    return string_to_date(result)


@xl_func("object cal, datetime date, var rule, str calendarCodes: datetime", macro=False, recalc_on_open=False)
def CalendarAdjust(cal, date, rule, calendarCodes=""):
    """按给定调整规则（Following/ModifiedFollowing/Preceding...）对日期调整"""
    sdate = date_to_string(date)
    n = enum_wrapper.parse2(rule, DateAdjusterRule().__class__.__name__)
    result = cal.Adjust(sdate, n, calendarCodes)
    return string_to_date(result)


@xl_func(macro=False, recalc_on_open=False)
@xl_arg("cal", "object")
@xl_arg("date", "datetime")
@xl_arg("tenor", "var")
@xl_arg("dateAdjustRule", "var")
@xl_arg("endOfMonthRule", "bool")
@xl_arg("lastOpenDay", "bool")
@xl_arg("calendarCodes", "str")
def CalendarAddPeriod(
    cal,
    date,
    tenor,
    dateAdjustRule=DateAdjusterRule.Actual,
    endOfMonthRule=False,
    lastOpenDay=False,
    calendarCodes="",
):
    """Date + Tenor（如 3M/1Y），并按规则调整"""
    t = str(tenor).strip()
    if t == "":
        return "Invalid tenor:" + str(tenor)
    sdate = date_to_string(date)
    dateAdjustRule = enum_wrapper.parse2(dateAdjustRule, "DateAdjusterRule")
    result = cal.AddPeriod(sdate, t, dateAdjustRule, endOfMonthRule, lastOpenDay, calendarCodes)
    return string_to_date(result)


@xl_func("object cal, datetime date, str[] tenors: datetime[]", macro=False, recalc_on_open=True, auto_resize=True)
def CalendarAddPeriods(cal, date, tenors):
    """批量 Date + Tenor"""
    result = []
    for tenor in tenors:
        t = str(tenor).strip()
        if t == "":
            result.append(date)
        else:
            s = date_to_string(date)
            s = cal.AddPeriod(s, t)
            result.append(string_to_date(s))
    return result


@xl_func(macro=False, recalc_on_open=False)
@xl_arg("cal", "object")
@xl_arg("date", "str")
@xl_arg("isFollowing", "bool")
@xl_arg("calendarCodes", "str")
def CalendarValueDate(cal, date, isFollowing=True, calendarCodes=""):
    """给定交易日期，返回起息日（ValueDate）"""
    s = date_to_string(parse_excel_date(date))
    result = cal.ValueDate(s, isFollowing, calendarCodes)
    return pd.to_datetime(result)


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("cal", "object")
@xl_arg("date", "datetime")
@xl_arg("tenor", "str")
@xl_arg("calendarCodes", "str")
@xl_arg("isFarLeg", "var")
def CalendarValueDateTenor(cal, date, tenor, calendarCodes="", isFarLeg=True):
    """给定交易日 + Tenor，返回 ValueDate（isFarLeg 指示远端/近端）"""
    s = date_to_string(parse_excel_date(date))
    t = str(tenor).strip()
    result = cal.ValueDate(s, t, calendarCodes, isFarLeg)
    return pd.to_datetime(result)


@xl_func(macro=False, recalc_on_open=False)
@xl_arg("cal", "object")
@xl_arg("date", "datetime")
@xl_arg("calendarCodes", "str")
def CalendarFXOExpiryDate(cal, date, calendarCodes=""):
    """FXO 到期日（按日历规则）"""
    s = pf_date(date)
    result = cal.FXOExpiryDate(s, calendarCodes)
    return pd.to_datetime(result)


@xl_func(macro=False, recalc_on_open=False)
@xl_arg("cal", "object")
@xl_arg("date", "datetime")
@xl_arg("calendarCodes", "str")
def CalendarFXODeliveryDate(cal, date, calendarCodes=""):
    """FXO 交割日（按日历规则）"""
    s = pf_date(date)
    result = cal.FXODeliveryDate(s, calendarCodes)
    return pd.to_datetime(result)


@xl_func(macro=False, recalc_on_open=False)
@xl_arg("cal", "object")
@xl_arg("referenceDate", "datetime")
@xl_arg("tenor", "var")
@xl_arg("spotDate", "datetime")
@xl_arg("calendarCodes", "str")
def CalendarFXOExpiryDateFromTenor(cal, referenceDate, tenor, spotDate, calendarCodes=""):
    """
    从参考日 + Tenor（与可选 SpotDate）推导 FXO 到期日
    spotDate 不合法时留空交由底层推导
    """
    _tenor = str(tenor).strip()
    if _tenor == "":
        return "Invalid tenor:" + str(tenor)
    _referenceDate = date_to_string(referenceDate)
    _spotDate = date_to_string(spotDate) if is_valid_datetime(spotDate) else ""
    result = cal.FXOExpiryDateFromTenor(_referenceDate, _tenor, _spotDate, calendarCodes)
    return pd.to_datetime(result)


@xl_func(macro=False, recalc_on_open=False)
@xl_arg("cal", "object")
@xl_arg("referenceDate", "datetime")
@xl_arg("tenor", "var")
@xl_arg("spotDate", "datetime")
@xl_arg("calendarCodes", "str")
def CalendarFXODeliveryDateFromTenor(cal, referenceDate, tenor, spotDate, calendarCodes=""):
    """从参考日 + Tenor 推导 FXO 交割日"""
    _tenor = str(tenor).strip()
    if _tenor == "":
        return "Invalid tenor:" + str(tenor)
    _referenceDate = date_to_string(referenceDate)
    _spotDate = date_to_string(spotDate) if is_valid_datetime(spotDate) else ""
    result = cal.FXODeliveryDateFromTenor(_referenceDate, _tenor, _spotDate, calendarCodes)
    return pd.to_datetime(result)


@xl_func(macro=False, recalc_on_open=False)
@xl_arg("cal", "object")
@xl_arg("date", "datetime")
@xl_arg("calendarCodes", "str")
def CalendarIsBusinessDay(cal, date, calendarCodes=""):
    """判定是否工作日"""
    s = pf_date(date)
    result = cal.IsBusinessDay(s, calendarCodes)
    return result


# =========================
# 日计数法 & 期限运算
# =========================
@xl_func(macro=False, recalc_on_open=True)
@xl_arg("dayCounter", "str")
def McpDayCounter(dayCounter):
    """构造日计数法对象（如 Actual/360、30/360 等）"""
    return mcp.wrapper.McpDayCounter(dayCounter)


@xl_func(macro=False, recalc_on_open=False)
@xl_arg("dayCounter", "str")
@xl_arg("startDate", "datetime")
@xl_arg("endDate", "datetime")
def DayCounterYearFraction(dayCounter, startDate, endDate):
    """按指定日计数法计算年化天数比例"""
    obj = mcp.wrapper.McpDayCounter(dayCounter)
    return obj.YearFraction(mcp_dt.to_pure_date(startDate), mcp_dt.to_pure_date(endDate))


@xl_func(macro=False, recalc_on_open=True)
@xl_arg("term1", "str")
@xl_arg("operator", "str")
@xl_arg("term2", "str")
def McpCalTerm(term1: str, operator: str, term2: str) -> str:
    """
    对两个期限字符串做加减，返回以月为单位的结果（可为负或零）。
    支持形式：nY、nM、nYnM（如 1Y3M）
    例：
      '1Y' + '3M' -> '15M'
      '12M' - '1Y' -> '0M'
    """
    if operator not in ["+", "-"]:
        raise ValueError("Operator must be '+' or '-'")

    def parse_term(term: str) -> int:
        term = term.strip().upper()
        # 支持 nY / nM / nYnM
        match = re.match(r"^(\d+)([YM])(?:(\d+)M)?$", term)
        if not match:
            raise ValueError(f"Invalid term format: {term}. Expected 'nY', 'nM', or 'nYnM'")
        value1, unit, value2 = match.groups()
        value1 = int(value1)
        months = value1 * 12 if unit == "Y" else value1
        if value2:
            if unit != "Y":
                raise ValueError(f"Invalid format: {term}. Months cannot follow months")
            months += int(value2)
        return months

    m1 = parse_term(term1)
    m2 = parse_term(term2)
    result_months = m1 + m2 if operator == "+" else m1 - m2
    return f"{result_months}M"


# =========================
# Schedule 构造与导出
# =========================
@xl_func(macro=False, recalc_on_open=True)
@xl_arg("args1", "var[][]")
@xl_arg("args2", "var[][]")
@xl_arg("args3", "var[][]")
@xl_arg("args4", "var[][]")
@xl_arg("args5", "var[][]")
@xl_arg("fmt", "str")
def McpSchedule(args1, args2, args3, args4, args5, fmt="VP"):
    """通过多段参数区域构造 Schedule"""
    args = [args1, args2, args3, args4, args5, fmt]
    try:
        return tool_def.xls_create(*args, key="McpSchedule")
    except Exception as e:
        s = f"McpSchedule except: {e}"
        logging.warning(args)
        logging.warning(s, exc_info=True)
        return s


@xl_func(macro=False, recalc_on_open=False, auto_resize=True)
def ScheduleDates(obj):
    """导出 Schedule 的日期序列"""
    return obj.dates()


@xl_func(macro=False, recalc_on_open=False, auto_resize=True)
@xl_arg("valueDate", "datetime")
def ScheduleAsTimes(obj, valueDate):
    """导出相对于 valueDate 的 year-fraction 时间点序列"""
    return obj.asTimes(valueDate)