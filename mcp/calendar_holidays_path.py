# -*- coding: utf-8 -*-
"""Resolve Holidays.txt path (aligned with qag-time/Calendar.cpp) and attach to McpCalendar."""

from __future__ import annotations

import os
from typing import Any, Optional, Sequence, Tuple

HOLIDAYS_ENV = "MCP_HOLIDAYS_PATH"
_HOLIDAYS_FILE = "Holidays.txt"
_CPP_FALLBACK_DIRS = (
    ".",
    "..",
    "../control",
    "../data",
    "../../",
    "../../control",
    "../../data",
    "../../..",
    "../../../config",
)


def get_pyd_dir() -> str:
    try:
        import mcp.mcp

        ext = getattr(mcp.mcp, "_mcp", None)
        pyd_path = getattr(ext, "__file__", "") if ext is not None else ""
        if not pyd_path:
            pyd_path = getattr(mcp.mcp, "__file__", "") or ""
        return os.path.dirname(os.path.abspath(pyd_path)) if pyd_path else ""
    except Exception:
        return ""


def _join_path(base: str, rel: str, filename: str) -> str:
    return os.path.normpath(os.path.join(base, rel, filename))


def _abs_relative_to_pyd(path: str) -> str:
    path = (path or "").strip()
    if not path:
        return ""
    if os.path.isabs(path) or (len(path) >= 2 and path[1] == ":") or path.startswith("\\\\"):
        return os.path.normpath(path)
    base = get_pyd_dir() or os.getcwd()
    return os.path.normpath(os.path.join(base, path))


def resolve_holidays_path_cpp(*, existing_only: bool = True) -> str:
    """Mirror Calendar::Calendar(string) Holidays.txt search (relative to _mcp.pyd dir)."""
    base = get_pyd_dir()
    if not base:
        return ""

    tried = []
    env_val = os.environ.get(HOLIDAYS_ENV, "").strip()
    if env_val:
        cand = _abs_relative_to_pyd(env_val)
        tried.append(cand)
        if os.path.isfile(cand):
            return os.path.realpath(cand)
        if not existing_only:
            return cand

    for rel in _CPP_FALLBACK_DIRS:
        cand = _join_path(base, rel, _HOLIDAYS_FILE)
        tried.append(cand)
        if os.path.isfile(cand):
            return os.path.realpath(cand)

    if not existing_only and tried:
        return tried[0]
    return ""


def infer_holidays_file_path(raw_args: Sequence[Any]) -> str:
    """Infer Holidays.txt path from McpCalendar constructor args."""
    if not raw_args:
        return ""

    if len(raw_args) == 1:
        return resolve_holidays_path_cpp(existing_only=True)

    if len(raw_args) >= 3:
        is_file = raw_args[2]
        if is_file is True or is_file == 1:
            p = str(raw_args[1])
            if os.path.isabs(p) or (len(p) >= 2 and p[1] == ":") or p.startswith("\\\\"):
                return os.path.realpath(p)
            try:
                from mcp.utils.workbook_path import resolve_data_path

                ok, resolved, _err = resolve_data_path(p, must_exist=True)
                if ok:
                    return os.path.realpath(resolved)
            except Exception:
                pass
            return _abs_relative_to_pyd(p)

    return ""


def attach_holidays_file_path(cal: Any, raw_args: Optional[Sequence[Any]] = None) -> None:
    if cal is None or isinstance(cal, str):
        return
    args = raw_args if raw_args is not None else getattr(cal, "raw_args", None)
    fp = infer_holidays_file_path(args) if args else ""
    if not fp:
        fp = getattr(cal, "_holidays_info_path", "") or ""
    if fp:
        try:
            cal._holidays_file_path = os.path.realpath(fp)
        except Exception:
            pass


def holidays_file_path_for_calendar(cal: Any = None) -> str:
    """
    Return Holidays.txt path for a calendar object, or default C++ search path when cal is None.
    Returns empty string when the calendar was built without a holidays file.
    """
    if cal is None:
        return resolve_holidays_path_cpp(existing_only=True)

    if isinstance(cal, str):
        return ""

    for attr in ("_holidays_file_path", "_holidays_info_path"):
        fp = getattr(cal, attr, None)
        if fp:
            return os.path.realpath(str(fp))

    raw = getattr(cal, "raw_args", None)
    if raw:
        return infer_holidays_file_path(raw)

    return ""
