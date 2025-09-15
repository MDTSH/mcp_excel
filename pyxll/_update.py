"""
Copyright (c) 2020, All Rights Reserved, http://www.pyxll.com/

THIS CODE AND INFORMATION ARE PROVIDED "AS IS" WITHOUT WARRANTY OF ANY
KIND, EITHER EXPRESSED OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND/OR FITNESS FOR A
PARTICULAR PURPOSE.
"""
from ._errors import Help, Error
from ._cert import _install_certificate
from ._utils import (
    AutoDeleteFile,
    AutoDeleteFolder,
    _print,
    _input,
    _find_and_check_excel,
    _get_latest_pyxll_version,
    _compare_pyxll_versions,
    _get_dll_bitness,
    _get_exe_bitness,
    _check_excel_is_not_running,
    _check_python_exe,
    _find_pyxll_addin,
    _get_xll_version_info,
    _get_xll_file_version,
    _download_pyxll,
    _unzip_pyxll,
    _backup_files,
    _clear_zone_identifier,
    _is_forced
)
import tempfile
import logging
import shutil
import glob
import sys
import os

_log = logging.getLogger(__name__)

def update(*args):
    pyxll_version = None
    pyxll_download_path = None
    force = _is_forced()

    auto_delete_files = []
    unexpected_args = []
    args = list(args)
    while args:
        arg = args.pop(0)
        value = None
        if "=" in arg:
            arg, value = arg.split("=", 1)
        value = value[0].strip("\'\"") if value else None
        if arg == "--version":
            if not value and args and not args[0].startswith("-"):
                value = args.pop(0)
            if not value:
                raise Help("No version specified with --version option")
            pyxll_version = value
        else:
            unexpected_args.append(arg)

    if len(unexpected_args) == 1:
        pyxll_download_path = unexpected_args.pop(0)
        if not os.path.exists(pyxll_download_path):
            raise Error("Path '%s' not found." % pyxll_download_path)

        if pyxll_version:
            raise Error("Use --version or a filename, not both.")

    if unexpected_args:
        raise Help("Unexpected arguments '%s' to command 'update'." % ", ".join(unexpected_args))

    _check_python_exe()
    _check_excel_is_not_running()

    # Check Excel is installed and exists
    excel_exe, excel_bits, xl_version_info = _find_and_check_excel()
    xl_version, root_hkey, subkey, flags = xl_version_info
    python_bits = _get_exe_bitness(sys.executable)

    # Check PyXLL is already installed
    pyxll_path = _find_pyxll_addin(root_hkey, subkey, flags)
    if not pyxll_path or not os.path.exists(pyxll_path):
        raise Error(("No existing install of PyXLL was found.\n\n"
                     "Please use the 'pyxll install' to install PyXLL instead."))

    # Get the existing version info and check if there is a new version available
    latest_version = _get_latest_pyxll_version()
    installed_version = _get_xll_file_version(pyxll_path)
    version_info = _get_xll_version_info(pyxll_path)
    if version_info is not None:
        _, installed_version, _ = version_info

        if pyxll_version is None and pyxll_download_path is None and not force:
            if _compare_pyxll_versions(installed_version, latest_version) >= 0:
                raise Error("PyXLL %s is already installed and no newer version was found." % installed_version)

    _print("\nPyXLL is installed in '%s'." % os.path.dirname(pyxll_path))
    _print("\nYour existing PyXLL add-in will be backed up before updating.")
    _print("\nYour existing pyxll.cfg file will *not* be changed and any new "
            "examples will not be installed.")
    _print("\nIf you want to try out a new version before updating use 'pyxll install' "
            "and install PyXLL into a different folder than your current installation.")

    # Find or download PyXLL
    pyxll_install_path = os.path.dirname(pyxll_path)

    # Look for pyxll in the current directory (if it's not the folder PyXLL is installed in)
    if not pyxll_download_path:
        cwd = os.getcwd()
        if os.path.normpath(pyxll_install_path) != os.path.normpath(cwd) \
        and os.path.exists(os.path.join(cwd, "pyxll.xll")):
            response = None
            _print("\nA PyXLL add-in was found in the current folder.")
            while response not in ("y", "n"):
                response = _input("Do you want to update your install of PyXLL to use the pyxll.xll found "
                                  "in the current folder ([y]/n)? ", default="y").strip().lower()
                if not response:
                    response = "y"
            if response == "y":
                pyxll_download_path = cwd

    # If not found prompt the user for another path
    if not pyxll_download_path:
        _print("")
        response = None
        while response not in ("y", "n"):
            response = _input("Have you already downloaded the new version of the PyXLL add-in you "
                              "want to update to (y/[n])? ").strip().lower()
            if not response:
                response = "n"

        if response == "y":
            _print("")
            while True:
                pyxll_download_path = _input("Enter the path of new PyXLL version you downloaded: ", is_path=True).strip()
                if not pyxll_download_path:
                    continue

                if not os.path.exists(pyxll_download_path):
                    _print("\nThe path entered does not exist. Please try again.\n\n")
                    continue

                # Use the absolute path
                pyxll_download_path = os.path.abspath(pyxll_download_path)

                if os.path.isfile(pyxll_download_path):
                    if os.path.basename(pyxll_download_path).lower() == "pyxll.xll":
                        # Update to the pyxll.xll file found in this folder
                        pyxll_download_path = os.path.dirname(pyxll_download_path)
                        if os.path.normpath(pyxll_download_path) == os.path.normpath(pyxll_install_path):
                            _print("\nThe path you entered for the downloaded new version is the same as where PyXLL "
                                   "is currently installed.\n\n")
                            continue
                        break

                    _, ext = os.path.splitext(pyxll_download_path)
                    if ext.lower() == ".zip":
                        break

                    _print("\nThe downloaded file should be a zip file. Please try again.\n\n")
                    continue

                elif os.path.isdir(pyxll_download_path):
                    if os.path.normpath(pyxll_download_path) == os.path.normpath(pyxll_install_path):
                        _print("\nThe path you entered for the downloaded new version is the same as where PyXLL "
                               "is currently installed.\n\n")
                        continue
                    if not os.path.exists(os.path.join(pyxll_download_path, "pyxll.xll")):
                        _print("\npyxll.xll is missing from the folder specified. Please try again.\n\n")
                        continue
                    else:
                        break

    # If the user doesn't already have PyXLL then download it
    if not pyxll_download_path:
        pyxll_download_path, pyxll_version = _download_pyxll(python_bits, pyxll_version)
        auto_delete_files.append(AutoDeleteFile(pyxll_download_path))

    # Check we're not trying to use the installed version to update from
    if os.path.normpath(pyxll_download_path) == os.path.normpath(pyxll_install_path):
        raise Error(("The PyXLL add-in '%s' is already installed. Please try again and "
                     "choose the path of the new version of PyXLL you wish to update to.") % pyxll_path)

    # Unzip the download into the install path if necessary
    if os.path.isdir(pyxll_download_path):
        pyxll_unzipped_path = pyxll_download_path
    elif os.path.basename(pyxll_download_path) == "pyxll.xll":
        pyxll_unzipped_path = os.path.dirname(pyxll_download_path)
    else:
        pyxll_unzipped_path = tempfile.mkdtemp()
        auto_delete_files.append(AutoDeleteFolder(pyxll_unzipped_path))
        _unzip_pyxll(pyxll_download_path, pyxll_unzipped_path)

    # Check the pyxll.xll file exists
    pyxll_xll_path = os.path.join(pyxll_unzipped_path, "pyxll.xll")
    if not os.path.exists(pyxll_xll_path):
        raise Error("Couldn't find pyxll.xll file in '%s'" % pyxll_unzipped_path)

    # Check the installed version of PyXLL is the correct bitness
    pyxll_bits = _get_dll_bitness(pyxll_xll_path)
    if pyxll_bits != python_bits:
        raise Error(("Excel and Python are %(excel_bits)s but the downloaded PyXLL add-in is %(pyxll_bits)s.\n\n"
                     "You should download the %(excel_bits)s version of PyXLL and install that, or "
                     "you can use the following command to re-install PyXLL:\n\n"
                     "pyxll install\n\n"
                     "See the PyXLL website https://www.pyxll.com for detailed installation instructions.")
                    % {"excel_bits": excel_bits, "python_bits": python_bits, "pyxll_bits": pyxll_bits})

    # Check the PyXLL version matches our Python version
    version_info = _get_xll_version_info(pyxll_xll_path)
    unzipped_version = _get_xll_file_version(pyxll_xll_path)

    # Older PyXLL add-ins do not have version information we can extract
    if version_info is not None:
        name, unzipped_version, py_version = version_info
        if py_version != "py%d%d" % sys.version_info[:2]:
            raise Error(("The downloaded PyXLL add-in is for a different version of Python.\n\n"
                         "The PyXLL add-in downloaded is for Python %(pyxll_py_version)s but the actual Python "
                         "interpreter in use is Python %(py_version)s.\n\n" +
                         "You will need to download the correct version of PyXLL, or change the version "
                         "of Python you are using.\n\n"
                         "You can re-install PyXLL by running:\n\n"
                         "pyxll install\n\n"
                         "or see the PyXLL website https://www.pyxll.com for installation instructions.") % {
                            "py_version": "%d.%d" % sys.version_info[:2],
                            "pyxll_py_version": "%s.%s" % (py_version[2:3], py_version[3:])})

        if pyxll_version is not None \
        and unzipped_version != pyxll_version:
            raise Error(("PyXLL version '%s' was requested but version '%s' was found." % (
                            pyxll_version, unzipped_version)) +
                        ("\nPlease check the version and try again."))

    if not force:
        _print("")
        response = None
        while response not in ("y", "n"):
            response = _input("Do you want to update PyXLL from %s to %s ([y]/n)? " % (
                installed_version or "<unknown>", unzipped_version or "<unknown>"), default="y").lower()
            if not response:
                response = "y"
        if response != "y":
            return 1

    # Backup the previous files and copy over the new ones
    whl_files = [os.path.basename(x) for x in glob.glob(os.path.join(pyxll_unzipped_path, "pyxll-*.whl"))]
    files_to_copy = [
        "pyxll.xll",
        "readme.pdf",
        "license-agreement.pdf",
    ] + whl_files

    unchanged = _backup_files(pyxll_unzipped_path, pyxll_install_path, files_to_copy)

    for filename in files_to_copy:
        if filename in unchanged:
            continue
        if os.path.exists(os.path.join(pyxll_unzipped_path, filename)):
            shutil.copyfile(os.path.join(pyxll_unzipped_path, filename),
                            os.path.join(pyxll_install_path, filename))

    # Unblock the file if it is blocked
    _clear_zone_identifier(pyxll_xll_path)

    # Try installing the certificate
    try:
        _install_certificate()
    except Exception:
        _log.warning("Unable to install the Trusted Publisher certificate.",
                     exc_info=_log.getEffectiveLevel() <= logging.DEBUG)
        _log.warning("If Excel cannot load the PyXLL add-in check your Trust Center Settings in Options in Excel.")

    _print("\n")
    _print("-" * 79)
    _print("PyXLL has been successfully updated%s" % ((" to " + unzipped_version) if unzipped_version else ""))
    _print("-" * 79)

    return 0