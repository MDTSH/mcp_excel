# -*- coding: utf-8 -*-
"""
PyXLL 关闭钩子：释放 MCP 公式在工作簿中创建的全局 C++/Python 缓存。

含 MCP UDF 的工作簿关闭后 EXCEL.EXE 仍驻留，通常是因为各模块的单例/cache
持有 SWIG 对象且无 xl_on_close 清理。在 pyxll.cfg [PYXLL] modules 末尾加入：

    mcp_lifecycle

（须在其他 MCP 模块之后加载）
"""

from __future__ import absolute_import

import gc
import logging
import os

from pyxll import xl_on_close

_log = logging.getLogger(__name__)


def _logs_dir():
    """固定到 python/logs，避免 MCP_LOGPATH 相对路径随 Excel 工作目录漂移。"""
    return os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", "logs"))


_LOAD_MARKER = os.path.join(_logs_dir(), "mcp_lifecycle.loaded")
try:
    os.makedirs(os.path.dirname(_LOAD_MARKER), exist_ok=True)
    with open(_LOAD_MARKER, "w", encoding="utf-8") as _f:
        _f.write("loaded\n")
except Exception:
    pass


def _clear_dict(name, d):
    if d is not None and hasattr(d, "clear"):
        n = len(d)
        d.clear()
        _log.info("mcp_on_close: cleared %s (%d entries)", name, n)


def _safe(fn, label):
    try:
        fn()
    except Exception as e:
        _log.warning("mcp_on_close: %s failed: %s", label, e)


@xl_on_close
def mcp_on_close():
    """Excel 即将关闭时释放 MCP 全局状态（best-effort）。"""
    _marker = os.path.join(_logs_dir(), "mcp_on_close.marker")
    try:
        with open(_marker, "w", encoding="utf-8") as f:
            f.write("start\n")
    except Exception:
        pass
    print("mcp_on_close: start", flush=True)

    def _foundation():
        from mcp.strategy.fi_foundation.batch_foundation import _FOUNDATION_CACHE
        _clear_dict("_FOUNDATION_CACHE", _FOUNDATION_CACHE)

    def _rawmd():
        from pyxll_func.custom import mcp_raw_market_data as rawmd
        _clear_dict("_rawmd_manager_cache", rawmd._rawmd_manager_cache)

    def _portfolio():
        from pyxll_func.custom import mcp_portfolio_adapter as pa
        for name in (
            "_asset_portfolio_managers",
            "_valuator_instances",
            "_global_portfolio_adapters",
            "_hierarchical_managers",
        ):
            _clear_dict(name, getattr(pa, name, None))

    def _xscript():
        from mcp.xscript.structure import stt_def_manager
        _clear_dict("stt_def_manager.stt", stt_def_manager.stt().data)
        _clear_dict("stt_def_manager.model", stt_def_manager.model().data)

    def _forward_rtd():
        from mcp.forward.custom import general_fwd_register
        _clear_dict("general_fwd_register.fwd_def_dict", general_fwd_register.fwd_def_dict)
        _clear_dict("general_fwd_register.def_listener_dict", general_fwd_register.def_listener_dict)

    def _metrics():
        from pyxll_func.core import metrics
        _clear_dict("_risk_metrics_cache", metrics._risk_metrics_cache)
        _clear_dict("_credit_risk_metrics_cache", metrics._credit_risk_metrics_cache)

    def _calendar():
        from pyxll_func.core import mcp_calendar
        _clear_dict("_holidays_cache", mcp_calendar._holidays_cache)

    def _excel_utils():
        from mcp.utils.excel_utils import data_cache, mcp_method_args_cache
        _clear_dict("data_cache", data_cache.cache_dict)
        _clear_dict("mcp_method_args_cache", mcp_method_args_cache.cache_dict)

    def _server_cache():
        from mcp.server_version import mcp_server
        _clear_dict("mcp_server.all_cache", mcp_server.all_cache)
        _clear_dict("mcp_server.object_data_cache", mcp_server.object_data_cache)

    def _wrapper():
        from mcp import wrapper
        _clear_dict("wrapper.cls_dict", wrapper.cls_dict)

    def _async():
        from mcp.utils.async_func import async_func_manager
        for t in async_func_manager.thread_group:
            t.is_running = False
        async_func_manager.func_dict.clear()
        async_func_manager.rtd_dict.clear()

    def _process_pool():
        from mcp.utils.async_process import process_pool
        if process_pool.pool is not None:
            process_pool.dispose()

    for label, fn in (
        ("foundation", _foundation),
        ("rawmd", _rawmd),
        ("portfolio", _portfolio),
        ("xscript", _xscript),
        ("forward_rtd", _forward_rtd),
        ("metrics", _metrics),
        ("calendar", _calendar),
        ("excel_utils", _excel_utils),
        ("server_cache", _server_cache),
        ("wrapper", _wrapper),
        ("async", _async),
        ("process_pool", _process_pool),
    ):
        _safe(fn, label)

    gc.collect()
    try:
        runmode = os.environ.get("MCP_RUNMODE", "")
        with open(_marker, "a", encoding="utf-8") as f:
            f.write("done runmode=%s\n" % runmode)
    except Exception:
        pass
    print("mcp_on_close: done", flush=True)
