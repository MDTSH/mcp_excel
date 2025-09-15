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
    _get_dll_bitness,
    _get_exe_bitness,
    _check_excel_is_not_running,
    _check_python_exe,
    _find_pyxll_addin,
    _uninstall_pyxll_addin,
    _get_xll_version_info,
    _get_xll_file_version,
    _unzip_pyxll,
    _download_pyxll,
    _install_pyxll_addin,
    _configure_pyxll,
    _find_pyxll_config,
    _get_pyxll_config,
    _backup_files,
    _copy_tree,
    _clear_zone_identifier
)
import platform
import tempfile
import logging
import shutil
import sys
import os

_log = logging.getLogger(__name__)

def install(*args):
    pyxll_version = None
    pyxll_download_path = None
    pyxll_install_path = None
    pyxll_unzipped_path = None
    install_first = False

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
        if arg == "--install-first" or arg == "-if":
            install_first = True
        else:
            unexpected_args.append(arg)

    if len(unexpected_args) == 1:
        pyxll_download_path = unexpected_args.pop(0)
        if not os.path.exists(pyxll_download_path):
            raise Error("Path '%s' not found." % pyxll_download_path)

        if pyxll_version:
            raise Error("Use --version or a filename, not both.")

    if unexpected_args:
        raise Help("Unexpected arguments '%s' to command 'install'." % ", ".join(unexpected_args))

    _check_python_exe()
    _check_excel_is_not_running()

    # Check Excel is installed and exists
    excel_exe, excel_bits, xl_version_info = _find_and_check_excel()
    xl_version, root_hkey, subkey, flags = xl_version_info
    python_bits = _get_exe_bitness(sys.executable)

    # See if PyXLL is already installed
    existing_pyxll_path = _find_pyxll_addin(root_hkey, subkey, flags)
    if existing_pyxll_path and os.path.exists(existing_pyxll_path):
        _print("\nA previously installed PyXLL add-in was found '%s'" % existing_pyxll_path)
        _print("You can use 'pyxll update' to update PyXLL rather than re-install it.")
        response = None
        while response not in ("y", "n"):
            response = _input("Do you want to continue ([y]/n)? ", default="y").strip().lower()
            if not response:
                response = "y"
        if response != "y":
            return 1

    # Look for pyxll in the current directory if we don't already have the download path
    if not pyxll_download_path:
        cwd = os.getcwd()
        if os.path.exists(os.path.join(cwd, "pyxll.xll")) and os.path.exists(os.path.join(cwd, "pyxll.cfg")):
            response = None
            _print("\nA PyXLL add-in was found in the current folder.")
            while response not in ("y", "n"):
                response = _input("Do you want to install PyXLL from the current folder ([y]/n)? ").strip().lower()
                if not response:
                    response = "y"

            if response == "y":
                pyxll_download_path = cwd

    # If not found prompt the user for another path
    if not pyxll_download_path:
        _print("")
        response = None
        while response not in ("y", "n"):
            response = _input("Have you already downloaded the PyXLL add-in (y/[n])? ").strip().lower()
            if not response:
                response = "n"

        if response == "y":
            _print("")
            while True:
                pyxll_download_path = _input("Enter the path of where you downloaded PyXLL to: ", is_path=True).strip()
                if not pyxll_download_path:
                    continue

                if not os.path.exists(pyxll_download_path):
                    print("The path entered does not exist. Please try again.")
                    continue

                if os.path.isfile(pyxll_download_path):
                    if os.path.basename(pyxll_download_path).lower() == "pyxll.xll":
                        # Use the same directory for the download and install path
                        pyxll_download_path = pyxll_install_path = os.path.dirname(pyxll_download_path)
                        break

                    _, ext = os.path.splitext(pyxll_download_path)
                    if ext.lower() == ".zip":
                        break

                    print("The downloaded file should be a zip file. Please try again.")
                    continue

                elif os.path.isdir(pyxll_download_path):
                    if not os.path.exists(os.path.join(pyxll_download_path, "pyxll.xll")):
                        print("pyxll.xll is missing from the folder specified. Please try again.")
                        continue
                    elif not os.path.exists(os.path.join(pyxll_download_path, "pyxll.cfg")):
                        print("pyxll.cfg is missing from the folder specified. Please try again.")
                        continue
                    break

    # If the user doesn't already have PyXLL then download it
    if not pyxll_download_path:
        pyxll_download_path, pyxll_version = _download_pyxll(python_bits, pyxll_version)
        auto_delete_files.append(AutoDeleteFile(pyxll_download_path))

    # Unzip the download into a temporary folder
    if os.path.isfile(pyxll_download_path):
        pyxll_unzipped_path = tempfile.mkdtemp()
        auto_delete_files.append(AutoDeleteFolder(pyxll_unzipped_path))
        _unzip_pyxll(pyxll_download_path, pyxll_unzipped_path)
    elif os.path.basename(pyxll_download_path) == "pyxll.xll":
        pyxll_unzipped_path = os.path.dirname(pyxll_download_path)
    else:
        pyxll_unzipped_path = pyxll_download_path

    # Check the pyxll.xll file exists in the download
    pyxll_xll_path = os.path.join(pyxll_unzipped_path, "pyxll.xll")
    if not os.path.exists(pyxll_xll_path):
        raise Error("Couldn't find pyxll.xll file in '%s'" % pyxll_unzipped_path)

    # Check the downloaded version of PyXLL is the correct bitness
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
    pyxll_version = _get_xll_file_version(pyxll_xll_path)

    # Older PyXLL add-ins do not have version information we can extract
    if version_info is not None:
        name, pyxll_version, py_version = version_info
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

    # Get the folder to install PyXLL to
    if not pyxll_install_path:
        pyxll_install_path = _get_install_path(existing_pyxll_path, pyxll_download_path)

    # Make sure the install path is an absolute path
    if not os.path.isabs(pyxll_install_path):
        pyxll_install_path = os.path.abspath(pyxll_install_path)

    # Get the license key from the existing config file, if there is one
    license_key = None
    license_file = None

    if existing_pyxll_path and os.path.exists(existing_pyxll_path):
        cfg_file = _find_pyxll_config(existing_pyxll_path)
        if os.path.exists(cfg_file):
            cfg = _get_pyxll_config(existing_pyxll_path)
            if cfg.has_option("LICENSE", "key"):
                license_key = cfg.get("LICENSE", "key")
            if cfg.has_option("LICENSE", "file"):
                license_file = cfg.get("LICENSE", "file")

    # Ask for a license key if we didn't find one in the current install
    if not license_key and not license_file \
    and not os.environ.get("PYXLL_LICENSE_KEY") and not os.environ.get("PYXLL_LICENSE_FILE"):
        response = None
        _print("\nA license key is not required to evaluate PyXLL.")
        while response not in ("y", "n"):
            response = _input("Do you have a PyXLL license key (y/[n])? ").strip().lower()
            if not response:
                break

        if response == "y":
            _print("")
            license_key = _input("Please enter your license key: ").strip()

    # Copy the new files into the install folder
    _log.debug("Copying PyXLL files...")
    if os.path.normpath(pyxll_unzipped_path) != os.path.normpath(pyxll_install_path):
        if not os.path.exists(pyxll_install_path):
            os.makedirs(pyxll_install_path)

        # Make a backup of everything in the install folder
        for root, dirs, files in os.walk(pyxll_install_path):
            relative_root = os.path.relpath(root, pyxll_install_path)
            src_root = os.path.join(pyxll_unzipped_path, relative_root)
            _backup_files(src_root, root, files)

        # Copy everything from the download folder to the install path
        _copy_tree(pyxll_unzipped_path, pyxll_install_path)

    # Get the new PyXLL xll path
    installed_xll_path = os.path.join(pyxll_install_path, "pyxll.xll")
    if not os.path.exists(pyxll_xll_path):
        raise Error("Couldn't find pyxll.xll file in '%s'" % pyxll_install_path)

    # Update the pyxll.cfg file with the right basic settings
    _log.debug("Configuring PyXLL...")
    _configure_pyxll(pyxll_install_path, license_key=license_key, license_file=license_file)

    if existing_pyxll_path:
        _log.debug("Uninstalling previous PyXLL add-in...")
        _uninstall_pyxll_addin(root_hkey, subkey, flags, existing_pyxll_path)

    _log.debug("Installing Excel add-in")
    _install_pyxll_addin(installed_xll_path, root_hkey, subkey, flags, install_first=install_first)

    # Unblock the file if it is blocked
    _clear_zone_identifier(installed_xll_path)

    # Try installing the certificate
    try:
        _install_certificate()
    except Exception:
        _log.warning("Unable to install the Trusted Publisher certificate.",
                     exc_info=_log.getEffectiveLevel() <= logging.DEBUG)
        _log.warning("If Excel cannot load the PyXLL add-in check your Trust Center Settings in Options in Excel.")

    _print("\n")
    _print("-" * 79)
    _print("PyXLL%s has been successfully installed in:\n%s\n" % (
        (" " + pyxll_version) if pyxll_version else "",
        pyxll_install_path))
    _print("-" * 79)

    _print("\nComplete the set up of PyXLL by updating your config file:\n" +
           os.path.join(pyxll_install_path, "pyxll.cfg") +
           "\n\nTIP: You can use the 'pyxll configure' command to open the config file and "
           "use 'pyxll status' to check where PyXLL is installed.")

    return 0

def _get_install_path(pyxll_path, download_path):
    default = None

    # If PyXLL is already installed then use that path
    if pyxll_path and os.path.exists(pyxll_path):
        default = os.path.dirname(pyxll_path)

    # Otherwise if the download path is a folder then use that
    elif os.path.exists(download_path) \
    and os.path.isdir(download_path) \
    and os.path.exists(os.path.join(download_path, "pyxll.xll")):
        default = download_path

    if not default:
        try:
            default = os.path.join(os.environ["USERPROFILE"], "AppData", "Local", "Programs", "PyXLL")
        except KeyError:
            default = None

    prompt = "Enter the path where you would like to install PyXLL"
    if default:
        prompt += "\n[%s]:\n" % default
    _print("")
    path = None
    while not path:
        path = _input(prompt, is_path=True).strip() or default
        if os.path.exists(path):
            # If the install path is the download path don't warn about overwriting anything
            if os.path.normpath(path) == os.path.normpath(download_path):
                break

            if not os.path.isdir(path):
                _print("\nThat path already exists and is not a directory. Please try again.")
                path = None
                continue

            response = None
            while response not in ("y", "n"):
                response = _input("\nThat path already exists and files may be overridden.\n"
                                  "Any existing files will be backed up.\n"
                                  "Do you want to continue (y/n)? ").strip().lower()
            if response != "y":
                raise Error("Install was cancelled.")
            break

        try:
            os.makedirs(path)
        except OSError:
            _print("\nIt was not possible to create that folder. Please try another path.")
            path = None
            continue

    return path