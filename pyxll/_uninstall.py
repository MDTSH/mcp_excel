"""
Copyright (c) 2009-2012, All Rights Reserved, http://www.pyxll.com/

THIS CODE AND INFORMATION ARE PROVIDED "AS IS" WITHOUT WARRANTY OF ANY
KIND, EITHER EXPRESSED OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND/OR FITNESS FOR A
PARTICULAR PURPOSE.
"""
from ._errors import Help
from ._utils import (
    _print,
    _input,
    _find_excel_version_info,
    _find_pyxll_addin,
    _uninstall_pyxll_addin,
    _check_excel_is_not_running,
    _wow64_flags,
    _is_forced
)
import logging

try:
    import winreg
except ImportError:
    import _winreg as winreg  # type: ignore

_log = logging.getLogger(__name__)

def uninstall(*args):
    dry_run = False
    unexpected_args = []
    for arg in args:
        if arg == "--dry-run" or arg == "-n":
            dry_run = True
        else:
            unexpected_args.append(arg)

    if unexpected_args:
        raise Help("Unexpected arguments '%s' to command 'uninstall'." % ", ".join(unexpected_args))

    _check_excel_is_not_running()

    xl_version_info = None
    pyxll_path = None
    for bits in _wow64_flags:
        xl_version_info = _find_excel_version_info(bits)
        if not xl_version_info:
            continue

        xl_version, root_hkey, subkey, flags = xl_version_info
        pyxll_path = _find_pyxll_addin(root_hkey, subkey, flags)
        if pyxll_path:
            break

    if not pyxll_path:
        _print("The PyXLL Excel add-in is not installed.")
        return 0

    xl_version, root_hkey, subkey, flags = xl_version_info
    _print("Found PyXLL installed in Excel %s" % xl_version)
    _print("The PyXLL add-in location is '%s'" % pyxll_path)

    if not _is_forced():
        response = None
        while response not in ("y", "n"):
            response = _input("Do you want to uninstall this add-in ([y]/n)? ", default="y").strip().lower()
            if not response:
                response = "y"

        if response != "y":
            _print("Uninstalling has been cancelled")
            return 1

    _uninstall_pyxll_addin(root_hkey, subkey, flags, pyxll_path, dry_run)
    _print("Uninstall of the PyXLL Excel add-in is complete.")