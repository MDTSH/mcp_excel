"""
Copyright (c) 2009-2012, All Rights Reserved, http://www.pyxll.com/

THIS CODE AND INFORMATION ARE PROVIDED "AS IS" WITHOUT WARRANTY OF ANY
KIND, EITHER EXPRESSED OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND/OR FITNESS FOR A
PARTICULAR PURPOSE.
"""
from ._errors import Error
from zipfile import ZipFile
import datetime as dt
import tempfile
import hashlib
import logging
import ctypes.wintypes
import ctypes
import shutil
import shlex
import time
import sys
import re
import os

try:
    import winreg
except ImportError:
    import winreg as winreg  # type: ignore

try:
    from prompt_toolkit import prompt  # type: ignore
    from prompt_toolkit.completion import PathCompleter  # type: ignore
    from prompt_toolkit.output.win32 import NoConsoleScreenBufferError  # type: ignore
    have_prompt_toolkit = True
except ImportError:
    have_prompt_toolkit = False

if sys.version_info[0] >= 3:
    from urllib.request import urlopen, Request  # type: ignore
    from urllib.error import URLError  # type: ignore
    from urllib.parse import quote  # type: ignore
    from configparser import RawConfigParser  # type: ignore
else:
    from urllib.request import urlopen, Request
    from urllib.error import URLError  # type: ignore
    from urllib.parse import quote  # type: ignore
    from configparser import RawConfigParser  # type: ignore

_log = logging.getLogger(__name__)

_root_keys = {
    winreg.HKEY_CURRENT_USER: "HKEY_CURRENT_USER",
    winreg.HKEY_LOCAL_MACHINE: "HKEY_LOCAL_MACHINE",
}

_wow64_flags = {
    "32bit": winreg.KEY_WOW64_32KEY,
    "64bit": winreg.KEY_WOW64_64KEY
}

_get_binary_type_result = {
    0: "32bit",
    6: "64bit",
}

_get_dll_bitness_result = {
    0x14c: "32bit",
    0x8664: "64bit"
    # 0xc0ee: "CLR"
}

_registered_com_components = [
    "ActiveX"
]

_clsids = {
    "ActiveX": [
        "170E3CEE-B905-4FC7-A6A0-5415CC50226A"
    ]
}

_progids = {
    "ActiveX": [
        "PyXLL.AtxHostControl",
        "PyXLL.AtxHostControl.1",
    ]
}

_typelibs = {
    "ActiveX": [
        "4D60F002-53B9-475F-98D6-2D8D34109C5C"
    ]
}

_http_headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36'
}

class AutoDeleteFile:
    def __init__(self, path):
        self.path = path

    def __del__(self):
        _log.debug("Deleting temporary file %s" % self.path)
        os.unlink(self.path)

class AutoDeleteFolder:
    def __init__(self, path):
        self.path = path

    def __del__(self):
        _log.debug("Deleting temporary folder %s" % self.path)
        for x in range(10):
            try:
                if os.path.exists(self.path):
                    shutil.rmtree(self.path)
                break
            except:
                time.sleep(0.01)
        else:
            def onerror(_func, path, _exc_info):
                _log.warning("Error deleting temporary file '%s'" % path)
            shutil.rmtree(self.path, onerror=onerror)

def _urlopen_ssl(url, data=None):
    # cafile option was added in Python 3.2
    if sys.version_info[:2] < (3, 2):
        return urlopen(url, data=data)

    # Try urlopen first but if that fails look for certifi and use
    # the certificates from that package.
    try:
        return urlopen(url, data=data)
    except URLError:
        try:
            import certifi  # type: ignore
            return urlopen(url, data=data, cafile=certifi.where())
        except ImportError:
            pass
        raise

def _print(msg, line_limit=79):
    if not msg:
        print("")
        return

    for line in msg.splitlines():
        if len(line) > line_limit:
            words = line.split(" ")
            line, words = words[0], words[1:]
            while words:
                tmp = line + " " + words[0]
                if len(tmp) > line_limit:
                    print(line)
                    line, words = words[0], words[1:]
                else:
                    line = tmp
                    words = words[1:]
        print(line)

_non_interactive = False
def _set_non_interactive(non_interactive):
    global _non_interactive
    _non_interactive = non_interactive

def _is_non_interactive():
    return _non_interactive

_forced = False
def _set_forced(is_forced):
    global _forced
    _forced = is_forced

def _is_forced():
    return _forced

def _input(msg, is_path=False, line_limit=79, default=None):
    if _non_interactive and default is not None:
        return default

    lines = []
    for line in msg.splitlines():
        if len(line) > line_limit:
            words = line.split(" ")
            line, words = words[0], words[1:]
            while words:
                tmp = line + " " + words[0]
                if len(tmp) > line_limit:
                    print(line)
                    line, words = words[0], words[1:]
                else:
                    line = tmp
                    words = words[1:]
        lines.append(line)

    if lines:
        for line in lines[:-1]:
            _print(line, line_limit=line_limit)
        msg = lines[-1]

    if _non_interactive:
        print(msg)
        raise Error("Input required. Cannot run in non-interactive mode.")

    result = None
    if have_prompt_toolkit:
        try:
            completer = None
            if is_path:
                completer = PathCompleter()
            result = prompt(msg, completer=completer)
        except NoConsoleScreenBufferError:
            pass

    if result is None:
        try:
            result = input(msg)
        except NameError:
            pass

    if result is None:
        result = eval(input(msg))

    if is_path:
        # Strip matching start and end quotes only
        result = result.strip()
        while result and result[0] == result[-1] and result[0] in "\"'":
            result = result[1:-1]

    return result

def _find_excel_path():
    # Search starting with the same bitness as Python
    python_bits = _get_exe_bitness(sys.executable)
    wow64_keys = list(_wow64_flags.keys())
    if python_bits in wow64_keys and wow64_keys[0] != python_bits:
        wow64_keys.reverse()

    for wow64_key in wow64_keys:
        # Check for Excel InstallRoot first
        for root in _root_keys:
            key = None
            try:
                try:
                    wow64_flags = _wow64_flags[wow64_key]
                    flags = wow64_flags | winreg.KEY_READ
                    key = winreg.OpenKey(root, r"SOFTWARE\Microsoft\Office", 0, flags)
                except WindowsError:
                    continue

                xl_versions = []
                i = 0
                while True:
                    try:
                        value = winreg.EnumKey(key, i)
                        if re.match(r"^\d+\.\d+$", value):
                            xl_versions.append(value)
                        i += 1
                    except IOError:
                        break

                xl_versions.sort(reverse=True, key=lambda x: float(x))
                for xl_version in xl_versions:
                    subkey = None
                    try:
                        subkey = winreg.OpenKey(key, r"%s\Excel\InstallRoot" % xl_version, 0, flags)
                        excel_folder = winreg.QueryValueEx(subkey, "Path")[0]
                        path = os.path.join(excel_folder, "EXCEL.EXE")
                        if os.path.exists(path):
                            return path
                    except WindowsError:
                        continue
                    finally:
                        if subkey is not None:
                            winreg.CloseKey(subkey)
                else:
                    continue
            finally:
                if key is not None:
                    winreg.CloseKey(key)

        # Next look in CurrentVersion
        for root in _root_keys:
            try:
                wow64_flags = _wow64_flags[wow64_key]
                flags = wow64_flags | winreg.KEY_READ
                key = winreg.OpenKey(root, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\excel.exe", 0, flags)
            except WindowsError:
                continue

            value = winreg.QueryValue(key, None)
            winreg.CloseKey(key)

            if os.path.exists(value):
                return value

        # If we've not found anything in CurrentVersion then check the Excel file associations
        for ext in (".xlsx", ".xlsm", ".xlsb", ".xls"):
            try:
                wow64_flags = _wow64_flags[wow64_key]
                flags = wow64_flags | winreg.KEY_READ

                # Get the program name from the extension
                key = winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, ext, 0, flags)
                name = winreg.QueryValue(key, None)
                winreg.CloseKey(key)

                # Find the shell command from the program name
                key = winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, name + r"\shell\Open\command", 0, flags)
                cmd = winreg.QueryValue(key, None)
                winreg.CloseKey(key)
            except WindowsError:
                continue

            # Try parsing the command to get the executable path
            _log.debug("Found file association '%s' for %s" % (cmd, ext))
            args = shlex.split(cmd, posix=False)
            if args and args[0]:
                path = args[0].strip("\"'")
                if os.path.exists(path):
                    return path

def _guess_exe_bitness_from_path(exe_path):
    # Check to see if the exe is in the WindowsApps folder
    exe_path = os.path.abspath(exe_path)
    drive, folder = os.path.splitdrive(exe_path)
    windows_apps = os.path.join(drive, os.path.sep, "Program Files", "WindowsApps")
    if windows_apps == os.path.commonpath([exe_path, windows_apps]):
        folder, _unused = os.path.split(os.path.relpath(exe_path, windows_apps))
        if re.search("_x86_", folder, re.IGNORECASE):
            return "32bit"
        elif re.search("_x64_", folder, re.IGNORECASE):
            return "64bit"

def _get_exe_bitness(exe_path):
    kernel32 = ctypes.windll.kernel32
    bits_dword = ctypes.wintypes.DWORD()
    kernel32.GetBinaryTypeW.argtypes = [ctypes.c_wchar_p, ctypes.POINTER(ctypes.wintypes.DWORD)]
    result = kernel32.GetBinaryTypeW(exe_path, ctypes.byref(bits_dword))
    if 0 == result:
        error = ctypes.GetLastError()

        # If Excel is installed as a UWP app then we will not be able to inspect the file but
        # we can still tell if it's 32 bit or 64 bit from the path.
        exe_bits = _guess_exe_bitness_from_path(exe_path)
        if exe_bits is not None:
            return exe_bits

        raise Error("Unable to determine the bitness of '%s': 0x%x." % (exe_path, error))

    exe_bits = _get_binary_type_result.get(bits_dword.value)
    if exe_bits is None:
        raise Error("Unexpected result when determining the bitness of '%s': 0x%x." % (exe_path, bits_dword.value))

    return exe_bits

def _get_dll_bitness(dll_path):
    fh = open(dll_path, "rb")

    dos_signature = bytes(fh.read(2))
    if dos_signature != b'MZ':
        raise Error("Invalid DOS signature found in file '%s'." % dll_path)

    fh.seek(0x3c, 0)
    pe_offset = fh.read(4)
    pe_offset = ctypes.c_ulong.from_buffer_copy(pe_offset)
    fh.seek(pe_offset.value, 0)

    pe_signature = bytes(fh.read(4))
    if pe_signature != b'PE\0\0':
        raise Error("Invalid PE signature found in file '%s'." % dll_path)

    machine = fh.read(2)
    machine = ctypes.c_ushort.from_buffer_copy(machine)

    fh.seek(pe_offset.value + 22, 0)
    characteristics = fh.read(2)
    characteristics = ctypes.c_ushort.from_buffer_copy(characteristics)

    if 0 == (characteristics.value & 0x2000):
        raise Error("File '%s' is not a DLL." % dll_path)

    return _get_dll_bitness_result.get(machine.value)

def _get_dll_file_info(dll_path, key):
    """Return dll property"""
    version = ctypes.windll.version
    version.GetFileVersionInfoSizeW.argtypes = [ctypes.c_wchar_p, ctypes.POINTER(ctypes.wintypes.DWORD)]

    handle = ctypes.wintypes.DWORD()
    size = version.GetFileVersionInfoSizeW(dll_path, ctypes.byref(handle))
    if size == 0:
        error = ctypes.GetLastError()
        raise Error("Error calling GetFileVersionInfoSizeW for '%s': 0x%x." % (dll_path, error))

    buffer = ctypes.create_string_buffer(size)

    version.GetFileVersionInfoW.rettype = ctypes.wintypes.BOOL
    version.GetFileVersionInfoW.argtypes = [ctypes.c_wchar_p,
                                            ctypes.wintypes.DWORD,
                                            ctypes.wintypes.DWORD,
                                            ctypes.c_void_p]

    if not version.GetFileVersionInfoW(dll_path, handle, size, buffer):
        error = ctypes.GetLastError()
        raise Error("Error calling GetFileVersionInfoW for '%s': 0x%x." % (dll_path, error))

    version.VerQueryValueA.rettype = ctypes.wintypes.BOOL
    version.VerQueryValueA.argtypes = [ctypes.c_void_p,
                                       ctypes.c_char_p,
                                       ctypes.POINTER(ctypes.c_void_p),
                                       ctypes.POINTER(ctypes.wintypes.UINT)]

    ptr = ctypes.c_void_p()
    size = ctypes.wintypes.UINT()
    if not version.VerQueryValueA(ctypes.cast(buffer, ctypes.c_void_p),
                                  b"\\VarFileInfo\\Translation",
                                  ctypes.byref(ptr),
                                  ctypes.byref(size)):
        error = ctypes.GetLastError()
        raise Error("Error getting \\VarFileInfo\\Translation for '%s': 0x%x." % (dll_path, error))

    translation = ctypes.cast(ptr, ctypes.POINTER(ctypes.c_ubyte * 4)).contents
    lang = b"%02X%02X%02X%02X" % (translation[1], translation[0], translation[3], translation[2])

    if not version.VerQueryValueA(ctypes.cast(buffer, ctypes.c_void_p),
                                  b"\\StringFileInfo\\%s\\%s" % (lang, key.encode()),
                                  ctypes.byref(ptr),
                                  ctypes.byref(size)):
        error = ctypes.GetLastError()
        raise Error("Error getting \\VarFileInfo\\%s for '%s': 0x%x." % (key, dll_path, error))

    return ctypes.cast(ptr, ctypes.c_char_p).value.decode()

def _get_xll_version_info(dll_path):
    """Return tuple (name, version, py version)"""
    internal_name = _get_dll_file_info(dll_path, "InternalName")

    # InternalName should be in the form "pyxll-<version>-<py version>"
    # but older versions of PyXLL (< 4.6) do not have this.
    match = re.match(r"^([a-z]+)\-(.+)\-(py\d{2,3})$", internal_name, re.IGNORECASE)
    if not match:
        _log.debug("Could not extract version information from InternalName '%s'." % internal_name)
        return None

    return match.group(1), match.group(2), match.group(3)

def _get_xll_file_version(dll_path):
    """Return 'FileVersion'"""
    return _get_dll_file_info(dll_path, "FileVersion")

def _find_excel_version_info(bits):
    """Returns a tuple of information about Excel from the registry:
    (version, root_hkey, subkey, flags)
    """
    max_office_version_number = -1
    max_office_version = None
    office_subkey = r"Software\Microsoft\Office"
    flags = _wow64_flags[bits] | winreg.KEY_READ
    for root in _root_keys:
        try:
            office_root = winreg.OpenKey(root, office_subkey, 0, flags)
        except WindowsError:
            continue

        # Look for all installed versions of Excel
        i = -1
        while True:
            i += 1

            try:
                subkey = winreg.EnumKey(office_root, i)
            except WindowsError:
                break

            match = re.match(r"^(\d+(?:\.\d+)?)$", subkey)
            if match:
                # Check Excel is installed
                try:
                    excel_subkey = subkey + r"\Excel"
                    excel_root = winreg.OpenKey(office_root, subkey + r"\Excel", 0, flags)
                except WindowsError:
                    continue

                winreg.CloseKey(excel_root)

                # Get the max installed version as the original string
                office_version = float(match.group(1))
                if office_version > max_office_version_number:
                    max_office_version_number = office_version
                    max_office_version = (subkey, root, office_subkey + "\\" + excel_subkey, _wow64_flags[bits])

        winreg.CloseKey(office_root)

    return max_office_version

def _find_pyxll_addin(root=None, excel_key=None, flags=None):
    """Finds the PyXLL addin installed in the registry.
    The args for this function are returned by _find_excel_version_info.
    """
    if root is None and excel_key is None and flags is None:
        pyxll_path = None
        for bits in _wow64_flags:
            xl_version_info = _find_excel_version_info(bits)
            if not xl_version_info:
                continue

            xl_version, root_hkey, subkey, flags = xl_version_info
            pyxll_path = _find_pyxll_addin(root_hkey, subkey, flags)
            if pyxll_path:
                break

        return pyxll_path

    if root is None:
        raise ValueError("Missing value for 'root'")

    if excel_key is None:
        raise ValueError("Missing value for 'excel_key'")

    if flags is None:
        raise ValueError("Missing value for 'flags'")

    try:
        options_key = winreg.OpenKey(root, excel_key + r"\Options", 0, flags | winreg.KEY_READ)
    except WindowsError:
        _log.error("Error accessing Excel options in the registry.")
        return None

    pyxll_path = None
    try:
        i = 0
        while True:
            name, data, dtype = winreg.EnumValue(options_key, i)
            if "OPEN" in name and dtype == winreg.REG_SZ:
                data = re.sub(r"^(\/[a-z]+\s*)+", "", data, flags=re.IGNORECASE)
                path = data.strip('"\'')
                if path.lower().endswith("pyxll.xll"):
                    pyxll_path = path
                    break
            i += 1
    except WindowsError:
        pass

    winreg.CloseKey(options_key)

    return pyxll_path

def _renumber_excel_options(root, excel_key, flags, first_key=None, dry_run=False):
    """Excel maintains a list of OPEN/d keys in its Options settings.
    These need to be numbered correctly otherwise Excel will ignore them.
    This function reorganizes those keys after making changes to then Options.
    The key must be opened for read and write.
    """
    try:
        options_key = winreg.OpenKey(root, excel_key + r"\Options", 0, flags | winreg.KEY_READ)
    except WindowsError:
        raise Error("Couldn't read the Excel options in the registry to renumber the OPEN keys.")

    open_values = {}
    try:
        i = 0
        while True:
            name, data, dtype = winreg.EnumValue(options_key, i)
            if "OPEN" in name and dtype == winreg.REG_SZ:
                open_values[name] = data
            i += 1
    except WindowsError:
        pass

    # Order the keys by number, but with the first_key first
    def key_order(name):
        if first_key is not None and name == first_key:
            return -1

        match = re.match(r"^OPEN(\d*)$", name)
        if not match:
            raise RuntimeError("Unexpected key '%s'" % name)

        return int(match.group(1) or 0)

    ordered_keys = list(sorted(list(open_values.keys()), key=key_order))

    # Check if they're already in the correct order
    expected = ["OPEN" + (str(i) if i > 0 else "") for i in range(len(open_values))]
    if expected == ordered_keys:
        return

    # Write the keys out with the right numbers
    if dry_run:
        _log.info("[DRY-RUN] Not re-numbering Excel's OPEN options")
        return

    _log.debug("Re-numbering Excel's OPEN options")
    try:
        options_key = winreg.OpenKey(root, excel_key + r"\Options", 0, flags | winreg.KEY_WRITE)

        new_values = {}
        for i, key in enumerate(ordered_keys):
            value = open_values[key]
            new_key = "OPEN" + (str(i) if i > 0 else "")
            winreg.SetValueEx(options_key, new_key, 0, winreg.REG_SZ, value)
            new_values[new_key] = value

        for key in list(open_values.keys()):
            if key not in new_values:
                winreg.DeleteValue(options_key, key)

        winreg.CloseKey(options_key)
    except WindowsError:
        raise Error("Couldn't update the Excel options in the registry to renumber the OPEN keys.")

def _uninstall_pyxll_addin(root, excel_key, flags, xll_path, dry_run=False):
    """Finds the PyXLL addin installed in the registry.
    The args for this function are returned by _find_excel_version_info.
    """
    # uninstall entries from \Software\Microsoft\Office\<version>\Excel\Options
    # (this is what Excel uses to determine what to load on start-up)
    try:
        options_key = winreg.OpenKey(root, excel_key + r"\Options", 0, flags | winreg.KEY_READ)
    except WindowsError:
        raise Error("Couldn't read the Excel options in the registry.")

    to_delete = []
    try:
        i = 0
        while True:
            name, data, dtype = winreg.EnumValue(options_key, i)
            if "OPEN" in name and dtype == winreg.REG_SZ:
                data = re.sub(r"^(\/[a-z]+\s*)+", "", data, flags=re.IGNORECASE)
                path = data.strip('"\'')
                if path == xll_path:
                    to_delete.append((name, data))
            i += 1
    except WindowsError:
        pass

    winreg.CloseKey(options_key)

    if not to_delete:
        raise Error("Couldn't find add-in '%s' installed in the Excel options." % xll_path)

    # Delete the keys found
    try:
        _log.debug("Found PyXLL add-in in Excel's Options")
        options_key = winreg.OpenKey(root, excel_key + r"\Options", 0, flags | winreg.KEY_WRITE)
        for name, data in to_delete:
            if dry_run:
                _log.info("[DRY-RUN] Not deleting Options key %s=%s" % (name, data))
                continue
            _log.debug("Deleting key from Excel options: %s=%s" % (name, data))
            winreg.DeleteValue(options_key, name)

        winreg.CloseKey(options_key)
    except WindowsError:
        raise Error("Couldn't update the Excel options in the registry, write access denied.")

    _renumber_excel_options(root, excel_key, flags, dry_run=dry_run)

    # uninstall entries from \Software\Microsoft\Office\<version>\Excel\Add-in Manager
    # (this is what Excel uses to list addins in the addin manager)
    addins_key = None
    try:
        addins_key = winreg.OpenKey(root, excel_key + r"\Add-in Manager", 0, flags | winreg.KEY_READ)
    except WindowsError:
        pass

    if addins_key:
        to_delete = []
        try:
            i = 0
            while True:
                name, data, dtype = winreg.EnumValue(addins_key, i)
                filename = os.path.basename(name)
                if filename.lower() == os.path.basename(xll_path).lower():
                    to_delete.append((name, data))
                i += 1
        except WindowsError:
            pass
        winreg.CloseKey(addins_key)

        # If there were any keys found delete them
        if to_delete:
            _log.debug("Found PyXLL add-in in Excel's 'Add-in Manager'")
            try:
                addins_key = winreg.OpenKey(root, excel_key + r"\Add-in Manager", 0, flags | winreg.KEY_WRITE)
                for name, data in to_delete:
                    if dry_run:
                        _log.info("[DRY-RUN] Not deleting Add-in Manager key %s")
                        continue
                    _log.debug("Deleting add-in from Excel Add-in Manager: '%s'" % name)
                    winreg.DeleteValue(addins_key, name)
                winreg.CloseKey(addins_key)
            except WindowsError:
                raise Error("Couldn't update the Excel Add-in Manager settings in the registry, write access denied.")

    # Uninstall entries from \Software\Microsoft\Office\<version>\Excel\Resiliency\DisabledItems
    # (this is what Excel uses to list blacklist badly behaving addins)
    disabled_key = None
    try:
        disabled_key = winreg.OpenKey(root, excel_key + r"\Resiliency\DisabledItems", 0, flags | winreg.KEY_READ)
    except WindowsError:
        pass

    if disabled_key:
        to_delete = []
        try:
            i = 0
            while True:
                name, data, dtype = winreg.EnumValue(disabled_key, i)
                if dtype == winreg.REG_BINARY:
                    value = data.decode("utf-16", "ignore").lower()
                    if os.path.basename(xll_path).lower() in value:
                        to_delete.append(name)
                i += 1
        except WindowsError:
            pass
        winreg.CloseKey(disabled_key)

        # if there were any PyXLL keys found delete them
        if to_delete:
            _log.debug("Found PyXLL in Excel's disabled addins")
            try:
                disabled_key = winreg.OpenKey(root, excel_key + r"\Resiliency\DisabledItems", 0, flags | winreg.KEY_WRITE)
                for name in to_delete:
                    if dry_run:
                        _log.info("[DRY-RUN] Not deleting DisabledItems key %s" % name)
                        continue
                    winreg.DeleteValue(disabled_key, name)
                winreg.CloseKey(addins_key)
                if not dry_run:
                    _log.debug("Deleted PyXLL from Excel's disabled addins")
            except WindowsError:
                raise Error("Couldn't update the Excel's DisabledItems, write access denied.")

    # Uninstall registered classes
    _uninstall_registered_com_comonents(dry_run=dry_run)

def _uninstall_registered_com_comonents(dry_run=False):
    """Remove any registered COM classes from the registry."""

    def _deleteAllSubKeys(key, flags):
        assert key.strip()
        try:
            hkey = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key, 0, flags | winreg.KEY_READ)
        except WindowsError:
            return False

        num_subkeys, num_values, last_modified = winreg.QueryInfoKey(hkey)
        subkeys = []
        for i in range(0, num_subkeys):
            subkeys.append(winreg.EnumKey(hkey, i))

        for subkey in subkeys:
            # Delete sub keys of the sub key...
            _deleteAllSubKeys("\\".join((key, subkey)), flags)

            # And delete the sub key itself
            _deleteSubKey(key, subkey, flags)

        hkey.Close()
        return True

    def _deleteSubKey(key, subkey, flags=None):
        assert subkey.strip()  # don't accidentally delete the whole key

        all_flags = list(_wow64_flags.values())
        if flags is not None:
            all_flags = [flags]

        for flags in all_flags:
            # Delete all sub keys first (returns true if the subkey exists, false otherwise)
            if _deleteAllSubKeys("\\".join((key, subkey)), flags):
                # Then delete the actual key
                try:
                    hkey = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key, 0, flags | winreg.KEY_WRITE)
                except WindowsError:
                    _log.debug("Unable to open registry key '%s' to delete sub key '%s'" % (key, subkey))
                    return

                try:
                    if dry_run:
                        _log.info("[DRY-RUN] Not deleting registry key %s\\%s" % (key, subkey))
                        return

                    try:
                        winreg.DeleteKey(hkey, subkey)
                    except WindowsError:
                        _log.debug("Unable to delete registry key '%s\\%s'" % (key, subkey))
                finally:
                    hkey.Close()

    for key in _registered_com_components:
        if dry_run:
            _log.debug("[DRY-RUN] Not unregistering %s component" % key)

        for clsid in _clsids.get(key, []):
            _deleteSubKey(r"Software\Classes\CLSID", "{%s}" % clsid)

        for progid in _progids.get(key, []):
            _deleteSubKey(r"Software\Classes", progid)

        for typelib in _typelibs.get(key, []):
            _deleteSubKey(r"Software\Classes\TypeLib", "{%s}" % typelib)

        if not dry_run:
            _log.debug("Unregistered %s component" % key)

def _find_pyxll_config(pyxll_path):
    """Finds the config file that this add-in will use.
    Does not check if the file exists or not.
    """
    pyxll_cfg = os.environ.get("PYXLL_CONFIG_FILE")
    if pyxll_cfg:
        _log.debug("PyXLL config file path is set using the environment variable PYXLL_CONFIG_FILE")
        return pyxll_cfg

    pyxll_cfg, ext = os.path.splitext(pyxll_path)
    pyxll_cfg += ".cfg"

    return pyxll_cfg

def _load_config_file(cfg_path):
    """Load a config file and return a ConfigParser instance."""
    cfg = RawConfigParser()

    if sys.version_info[0] >= 3:
        cfg.read(cfg_path, encoding="utf-8")
    else:
        from io import StringIO
        data = StringIO()
        with open(cfg_path, "rb") as fh:
            data.write(fh.read().decode("utf-8"))
        data.seek(0)
        cfg.readfp(data)

    return cfg

def _get_pyxll_config(pyxll_path):
    """Returns the PyXLL config as a RawConfigParser object"""
    cfg_file = _find_pyxll_config(pyxll_path)
    if not os.path.exists(cfg_file):
        raise Error("Config file '%s' does not exist." % cfg_file)

    return _load_config_file(cfg_file)

def _get_process_name(pid):
    """Return the module name of a process."""
    PROCESS_QUERY_INFORMATION = 0x0400
    PROCESS_VM_READ = 0x0010
    LIST_MODULES_ALL = 0x03
    MAX_PATH = 260

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.OpenProcess.rettype = ctypes.wintypes.HANDLE
    kernel32.OpenProcess.argtypes = [
        ctypes.wintypes.DWORD,
        ctypes.wintypes.BOOL,
        ctypes.wintypes.DWORD
    ]

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.CloseHandle.rettype = ctypes.wintypes.BOOL
    kernel32.CloseHandle.argtypes = [
        ctypes.wintypes.HANDLE
    ]

    psapi = ctypes.WinDLL("psapi", use_last_error=True)
    psapi.EnumProcessModulesEx.retype = ctypes.wintypes.BOOL
    psapi.EnumProcessModulesEx.argtypes = [
        ctypes.wintypes.HANDLE,
        ctypes.POINTER(ctypes.wintypes.HMODULE),
        ctypes.wintypes.DWORD,
        ctypes.POINTER(ctypes.wintypes.DWORD),
        ctypes.wintypes.DWORD]

    psapi.GetModuleBaseNameW.retype = ctypes.wintypes.DWORD
    psapi.GetModuleBaseNameW.argtypes = [
        ctypes.wintypes.HANDLE,
        ctypes.wintypes.HMODULE,
        ctypes.wintypes.LPWSTR,
        ctypes.wintypes.DWORD
    ]

    proc = kernel32.OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, False, pid)
    if not proc:
        return

    module = ctypes.wintypes.HMODULE()
    needed = ctypes.wintypes.DWORD()
    result = psapi.EnumProcessModulesEx(proc,
                                        ctypes.byref(module),
                                        ctypes.sizeof(ctypes.wintypes.HMODULE),
                                        ctypes.byref(needed),
                                        LIST_MODULES_ALL)
    if not result:
        kernel32.CloseHandle(proc)
        return

    buffer_length = MAX_PATH
    buffer = ctypes.create_unicode_buffer(buffer_length)
    size = psapi.GetModuleBaseNameW(proc, module, buffer, buffer_length)

    while size > 0 and ctypes.get_last_error() == 122:  # ERROR_INSUFFICIENT_BUFFER
        buffer_length += MAX_PATH
        buffer = ctypes.create_unicode_buffer(buffer_length)
        size = psapi.GetModuleBaseNameW(proc, module, buffer, buffer_length)

    kernel32.CloseHandle(module)
    kernel32.CloseHandle(proc)

    if not size:
        return

    name = buffer.value[:size]
    return name

def _excel_is_running():
    """Returns True if Excel is currently running."""

    # Get a list of all running processes
    psapi = ctypes.windll.psapi
    psapi.EnumProcesses.rettype = ctypes.wintypes.BOOL
    psapi.EnumProcesses.argtypes = [ctypes.POINTER(ctypes.wintypes.DWORD),
                                       ctypes.wintypes.DWORD,
                                       ctypes.POINTER(ctypes.wintypes.DWORD)]

    # Keep going until the buffer is larger than the number of running processes
    num_processes = 1024
    while True:
        processes = (ctypes.wintypes.DWORD * num_processes)()
        size = num_processes * ctypes.sizeof(ctypes.wintypes.DWORD)
        needed = ctypes.wintypes.DWORD()
        result = psapi.EnumProcesses(processes, size, ctypes.byref(needed))
        if not result:
            error = ctypes.GetLastError()
            raise Error("Unable to determine if Excel is currently running. EnumProcesses failed (0x%x)." % error)

        if needed.value < size:
            # Update with the actual number of processes and stop
            num_processes = int(needed.value / ctypes.sizeof(ctypes.wintypes.DWORD))
            break

        num_processes *= 2
        continue

    for i in range(num_processes):
        pid = processes[i]
        name = _get_process_name(pid)
        if not name:
            continue

        if name.lower() == "excel.exe":
            return True

    return False

def _check_excel_is_not_running():
    """Raise an error if Excel is running, or if --force was used the log a warning."""
    if _excel_is_running():
        if _is_forced():
            _log.warning("A running Excel process was found which may interfere with this task.")
            return

        raise Error("Please close Excel before running this command.\n\n"
                    "If you do not have Excel open, look for any processes named 'EXCEL.EXE'\n"
                    "in the Windows Task Manager.")

def _get_file_hash(path):
    block_size = 65536
    file_hash = hashlib.sha256()
    with open(path, "rb") as fh:
        data = fh.read(block_size)
        while len(data) > 0:
            file_hash.update(data)
            data = fh.read(block_size)
    return file_hash.hexdigest()

def _copy_tree(src, dst):
    # Get all the source files before starting to copy anything
    def _get_files(src, dst):
        for name in os.listdir(src):
            src_file = os.path.join(src, name)
            dst_file = os.path.join(dst, name)
            if not os.path.isdir(src_file):
                yield src_file, dst_file
                continue
            for s, d in _get_files(src_file, dst_file):
                yield s, d

    # Copy the files, careful not to include any new ones if we're copying into a folder in src
    for src_file, dst_file in list(_get_files(src, dst)):
        dstdir = os.path.dirname(dst_file)
        if not os.path.exists(dstdir):
            os.makedirs(dstdir)
        shutil.copyfile(src_file, dst_file)

    try:
        shutil.copystat(src, dst)
    except OSError:
        pass

def _backup_files(src_path, dst_path, filenames):
    """Backup changed files before copying.
    Returns a list of files that are unchanged between src_path and dst_path
    and therefore do not need backing up."""
    unchanged = []
    suffix = dt.datetime.now().strftime("-backup-%Y%m%d%H%M%S")
    for filename in filenames:
        # Don't bother backing up pyc or log files
        basename, ext = os.path.splitext(filename)
        if ext in (".pyc", ".log"):
            continue

        src_file = os.path.join(src_path, filename)
        dst_file = os.path.join(dst_path, filename)
        if os.path.exists(src_file) and os.path.exists(dst_file):
            # Check if the two files are the same
            src_hash = _get_file_hash(src_file)
            dst_hash = _get_file_hash(dst_file)
            if src_hash == dst_hash:
                unchanged.append(filename)
                continue

            # If not make a backup of dst_file
            _log.debug("Making a backup of '%s'" % dst_file)
            shutil.copyfile(dst_file, os.path.join(dst_path, basename + suffix + ext))

    return unchanged

def _unzip_pyxll(pyxll_download_path, pyxll_install_path):
    # Unzip the downloaded file
    _log.debug("Unzipping download file to %s" % pyxll_install_path)
    with ZipFile(pyxll_download_path) as zf:
        zf.extractall(path=pyxll_install_path)

_latest_pyxll_version = None
def _get_latest_pyxll_version():
    """Return the latest PyXLL version available for download."""
    global _latest_pyxll_version
    if _latest_pyxll_version is not None:
        return _latest_pyxll_version
    try:
        _log.debug("Looking up the latest PyXLL version.")
        request = Request("https://www.pyxll.com/version.txt", headers=_http_headers)
        pyxll_version = _urlopen_ssl(request).read().decode().strip()
        if not re.match(r"\d+\.\d+\.\d+([\.-][a-z0-9]+)?", pyxll_version, re.IGNORECASE):
            _log.error("Invalid version: %s" % pyxll_version)
            raise Error("Invalid version response when finding the latest PyXLL version.")
        _log.debug("Latest PyXLL version is %s." % pyxll_version)
    except URLError:
        exc_type, exc_value, exc_tb = sys.exc_info()
        raise Error("Error getting latest PyXLL version from pyxll.com:\n%s" % exc_value)
    _latest_pyxll_version = pyxll_version
    return pyxll_version

def _compare_pyxll_versions(a, b):
    """Return 1 if a > b."""
    if a == "dev":
        return -1
    if b == "dev":
        return 1
    if a == b:
        return 0

    # Split the version numbers into their parts (major, minor, patch[, variant])
    a_parts = a.split(".")
    b_parts = b.split(".")
    num_parts = max(4, len(a_parts), len(b_parts))
    a_parts = list(a_parts) + (["zzz"] * (num_parts - len(a_parts)))
    b_parts = list(b_parts) + (["zzz"] * (num_parts - len(b_parts)))

    # major, minor and patch are numbers, everything else is a string
    a_norm = [int(x or 0) for x in a_parts[:3]] + [str(x) for x in a_parts[3:]]
    b_norm = [int(x or 0) for x in b_parts[:3]] + [str(x) for x in b_parts[3:]]

    return 1 if a_norm > b_norm else -1 if a_norm < b_norm else 0

def _download_pyxll(python_bits, pyxll_version=None):
    # Get the version of PyXLL to download
    if pyxll_version is None:
        pyxll_version = _get_latest_pyxll_version()

    _print("")
    while True:
        name = _input("Please enter your name to download PyXLL: ").strip()
        if name:
            break

    _print("")
    while True:
        email = _input("Please enter your email address to download PyXLL: ").strip()
        if re.match(r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)", email):
            break
        _print("The given email address is not valid. Please try again.")

    _print("")
    newsletter = None
    while newsletter not in ("y", "n"):
        newsletter = _input("Would you like to sign up to the PyXLL mailing list (y/n)? ").strip().lower()
    newsletter = newsletter == "y"

    _print("")
    terms_agreed = None
    while terms_agreed not in ("y", "n"):
        _print("For terms and conditions please see https://www.pyxll.com/termsandconditions.html")
        terms_agreed = _input("Do you agree to the terms and conditions above (y/n)? ").strip().lower()

    terms_agreed = terms_agreed == "y"
    if not terms_agreed:
        _print("\nYou must agree to the terms and conditions in order to download PyXLL.")
        _print("For terms and conditions please see https://www.pyxll.com/termsandconditions.html")
        return 1

    # Download PyXLL
    url = ("https://api.pyxll.com/download?version=%(pyxll_version)s"
           "&name=%(name)s"
           "&email=%(email)s"
           "&platform-version=%(py_version)s"
           "&architecture=%(arch)s"
           "&terms-agreed=%(terms)s"
           "&email-opt-in=%(newsletter)s"
           "&utm_source=wheel") % {
              "pyxll_version": pyxll_version,
              "name": quote(name),
              "email": quote(email),
              "py_version": "py%d%d" % sys.version_info[:2],
              "arch": "x86" if python_bits == "32bit" else "x64",
              "terms": "1" if terms_agreed else "0",
              "newsletter": "1" if newsletter else "0"
          }

    try:
        _print("")
        sys.stdout.write("Downloading PyXLL...")
        request = Request(url, headers=_http_headers)
        response = _urlopen_ssl(request)
        if sys.version_info[0] == 2:
            length = response.info().getheader('Content-Length')
        else:
            length = response.getheader('content-length')
        if length:
            length = int(length)
            block_size = max(4096, length // 100)
        else:
            block_size = 1000000

        with tempfile.NamedTemporaryFile("wb", suffix=".zip", delete=False) as temp_file:
            try:
                size = 0
                while True:
                    buffer = response.read(block_size)
                    if not buffer:
                        break
                    temp_file.write(buffer)
                    size += len(buffer)
                    if length:
                        sys.stdout.write("\rDownloading PyXLL: %d%% complete" % (100 * size / length))
                print("\rDownloaded PyXLL                    ")
                return temp_file.name, pyxll_version
            except Exception:
                os.unlink(temp_file.name)
                raise
    except URLError:
        exc_type, exc_value, exc_tb = sys.exc_info()
        raise Error("Error downloading PyXLL from pyxll.com:\n%s" % exc_value)

def _install_pyxll_addin(xll_path, root, excel_key, flags, install_first=False, dry_run=False):
    """Installs the PyXLL add-in in Excel."""
    # Find existing OPEN entries in \Software\Microsoft\Office\<version>\Excel\Options
    # (this is what Excel uses to determine what to load on start-up)
    try:
        options_key = winreg.OpenKey(root, excel_key + r"\Options", 0, flags | winreg.KEY_READ)
    except WindowsError:
        raise Error("Couldn't read the Excel options in the registry.")

    open_num = 0
    try:
        i = 0
        while True:
            name, data, dtype = winreg.EnumValue(options_key, i)
            match = re.match(r"^OPEN(\d*)$", name)
            if match:
                open_num = max(int(match.group(1) or 0) + 1, open_num)
            i += 1
    except WindowsError:
        pass

    winreg.CloseKey(options_key)

    try:
        options_key = winreg.OpenKey(root, excel_key + r"\Options", 0, flags | winreg.KEY_READ | winreg.KEY_WRITE)
    except WindowsError:
        raise Error("Couldn't update the Excel options in the registry, write access denied.")

    try:
        open_key = "OPEN"
        if open_num > 0:
            open_key += str(open_num)

        if dry_run:
            _log.info("[DRY-RUN] Not updating Excel's OPEN options")
        else:
            winreg.SetValueEx(options_key, open_key, 0, winreg.REG_SZ, "/R \"%s\"" % os.path.normpath(xll_path))
    except WindowsError:
        raise Error("Couldn't create the OPEN key in the Excel options in the registry, write access denied.")

    winreg.CloseKey(options_key)

    # Check if the OPEN keys need re-numbering, and move the PyXLL add-in to be first if needed
    first_key = open_key if install_first else None
    _renumber_excel_options(root, excel_key, flags, first_key=first_key, dry_run=dry_run)

def _configure_pyxll(pyxll_install_path, license_key=None, license_file=None):
    """Updates the pyxll.cfg file in place.
    If any unexpected changes from the default pyxll.cfg file are needed a backup copy is made.
    """
    pyxll_cfg_path = os.path.join(pyxll_install_path, "pyxll.cfg")
    if not os.path.exists(pyxll_cfg_path):
        raise Error("PyXLL config file not found in %s. Try re-installing PyXLL." % pyxll_install_path)

    sys_executable = sys.executable
    pythonw = os.path.join(os.path.dirname(sys_executable), "pythonw.exe")
    if os.path.exists(pythonw):
        sys_executable = pythonw

    all_section_values = {
        # Section / option / (value, expected)
        "PYTHON": {
            "executable": (sys_executable, "c:/Python_XX/pythonw.exe"),
            "pythonhome": (None, None),
            "dll": (None, None),
        }
    }

    if license_key:
        all_section_values.setdefault("LICENSE", {}).update({
            "key": (license_key, "uncomment this line and add your license key here")
        })

    if license_file:
        all_section_values.setdefault("LICENSE", {}).update({
            "file": (license_file, "path or URL of the license file")
        })

    newline = "\r\n"
    make_backup = False
    new_cfg_lines = []
    section_values = {}
    with open(pyxll_cfg_path, "rb") as fh:
        cfg_lines = fh.read().decode("utf-8").splitlines()
        section = None
        for idx, line in enumerate(cfg_lines):
            match = re.match(r"^\[([A-Z]+)\]\s*$", line)
            if match:
                # If there are any values still left to set then add them now
                if section_values:
                    added_cfg_lines = []
                    for key, (value, expected) in list(section_values.items()):
                        if value:
                            _log.debug("Adding %s.%s = %s" % (section, key, value))
                            added_cfg_lines.append("%s = %s%s" % (key, value, newline))
                    if added_cfg_lines:
                        make_backup = True
                        if idx > 0 and cfg_lines[idx-1].strip():
                            new_cfg_lines.append(newline)
                        new_cfg_lines.extend(added_cfg_lines)
                        new_cfg_lines.append(newline)

                # Continue to the next section
                section = match.group(1)
                section_values = all_section_values.get(section, {})
                new_cfg_lines.append(line)
                continue

            match = re.match(r"^\s*([;#]*)\s*([a-z_]+)\s*=\s*(.*)\s*", line)
            if not match:
                new_cfg_lines.append(line)
                continue

            is_comment = len(match.group(1)) > 0
            option = match.group(2)
            value = match.group(3)

            if option not in section_values:
                new_cfg_lines.append(line)
                continue

            # If this line is commented out and the next line is the same option then
            # continue to the next line
            if is_comment and (idx + 1) < len(cfg_lines):
                next_line = cfg_lines[idx + 1]
                next_match = re.match(r"^\s*([;#]*)\s*([a-z_]+)\s*=\s*(.*)\s*", next_line)
                if next_match and next_match.group(2) == option:
                    new_cfg_lines.append(line)
                    continue

            # If the new value matches the old one there's nothing to do
            new_value, expected_value = section_values.pop(option)
            if new_value == value and not is_comment:
                new_cfg_lines.append(line)
                continue

            # If the value is the expected default value replace it without commenting it
            # out or requiring making a backup.
            if value == expected_value:
                _log.debug("Setting %s.%s = %s" % (section, option, new_value))
                new_cfg_lines.append("%s = %s%s" % (option, new_value, newline))
                continue

            # Comment out the old line
            if not is_comment:
                _log.debug("Commenting out %s.%s = %s" % (section, option, value))
                make_backup = True
                line = ";" + line
            new_cfg_lines.append(line)

            # If the new value is None then do nothing
            if new_value is None:
                continue

            # Add the new value to the config
            _log.debug("Setting %s.%s = %s" % (section, option, new_value))
            make_backup = True
            new_cfg_lines.append("%s = %s%s" % (option, new_value, newline))

    if make_backup:
        suffix = dt.datetime.now().strftime("-backup-%Y%m%d%H%M%S")
        backup_cfg = os.path.join(os.path.dirname(pyxll_cfg_path), "pyxll%s.cfg" % suffix)
        _log.debug("Making backup file '%s'" % backup_cfg)
        shutil.copyfile(pyxll_cfg_path, backup_cfg)

    with open(pyxll_cfg_path, "wb") as fh:
        fh.write(newline.join(new_cfg_lines).encode("utf-8"))
        fh.write(newline.encode("utf-8"))

    _log.debug("Updated config file '%s'" % pyxll_cfg_path)

def _check_python_exe():
    if not os.path.exists(sys.executable):
        raise Error("Python executable '%s' is not accessible. Check you Python installation." % sys.executable)

    # Check if Python is running as a UWP app (GetCurrentPackageFullName doesn't exist before Windows 8)
    GetCurrentPackageFullName = getattr(ctypes.windll.kernel32, "GetCurrentPackageFullName", None)
    if not GetCurrentPackageFullName:
        return

    length = ctypes.c_int(0)
    error = GetCurrentPackageFullName(ctypes.byref(length), None)
    if error in (0, 0x7A):  # SUCCESS, ERROR_INSUFFICIENT_BUFFER
        raise Error(("Invalid Python executable '%s'\n\n" % sys.executable) +
                     "Python installed via the Windows Store cannot be used with PyXLL.\n"
                     "Instead we recommend downloading Python from https://www.python.org.")

def _clear_zone_identifier(filename):
    """Clear the NTFS ADS 'Zone.Identifier' from a file."""
    if os.path.exists(filename + ":Zone.Identifier"):
        try:
            _log.debug("Removing Zone.Identifier information from '%s'." % filename)
            os.remove(filename + ":Zone.Identifier")
        except:
            _log.warning("Error unblocking '%s'." % filename, exc_info=_log.getEffectiveLevel() <= logging.DEBUG)
            _log.warning("Excel will not be able to load '%s' until it is unblocked." % filename)
            _log.warning("To unblock the file right click on it in Explorer and go to Properties, then "
                         "check the 'Unblock' checkbox next to 'Security' in the 'General' tab.")

def _is_admin():
    try:
        from ._admin import process_user_is_admin
        kernel32 = ctypes.windll.kernel32
        kernel32.GetCurrentProcessId.argtypes = []
        kernel32.GetCurrentProcessId.rettype = ctypes.wintypes.DWORD
        pid = kernel32.GetCurrentProcessId()
        return process_user_is_admin(pid)
    except:
        _log.warning("Checking if current user is admin failed", exc_info=_log.getEffectiveLevel() <= logging.DEBUG)
        return False

def _find_and_check_excel():
    excel_exe = _find_excel_path()
    if not excel_exe:
        if _is_admin():
            _log.warning("It looks like you are running this command as an administrator user. "
                         "Excel may not be installed for your admin user.")
            _log.warning("You should run this command using the same user Excel is installed for.")
        raise Error(("Excel does not appear to be installed.\n\n"
                     "Please ensure that Excel is installed correctly and try again."))

    # Check the bitness of Excel matches Python
    excel_bits = _get_exe_bitness(excel_exe)
    python_bits = _get_exe_bitness(sys.executable)
    if python_bits != excel_bits:
        raise Error(("Excel is %(excel_bits)s but Python is %(python_bits)s.\n\n"
                     "Please check the version of Office you have installed and either install "
                     "the %(python_bits)s version of Excel or install a %(excel_bits)s version of Python.")
                    % {"excel_bits": excel_bits, "python_bits": python_bits})

    xl_version_info = _find_excel_version_info(python_bits)
    if xl_version_info is None:
        if _is_admin():
            _log.warning("It looks like you are running this command as an administrator user. "
                         "Excel may not be installed for your admin user.")
            _log.warning("You should run this command using the same user Excel is installed for.")
        raise Error(("Excel does not appear to be installed.\n\n"
                     "Please ensure that Excel is installed correctly and try again."))

    excel_version, hkey_root, excel_subkey, flags = xl_version_info
    _log.debug("Found %s Excel %s installed: %s" % (excel_bits, excel_version, excel_exe))
    return excel_exe, excel_bits, xl_version_info