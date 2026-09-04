# -*- coding: utf-8 -*-
"""Resolve data / yaml / json paths against the Excel workbook directory.

Call from macro-equivalent UDFs (macro=True). Prefer xlfGetDocument(2)
(GET.DOCUMENT 2) over xl_app() / ActiveWorkbook.Path — COM during workbook
open can native-crash Excel.
"""

from __future__ import absolute_import

import os
import re


def _is_abs_path(path):
    p = path or ""
    return os.path.isabs(p) or (len(p) >= 2 and p[1] == ":") or p.startswith("\\\\")


def _as_dir(path):
    if path is None:
        return ""
    if not isinstance(path, str):
        try:
            path = str(path)
        except Exception:
            return ""
    p = path.strip().strip('"').strip("'")
    if not p or p.startswith("#"):
        return ""
    p = os.path.normpath(p)
    if os.path.isdir(p):
        return p
    if os.path.isfile(p):
        return os.path.dirname(p)
    parent = os.path.dirname(p)
    if parent and os.path.isdir(parent):
        return parent
    # GET.DOCUMENT(2) returns a folder; keep it even if the volume is offline.
    if _is_abs_path(p) and not os.path.splitext(p)[1]:
        return p
    return ""


def _dir_from_caller_address(address):
    """Parse PyXLL caller address like '[E:\\kit\\file.xlsx]Sheet1!A1'."""
    s = str(address or "")
    m = re.search(r"\[([^\]]+)\]", s)
    if not m:
        return ""
    inner = m.group(1).strip()
    if _is_abs_path(inner) or ("/" in inner) or ("\\" in inner):
        return _as_dir(inner)
    return ""


def _dir_from_xlf_get_document(sheet_name=None):
    """Excel 4.0 GET.DOCUMENT(2) = path of the named / current document."""
    from pyxll import xlfGetDocument

    names = []
    if sheet_name:
        names.append(sheet_name)
    names.append(None)
    seen = set()
    for name in names:
        key = name if name is not None else ""
        if key in seen:
            continue
        seen.add(key)
        try:
            raw = xlfGetDocument(2, name) if name else xlfGetDocument(2)
        except TypeError:
            try:
                raw = xlfGetDocument(2)
            except Exception:
                continue
        except Exception:
            continue
        d = _as_dir(raw)
        if d:
            return d
    return ""


def get_active_workbook_dir():
    """Return the directory of the calling workbook, or ''."""
    caller = None
    sheet_name = None
    try:
        from pyxll import xlfCaller

        caller = xlfCaller()
        sheet_name = getattr(caller, "sheet_name", None) or None
        if not sheet_name:
            addr = getattr(caller, "address", None) or str(caller)
            m = re.search(r"(\[[^\]]+\][^!]+)", str(addr or ""))
            if m:
                sheet_name = m.group(1)
    except Exception:
        caller = None

    try:
        d = _dir_from_xlf_get_document(sheet_name)
        if d:
            return d
    except Exception:
        pass

    if caller is not None:
        try:
            rng = caller.to_range()
            wb = rng.Worksheet.Parent
            d = _as_dir(getattr(wb, "Path", "") or "")
            if d:
                return d
        except Exception:
            pass
        try:
            for attr in ("filename", "workbook_path", "path"):
                d = _as_dir(getattr(caller, attr, None))
                if d:
                    return d
            d = _dir_from_caller_address(getattr(caller, "address", None))
            if d:
                return d
            d = _dir_from_caller_address(str(caller))
            if d:
                return d
        except Exception:
            pass
    return ""


def _python_root():
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.normpath(os.path.join(here, "..", ".."))


def _kit_relative_candidates(raw):
    """excel/<kit>/<relative> — only used when the hit is unique."""
    excel_root = os.path.join(_python_root(), "excel")
    if not os.path.isdir(excel_root):
        return []
    try:
        names = os.listdir(excel_root)
    except OSError:
        return []
    return [os.path.normpath(os.path.join(excel_root, name, raw)) for name in names]


def resolve_data_path(path, must_exist=True, allow_dir=False):
    """Resolve a data/yaml/json path against the active workbook directory.

    Returns (ok, resolved_path, err_message).
    """
    raw = (path or "").strip().strip('"').strip("'")
    if not raw:
        return False, "", "Path is empty"

    raw = raw.replace("/", os.sep)

    def _exists(p):
        if os.path.isfile(p):
            return True
        return bool(allow_dir and os.path.isdir(p))

    candidates = []
    seen = set()

    def _add(p):
        p = os.path.normpath(p)
        key = os.path.normcase(p)
        if key not in seen:
            seen.add(key)
            candidates.append(p)

    wb_dir = ""
    if _is_abs_path(raw):
        _add(raw)
    else:
        wb_dir = get_active_workbook_dir()
        if wb_dir:
            _add(os.path.join(wb_dir, raw))
        _add(os.path.abspath(raw))
        _add(os.path.join(_python_root(), raw))
        kit_existing = [c for c in _kit_relative_candidates(raw) if _exists(c)]
        if len(kit_existing) == 1:
            _add(kit_existing[0])

    if not candidates:
        return False, "", "Path is empty"

    if not must_exist:
        return True, candidates[0], ""

    for cand in candidates:
        if _exists(cand):
            return True, cand, ""

    kind = "file or directory" if allow_dir else "file"
    hint = ""
    if not wb_dir and not _is_abs_path(raw):
        kit_existing = [c for c in _kit_relative_candidates(raw) if _exists(c)]
        if len(kit_existing) > 1:
            hint = " (relative path is ambiguous without workbook directory)"
    return False, "", "Path not found (%s): %s%s" % (kind, path, hint)
