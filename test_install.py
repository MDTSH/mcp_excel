#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Verify MCP Excel files and that this Python can import mcp."""

import os
import platform
import sys
from pathlib import Path

SUPPORTED = (9, 10, 11, 12, 13)
ROOT = Path(__file__).resolve().parent
LIB = ROOT / "lib" / "X64"


def test_python_version():
    print("Testing Python version...")
    v = sys.version_info
    print("  Python version: %s.%s.%s" % (v.major, v.minor, v.micro))
    if v.major == 3 and v.minor in SUPPORTED and platform.architecture()[0] == "64bit":
        print("  OK 64-bit CPython 3.9–3.13")
        return True
    print("  FAIL need 64-bit CPython 3.9–3.13")
    return False


def test_system_architecture():
    print("\nTesting system architecture...")
    arch = platform.machine().lower()
    print("  Architecture: %s" % arch)
    if arch in ("amd64", "x86_64"):
        print("  OK 64-bit")
        return True
    print("  FAIL MCP Excel is 64-bit only")
    return False


def test_mcp_files():
    print("\nTesting MCP file structure...")
    ok = True
    for name in ("requirements.txt", "quick_install.bat", "install.bat", "install_mcp_excel.py"):
        path = ROOT / name
        if path.exists():
            print("  OK %s" % name)
        else:
            print("  FAIL %s - MISSING" % name)
            ok = False
    return ok


def test_lib_directories():
    print("\nTesting library directories...")
    if not LIB.is_dir():
        print("  FAIL lib/X64/ not found")
        return False
    print("  OK lib/X64/")
    ok = True
    for name in ("pyxll.xll", "pyxll.cfg", "cudart64_12.dll", "curand64_10.dll"):
        if (LIB / name).exists():
            print("    OK %s" % name)
        else:
            print("    FAIL %s - MISSING" % name)
            ok = False
    pyds = sorted(LIB.glob("_mcp.cp*-win_amd64.pyd"))
    if pyds:
        print("    OK %d tagged _mcp pyd(s): %s" % (len(pyds), ", ".join(p.name for p in pyds)))
    else:
        print("    FAIL _mcp.cp*-win_amd64.pyd - MISSING")
        ok = False
    tag = "cp%d%d" % (sys.version_info.major, sys.version_info.minor)
    tagged = LIB / ("_mcp.%s-win_amd64.pyd" % tag)
    if tagged.exists():
        print("    OK matching this Python: %s" % tagged.name)
    else:
        print("    FAIL no %s for this Python" % tagged.name)
        ok = False
    xll_tag = "py%d%d" % (sys.version_info.major, sys.version_info.minor)
    xll_stock = LIB / "pyxll" / xll_tag / "pyxll.xll"
    if xll_stock.is_file():
        print("    OK matching PyXLL xll: %s" % xll_stock.relative_to(LIB))
    else:
        print("    FAIL no lib/X64/pyxll/%s/pyxll.xll" % xll_tag)
        ok = False
    return ok


def test_mcp_import():
    print("\nTesting MCP library import...")
    root = str(ROOT)
    if root not in sys.path:
        sys.path.insert(0, root)
    try:
        import mcp
        pyd = getattr(getattr(mcp, "_mcp", None), "__file__", None)
        print("  OK import mcp")
        if pyd:
            print("    %s" % pyd)
        return True
    except Exception as exc:
        print("  FAIL import mcp: %s" % exc)
        return False


def test_pyxll_module():
    print("\nTesting PyXLL module...")
    root = str(ROOT)
    if root not in sys.path:
        sys.path.insert(0, root)
    try:
        import pyxll  # noqa: F401
        print("  OK import pyxll")
        return True
    except ImportError as exc:
        print("  FAIL import pyxll: %s" % exc)
        return False


def main():
    print("MCP Installation Test")
    print("=" * 50)
    tests = [
        ("Python Version", test_python_version),
        ("System Architecture", test_system_architecture),
        ("MCP Files", test_mcp_files),
        ("Library Directories", test_lib_directories),
        ("PyXLL Module", test_pyxll_module),
        ("MCP Import", test_mcp_import),
    ]
    results = []
    for name, fn in tests:
        try:
            results.append((name, bool(fn())))
        except Exception as exc:
            print("  FAIL %s: %s" % (name, exc))
            results.append((name, False))

    print("\n" + "=" * 50)
    print("Test Summary:")
    print("=" * 50)
    passed = 0
    for name, ok in results:
        print("  %s: %s" % (name, "PASS" if ok else "FAIL"))
        if ok:
            passed += 1
    print("\nOverall: %d/%d tests passed" % (passed, len(results)))
    if passed == len(results):
        print("All tests passed. MCP is ready to use.")
        return 0
    print("Some tests failed. Run install.bat (or quick_install.bat).")
    return 1


if __name__ == "__main__":
    sys.exit(main())
