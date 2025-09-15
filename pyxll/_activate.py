"""
Copyright (c) 2020, All Rights Reserved, http://www.pyxll.com/

THIS CODE AND INFORMATION ARE PROVIDED "AS IS" WITHOUT WARRANTY OF ANY
KIND, EITHER EXPRESSED OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND/OR FITNESS FOR A
PARTICULAR PURPOSE.
"""
from ._cli import Help, Error, _print
from ._cert import _install_certificate
from ._utils import (
    _input,
    _find_and_check_excel,
    _get_dll_bitness,
    _get_exe_bitness,
    _check_excel_is_not_running,
    _find_pyxll_addin,
    _get_xll_version_info,
    _get_xll_file_version,
    _uninstall_pyxll_addin,
    _install_pyxll_addin,
    _clear_zone_identifier
)
import logging
import sys
import os

_log = logging.getLogger(__name__)

def activate(*args):
    dry_run = False
    install_first = False
    pyxll_install_path = None

    unexpected_args = []
    for arg in args:
        if arg == "--dry-run" or arg == "-n":
            dry_run = True
        elif arg == "--install-first" or arg == "-if":
            install_first = True
        else:
            unexpected_args.append(arg)

    if len(unexpected_args) == 1:
        pyxll_install_path = unexpected_args.pop(0)
        if not os.path.exists(pyxll_install_path):
            raise Error("Path '%s' not found." % pyxll_install_path)

    if unexpected_args:
        raise Help("Unexpected arguments '%s' to command 'activate'." % ", ".join(unexpected_args))

    _check_excel_is_not_running()

    # Check Excel is installed and exists
    excel_exe, excel_bits, xl_version_info = _find_and_check_excel()
    xl_version, root_hkey, subkey, flags = xl_version_info

    # Look for pyxll in the current directory
    if not pyxll_install_path:
        cwd = os.getcwd()
        if os.path.exists(os.path.join(cwd, "pyxll.xll")) and os.path.exists(os.path.join(cwd, "pyxll.cfg")):
            response = None
            _print("\nA PyXLL add-in was found in the current folder.")
            while response not in ("y", "n"):
                response = _input("Do you want to activate pyxll.xll from the current folder ([y]/n)? ", default="y").strip().lower()
                if not response:
                    response = "y"
            if response == "y":
                pyxll_install_path = cwd

    # If not found prompt the user for another path
    if not pyxll_install_path:
        _print("")
        while True:
            pyxll_install_path = _input("Enter the path where PyXLL is located: ", is_path=True).strip()
            if not pyxll_install_path:
                continue

            if not os.path.exists(pyxll_install_path):
                _print("The path entered does not exist. Please try again.")
                continue

            if os.path.isfile(pyxll_install_path):
                if os.path.basename(pyxll_install_path).lower() == "pyxll.xll":
                    pyxll_install_path = os.path.dirname(pyxll_install_path)
                    break

                _print("The entered path does not look like a PyXLL add-in. Please try again.")
                continue

            elif os.path.isdir(pyxll_install_path):
                if os.path.exists(os.path.join(pyxll_install_path, "pyxll.xll")):
                    break
                _print("pyxll.xll is missing from the folder specified. Please try again.")
                continue

    # Check the install path looks ok
    if not os.path.exists(pyxll_install_path):
        raise Error("The path '%s' does not exist." % pyxll_install_path)

    if os.path.isfile(pyxll_install_path):
        if os.path.basename(pyxll_install_path).lower() != "pyxll.xll":
            raise Error("The file '%s' does not look like a PyXLL add-in." % pyxll_install_path)
        pyxll_install_path = os.path.dirname(pyxll_install_path)

    # Check the pyxll.xll file exists and use the abspath
    pyxll_install_path = os.path.abspath(pyxll_install_path)
    pyxll_xll_path = os.path.join(pyxll_install_path, "pyxll.xll")
    if not os.path.exists(pyxll_xll_path):
        raise Error("Couldn't find pyxll.xll file in '%s'" % pyxll_install_path)

    # Check the installed version of PyXLL is the correct bitness
    pyxll_bits = _get_dll_bitness(pyxll_xll_path)
    python_bits = _get_exe_bitness(sys.executable)
    if pyxll_bits != python_bits:
        raise Error(("Excel and Python are %(excel_bits)s but the PyXLL add-in is %(python_bits)s.\n\n"
                     "You should download the %(excel_bits)s version of PyXLL and install that, or "
                     "you can use the following command to re-install PyXLL:\n\n"
                     "pyxll install\n\n"
                     "See the PyXLL website https://www.pyxll.com for detailed installation instructions.")
                    % {"excel_bits": excel_bits, "python_bits": python_bits, "pyxll_bits": pyxll_bits})

    # Check the PyXLL version matches our Python version
    version_info = _get_xll_version_info(pyxll_xll_path)
    pyxll_version = _get_xll_file_version(pyxll_xll_path)

    # Older PyXLL add-ins do not have version information we can extract
    if version_info is not None:
        name, pyxll_version, py_version = version_info
        if py_version != "py%d%d" % sys.version_info[:2]:
            raise Error(("The selected PyXLL add-in is for a different version of Python.\n\n"
                         "The PyXLL add-in selected is for Python %(pyxll_py_version)s but the actual Python "
                         "interpreter in use is Python %(py_version)s.\n\n" +
                         "You will need to download the correct version of PyXLL, or change the version "
                         "of Python you are using.\n\n"
                         "You can re-install PyXLL by running:\n\n"
                         "pyxll install\n\n"
                         "or see the PyXLL website https://www.pyxll.com for installation instructions.") % {
                            "py_version": "%d.%d" % sys.version_info[:2],
                            "pyxll_py_version": "%s.%s" % (py_version[2:3], py_version[3:])})

    existing_pyxll_path = _find_pyxll_addin(root_hkey, subkey, flags)
    if existing_pyxll_path:
        _log.debug("Uninstalling previous PyXLL add-in...")
        _uninstall_pyxll_addin(root_hkey, subkey, flags, existing_pyxll_path, dry_run=dry_run)

    _log.debug("Installing Excel add-in")
    _install_pyxll_addin(pyxll_xll_path, root_hkey, subkey, flags,
                         install_first=install_first,
                         dry_run=dry_run)

    # Unblock the file if it is blocked
    _clear_zone_identifier(pyxll_xll_path)

    # Try installing the certificate
    if dry_run:
        _log.info("[DRY-RUN] Not installing Trusted Publisher certificate")

        _print("\n")
        _print("-" * 79)
        _print("[DRY-RUN] PyXLL%s would have been activated from:\n%s\n" % (
            (" " + pyxll_version) if pyxll_version else "",
            pyxll_install_path))
        _print("-" * 79)
        return 0

    try:
        _install_certificate()
    except Exception:
        _log.warning("Unable to install the Trusted Publisher certificate.",
                     exc_info=_log.getEffectiveLevel() <= logging.DEBUG)
        _log.warning("If Excel cannot load the PyXLL add-in check your Trust Center Settings in Options in Excel.")

    _print("\n")
    _print("-" * 79)
    _print("PyXLL%s has been successfully activated from:\n%s\n" % (
        (" " + pyxll_version) if pyxll_version else "",
        pyxll_install_path))
    _print("-" * 79)

    return 0