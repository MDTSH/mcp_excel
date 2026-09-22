# -*- coding: utf-8 -*-
"""Resolve data / yaml / json paths against the Excel workbook directory.

UDF 计算线程默认绝不回打 Excel（GET.DOCUMENT / xl_app / COM）——打开工作簿
时会死锁。工作簿目录来自：xlfCaller 自带路径 → excel_open_gate 注册表
（打开后 C API / COM 快照）→ 同名套件搜索 → 显式 allow_get_document=True
（仅限 recalc_on_open=False 的手动 UDF，且门控未武装时）。
"""

from __future__ import absolute_import

import os
import re
from datetime import datetime


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


def caller_external_address():
    """Caller cell address via xlfCaller only. Never xl_app / Range / GetAddress.

    ``macro=False`` + ``xl_app().Caller.GetAddress`` during sheet calc can
    deadlock Excel (works sometimes, hangs the next open).
    """
    try:
        from pyxll import xlfCaller

        caller = xlfCaller()
        addr = getattr(caller, "address", None)
        if addr:
            return str(addr)
        return str(caller or "")
    except Exception:
        return ""


def udf_trace(msg):
    """Append one line so Excel hangs/crashes leave a breadcrumb on disk."""
    try:
        from datetime import datetime

        folder = os.path.join(_python_root(), "logs")
        if not os.path.isdir(folder):
            os.makedirs(folder)
        path = os.path.join(folder, "livestore_udf.log")
        line = "%s %s\n" % (datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3], msg)
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(line)
    except Exception:
        pass


def get_active_workbook_dir(allow_get_document=False):
    """Return the directory of the calling workbook, or ''.

    默认绝不调 GET.DOCUMENT：UDF 在打开工作簿的计算线程里调它会死锁。
    顺序：xlfCaller 自带路径 → 当前簿注册表 → 按当前 xlsx 文件名找唯一同名套件
    → 仅当簿名未知时才用 last_dir → 显式 allow_get_document=True
    且门控未武装时才 GET.DOCUMENT。
    """
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

    # 先解析 xlfCaller 自带路径。不要 caller.to_range() / xl_app：
    # UDF 计算中回打 COM 会和 Excel 互相等待而死锁。
    if caller is not None:
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

    # 打开期门控的工作簿注册表（宏上下文 C API / COM 快照，UDF 只读）。
    wb_name = ""
    try:
        from mcp.utils import excel_open_gate as _gate

        wb_name = _gate.caller_workbook_name()
        d = _gate.workbook_dir_for(wb_name)
        if d:
            return d
    except Exception:
        pass

    # 当前簿名已知时，按同名套件找目录。禁止先用上一本的 last_dir：
    # 两套 kit 都写 data/MCP_MARKET_DATA_*.json 时，第二本会加载第一本的市场数据。
    kit = _kit_dir_fallback(wb_name)
    if kit:
        return kit
    if not wb_name:
        try:
            from mcp.utils import excel_open_gate as _gate

            # 只在登记了唯一一本时用它。两本都开着时绝不能用 last_dir，
            # CalculateFull 会把两本都解析到最后打开的那套 JSON。
            d = _gate.workbook_dir_if_unique()
            if d:
                return d
        except Exception:
            pass

    if not allow_get_document:
        return ""
    if os.environ.get("MCP_SKIP_XLF_GET_DOCUMENT", "").strip() in ("1", "true", "yes"):
        return _kit_dir_fallback(wb_name)
    try:
        from mcp.utils import excel_open_gate as _gate

        if _gate.is_armed():
            return _kit_dir_fallback(wb_name)
    except Exception:
        pass

    try:
        d = _dir_from_xlf_get_document(sheet_name)
        if d:
            _remember_workbook_dir(wb_name, d)
            return d
    except Exception:
        pass
    return _kit_dir_fallback(wb_name)


def _python_root():
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.normpath(os.path.join(here, "..", ".."))


def bundled_market_data_dir():
    """Repo sample snapshots: excel/data/market_data (portable, no machine drive)."""
    return os.path.join(_python_root(), "excel", "data", "market_data")


def _bundled_market_data_candidates(raw):
    """Same basename under shipped sample dirs / MCP_MARKET_DATA_ROOT."""
    base = os.path.basename((raw or "").replace("/", os.sep).replace("\\", os.sep))
    if not base:
        return []
    out = [
        os.path.join(bundled_market_data_dir(), base),
        os.path.join(_python_root(), "excel", "data", base),
        os.path.join(_python_root(), "data", base),
    ]
    env = (os.environ.get("MCP_MARKET_DATA_ROOT") or "").strip()
    if env:
        out.append(os.path.join(env, base))
        out.append(os.path.join(env, raw.replace("/", os.sep)))
    return out


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


def _registered_workbook_names():
    try:
        from mcp.utils import excel_open_gate as _gate

        return list(_gate.registered_workbook_dirs().keys())
    except Exception:
        return []


def _unique_registered_relative(raw, allow_dir=False):
    """caller 为空时：登记表里恰好一份相对路径命中才用，避免两套同名 JSON 互串。"""
    try:
        from mcp.utils import excel_open_gate as _gate

        items = list(_gate.registered_workbook_dirs().items())
    except Exception:
        return []
    hits = []
    seen = set()
    for name, directory in items:
        for cand in _workbook_relative_candidates(raw, directory, name):
            if os.path.isfile(cand) or (allow_dir and os.path.isdir(cand)):
                key = os.path.normcase(os.path.normpath(cand))
                if key not in seen:
                    seen.add(key)
                    hits.append(os.path.normpath(cand))
    if len(hits) == 1:
        return hits
    return []


def _workbook_stem(wb_name=None):
    name = (wb_name or "").strip()
    if not name:
        try:
            from mcp.utils import excel_open_gate as _gate

            name = _gate.caller_workbook_name()
        except Exception:
            name = ""
    if not name:
        keys = _registered_workbook_names()
        if len(keys) == 1:
            name = keys[0]
    if not name:
        return ""
    base = os.path.basename(str(name).replace("/", os.sep).replace("\\", os.sep))
    stem, _ext = os.path.splitext(base)
    return stem


def _remember_workbook_dir(wb_name, directory, only_if_missing=True):
    if not directory:
        return
    try:
        from mcp.utils import excel_open_gate as _gate

        _gate.record_name_path(wb_name or _workbook_stem(), directory, only_if_missing=only_if_missing)
    except Exception:
        pass


def _kit_dir_fallback(wb_name=None):
    """工作簿目录未知时，按 xlsx 文件名找唯一同名套件。"""
    kit = find_unique_kit_dir(wb_name)
    if kit:
        _remember_workbook_dir(wb_name, kit)
    return kit or ""


def user_kit_search_roots():
    """Downloads / Documents / Desktop（及 OneDrive）。MCP_KIT_SEARCH_ROOTS 可覆盖。"""
    env = (os.environ.get("MCP_KIT_SEARCH_ROOTS") or "").strip()
    if env:
        return [os.path.normpath(p.strip()) for p in env.split(os.pathsep) if p.strip()]

    homes = []
    for key in ("USERPROFILE", "HOME"):
        v = (os.environ.get(key) or "").strip()
        if v:
            homes.append(os.path.normpath(v))
    home = os.path.expanduser("~")
    if home:
        homes.append(os.path.normpath(home))

    roots = []
    seen = set()

    def _add(path):
        if not path:
            return
        p = os.path.normpath(path)
        key = os.path.normcase(p)
        if key not in seen:
            seen.add(key)
            roots.append(p)

    for base in homes:
        for sub in ("Downloads", "Documents", "Desktop"):
            _add(os.path.join(base, sub))
        try:
            for name in os.listdir(base):
                if name.lower().startswith("onedrive"):
                    od = os.path.join(base, name)
                    if os.path.isdir(od):
                        for sub in ("Downloads", "Documents", "Desktop"):
                            _add(os.path.join(od, sub))
        except OSError:
            pass
    return roots


def find_unique_kit_dir(wb_name=None):
    """按工作簿文件名在搜索根下找唯一同名文件夹。多个命中则不用。"""
    stem = _workbook_stem(wb_name)
    if not stem:
        return ""
    hits = []
    seen = set()
    for root in user_kit_search_roots():
        if not os.path.isdir(root):
            continue
        cand = os.path.join(root, stem)
        if os.path.isdir(cand):
            key = os.path.normcase(os.path.normpath(cand))
            if key not in seen:
                seen.add(key)
                hits.append(os.path.normpath(cand))
        if os.path.normcase(os.path.basename(root)) == os.path.normcase(stem):
            key = os.path.normcase(os.path.normpath(root))
            if key not in seen:
                seen.add(key)
                hits.append(os.path.normpath(root))
    if len(hits) == 1:
        return hits[0]
    return ""


def _workbook_relative_candidates(raw, wb_dir, wb_name=None):
    """xlsx 在套件内，或与同名文件夹并排。"""
    out = []
    if not wb_dir:
        return out
    out.append(os.path.join(wb_dir, raw))
    stems = []
    name_stem = _workbook_stem(wb_name)
    if name_stem:
        stems.append(name_stem)
    current_key = ""
    try:
        from mcp.utils import excel_open_gate as _gate

        current_key = _gate.workbook_key(wb_name) if wb_name else ""
    except Exception:
        current_key = ""
    for key in _registered_workbook_names():
        if current_key:
            try:
                from mcp.utils import excel_open_gate as _gate

                if _gate.workbook_key(key) != current_key:
                    continue
            except Exception:
                pass
        stem = os.path.splitext(os.path.basename(key))[0]
        if stem and stem not in stems:
            stems.append(stem)
    folder_stem = os.path.basename(wb_dir)
    if folder_stem and folder_stem not in stems:
        stems.append(folder_stem)
    parent = os.path.dirname(wb_dir)
    for stem in stems:
        beside = os.path.join(wb_dir, stem)
        if os.path.isdir(beside):
            out.append(os.path.join(beside, raw))
        if parent:
            sibling = os.path.join(parent, stem)
            if os.path.isdir(sibling):
                out.append(os.path.join(sibling, raw))
    return out


def _user_kit_relative_candidates(raw, wb_name=None):
    """无工作簿目录时，按文件名在 Downloads 等找同名套件。"""
    kit = find_unique_kit_dir(wb_name)
    if not kit:
        return []
    _remember_workbook_dir(wb_name, kit)
    return [os.path.join(kit, raw), os.path.join(kit, "data", os.path.basename(raw))]


def _latest_json_in_dirs(directories):
    import glob

    files = []
    seen = set()
    for directory in directories:
        if not directory or not os.path.isdir(directory):
            continue
        for path in glob.glob(os.path.join(directory, "MCP_MARKET_DATA_*.json")):
            if not os.path.isfile(path):
                continue
            key = os.path.normcase(os.path.normpath(path))
            if key not in seen:
                seen.add(key)
                files.append(os.path.normpath(path))
    if not files:
        return ""
    files.sort(key=lambda p: os.path.basename(p), reverse=True)
    return files[0]


def latest_mcp_market_data_json():
    """空路径时扫工作簿/同名套件 data/，再扫仓库样例。"""
    dirs = []
    wb = get_active_workbook_dir(allow_get_document=False)
    if wb:
        dirs.append(os.path.join(wb, "data"))
        stem = _workbook_stem()
        if stem:
            dirs.append(os.path.join(wb, stem, "data"))
        parent = os.path.dirname(wb)
        if stem and parent:
            dirs.append(os.path.join(parent, stem, "data"))
    kit = find_unique_kit_dir()
    if kit:
        dirs.append(os.path.join(kit, "data"))
    dirs.append(bundled_market_data_dir())
    dirs.append(os.path.join(_python_root(), "excel", "data"))
    dirs.append(os.path.join(_python_root(), "data"))
    env = (os.environ.get("MCP_MARKET_DATA_ROOT") or "").strip()
    if env:
        dirs.append(env)
    return _latest_json_in_dirs(dirs)


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
    wb_name = ""
    try:
        from mcp.utils import excel_open_gate as _gate

        wb_name = _gate.caller_workbook_name()
    except Exception:
        wb_name = ""

    if _is_abs_path(raw):
        _add(raw)
    else:
        wb_dir = get_active_workbook_dir(allow_get_document=False)
        for cand in _workbook_relative_candidates(raw, wb_dir, wb_name):
            _add(cand)
        if not wb_dir:
            for cand in _unique_registered_relative(raw, allow_dir=allow_dir):
                _add(cand)
        for cand in _user_kit_relative_candidates(raw, wb_name):
            _add(cand)
        _add(os.path.abspath(raw))
        _add(os.path.join(_python_root(), raw))
        for bundled in _bundled_market_data_candidates(raw):
            _add(bundled)
        kit_existing = [c for c in _kit_relative_candidates(raw) if _exists(c)]
        if len(kit_existing) == 1:
            _add(kit_existing[0])

    if not candidates:
        return False, "", "Path is empty"

    if not must_exist:
        return True, candidates[0], ""

    for cand in candidates:
        if _exists(cand):
            hit_dir = cand if os.path.isdir(cand) else os.path.dirname(cand)
            if hit_dir and not wb_dir:
                _remember_workbook_dir(wb_name, hit_dir if os.path.basename(hit_dir).lower() != "data" else os.path.dirname(hit_dir))
            return True, cand, ""

    kind = "file or directory" if allow_dir else "file"
    hint = ""
    if not wb_dir and not _is_abs_path(raw):
        kit_existing = [c for c in _kit_relative_candidates(raw) if _exists(c)]
        nreg = 0
        try:
            from mcp.utils import excel_open_gate as _gate

            nreg = _gate.registered_workbook_count()
        except Exception:
            nreg = 0
        if nreg > 1:
            hint = (
                " (calling workbook unknown with %d workbooks open; "
                "press F9 on this sheet, do not Calculate Full)"
                % nreg
            )
        elif len(kit_existing) > 1:
            hint = " (relative path is ambiguous without workbook directory)"
        elif not wb_name and nreg == 0:
            hint = " (workbook directory unknown; press F9 on this sheet after PyXLL reload)"
    tried = "; ".join(candidates[:8])
    if len(candidates) > 8:
        tried += "; ..."
    return False, "", "Path not found (%s): %s%s (tried: %s)" % (kind, path, hint, tried)


def resolve_workbook_relative_file(path, extra_dirs=None):
    """解析相对文件名：工作簿目录优先，其次 extra_dirs / data / cwd。

    extra_dirs：市场数据 root、JSON 所在目录等。
    返回 (ok, resolved_path, err_message)。
    """
    raw = (path or "").strip().strip('"').strip("'")
    if not raw:
        return False, "", "Path is empty"
    raw = raw.replace("/", os.sep)
    if _is_abs_path(raw) and os.path.isfile(raw):
        return True, os.path.normpath(raw), ""

    candidates = []
    seen = set()

    def _add(p):
        if not p:
            return
        p = os.path.normpath(p)
        key = os.path.normcase(p)
        if key not in seen:
            seen.add(key)
            candidates.append(p)

    wb = get_active_workbook_dir(allow_get_document=False)
    if wb:
        _add(os.path.join(wb, raw))
        _add(os.path.join(wb, "data", os.path.basename(raw)))
        _add(os.path.join(wb, "data", raw))
    for d in extra_dirs or []:
        if d:
            _add(os.path.join(d, raw))
            _add(os.path.join(d, os.path.basename(raw)))
    _add(os.path.abspath(raw))
    ok, resolved, err = resolve_data_path(raw, must_exist=True)
    if ok and resolved:
        _add(resolved)

    for cand in candidates:
        if os.path.isfile(cand):
            return True, cand, ""
    return False, "", err or ("holidays file not found: %s" % path)


def default_xscript_trace_dir(workbook_dir=None):
    """Return {workbook}/xScript/YYYYMMDD, or '' if workbook dir is unknown."""
    wb = workbook_dir if workbook_dir is not None else get_active_workbook_dir(allow_get_document=False)
    if not wb:
        return ""
    return os.path.join(wb, "xScript", datetime.now().strftime("%Y%m%d"))


def resolve_xscript_trace_file(trace_file_name, allow_get_document=True, kind=""):
    """Resolve GetTraceFileName() (often data/xScript/YYYYMMDD/id_xscript.md).

    kind: "localvol" only *_LocalVol.md; "xscript" only *_xscript.md;
    empty = infer from filename, otherwise do not mix the two.
    """
    name = str(trace_file_name or "").replace("\\", os.sep).replace("/", os.sep)
    kind = str(kind or "").strip().lower()
    if not kind:
        base = os.path.basename(name)
        if "LocalVol" in base:
            kind = "localvol"
        elif "xscript" in base.lower():
            kind = "xscript"
    if name.startswith("file:" + os.sep + os.sep + os.sep):
        name = name[8:]
    elif name.startswith("file:" + os.sep + os.sep):
        name = name[7:]

    candidates = []
    seen = set()

    def _add(p):
        if not p:
            return
        p = os.path.normpath(p)
        key = os.path.normcase(p)
        if key not in seen:
            seen.add(key)
            candidates.append(p)

    wb = get_active_workbook_dir(allow_get_document=allow_get_document)
    if name and _is_abs_path(name):
        _add(name)
    elif name:
        if wb:
            _add(os.path.join(wb, name))
            _add(os.path.join(wb, "xScript", datetime.now().strftime("%Y%m%d"), os.path.basename(name)))
            _add(os.path.join(wb, "data", "xScript", datetime.now().strftime("%Y%m%d"), os.path.basename(name)))
        env_root = (os.environ.get("MCP_XSCRIPT_TRACE_ROOT") or "").strip()
        if env_root:
            _add(os.path.join(env_root, datetime.now().strftime("%Y%m%d"), os.path.basename(name)))
            _add(os.path.join(env_root, os.path.basename(name)))
        excel_trace_dir = default_xscript_trace_dir(wb if wb else None)
        if excel_trace_dir:
            _add(os.path.join(excel_trace_dir, os.path.basename(name)))
        _add(os.path.abspath(name))
        _add(os.path.join(os.getcwd(), name))
        _add(os.path.join(os.path.expanduser("~"), "Documents", name))
        _add(os.path.join(_python_root(), name))
    else:
        if wb:
            _add(os.path.join(wb, "xScript"))
            _add(os.path.join(wb, "xScript", datetime.now().strftime("%Y%m%d")))
            _add(os.path.join(wb, "data", "xScript"))
        env_root = (os.environ.get("MCP_XSCRIPT_TRACE_ROOT") or "").strip()
        if env_root:
            _add(env_root)
            _add(os.path.join(env_root, datetime.now().strftime("%Y%m%d")))

    import glob

    def _latest_in_dir(directory, pattern):
        if not directory:
            return ""
        matches = [
            p for p in glob.glob(os.path.join(directory, pattern)) if os.path.isfile(p)
        ]
        if pattern.endswith("*_LocalVol.md"):
            matches = [
                p for p in matches
                if "_py_LocalVol" not in os.path.basename(p) and _localvol_md_has_plots(p)
            ]
        if not matches:
            return ""
        matches.sort(key=os.path.getmtime, reverse=True)
        return os.path.normpath(matches[0])

    checked = []
    for cand in candidates:
        checked.append(cand)
        if os.path.isfile(cand):
            base_c = os.path.basename(cand)
            if kind == "localvol" and "_xscript.md" in base_c.lower():
                continue
            if kind == "xscript" and "LocalVol" in base_c:
                continue
            return cand, checked
        # LocalVol OpenTraceFile historically treated "..._LocalVol.md" as a
        # directory and wrote a nested * _LocalVol.md inside it.
        if os.path.isdir(cand):
            pats = []
            if kind != "xscript":
                pats.append("*_LocalVol.md")
            if kind != "localvol":
                pats.append("*_xscript.md")
            for pat in pats:
                latest = _latest_in_dir(cand, pat)
                if latest:
                    checked.append(latest)
                    return latest, checked
        directory, base = os.path.split(cand)
        if directory and kind != "localvol" and base.endswith("_xscript.md"):
            stem = base[: -len("_xscript.md")]
            # Price() 写成 {stem}_price_{id}_xscript.md，GetTraceFileName 却常返回 {stem}_xscript.md
            latest = _latest_in_dir(directory, stem + "*_xscript.md")
            if latest:
                checked.append(latest)
                return latest, checked
            latest = _latest_in_dir(directory, "*_xscript.md")
            if latest:
                checked.append(latest)
                return latest, checked
        if directory and kind != "xscript" and "LocalVol" in base:
            latest = _latest_in_dir(directory, "*_LocalVol.md")
            if latest:
                checked.append(latest)
                return latest, checked
    # 工作簿 xScript/ 下任意日期目录里最新的一份（打开当天换了 unique id 时）
    if wb:
        xs = os.path.join(wb, "xScript")
        if os.path.isdir(xs):
            import glob as _glob

            patterns = []
            if kind != "xscript":
                patterns.append("*_LocalVol.md")
            if kind != "localvol":
                patterns.append("*_xscript.md")
            matches = []
            for pat in patterns:
                matches.extend(
                    p
                    for p in _glob.glob(os.path.join(xs, "*", pat))
                    if os.path.isfile(p) and "_py_LocalVol" not in os.path.basename(p)
                )
            if kind == "localvol":
                matches = [p for p in matches if _localvol_md_has_plots(p)]
            if matches:
                matches.sort(key=os.path.getmtime, reverse=True)
                latest = os.path.normpath(matches[0])
                checked.append(latest)
                return latest, checked
        else:
            checked.append(xs)
    if not name:
        return "", checked
    return os.path.normpath(name), checked


def apply_excel_sdp_trace_directory(product=None, workbook_dir=None):
    """Default SDP reports to {xlsx_dir}/xScript/YYYYMMDD.

    Sets MCP_XSCRIPT_TRACE_ROOT so C++ generateDirectoryString picks it up
    during construct. After construct, also calls SetTraceDirectory when present.
    Uses GET.DOCUMENT only — no COM during Excel calculation.
    """
    wb = workbook_dir if workbook_dir is not None else get_active_workbook_dir(allow_get_document=False)
    if not wb:
        return ""
    date = datetime.now().strftime("%Y%m%d")
    root = os.path.join(wb, "xScript")
    trace_dir = os.path.join(root, date)
    os.environ["MCP_XSCRIPT_TRACE_ROOT"] = root
    if product is not None and hasattr(product, "SetTraceDirectory"):
        try:
            product.SetTraceDirectory(trace_dir)
        except Exception:
            pass
    return trace_dir


def _want_generate(flag):
    if flag is True:
        return True
    if isinstance(flag, (int, float)) and flag == 1:
        return True
    s = str(flag or "").strip().lower()
    return s in ("generate", "true", "yes", "1", "gen")


def _localvol_md_has_plots(path):
    base = os.path.basename(path or "")
    if "_py_LocalVol" in base:
        return False
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as fh:
            text = fh.read(12000)
        # Python GetVolatility+Black 假报告：预测价几乎全 0，不能当校准结果复用
        if "使用已构建 LocalVol 复算" in text:
            return False
        return "<!--PLOT1-->" in text or "<!--PLOT2-->" in text
    except Exception:
        return False


def _call_native_sdp_generate_report(obj, trace_dir):
    type_name = type(obj).__name__ if obj is not None else ""
    prefixes = []
    if "StructuredDerivative" in type_name:
        prefixes.append("MStructuredDerivativeProduct_GenerateReport")
    if "XScriptStructure" in type_name or "StructuredDerivative" in type_name:
        prefixes.append("MXScriptStructure_GenerateReport")
    candidates = []
    try:
        import mcp.mcp as mcp_mod

        for name in prefixes:
            candidates.append(getattr(mcp_mod, name, None))
        inner = getattr(mcp_mod, "_mcp", None)
        if inner is not None:
            for name in prefixes:
                candidates.append(getattr(inner, name, None))
    except Exception:
        pass
    try:
        import _mcp

        for name in prefixes:
            candidates.append(getattr(_mcp, name, None))
    except Exception:
        pass
    for native in candidates:
        if not callable(native):
            continue
        try:
            out = native(obj, trace_dir or "")
            if out:
                return out
        except Exception:
            continue
    return ""


def generate_sdp_report(obj, trace_dir=""):
    """先找已有 *_xscript.md；没有再调 C++ GenerateReport（内部临时 Trace + Price）。"""
    if obj is None:
        return ""
    if trace_dir:
        try:
            if hasattr(obj, "SetTraceDirectory"):
                obj.SetTraceDirectory(trace_dir)
        except Exception:
            pass
    name = ""
    if hasattr(obj, "GetTraceFileName"):
        try:
            name = obj.GetTraceFileName() or ""
        except Exception:
            name = ""
    resolved, _checked = resolve_xscript_trace_file(name)
    if resolved and os.path.isfile(resolved):
        return resolved

    native = _call_native_sdp_generate_report(obj, trace_dir)
    if native:
        resolved2, _ = resolve_xscript_trace_file(native)
        if resolved2 and os.path.isfile(resolved2):
            return resolved2
        if os.path.isfile(str(native)):
            return os.path.normpath(str(native))

    price = getattr(obj, "Price", None)
    if callable(price):
        try:
            price(True)
        except TypeError:
            try:
                price()
            except Exception:
                pass
        except Exception:
            pass
        name2 = ""
        if hasattr(obj, "GetTraceFileName"):
            try:
                name2 = obj.GetTraceFileName() or ""
            except Exception:
                name2 = ""
        resolved3, _ = resolve_xscript_trace_file(name2 or name)
        if resolved3 and os.path.isfile(resolved3):
            return resolved3
    return resolved or ""


def bind_sdp_generate_report():
    """给 SWIG 的 MStructuredDerivativeProduct / MXScriptStructure 补 GenerateReport。"""
    fn = generate_sdp_report
    try:
        import mcp.mcp as mcp_mod
    except Exception:
        mcp_mod = None
    for cls_name in ("MStructuredDerivativeProduct", "MXScriptStructure"):
        cls = getattr(mcp_mod, cls_name, None) if mcp_mod is not None else None
        if cls is None:
            continue
        native = getattr(cls, "GenerateReport", None)
        if native is None or getattr(cls, "_mcp_py_sdp_generate_report", False) is True:
            cls.GenerateReport = fn
            cls._mcp_py_sdp_generate_report = True
        elif getattr(native, "__func__", native) is not fn:
            def _safe_generate(self, traceDir="", _native=native, _fn=fn):
                try:
                    out = _native(self, traceDir)
                    if out and os.path.isfile(str(out)):
                        return out
                except Exception:
                    pass
                return _fn(self, traceDir)

            cls.GenerateReport = _safe_generate
            cls._mcp_py_sdp_generate_report = True


def ensure_xscript_trace_file(obj, generate=False):
    """Return (md_path, candidates).

    generate=False (Excel default): only resolve an existing md. Never re-price.
    generate=True: call GenerateReport. SDP may run a full Trace MC — do not
    put this on a recalc-on-open cell.
    """
    name = ""
    if obj is not None and hasattr(obj, "GetTraceFileName"):
        try:
            name = obj.GetTraceFileName() or ""
        except Exception:
            name = ""
    type_name = type(obj).__name__ if obj is not None else ""
    is_localvol = "LocalVol" in type_name
    is_sdp = "StructuredDerivative" in type_name or "XScriptStructure" in type_name
    kind = "localvol" if is_localvol else ("xscript" if is_sdp else "")
    resolved, candidates = resolve_xscript_trace_file(name, kind=kind)
    if resolved and os.path.isfile(resolved):
        if is_localvol and (
            "_xscript.md" in os.path.basename(resolved).lower()
            or not _localvol_md_has_plots(resolved)
        ):
            resolved = ""
        elif not is_localvol or _localvol_md_has_plots(resolved):
            return resolved, candidates
    try:
        from mcp.utils.localvol_report import bind_localvol_generate_report

        bind_localvol_generate_report()
    except Exception:
        pass
    try:
        bind_sdp_generate_report()
    except Exception:
        pass
    # LocalVol / SDP 的 GetTraceFileName 经常指向尚未落盘的名字（Price 写成 *_price_*）。
    # 打开期 HmReport 已被门控推迟；打开后再自动 GenerateReport，避免格子报 "file not generated"。
    if not _want_generate(generate) and not is_localvol and not is_sdp:
        return resolved, candidates

    trace_dir = apply_excel_sdp_trace_directory(
        obj if obj is not None and hasattr(obj, "SetTraceDirectory") else None
    )
    gen = getattr(obj, "GenerateReport", None) if obj is not None else None
    generated = ""
    if callable(gen):
        try:
            generated = gen(trace_dir or "")
        except TypeError:
            generated = gen()
        except Exception as ex:
            candidates.append("GenerateReport: %s" % ex)
            generated = ""
    elif not is_localvol:
        candidates.append("GenerateReport not available on this object")
        return resolved, candidates
    if is_localvol and (not generated or not os.path.isfile(str(generated))):
        try:
            from mcp.utils.localvol_report import generate_localvol_report

            generated = generate_localvol_report(obj, trace_dir or "") or generated
        except Exception as ex:
            candidates.append("generate_localvol_report: %s" % ex)
    resolved2, extra = resolve_xscript_trace_file(generated, kind=kind)
    for p in extra:
        if p not in candidates:
            candidates.append(p)
    if resolved2 and os.path.isfile(resolved2):
        return resolved2, candidates
    if generated and os.path.isfile(str(generated)):
        return os.path.normpath(str(generated)), candidates
    if is_localvol:
        candidates.append(
            "GetTraceFileName=%s; Heston report needs Parameters() plus strike/expiry quotes"
            % (name or "(empty)")
        )
    return resolved2 or resolved, candidates
