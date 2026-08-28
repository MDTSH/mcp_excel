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
from mcp.optional_deps import pandas as pd
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
from mcp.calendar_holidays_path import holidays_file_path_for_calendar


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


def date_to_string(dt) -> str:
    """将日期对象转换为 YYYY-MM-DD 格式字符串。支持 datetime, pd.Timestamp 等类型，NaT/None 返回空串。"""
    if dt is None:
        return ""
    try:
        s = str(dt)
        if s in ("NaT", "nan", "None", ""):
            return ""
        if isinstance(dt, (int, float)):
            dt = pd.Timestamp(dt)
        return format_date(dt, "%Y-%m-%d")
    except (ValueError, AttributeError, TypeError):
        return ""


def string_to_date(date: str):
    """将 YYYY-MM-DD 格式的日期字符串转换为 datetime。空字符串返回 None。"""
    if not date or date == "":
        return None
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
@xl_func("str code, datetime[] dates=None: object", macro=False, recalc_on_open=True)
def McpCalendar(code, dates=None):
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


@xl_func("object cal=None: str", macro=False, recalc_on_open=True)
def calendarFilePath(cal=None):
    """Return the Holidays.txt path used by an McpCalendar.

    - cal omitted: path that ``=McpCalendar("CNY")`` would load (C++ search rules).
    - cal provided: path for that calendar object.
    - Empty string if the calendar was built from in-memory holidays only.
    """
    try:
        return holidays_file_path_for_calendar(cal)
    except Exception as e:
        logging.warning(f"calendarFilePath failed: {e}", exc_info=True)
        return ""


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
# Holidays.txt 一次加载 + 按 code 取视图
# =========================
# 模块级缓存：
#   _holidays_cache[abs_path] = {
#       "path":     str,
#       "cal":      McpCalendar,           # 全币种主日历（真实 MCalendar）
#       "codes":    [str],                 # 文件中出现的全部 code
#       "by_code":  {code: [iso_date, ...]}, # 解析得到的全部节假日
#       "subcache": {tuple(codes): McpCalendar}, # 按子集缓存的子日历
#   }
_holidays_cache: dict = {}

# 通过 pyxll.cfg [ENVIRONMENT] 配置的环境变量名，用法示例：
#   [ENVIRONMENT]
#   MCP_HOLIDAYS_PATH = ../../config/Holidays.txt
HOLIDAYS_ENV = "MCP_HOLIDAYS_PATH"


def _get_pyd_dir() -> str:
    """返回 _mcp.pyd 所在目录（如 .../python/lib/X64）。取不到时返回空串。"""
    try:
        ext = getattr(mcp.mcp, "_mcp", None)
        pyd_path = getattr(ext, "__file__", "") if ext is not None else ""
        if not pyd_path:
            pyd_path = getattr(mcp.mcp, "__file__", "") or ""
        return os.path.dirname(os.path.abspath(pyd_path)) if pyd_path else ""
    except Exception:
        return ""


def _abs_relative_to_pyd(p: str) -> str:
    """绝对路径原样返回；相对路径以 .pyd 所在目录为基准。"""
    p = (p or "").strip()
    if not p:
        return ""
    if os.path.isabs(p) or (len(p) >= 2 and p[1] == ":") or p.startswith("\\\\"):
        return os.path.normpath(p)
    base = _get_pyd_dir() or os.getcwd()
    return os.path.normpath(os.path.join(base, p))


def _resolve_holidays_path(path) -> str:
    """Holidays.txt 路径解析优先级：
        1. 函数显式传入 path（相对路径优先按 ActiveWorkbook.Path 解析）
        2. 环境变量 MCP_HOLIDAYS_PATH（pyxll.cfg [ENVIRONMENT] 推荐用此名）
        3. .pyd 目录的 ../../config/Holidays.txt（默认布局）
        4. .pyd 目录的 ./Holiday.txt（C++ 侧旧默认，作最后回落）
    """
    if path is not None and str(path).strip():
        raw = str(path).strip()
        try:
            from mcp.utils.workbook_path import resolve_data_path

            ok, resolved, _err = resolve_data_path(raw, must_exist=True)
            if ok:
                return resolved
        except Exception:
            pass
        return _abs_relative_to_pyd(raw)

    env_val = os.environ.get(HOLIDAYS_ENV, "").strip()
    if env_val:
        return _abs_relative_to_pyd(env_val)

    pyd_dir = _get_pyd_dir()
    if pyd_dir:
        cand = os.path.normpath(os.path.join(pyd_dir, "..", "..", "config", "Holidays.txt"))
        if os.path.isfile(cand):
            return cand
        cand_old = os.path.normpath(os.path.join(pyd_dir, "Holiday.txt"))
        if os.path.isfile(cand_old):
            return cand_old
        return cand
    return os.path.realpath("Holidays.txt")


def _parse_holidays_full(path: str) -> Tuple[List[str], dict]:
    """读取 Holidays.txt，得到 (按出现顺序的全部 code 列表, {code: [iso_date,...]})。"""
    codes: List[str] = []
    by_code: dict = {}
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        next(f, None)  # CALENDAR_C;HOLIDAY_D;GLOBAL_F
        for line in f:
            parts = line.split(";")
            if len(parts) < 2:
                continue
            code = parts[0].strip()
            date = parts[1].strip()
            if not code or not date:
                continue
            if code not in by_code:
                by_code[code] = []
                codes.append(code)
            by_code[code].append(date)
    return codes, by_code


def _load_master(path):
    p = _resolve_holidays_path(path)
    hit = _holidays_cache.get(p)
    if hit is not None:
        return hit
    if not os.path.isfile(p):
        raise FileNotFoundError(f"Holidays.txt not found: {p}")
    codes, by_code = _parse_holidays_full(p)
    if not codes:
        raise ValueError(f"Holidays.txt 未解析到任何 calendar code: {p}")
    # 直接走文件构造，等价于让 C++ 端把全部 code 一次装进去。
    master = mcp.wrapper.McpCalendar(json.dumps(codes), p, True)
    try:
        master._holidays_info_path = p  # 用于反向查缓存
        master._holidays_file_path = p
    except Exception:
        pass
    hit = {"path": p, "cal": master, "codes": codes, "by_code": by_code, "subcache": {}}
    _holidays_cache[p] = hit
    return hit


def _get_subcal(info: dict, codes: List[str]):
    """从内存中的 by_code 构造仅包含指定 code 的真实 McpCalendar，并缓存。"""
    key = tuple(sorted(c.upper() for c in codes))
    sub = info["subcache"].get(key)
    if sub is not None:
        return sub
    by_code = info["by_code"]
    dts = [by_code.get(c, []) for c in key]
    cal = mcp.wrapper.McpCalendar(json.dumps(list(key)), json.dumps(dts), False)
    try:
        cal._holidays_info_path = info["path"]
        cal._holidays_file_path = info["path"]
    except Exception:
        pass
    info["subcache"][key] = cal
    return cal


def _normalize_ccys(spec) -> List[str]:
    """把 ccys 规范成 code 列表。
    支持：'CNY' / 'USDCNY' / 'USD/CNY' / 'USD,JPY,CNY' / list / Excel 区域(嵌套)
    """
    if spec is None:
        return []
    if isinstance(spec, (list, tuple)):
        items: List[str] = []
        for x in spec:
            if isinstance(x, (list, tuple)):
                items.extend(str(y).strip() for y in x if str(y).strip())
            elif str(x).strip():
                items.append(str(x).strip())
    else:
        s = str(spec).strip()
        if not s:
            return []
        if "/" in s:
            items = [t.strip() for t in s.split("/") if t.strip()]
        elif "," in s:
            items = [t.strip() for t in s.split(",") if t.strip()]
        elif len(s) == 6 and s.isalpha():
            items = [s[:3], s[3:]]
        else:
            items = [s]
    out: List[str] = []
    seen = set()
    for it in items:
        u = it.upper()
        if u and u not in seen:
            seen.add(u)
            out.append(u)
    return out


def _info_for_cal(cal):
    """根据已有 cal 反查其所属 Holidays.txt 缓存条目；没有则返回 None。"""
    p = getattr(cal, "_holidays_info_path", None)
    if p is None:
        return None
    return _holidays_cache.get(p)


@xl_func("var path, bool returnPath: var", macro=True, recalc_on_open=True)
def McpHolidaysLoad(path=None, returnPath=False):
    """一次性加载 Holidays.txt 主日历（带缓存）。

    path 解析优先级：参数 > 环境变量 MCP_HOLIDAYS_PATH > pyd/../../config/Holidays.txt

    returnPath=False（默认）返回主日历对象；
    returnPath=True 返回当前会用到的绝对路径（不会触发加载，用于在 Excel 中诊断）。
    """
    if returnPath:
        return _resolve_holidays_path(path)
    try:
        return _load_master(path)["cal"]
    except Exception as e:
        logging.warning(f"McpHolidaysLoad failed: {e}", exc_info=True)
        return f"McpHolidaysLoad error: {e}"


@xl_func("var path: str[]", macro=True, recalc_on_open=True, auto_resize=True)
def McpHolidaysCodes(path=None):
    """返回 Holidays.txt 内全部 calendar code 列表（用于核对）。"""
    try:
        return _load_master(path)["codes"]
    except Exception as e:
        logging.warning(f"McpHolidaysCodes failed: {e}", exc_info=True)
        return [f"McpHolidaysCodes error: {e}"]


@xl_func("var path: bool", macro=True)
def McpHolidaysReload(path=None):
    """清缓存，下次调用会重新读取 Holidays.txt。
    path 留空则清空全部缓存；指定路径则只清该路径的缓存。
    """
    if path is None or str(path).strip() == "":
        _holidays_cache.clear()
    else:
        _holidays_cache.pop(_resolve_holidays_path(path), None)
    return True


@xl_func("var arg1, var arg2: object", macro=True, recalc_on_open=True)
def McpCalendarOf(arg1, arg2=None):
    """从 Holidays.txt 中切出仅含指定币种/货币对的真实 McpCalendar（带缓存）。

    返回的是 *真实* 的 McpCalendar，与 McpHolidaysLoad 同类型，可直接喂给
    CalendarAddBusinessDays / CalendarAddPeriod / CalendarFXOExpiryDate 等老 UDF；
    `calendarCodes` 留空时 C++ 会用该 cal 加载的全部 code（即你选的那几条）。

    两种用法：
        =McpCalendarOf(masterCal, ccys)      ' 推荐：masterCal 来自 McpHolidaysLoad
        =McpCalendarOf(ccys [, path])        ' 兼容：自动按 path 加载/复用主日历

    ccys 形式：
        'CNY'                  单币种
        'USDCNY' / 'USD/CNY'   货币对
        'USD,JPY,CNY'          多币种
        Excel 单元格区域       多币种
    """
    try:
        # 用法 1：第一参为已加载的 cal —— 反查所属缓存
        if isinstance(arg1, mcp.mcp.MCalendar):
            info = _info_for_cal(arg1)
            codes = _normalize_ccys(arg2)
            if not codes:
                return "Invalid ccys"
            if info is None:
                return ("masterCal not from McpHolidaysLoad/McpCalendarOf cache; "
                        "请改用 =McpCalendarOf(ccys [, path]) 形式。")
            known = set(info["codes"])
            miss = [c for c in codes if c not in known]
            if miss:
                logging.warning(f"Holidays.txt 缺少 code: {miss}, file={info['path']}")
            return _get_subcal(info, codes)

        # 用法 2：第一参为 ccys
        codes = _normalize_ccys(arg1)
        if not codes:
            return "Invalid ccys"
        info = _load_master(arg2)
        known = set(info["codes"])
        miss = [c for c in codes if c not in known]
        if miss:
            logging.warning(f"Holidays.txt 缺少 code: {miss}, file={info['path']}")
        return _get_subcal(info, codes)
    except Exception as e:
        logging.warning(f"McpCalendarOf failed: {e}", exc_info=True)
        return f"McpCalendarOf error: {e}"


# =========================
# 日历计算 UDF
# =========================
@xl_func("object cal, datetime date, var count, str calendarCodes: datetime", macro=False, recalc_on_open=False)
def CalendarAddBusinessDays(cal, date, count, calendarCodes=""):
    """加工作日，按指定日历组合调整"""
    sdate = date_to_string(date)
    if not sdate:
        return None
    cnt = int(count)
    result = cal.AddBusinessDays(sdate, cnt, calendarCodes)
    return string_to_date(result)


@xl_func("object cal, datetime date, var rule, str calendarCodes: datetime", macro=False, recalc_on_open=False)
def CalendarAdjust(cal, date, rule, calendarCodes=""):
    """按给定调整规则（Following/ModifiedFollowing/Preceding...）对日期调整"""
    sdate = date_to_string(date)
    if not sdate:
        return None
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
    if not sdate:
        return None
    dateAdjustRule = enum_wrapper.parse2(dateAdjustRule, "DateAdjusterRule")
    result = cal.AddPeriod(sdate, t, dateAdjustRule, endOfMonthRule, lastOpenDay, calendarCodes)
    return string_to_date(result)


@xl_func("object cal, datetime date, str[] tenors: datetime[]", macro=False, recalc_on_open=True, auto_resize=True)
def CalendarAddPeriods(cal, date, tenors):
    """批量 Date + Tenor"""
    s = date_to_string(date)
    if not s:
        return []
    result = []
    for tenor in tenors:
        t = str(tenor).strip()
        if t == "":
            result.append(date)
        else:
            result.append(string_to_date(cal.AddPeriod(s, t)))
    return result


@xl_func(macro=False, recalc_on_open=False)
@xl_arg("cal", "object")
@xl_arg("date", "str")
@xl_arg("isFollowing", "bool")
@xl_arg("calendarCodes", "str")
def CalendarValueDate(cal, date, isFollowing=True, calendarCodes=""):
    """给定交易日期，返回起息日（ValueDate）"""
    s = date_to_string(parse_excel_date(date))
    if not s:
        return None
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
    if not s:
        return None
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
    if not s:
        return None
    result = cal.FXOExpiryDate(s, calendarCodes)
    return pd.to_datetime(result)


@xl_func(macro=False, recalc_on_open=False)
@xl_arg("cal", "object")
@xl_arg("date", "datetime")
@xl_arg("calendarCodes", "str")
def CalendarFXODeliveryDate(cal, date, calendarCodes=""):
    """FXO 交割日（按日历规则）"""
    s = pf_date(date)
    if not s:
        return None
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
    if not _referenceDate:
        return None
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
    if not _referenceDate:
        return None
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
    if not s:
        return None
    result = cal.IsBusinessDay(s, calendarCodes)
    return result


# =========================
# 日历信息查询
# =========================
@xl_func(macro=False, recalc_on_open=False, auto_resize=True)
@xl_arg("cal", "object")
def CalendarGetCodes(cal):
    """返回 Calendar 中的所有日历代码（逗号分隔）"""
    try:
        return cal.GetCalendarCodes()
    except Exception as e:
        return f"CalendarGetCodes error: {e}"


@xl_func(macro=False, recalc_on_open=False)
@xl_arg("cal", "object")
def CalendarGetCodeCount(cal):
    """返回 Calendar 中的日历代码数量"""
    try:
        return cal.GetCalendarCodeCount()
    except Exception as e:
        return f"CalendarGetCodeCount error: {e}"


@xl_func(macro=False, recalc_on_open=False)
@xl_arg("cal", "object")
def CalendarGetHolidaysFileText(cal):
    """将 Calendar 导出为 holidays 文本，放入单元格。"""
    try:
        if cal is None:
            return ""
        getter = getattr(cal, "GetHolidaysFileText", None)
        if not callable(getter):
            return "GetHolidaysFileText not available on calendar"
        return getter() or ""
    except Exception as e:
        return f"CalendarGetHolidaysFileText error: {e}"


@xl_func(macro=False, recalc_on_open=False)
@xl_arg("cal", "object")
@xl_arg("calendarCode", "str")
def CalendarGetHolidayCount(cal, calendarCode=""):
    """返回指定日历代码的节假日数量；calendarCode 留空则返回全部节假日数量"""
    try:
        return cal.GetHolidayCount(calendarCode if calendarCode else "")
    except Exception as e:
        return f"CalendarGetHolidayCount error: {e}"


@xl_func(macro=False, recalc_on_open=False, auto_resize=True)
@xl_arg("cal", "object")
@xl_arg("calendarCode", "str")
def CalendarGetHolidayDates(cal, calendarCode=""):
    """返回指定日历代码的节假日列表（逗号分隔的日期字符串）；calendarCode 留空则返回全部"""
    try:
        return cal.GetHolidayDates(calendarCode if calendarCode else "")
    except Exception as e:
        return f"CalendarGetHolidayDates error: {e}"


_HOLIDAY_TABLE_HEADER = ["CalendarCode", "HolidayDate"]
_INTERNAL_HOLIDAY_CODES = frozenset({"NONUSD"})


def _parse_holidays_file_text(text: str) -> List[List[str]]:
    rows: List[List[str]] = [_HOLIDAY_TABLE_HEADER[:]]
    if not text:
        return rows
    for raw in str(text).splitlines():
        line = raw.strip()
        if not line or line.startswith("CALENDAR_C"):
            continue
        parts = line.split(";")
        if len(parts) < 2:
            continue
        code = parts[0].strip()
        date = parts[1].strip()
        if code and date:
            rows.append([code, date])
    return rows


def _holiday_rows_via_codes(cal) -> List[List[str]]:
    rows: List[List[str]] = [_HOLIDAY_TABLE_HEADER[:]]
    raw_codes = cal.GetCalendarCodes() if cal is not None else ""
    codes = [c.strip() for c in str(raw_codes or "").split(",") if c.strip()]
    for code in codes:
        if code in _INTERNAL_HOLIDAY_CODES:
            continue
        dates = str(cal.GetHolidayDates(code) or "")
        items = [d.strip() for d in dates.split(",") if d.strip()]
        if code == "Added" and not items:
            continue
        for date in items:
            rows.append([code, date])
    return rows


def _calendar_holiday_table(cal) -> List[List[str]]:
    getter = getattr(cal, "GetHolidaysFileText", None)
    if callable(getter):
        try:
            text = getter()
            parsed = _parse_holidays_file_text(text)
            if len(parsed) > 1:
                return parsed
            if text and str(text).strip().startswith("CALENDAR_C"):
                return parsed
        except Exception:
            pass
    return _holiday_rows_via_codes(cal)


@xl_func(macro=False, recalc_on_open=False, auto_resize=True)
@xl_arg("cal", "object")
@xl_return("var[][]")
def CalendarToHolidaysTable(cal):
    """将 Calendar 的 code / 日期铺成两列表格（不含 NONUSD、空 Added）。"""
    try:
        if cal is None:
            return [_HOLIDAY_TABLE_HEADER[:], ["", "calendar is empty"]]
        return _calendar_holiday_table(cal)
    except Exception as e:
        return [_HOLIDAY_TABLE_HEADER[:], ["error", str(e)]]


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