#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""MCP Excel one-click installer. Stdlib only — any Python 3.8+ can run this."""

from __future__ import annotations

import argparse
import filecmp
import json
import os
import re
import shutil
import struct
import subprocess
import sys
import time
import winreg
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

SUPPORTED_MINOR = (9, 10, 11, 12, 13)
REQUIRED_IMPORTS = ("numpy", "pandas", "requests", "dateutil")
MIN_BOOTSTRAP = (3, 8)

# ---------------------------------------------------------------------------
# i18n
# ---------------------------------------------------------------------------

LANG_MENU = """
==============================================================================
  MCP Excel Installer  /  MCP Excel 安装程序
==============================================================================
Select language / 选择语言:
  1) 中文  (default / 默认)
  2) English
"""

STRINGS = {
    "zh": {
        "banner": "MCP Excel 一键安装",
        "root": "安装目录",
        "excel_found": "已检测到 Excel（{bit} 位）: {path}",
        "excel_missing": "未检测到 Excel。仍会配置 PyXLL，但注册加载项可能失败。",
        "excel_32": "检测到 32 位 Excel。本包只支持 64 位 Excel，请改用 64 位 Office，或加 --skip-excel 仅配置 Python。",
        "scan": "正在扫描本机 Python 3.9–3.13（64 位）…",
        "none": "没有找到可用的 Python。请先安装 64 位 CPython 3.9–3.13：\n  https://www.python.org/downloads/\n安装时勾选 Add python.exe to PATH。",
        "table_hdr": "序号  版本      依赖          可写   类型        路径",
        "dep_ready": "已齐",
        "dep_miss": "稍后可装",
        "dep_numpy2": "numpy 2.x",
        "kind_official": "官方",
        "kind_conda": "conda",
        "kind_conda_base": "conda-base",
        "kind_venv": "venv",
        "recommend": "推荐",
        "pick": "请输入序号（回车=推荐 {n}），或粘贴 python.exe 路径: ",
        "picked": "已选择: {exe}",
        "invalid_pick": "无效选择，请重试。",
        "forced_python": "使用指定解释器: {exe}",
        "bad_forced": "指定的 Python 不可用: {reason}",
        "deps_ok": "常用计算库已就绪，无需再装。",
        "deps_need": "计算库尚未安装（{pkgs}）。现在不装也可以：Excel 能启动，只有用到需要这些库的函数时才会提示缺少。",
        "deps_ask": "现在安装这些库？不是必须，回车=以后再用时再装 [y/N] ",
        "deps_conda_base": "选中的是 conda 的 base 环境。现在装库可能影响其他项目。确定现在装？[y/N] ",
        "deps_numpy2": "该环境已有 NumPy 2.x。MCP 需要 NumPy 1.x。不会自动降级。请换一个 Python，或自行处理后再装。",
        "deps_run": "正在安装: {cmd}",
        "deps_ok_after": "依赖安装成功。",
        "deps_fail": "依赖安装失败。",
        "deps_offline": "可换另一个 Python，或把 wheel 放到 vendor\\wheels 后重试。手工命令:\n  {cmd}",
        "deps_skip": "已跳过，安装仍继续。以后需要时在本机运行:\n  {cmd}",
        "cfg_copy": "已从模板创建 {cfg}",
        "cfg_bak": "已备份配置: {bak}",
        "cfg_exe": "已写入 executable = {exe}",
        "cfg_fail": "写入 pyxll.cfg 失败: {err}",
        "xll_ok": "pyxll.xll 已匹配 Python {ver}（{tag}）",
        "xll_swapped": "已将 pyxll.xll 切换为 Python {ver}（{tag}）",
        "xll_legacy": "未找到按版本分的 xll，沿用现有 lib\\X64\\pyxll.xll",
        "xll_missing": "缺少 {path}。请换已带该 ABI 的 Python，或补齐 lib\\X64\\pyxll\\{tag}\\pyxll.xll",
        "xll_fail": "写入 pyxll.xll 失败: {err}",
        "lic_title": "—— PyXLL 许可 ——",
        "lic_note": "MCP 引擎可按项目许可使用；Excel 加载项依赖 PyXLL，需单独向 https://www.pyxll.com/ 购买或申请试用。\n本安装包不附带可用的 PyXLL 许可。密钥只写入本机 pyxll.cfg，不会上传。",
        "lic_have": "已检测到许可（末四位 {tail}），将保留。",
        "lic_env": "已从环境变量 PYXLL_LICENSE_KEY 读取许可。",
        "lic_file": "已找到许可文件: {path}",
        "lic_ask": "请粘贴 PyXLL 许可密钥（回车=跳过试用）\n或输入许可文件完整路径:\n> ",
        "lic_skip": "未写入许可。Excel 首次打开时请按 PyXLL 提示激活；试用到期后函数会停用。",
        "lic_written_key": "已写入许可密钥（末四位 {tail}）。",
        "lic_written_file": "已写入许可文件路径。",
        "excel_running": "Excel 正在运行。注册加载项前请先关闭 Excel。关闭后回车继续，或输入 s 跳过注册: ",
        "reg_run": "正在注册 PyXLL 加载项…",
        "reg_ok": "PyXLL 加载项已注册。请重新打开 Excel。",
        "reg_fail": "自动注册失败。可稍后运行:\n  {cmd}\n或在 Excel → 选项 → 加载项 中手动选择:\n  {xll}",
        "reg_skip": "已跳过加载项注册。",
        "probe_only": "仅探测，不修改系统。",
        "next": "下一步:\n  1. 完全退出 Excel 后重新打开\n  2. 文件 → 选项 → 加载项，确认 PyXLL 已启用\n  3. 打开 excel\\zh 下的示例工作簿试算",
        "done": "安装流程结束。",
        "log": "日志: {path}",
        "abort": "已中止。",
        "press": "按回车退出…",
    },
    "en": {
        "banner": "MCP Excel one-click setup",
        "root": "Install root",
        "excel_found": "Excel detected ({bit}-bit): {path}",
        "excel_missing": "Excel not found. PyXLL will still be configured; add-in registration may fail.",
        "excel_32": "32-bit Excel detected. This package is 64-bit only. Install 64-bit Office, or pass --skip-excel to configure Python only.",
        "scan": "Scanning local 64-bit Python 3.9–3.13…",
        "none": "No usable Python found. Install 64-bit CPython 3.9–3.13 from:\n  https://www.python.org/downloads/\nTick “Add python.exe to PATH”.",
        "table_hdr": " #    Version   Deps          Write  Kind        Path",
        "dep_ready": "ready",
        "dep_miss": "later",
        "dep_numpy2": "numpy 2.x",
        "kind_official": "CPython",
        "kind_conda": "conda",
        "kind_conda_base": "conda-base",
        "kind_venv": "venv",
        "recommend": "recommended",
        "pick": "Enter a number (Enter = #{n}), or a python.exe path: ",
        "picked": "Selected: {exe}",
        "invalid_pick": "Invalid choice, try again.",
        "forced_python": "Using --python: {exe}",
        "bad_forced": "The given Python cannot be used: {reason}",
        "deps_ok": "Numeric libraries are already present.",
        "deps_need": "Numeric libraries are not installed yet ({pkgs}). Optional now: Excel will start; a function prompts only when it actually needs a package.",
        "deps_ask": "Install them now? Optional. Enter = later, when you start using Excel [y/N] ",
        "deps_conda_base": "This is conda base. Installing here may affect other projects. Install now anyway? [y/N] ",
        "deps_numpy2": "This env has NumPy 2.x; MCP needs NumPy 1.x. Will not downgrade. Pick another Python.",
        "deps_run": "Installing: {cmd}",
        "deps_ok_after": "Dependencies installed.",
        "deps_fail": "pip install failed.",
        "deps_offline": "Pick another Python, or put wheels in vendor\\wheels and retry.\nManual command:\n  {cmd}",
        "deps_skip": "Skipped; setup continues. Install later with:\n  {cmd}",
        "cfg_copy": "Created {cfg} from template.",
        "cfg_bak": "Config backup: {bak}",
        "cfg_exe": "Wrote executable = {exe}",
        "cfg_fail": "Failed to update pyxll.cfg: {err}",
        "xll_ok": "pyxll.xll already matches Python {ver} ({tag})",
        "xll_swapped": "Switched pyxll.xll to Python {ver} ({tag})",
        "xll_legacy": "No per-ABI xll folder; keeping lib\\X64\\pyxll.xll",
        "xll_missing": "Missing {path}. Pick a Python that has a shipped xll, or add lib\\X64\\pyxll\\{tag}\\pyxll.xll",
        "xll_fail": "Failed to write pyxll.xll: {err}",
        "lic_title": "—— PyXLL license ——",
        "lic_note": "The MCP engine follows this product’s license. The Excel add-in needs a separate PyXLL license from https://www.pyxll.com/ (purchase or trial).\nThis zip does not include a working PyXLL key. The key is written only to local pyxll.cfg.",
        "lic_have": "Existing license kept (ends with {tail}).",
        "lic_env": "Read license from PYXLL_LICENSE_KEY.",
        "lic_file": "Found license file: {path}",
        "lic_ask": "Paste a PyXLL license key (Enter = skip / trial)\nor a full path to a license file:\n> ",
        "lic_skip": "No license written. Activate in Excel when prompted; UDFs stop after the trial.",
        "lic_written_key": "License key written (ends with {tail}).",
        "lic_written_file": "License file path written.",
        "excel_running": "Excel is running. Close it before registering the add-in. Enter to continue, or s to skip: ",
        "reg_run": "Registering the PyXLL add-in…",
        "reg_ok": "PyXLL add-in registered. Restart Excel.",
        "reg_fail": "Auto-register failed. Later run:\n  {cmd}\nor browse this file in Excel → Options → Add-ins:\n  {xll}",
        "reg_skip": "Skipped add-in registration.",
        "probe_only": "Probe only; nothing was changed.",
        "next": "Next:\n  1. Quit Excel completely and reopen it\n  2. File → Options → Add-ins: confirm PyXLL is enabled\n  3. Try a workbook under excel\\en",
        "done": "Installer finished.",
        "log": "Log: {path}",
        "abort": "Aborted.",
        "press": "Press Enter to exit…",
    },
}


class I18n:
    def __init__(self, lang: str) -> None:
        self.lang = "en" if lang == "en" else "zh"

    def t(self, key: str, **kwargs) -> str:
        text = STRINGS[self.lang].get(key) or STRINGS["en"].get(key, key)
        return text.format(**kwargs) if kwargs else text


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

@dataclass
class Candidate:
    exe: str
    version: Tuple[int, int, int]
    bits: int
    ready: bool
    installable: bool
    writable: bool
    has_pip: bool
    is_conda: bool
    is_conda_base: bool
    is_venv: bool
    numpy2: bool
    missing: List[str] = field(default_factory=list)
    score: int = 0
    reason_skip: str = ""

    @property
    def tag(self) -> str:
        return f"cp{self.version[0]}{self.version[1]}"

    @property
    def version_s(self) -> str:
        return f"{self.version[0]}.{self.version[1]}.{self.version[2]}"


def mcp_root() -> Path:
    return Path(__file__).resolve().parent


def log_path(root: Path) -> Path:
    d = root / "logs"
    d.mkdir(parents=True, exist_ok=True)
    return d / "mcp_install.log"


class Logger:
    def __init__(self, path: Path) -> None:
        self.path = path

    def write(self, msg: str) -> None:
        line = f"{datetime.now().isoformat(timespec='seconds')} {msg}"
        try:
            with self.path.open("a", encoding="utf-8") as fh:
                fh.write(line + "\n")
        except OSError:
            pass


def say(ui: I18n, key: str, log: Optional[Logger] = None, **kwargs) -> None:
    msg = ui.t(key, **kwargs)
    print(msg)
    if log:
        log.write(msg.replace("\n", " | "))


def ask(prompt: str, default: str = "") -> str:
    try:
        raw = input(prompt)
    except EOFError:
        return default
    return raw.strip() if raw.strip() else default


def yes(answer: str, default_yes: bool) -> bool:
    if not answer:
        return default_yes
    return answer[:1].lower() in ("y", "是")


def mask_key(key: str) -> str:
    key = key.strip()
    if len(key) < 4:
        return "****"
    return key[-4:]


def pe_machine(path: Path) -> Optional[str]:
    try:
        with path.open("rb") as fh:
            fh.seek(0x3C)
            pe_off = struct.unpack("<I", fh.read(4))[0]
            fh.seek(pe_off + 4)
            machine = struct.unpack("<H", fh.read(2))[0]
        return {0x14C: "x86", 0x8664: "x64"}.get(machine)
    except OSError:
        return None


def shipped_abi_tags(lib_dir: Path) -> List[str]:
    tags = []
    for p in lib_dir.glob("_mcp.cp*-win_amd64.pyd"):
        m = re.match(r"_mcp\.(cp\d+)-win_amd64\.pyd$", p.name, re.I)
        if m:
            tags.append(m.group(1).lower())
    return tags


def abi_available(lib_dir: Path, major: int, minor: int) -> bool:
    tag = f"cp{major}{minor}"
    return (lib_dir / f"_mcp.{tag}-win_amd64.pyd").exists()


def py_tag(major: int, minor: int) -> str:
    return f"py{major}{minor}"


def shipped_xll_tags(lib_dir: Path) -> List[str]:
    root = lib_dir / "pyxll"
    if not root.is_dir():
        return []
    tags = []
    for p in root.iterdir():
        if p.is_dir() and (p / "pyxll.xll").is_file() and re.match(r"^py\d{2,3}$", p.name, re.I):
            tags.append(p.name.lower())
    return tags


def xll_stock_path(lib_dir: Path, tag: str) -> Path:
    return lib_dir / "pyxll" / tag / "pyxll.xll"


def xll_available(lib_dir: Path, major: int, minor: int) -> bool:
    tags = shipped_xll_tags(lib_dir)
    if not tags:
        return (lib_dir / "pyxll.xll").is_file()
    return xll_stock_path(lib_dir, py_tag(major, minor)).is_file()


def apply_matching_xll(lib_dir: Path, major: int, minor: int, ui: "I18n", log: "Logger") -> bool:
    tag = py_tag(major, minor)
    ver = f"{major}.{minor}"
    dest = lib_dir / "pyxll.xll"
    stock = xll_stock_path(lib_dir, tag)
    tags = shipped_xll_tags(lib_dir)
    if not stock.is_file():
        if dest.is_file() and not tags:
            say(ui, "xll_legacy", log)
            return True
        say(ui, "xll_missing", log, path=str(stock), tag=tag)
        return False
    if dest.is_file() and filecmp.cmp(stock, dest, shallow=False):
        say(ui, "xll_ok", log, ver=ver, tag=tag)
        return True
    try:
        shutil.copy2(stock, dest)
    except OSError as exc:
        say(ui, "xll_fail", log, err=str(exc))
        return False
    say(ui, "xll_swapped", log, ver=ver, tag=tag)
    return True


# ---------------------------------------------------------------------------
# Excel
# ---------------------------------------------------------------------------

def _reg_sz(hive, subkey: str, name: str = "") -> Optional[str]:
    try:
        with winreg.OpenKey(hive, subkey) as key:
            val, _ = winreg.QueryValueEx(key, name)
            return str(val) if val else None
    except OSError:
        return None


def find_excel() -> Tuple[Optional[Path], Optional[str]]:
    paths: List[Path] = []
    app = _reg_sz(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\excel.exe")
    if app:
        paths.append(Path(app))
    client = _reg_sz(
        winreg.HKEY_LOCAL_MACHINE,
        r"SOFTWARE\Microsoft\Office\ClickToRun\Configuration",
        "ClientFolder",
    )
    if client:
        paths.append(Path(client) / "EXCEL.EXE")
    for p in (
        Path(r"C:\Program Files\Microsoft Office\root\Office16\EXCEL.EXE"),
        Path(r"C:\Program Files (x86)\Microsoft Office\root\Office16\EXCEL.EXE"),
    ):
        paths.append(p)
    for p in paths:
        if p.is_file():
            return p, pe_machine(p)
    return None, None


def excel_is_running() -> bool:
    try:
        r = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq EXCEL.EXE"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return "EXCEL.EXE" in (r.stdout or "").upper()
    except (OSError, subprocess.TimeoutExpired):
        return False


# ---------------------------------------------------------------------------
# Python discovery
# ---------------------------------------------------------------------------

def _norm_exe(path: str) -> Optional[str]:
    p = Path(path.strip().strip('"'))
    if not p.is_file():
        return None
    low = str(p).lower()
    if "windowsapps" in low:
        return None
    if p.name.lower() not in ("python.exe", "pythonw.exe"):
        if p.suffix.lower() != ".exe":
            return None
    if p.name.lower() == "pythonw.exe":
        sibling = p.with_name("python.exe")
        p = sibling if sibling.is_file() else p
    return str(p.resolve())


def _reg_pythons() -> List[str]:
    found = []
    for hive in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
        for sub in (r"SOFTWARE\Python\PythonCore", r"SOFTWARE\Python\ContinuumAnalytics"):
            try:
                with winreg.OpenKey(hive, sub) as root:
                    i = 0
                    while True:
                        try:
                            ver = winreg.EnumKey(root, i)
                        except OSError:
                            break
                        i += 1
                        install = _reg_sz(hive, f"{sub}\\{ver}\\InstallPath")
                        if install:
                            exe = Path(install) / "python.exe"
                            n = _norm_exe(str(exe))
                            if n:
                                found.append(n)
            except OSError:
                continue
    return found


def _common_pythons() -> List[str]:
    homes = [
        os.environ.get("LOCALAPPDATA", ""),
        os.environ.get("USERPROFILE", ""),
        os.environ.get("ProgramFiles", ""),
        r"C:\ProgramData",
        r"D:\ProgramData",
        "C:\\",
        "D:\\",
    ]
    names = []
    for minor in range(9, 14):
        names.append(f"Python3{minor}")
        names.append(f"Python3{minor}-32")
    names += [
        "anaconda3",
        "Anaconda3",
        "Anaconda39",
        "miniconda3",
        "Miniconda3",
        "miniforge3",
    ]
    found = []
    for home in homes:
        if not home:
            continue
        base = Path(home)
        for name in names:
            for rel in (Path(name) / "python.exe", Path("Programs") / "Python" / name / "python.exe"):
                n = _norm_exe(str(base / rel))
                if n:
                    found.append(n)
        # conda envs
        for env_root in (base / "anaconda3" / "envs", base / "Anaconda3" / "envs",
                         base / "Anaconda39" / "envs", base / "miniconda3" / "envs"):
            if env_root.is_dir():
                for child in env_root.iterdir():
                    n = _norm_exe(str(child / "python.exe"))
                    if n:
                        found.append(n)
    prefix = os.environ.get("CONDA_PREFIX")
    if prefix:
        n = _norm_exe(str(Path(prefix) / "python.exe"))
        if n:
            found.append(n)
    return found


def _py_launcher() -> List[str]:
    found = []
    try:
        r = subprocess.run(["py", "-0p"], capture_output=True, text=True, timeout=15)
    except (OSError, subprocess.TimeoutExpired):
        return found
    for line in (r.stdout or "").splitlines():
        line = line.strip()
        if not line:
            continue
        path = line.split()[-1]
        n = _norm_exe(path)
        if n:
            found.append(n)
    return found


def _where_pythons() -> List[str]:
    found = []
    for cmd in ("python", "python3"):
        try:
            r = subprocess.run(["where", cmd], capture_output=True, text=True, timeout=10)
        except (OSError, subprocess.TimeoutExpired):
            continue
        for line in (r.stdout or "").splitlines():
            n = _norm_exe(line)
            if n:
                found.append(n)
    return found


def collect_python_exes() -> List[str]:
    seen = set()
    out = []
    for src in (_py_launcher, _reg_pythons, _common_pythons, _where_pythons):
        for exe in src():
            key = os.path.normcase(exe)
            if key not in seen:
                seen.add(key)
                out.append(exe)
    return out


PROBE_CODE = r"""
import json, os, site, struct, sys
info = {
    "exe": sys.executable,
    "version": [sys.version_info.major, sys.version_info.minor, sys.version_info.micro],
    "bits": struct.calcsize("P") * 8,
    "impl": getattr(sys.implementation, "name", "unknown"),
    "prefix": sys.prefix,
    "base_prefix": getattr(sys, "base_prefix", sys.prefix),
    "is_venv": sys.prefix != getattr(sys, "base_prefix", sys.prefix),
    "is_conda": os.path.isdir(os.path.join(sys.prefix, "conda-meta")),
    "store": "WindowsApps" in sys.executable,
    "deps": {},
    "writable": False,
    "has_pip": False,
}
pkgs = {"numpy": "numpy", "pandas": "pandas", "requests": "requests", "dateutil": "dateutil"}
for key, mod in pkgs.items():
    try:
        m = __import__(mod)
        info["deps"][key] = {"ok": True, "version": getattr(m, "__version__", "")}
    except Exception as e:
        info["deps"][key] = {"ok": False, "error": str(e)}
try:
    targets = []
    try:
        targets.extend(site.getsitepackages())
    except Exception:
        pass
    try:
        targets.append(site.getusersitepackages())
    except Exception:
        pass
    info["writable"] = any(os.access(t, os.W_OK) for t in targets if t and os.path.isdir(t))
    if not info["writable"]:
        info["writable"] = os.access(sys.prefix, os.W_OK)
except Exception:
    pass
try:
    import pip  # noqa: F401
    info["has_pip"] = True
except Exception:
    info["has_pip"] = False
print(json.dumps(info))
"""


def probe(exe: str) -> Optional[dict]:
    try:
        r = subprocess.run(
            [exe, "-c", PROBE_CODE],
            capture_output=True,
            text=True,
            timeout=20,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if r.returncode != 0:
        return None
    try:
        return json.loads(r.stdout.strip().splitlines()[-1])
    except (json.JSONDecodeError, IndexError):
        return None


def evaluate(exe: str, lib_dir: Path, cfg_exe: Optional[str]) -> Optional[Candidate]:
    info = probe(exe)
    if not info or info.get("store"):
        return None
    ver = tuple(info["version"])
    if info["bits"] != 64:
        return None
    if ver[0] != 3 or ver[1] not in SUPPORTED_MINOR:
        return None
    if not abi_available(lib_dir, ver[0], ver[1]):
        return None
    if not xll_available(lib_dir, ver[0], ver[1]):
        return None
    deps = info.get("deps") or {}
    missing = [k for k in REQUIRED_IMPORTS if not deps.get(k, {}).get("ok")]
    np_ver = (deps.get("numpy") or {}).get("version") or ""
    numpy2 = False
    if deps.get("numpy", {}).get("ok") and np_ver.startswith("2"):
        numpy2 = True
    is_conda = bool(info.get("is_conda"))
    is_venv = bool(info.get("is_venv"))
    exe_l = exe.lower().replace("/", "\\")
    is_conda_base = is_conda and ("\\envs\\" not in exe_l) and not is_venv
    writable = bool(info.get("writable"))
    has_pip = bool(info.get("has_pip"))
    ready = (not missing) and (not numpy2)
    installable = writable and has_pip and (not numpy2)

    score = 0
    if ready:
        score += 100
    if installable:
        score += 40
    if cfg_exe and os.path.normcase(os.path.abspath(cfg_exe)) == os.path.normcase(os.path.abspath(exe)):
        score += 20
    if is_venv:
        score += 8
    if is_conda and not is_conda_base:
        score += 4
    if not is_conda:
        score += 6
    if is_conda_base:
        score -= 8
    pref = {(3, 11): 10, (3, 12): 9, (3, 10): 6, (3, 9): 5, (3, 13): 4}
    score += pref.get((ver[0], ver[1]), 0)

    return Candidate(
        exe=exe,
        version=ver,  # type: ignore[arg-type]
        bits=64,
        ready=ready,
        installable=installable,
        writable=writable,
        has_pip=has_pip,
        is_conda=is_conda,
        is_conda_base=is_conda_base,
        is_venv=is_venv,
        numpy2=numpy2,
        missing=missing,
        score=score,
    )


def rank(cands: List[Candidate]) -> List[Candidate]:
    return sorted(
        cands,
        key=lambda c: (c.ready, c.installable, c.score, c.version),
        reverse=True,
    )


def kind_label(ui: I18n, c: Candidate) -> str:
    if c.is_venv:
        return ui.t("kind_venv")
    if c.is_conda_base:
        return ui.t("kind_conda_base")
    if c.is_conda:
        return ui.t("kind_conda")
    return ui.t("kind_official")


def dep_label(ui: I18n, c: Candidate) -> str:
    if c.numpy2:
        return ui.t("dep_numpy2")
    if c.ready:
        return ui.t("dep_ready")
    return ui.t("dep_miss", pkgs=",".join(c.missing))


def print_table(ui: I18n, cands: List[Candidate], rec: int) -> None:
    print(ui.t("table_hdr"))
    print("-" * 100)
    for i, c in enumerate(cands, 1):
        mark = f"  ← {ui.t('recommend')}" if i == rec else ""
        writable = "Y" if c.writable else "N"
        print(
            f"{i:>3}  {c.version_s:<9} {dep_label(ui, c):<13} {writable:<5} "
            f"{kind_label(ui, c):<11} {c.exe}{mark}"
        )


# ---------------------------------------------------------------------------
# pyxll.cfg
# ---------------------------------------------------------------------------

def read_cfg_value(cfg: Path, key: str) -> Optional[str]:
    if not cfg.is_file():
        return None
    section = None
    for raw in cfg.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        m = re.match(r"^\[(.+)\]\s*$", line)
        if m:
            section = m.group(1).upper()
            continue
        if line.startswith("#") or "=" not in raw:
            continue
        k, _, v = raw.partition("=")
        if k.strip().lower() == key.lower():
            if key.lower() == "key" and section not in (None, "LICENSE"):
                continue
            if key.lower() == "executable" and section not in (None, "PYTHON"):
                continue
            val = v.strip()
            return val or None
    return None


def ensure_cfg(root: Path, lib_dir: Path, ui: I18n, log: Logger) -> Path:
    cfg = lib_dir / "pyxll.cfg"
    tmpl = lib_dir / "pyxll.cfg.txt"
    if not cfg.exists() and tmpl.exists():
        shutil.copy2(tmpl, cfg)
        say(ui, "cfg_copy", log, cfg=str(cfg))
    return cfg


def patch_cfg(cfg: Path, updates: Dict[Tuple[str, str], str]) -> None:
    """updates keys are (SECTION, option) -> value. Only those lines are changed."""
    text = cfg.read_text(encoding="utf-8", errors="replace")
    newline = "\r\n" if "\r\n" in text else "\n"
    lines = text.splitlines()
    section = None
    seen = set()
    out = []
    for raw in lines:
        m = re.match(r"^\[(.+)\]\s*$", raw.strip())
        if m:
            section = m.group(1).upper()
            out.append(raw)
            continue
        stripped = raw.lstrip()
        if stripped.startswith("#") or "=" not in raw:
            out.append(raw)
            continue
        k = raw.split("=", 1)[0].strip().lower()
        hit = None
        for (sec, opt), val in updates.items():
            if section == sec and k == opt.lower():
                hit = (sec, opt, val)
                break
        if hit:
            out.append(f"{hit[1]} = {hit[2]}")
            seen.add((hit[0], hit[1].lower()))
        else:
            out.append(raw)
    # append missing keys before EOF, grouped by last matching section
    missing = [(s, o, v) for (s, o), v in updates.items() if (s, o.lower()) not in seen]
    if missing:
        by_sec: Dict[str, List[Tuple[str, str]]] = {}
        for s, o, v in missing:
            by_sec.setdefault(s, []).append((o, v))
        for sec, items in by_sec.items():
            inserted = False
            rebuilt = []
            cur = None
            for raw in out:
                mm = re.match(r"^\[(.+)\]\s*$", raw.strip())
                if mm:
                    if cur == sec and not inserted:
                        for o, v in items:
                            rebuilt.append(f"{o} = {v}")
                        inserted = True
                    cur = mm.group(1).upper()
                rebuilt.append(raw)
            if not inserted:
                rebuilt.append(f"[{sec}]")
                for o, v in items:
                    rebuilt.append(f"{o} = {v}")
            out = rebuilt
    cfg.write_text(newline.join(out) + newline, encoding="utf-8")


def resolve_runtime_exe(python_exe: str) -> str:
    p = Path(python_exe)
    pythonw = p.with_name("pythonw.exe")
    return str(pythonw.resolve()) if pythonw.is_file() else str(p.resolve())


# ---------------------------------------------------------------------------
# deps / register
# ---------------------------------------------------------------------------

def pip_cmd(exe: str, root: Path) -> List[str]:
    req = root / "requirements.txt"
    cmd = [exe, "-m", "pip", "install", "-r", str(req)]
    wheels = root / "vendor" / "wheels"
    if wheels.is_dir():
        cmd[4:4] = ["--no-index", "--find-links", str(wheels)]
    return cmd


def install_deps(exe: str, root: Path, ui: I18n, log: Logger) -> bool:
    cmd = pip_cmd(exe, root)
    say(ui, "deps_run", log, cmd=" ".join(cmd))
    try:
        r = subprocess.run(cmd, cwd=str(root), timeout=600)
    except (OSError, subprocess.TimeoutExpired) as exc:
        log.write(f"pip error: {exc}")
        say(ui, "deps_fail", log)
        say(ui, "deps_offline", log, cmd=" ".join(cmd))
        return False
    if r.returncode != 0:
        say(ui, "deps_fail", log)
        say(ui, "deps_offline", log, cmd=" ".join(cmd))
        return False
    say(ui, "deps_ok_after", log)
    return True


def register_pyxll(exe: str, root: Path, lib_dir: Path, ui: I18n, log: Logger) -> bool:
    xll_dir = str(lib_dir)
    env = os.environ.copy()
    env["PYTHONPATH"] = str(root) + os.pathsep + env.get("PYTHONPATH", "")
    say(ui, "reg_run", log)
    cmd_install = [exe, "-m", "pyxll", "install", "--install-first", "--non-interactive", xll_dir]
    cmd_act = [exe, "-m", "pyxll", "activate", "--non-interactive", xll_dir]
    try:
        subprocess.run(cmd_install, cwd=str(root), env=env, timeout=90)
        r = subprocess.run(cmd_act, cwd=str(root), env=env, timeout=60)
        if r.returncode == 0:
            say(ui, "reg_ok", log)
            return True
    except (OSError, subprocess.TimeoutExpired) as exc:
        log.write(f"pyxll register error: {exc}")
    say(
        ui,
        "reg_fail",
        log,
        cmd=f'"{exe}" -m pyxll install --install-first --non-interactive "{xll_dir}"',
        xll=str(lib_dir / "pyxll.xll"),
    )
    return False


# ---------------------------------------------------------------------------
# language / CLI
# ---------------------------------------------------------------------------

def choose_language(preset: Optional[str], non_interactive: bool) -> str:
    if preset in ("zh", "en"):
        return preset
    env = (os.environ.get("MCP_INSTALL_LANG") or "").strip().lower()
    if env in ("zh", "en"):
        return env
    if non_interactive:
        return "zh"
    print(LANG_MENU)
    while True:
        choice = ask("> ", "1")
        low = choice.lower()
        if low in ("1", "zh", "cn", "中文"):
            return "zh"
        if low in ("2", "en", "english"):
            return "en"
        print("Please enter 1 or 2  /  请输入 1 或 2")


def parse_args(argv: List[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="MCP Excel one-click installer")
    p.add_argument("--lang", choices=("zh", "en"), help="zh or en; prompted if omitted")
    p.add_argument("--python", help="python.exe to use")
    p.add_argument("--license-key", dest="license_key", default="")
    p.add_argument("--license-file", dest="license_file", default="")
    p.add_argument("--skip-license", action="store_true")
    p.add_argument("--skip-deps", action="store_true", help="do not install numeric libraries (default)")
    p.add_argument("--install-deps", action="store_true", help="install numpy/pandas/etc now")
    p.add_argument("--skip-excel", action="store_true")
    p.add_argument("--yes", "-y", action="store_true", help="accept defaults (still prompts language unless --lang)")
    p.add_argument("--non-interactive", action="store_true")
    p.add_argument("--probe-only", action="store_true")
    return p.parse_args(argv)


def pick_candidate(
    ui: I18n,
    cands: List[Candidate],
    rec: int,
    forced: Optional[str],
    auto: bool,
) -> Optional[Candidate]:
    if forced:
        f = _norm_exe(forced)
        if not f:
            return None
        for c in cands:
            if os.path.normcase(c.exe) == os.path.normcase(f):
                return c
        return None
    if auto:
        return cands[rec - 1]
    while True:
        raw = ask(ui.t("pick", n=rec), str(rec))
        if raw.isdigit():
            idx = int(raw)
            if 1 <= idx <= len(cands):
                return cands[idx - 1]
            print(ui.t("invalid_pick"))
            continue
        n = _norm_exe(raw)
        if n:
            for c in cands:
                if os.path.normcase(c.exe) == os.path.normcase(n):
                    return c
            # allow an unscanned path if it probes OK — caller handles via evaluate
            return Candidate(
                exe=n,
                version=(0, 0, 0),
                bits=64,
                ready=False,
                installable=False,
                writable=False,
                has_pip=False,
                is_conda=False,
                is_conda_base=False,
                is_venv=False,
                numpy2=False,
                reason_skip="custom",
            )
        print(ui.t("invalid_pick"))


def license_sources(root: Path) -> Optional[Path]:
    for name in ("pyxll.lic", "license.lic", "pyxll.lic.txt", "license.txt"):
        p = root / name
        if p.is_file() and p.stat().st_size > 0:
            return p
    return None


def apply_license(
    cfg: Path,
    ui: I18n,
    log: Logger,
    args: argparse.Namespace,
    auto: bool,
) -> None:
    print()
    say(ui, "lic_title", log)
    say(ui, "lic_note", log)

    existing_key = read_cfg_value(cfg, "key")
    existing_file = read_cfg_value(cfg, "file")
    if existing_key and not args.license_key and not args.skip_license:
        say(ui, "lic_have", log, tail=mask_key(existing_key))
        return
    if existing_file and Path(existing_file).is_file() and not args.license_file:
        say(ui, "lic_file", log, path=existing_file)
        return

    env_key = (os.environ.get("PYXLL_LICENSE_KEY") or "").strip()
    key = (args.license_key or env_key).strip()
    lic_file = (args.license_file or "").strip()
    if not lic_file and not key:
        found = license_sources(mcp_root())
        if found:
            lic_file = str(found)

    if env_key and key == env_key:
        say(ui, "lic_env", log)

    if not key and not lic_file and not args.skip_license and not auto:
        raw = ask(ui.t("lic_ask"), "")
        if raw:
            if Path(raw).is_file():
                lic_file = raw
            else:
                key = raw

    if args.skip_license and not key and not lic_file:
        say(ui, "lic_skip", log)
        return

    updates = {}
    if key:
        updates[("LICENSE", "key")] = key
        say(ui, "lic_written_key", log, tail=mask_key(key))
    elif lic_file:
        updates[("LICENSE", "file")] = str(Path(lic_file).resolve())
        say(ui, "lic_written_file", log)
    else:
        say(ui, "lic_skip", log)
        return
    patch_cfg(cfg, updates)
    log.write("license field updated (value redacted)")


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def _safe_argv(items: List[str]) -> List[str]:
    redacted = []
    hide_next = False
    for item in items:
        if hide_next:
            redacted.append("***")
            hide_next = False
            continue
        if item in ("--license-key", "--license-file"):
            redacted.append(item)
            hide_next = True
            continue
        redacted.append(item)
    return redacted


def main(argv: Optional[List[str]] = None) -> int:
    if sys.version_info < MIN_BOOTSTRAP:
        print("Need Python 3.8+ to run this installer / 运行本安装程序需要 Python 3.8+")
        return 1

    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
            sys.stderr.reconfigure(encoding="utf-8")
        except OSError:
            pass

    args = parse_args(argv if argv is not None else sys.argv[1:])
    auto = bool(args.yes or args.non_interactive)
    lang = choose_language(args.lang, auto)
    ui = I18n(lang)
    root = mcp_root()
    logger = Logger(log_path(root))
    logger.write(f"start lang={lang} argv={_safe_argv(list(argv or sys.argv[1:]))}")

    print()
    print("=" * 78)
    print(f"  {ui.t('banner')}")
    print("=" * 78)
    print(f"{ui.t('root')}: {root}")
    print()

    excel, excel_bits = find_excel()
    if excel:
        say(ui, "excel_found", logger, bit=64 if excel_bits == "x64" else 32, path=str(excel))
        if excel_bits == "x86":
            say(ui, "excel_32", logger)
            if not args.skip_excel:
                if not auto:
                    ask(ui.t("press"), "")
                return 1
    else:
        say(ui, "excel_missing", logger)

    lib_dir = root / "lib" / "X64"

    cfg_preview = lib_dir / "pyxll.cfg"
    cfg_exe = read_cfg_value(cfg_preview, "executable") if cfg_preview.exists() else None

    say(ui, "scan", logger)
    cands: List[Candidate] = []
    for exe in collect_python_exes():
        c = evaluate(exe, lib_dir, cfg_exe)
        if c:
            cands.append(c)
    cands = rank(cands)

    if args.python:
        forced = _norm_exe(args.python)
        extra = evaluate(forced, lib_dir, cfg_exe) if forced else None
        if extra and all(os.path.normcase(c.exe) != os.path.normcase(extra.exe) for c in cands):
            cands.insert(0, extra)
            cands = rank(cands)

    if not cands:
        say(ui, "none", logger)
        if not auto:
            ask(ui.t("press"), "")
        return 1

    rec = 1
    print_table(ui, cands, rec)

    if args.probe_only:
        say(ui, "probe_only", logger)
        return 0

    chosen = pick_candidate(ui, cands, rec, args.python, auto)
    if chosen is None:
        say(ui, "bad_forced", logger, reason="not found")
        return 1
    if chosen.version == (0, 0, 0):
        rebuilt = evaluate(chosen.exe, lib_dir, cfg_exe)
        if not rebuilt:
            say(ui, "bad_forced", logger, reason="incompatible ABI / not 64-bit 3.9-3.13")
            return 1
        chosen = rebuilt
    say(ui, "picked", logger, exe=chosen.exe)

    # dependencies
    if chosen.numpy2:
        say(ui, "deps_numpy2", logger)
        if not auto:
            ask(ui.t("press"), "")
        return 1

    later_cmd = " ".join(pip_cmd(chosen.exe, root))
    if chosen.ready:
        say(ui, "deps_ok", logger)
    elif args.skip_deps or (auto and not args.install_deps):
        say(ui, "deps_skip", logger, cmd=later_cmd)
    else:
        say(ui, "deps_need", logger, pkgs=", ".join(chosen.missing))
        if args.install_deps:
            proceed = True
        elif chosen.is_conda_base:
            proceed = yes(ask(ui.t("deps_conda_base"), "n"), False)
        else:
            proceed = yes(ask(ui.t("deps_ask"), "n"), False)
        if not proceed:
            say(ui, "deps_skip", logger, cmd=later_cmd)
        else:
            if not install_deps(chosen.exe, root, ui, logger):
                say(ui, "deps_skip", logger, cmd=later_cmd)
            else:
                again = evaluate(chosen.exe, lib_dir, cfg_exe)
                if again:
                    chosen = again

    if not apply_matching_xll(lib_dir, chosen.version[0], chosen.version[1], ui, logger):
        if not auto:
            ask(ui.t("press"), "")
        return 1

    cfg = ensure_cfg(root, lib_dir, ui, logger)
    if not cfg.exists():
        say(ui, "cfg_fail", logger, err="pyxll.cfg missing")
        return 1
    bak = cfg.with_suffix(cfg.suffix + f".bak.{time.strftime('%Y%m%d%H%M%S')}")
    try:
        shutil.copy2(cfg, bak)
        say(ui, "cfg_bak", logger, bak=str(bak))
    except OSError as exc:
        logger.write(f"backup failed: {exc}")

    runtime = resolve_runtime_exe(chosen.exe)
    try:
        patch_cfg(cfg, {("PYTHON", "executable"): runtime})
        say(ui, "cfg_exe", logger, exe=runtime)
    except OSError as exc:
        say(ui, "cfg_fail", logger, err=str(exc))
        return 1

    apply_license(cfg, ui, logger, args, auto)

    if args.skip_excel:
        say(ui, "reg_skip", logger)
    else:
        if excel_is_running() and not auto:
            ans = ask(ui.t("excel_running"), "")
            if ans.lower() in ("s", "skip", "n"):
                say(ui, "reg_skip", logger)
            else:
                register_pyxll(chosen.exe, root, lib_dir, ui, logger)
        else:
            register_pyxll(chosen.exe, root, lib_dir, ui, logger)

    print()
    say(ui, "next", logger)
    print()
    say(ui, "done", logger)
    say(ui, "log", logger, path=str(logger.path))
    if not auto:
        ask(ui.t("press"), "")
    return 0


if __name__ == "__main__":
    sys.exit(main())
