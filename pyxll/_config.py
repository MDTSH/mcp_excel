"""
Copyright (c) 2009-2012, All Rights Reserved, http://www.pyxll.com/

THIS CODE AND INFORMATION ARE PROVIDED "AS IS" WITHOUT WARRANTY OF ANY
KIND, EITHER EXPRESSED OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND/OR FITNESS FOR A
PARTICULAR PURPOSE.
"""
from ._errors import Help, Error
from ._utils import (
    _print,
    _find_pyxll_addin,
    _find_pyxll_config,
    _get_process_name
)
import logging
import ctypes
import os

try:
    import winreg
except ImportError:
    import winreg as winreg  # type: ignore

_log = logging.getLogger(__name__)

def configure(*args):
    if args:
        raise Help("Unexpected arguments '%s' to command 'configure'." % ", ".join(args))

    # ShellExecuteExA requires STA
    ole32 = ctypes.windll.Ole32
    ole32.CoInitializeEx.rettype = ctypes.wintypes.DWORD
    ole32.CoInitializeEx.argtypes = [ctypes.c_void_p, ctypes.wintypes.DWORD]

    COINIT_APARTMENTTHREADED = 0
    ole32.CoInitializeEx(None, COINIT_APARTMENTTHREADED)

    pyxll_path = _find_pyxll_addin()
    if not pyxll_path:
        raise Error(("The PyXLL Excel add-in is not installed.\n\n"
                     "If you have installed the add-in manually you may need to close Excel\n"
                     "and try again.\n\n"
                     "Otherwise, you can install PyXLL first using the following command:\n\n"
                     "pyxll install"
                     "or see the PyXLL website https://www.pyxll.com for installation instructions."))

    pyxll_cfg = _find_pyxll_config(pyxll_path)
    if not pyxll_cfg:
        raise Error(("The PyXLL Excel add-in is not installed.\n\n"
                     "No PyXLL add-in was found installed in Excel.\n\n"
                     "Install PyXLL first using the following command:\n\n"
                     "pyxll install"
                     "or see the PyXLL website https://www.pyxll.com for installation instructions."))

    if not os.path.exists(pyxll_cfg):
        raise Error(("The PyXLL config file does not exist.\n\n"
                     "The path to the config file is:\n" +
                     pyxll_cfg + "\n\n"
                     "Please check that file, and if necessary you can reinstall PyXLL"
                     "using the following command:\n\n"
                     "pyxll install"
                     "or see the PyXLL website https://www.pyxll.com for installation instructions."))

    class SHELLEXECUTEINFO(ctypes.Structure):
        _fields_ = [
            ("cbSize", ctypes.wintypes.DWORD),
            ("fMask", ctypes.wintypes.ULONG),
            ("hwnd", ctypes.wintypes.HWND),
            ("lpVerb", ctypes.wintypes.LPCSTR),
            ("lpFile", ctypes.wintypes.LPCSTR),
            ("lpParameters", ctypes.wintypes.LPCSTR),
            ("lpDirectory", ctypes.wintypes.LPCSTR),
            ("nShow", ctypes.c_int),
            ("hInstApp", ctypes.wintypes.HINSTANCE),
            ("lpIDList", ctypes.c_void_p),
            ("lpClass", ctypes.wintypes.LPCSTR),
            ("hkeyClass", ctypes.wintypes.HKEY),
            ("dwHotKey", ctypes.wintypes.DWORD),
            ("hMonitor", ctypes.wintypes.HANDLE),
            ("hProcess", ctypes.wintypes.HANDLE)
        ]

    shell32 = ctypes.windll.Shell32
    shell32.ShellExecuteExA.rettype = ctypes.wintypes.BOOL
    shell32.ShellExecuteExA.argtypes = [ctypes.POINTER(SHELLEXECUTEINFO)]

    SEE_MASK_NOCLOSEPROCESS = 0x00000040
    SW_SHOWNORMAL = 1

    info = SHELLEXECUTEINFO(0)
    info.cbSize = ctypes.sizeof(SHELLEXECUTEINFO)
    info.fMask = SEE_MASK_NOCLOSEPROCESS
    info.lpVerb = "open".encode()
    info.lpFile = pyxll_cfg.encode()
    info.nShow = SW_SHOWNORMAL

    if not shell32.ShellExecuteExA(ctypes.byref(info)):
        error = ctypes.GetLastError()
        raise Error((("Unable to open the PyXLL config file (0x%x).\n\n" % error) +
                     "The path to the config file is:\n" +
                     pyxll_cfg + "\n\n"))

    kernel32 = ctypes.windll.kernel32
    kernel32.GetProcessId.rettype = ctypes.wintypes.DWORD
    kernel32.GetProcessId.argtypes = [ctypes.wintypes.HANDLE]

    pid = kernel32.GetProcessId(info.hProcess)
    if not pid:
        error = ctypes.GetLastError()
        raise Error((("Failed to launch app to edit the PyXLL config file (0x%x).\n\n" % error) +
                     "The path to the config file is:\n" +
                     pyxll_cfg + "\n\n"))

    name = _get_process_name(pid)
    if name:
        _print("Config file '%s' is being opened with %s..." % (pyxll_cfg, name))
        return 0

    _print("Config file '%s' is being opened..." % pyxll_cfg)
    return 0