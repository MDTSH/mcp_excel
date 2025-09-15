"""
Copyright (c) 2009-2012, All Rights Reserved, http://www.pyxll.com/

THIS CODE AND INFORMATION ARE PROVIDED "AS IS" WITHOUT WARRANTY OF ANY
KIND, EITHER EXPRESSED OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND/OR FITNESS FOR A
PARTICULAR PURPOSE.
"""
from ._cli import Error, Help
from ._utils import (
    _find_and_check_excel,
    _get_dll_bitness,
    _get_exe_bitness,
    _get_xll_version_info,
    _get_xll_file_version,
    _find_pyxll_config,
    _find_pyxll_addin,
    _load_config_file
)
import logging
import sys
import os

if sys.version_info[0] > 2:
    from configparser import RawConfigParser
else:
    from configparser import RawConfigParser

_log = logging.getLogger(__name__)

def _check_pyxll_config(cfg_path):
    """Check common errors in pyxll.cfg"""

    def _load_config(cfg_path, seen=None):
        """Loads config values including those in external configs."""
        seen = seen or {}
        seen[cfg_path] = None

        cfg = _load_config_file(cfg_path)

        values = {}
        if cfg.has_option("PYTHON", "executable"):
            values["executable"] = cfg.get("PYTHON", "executable")

        if cfg.has_option("PYTHON", "pythonhome"):
            values["pythonhome"] = cfg.get("PYTHON", "pythonhome")

        if cfg.has_option("PYTHON", "dll"):
            values["dll"] = cfg.get("PYTHON", "dll")

        external_configs = []
        external_config = os.environ.get("PYXLL_EXTERNAL_CONFIG_FILE", None)
        if external_config:
            external_configs.extend(external_config.splitlines())

        for external_config in external_configs:
            if not external_config or external_config in seen:
                continue

            _log.debug("Found external config file '%s'" % external_config)
            if not os.path.exists(external_config) \
            and not os.path.exists(os.path.join(os.path.dirname(cfg_path), external_config)):
                raise Error(("The 'external_config' specified does not exist\n\n" +
                             ("The external config file '%s' was not found." % external_config) + "\n\n"
                              "Check your config file, which is located here:\n" +
                              cfg_path + "\n\n"
                              "Or use the following command to open your config file:\n\n"
                              "pyxll configure"))

            ext_values = _load_config(external_config, seen)
            values.update(ext_values)

        return values

    values = _load_config(cfg_path)

    executable = values.get("executable")
    if not executable:
        raise Error(("The 'executable' option is missing from the PyXLL config file.\n\n"
                     "PyXLL should be configured by setting 'executable' in the PYTHON "
                     "section of the config file.\n\n"
                     "Edit your config file and set\n\n"
                     "[PYTHON]\n"
                     "executable = " + sys.executable + "\n\n"
                     "Your config file is located here:\n" +
                     cfg_path + "\n\n"
                     "Or use the following command to open your config file:\n\n"
                     "pyxll configure"))

    dirname = os.path.dirname(executable)
    basename = os.path.basename(executable)
    if basename.lower() not in ("python.exe", "pythonw.exe", "python", "pythonw"):
        raise Error(("The 'executable' option is set incorrectly in your PyXLL config file.\n\n"
                     "PyXLL should be configured by setting 'executable' in the "
                     "PYTHON section of the config file.\n\n"
                     "Edit your config file and set\n\n"
                     "[PYTHON]\n"
                     "executable = " + sys.executable + "\n\n"
                     "Your config file is located here:\n" +
                     cfg_path + "\n\n"
                     "You can use the following command to open your config file:\n\n"
                     "pyxll configure"))

    dirname = os.path.realpath(dirname).lower()
    py_dirname = os.path.realpath(os.path.dirname(sys.executable)).lower()
    if dirname != py_dirname:
        raise Error(("The 'executable' option is set to a different Python environment\n"
                     "than the current Python environment.\n\n"
                     "Edit your config file and set\n\n"
                     "[PYTHON]\n"
                     "executable = " + sys.executable + "\n\n"
                     "Your config file is located here:\n" +
                     cfg_path + "\n\n"
                     "You can use the following command to open your config file:\n\n"
                     "pyxll configure"))

    _log.debug("executable is set to '%s'." % executable)

    pythonhome = values.get("pythonhome")
    if pythonhome:
        raise Error(("We do not recommend setting the 'pythonhome' option.\n\n"
                     "Setting the 'executable' option in your config file should be sufficient.\n\n"
                     "Edit your config file and remove the 'pythonhome' setting "
                     "from the PYTHON section.\n\n"
                     "Your config file is located here:\n" +
                     cfg_path + "\n\n"
                     "Or use the following command to open your config file:\n\n"
                     "pyxll configure"))

    dll = values.get("dll")
    if dll:
        raise Error(("We do not recommend setting the 'dll' option.\n\n"
                     "Setting the 'executable' option in your config file should be sufficient.\n\n"
                     "Edit your config file and remove the 'dll' setting\n"
                     "from the PYTHON section.\n\n"
                     "Your config file is located here:\n" +
                     cfg_path + "\n\n"
                                "Or use the following command to open your config file:\n\n"
                                "pyxll configure"))

    return True

def check(*args):
    if args:
        raise Help("Unexpected arguments '%s' to command 'check'." % ", ".join(args))

    # Check Excel is installed and exists
    excel_exe, excel_bits, xl_version_info = _find_and_check_excel()
    excel_version, hkey_root, excel_subkey, flags = xl_version_info

    # Look to see if PyXLL is installed and check the file exists
    pyxll_path = _find_pyxll_addin(hkey_root, excel_subkey, flags)
    if not pyxll_path:
        raise Error(("PyXLL is not installed.\n\n"
                     "You can install PyXLL by running:\n\n"
                     "pyxll install\n\n"
                     "or see the PyXLL website https://www.pyxll.com for installation instructions"))

    _log.debug("Found PyXLL add-in '%s'." % pyxll_path)
    if not os.path.exists(pyxll_path):
        raise Error(("PyXLL was installed but the add-in file no longer exists.\n\n"
                     "The missing PyXLL add-in path is:\n" +
                     pyxll_path + "\n\n"
                     "You can re-install PyXLL by running:\n\n"
                     "pyxll install\n\n"
                     "or see the PyXLL website https://www.pyxll.com for installation instructions."))

    if not os.path.isabs(pyxll_path):
        raise Error(("PyXLL was installed but the path is incorrect.\n\n"
                     "The incorrect PyXLL add-in path is:\n" +
                     pyxll_path + "\n\n"
                                  "You can re-install PyXLL by running:\n\n"
                                  "pyxll install\n\n"
                                  "or see the PyXLL website https://www.pyxll.com for installation instructions."))

    # Check the installed version of PyXLL is the correct bitness
    pyxll_bits = _get_dll_bitness(pyxll_path)
    python_bits = _get_exe_bitness(sys.executable)
    if pyxll_bits != python_bits:
        raise Error(("Excel is Python are %(excel_bits)s but the installed PyXLL add-in is %(pyxll_bits)s.\n\n"
                     "You should download the %(excel_bits)s version of PyXLL and install that, or "
                     "you can use the following command to re-install PyXLL:\n\n"
                     "pyxll install\n\n"
                     "See the PyXLL website https://www.pyxll.com for detailed installation instructions.")
                    % {"excel_bits": excel_bits, "python_bits": python_bits, "pyxll_bits": pyxll_bits})

    _log.debug("The installed PyXLL add-in is %s." % pyxll_bits)

    # Check the PyXLL version matches our Python version
    version_info = _get_xll_version_info(pyxll_path)
    pyxll_version = _get_xll_file_version(pyxll_path)

    # Older PyXLL add-ins do not have version information we can extract
    if version_info is not None:
        name, pyxll_version, py_version = version_info
        if py_version != "py%d%d" % sys.version_info[:2]:
            raise Error(("The installed PyXLL add-in is for a different version of Python.\n\n"
                         "The PyXLL add-in found is for Python %(pyxll_py_version)s but the actual Python "
                         "interpreter in use is Python %(py_version)s.\n\n" +
                         "You will need to download the correct version of PyXLL, or change the version "
                         "of Python you are using.\n\n"
                         "You can re-install PyXLL by running:\n\n"
                         "pyxll install\n\n"
                         "or see the PyXLL website https://www.pyxll.com for installation instructions.") % {
                            "py_version": "%d.%d" % sys.version_info[:2],
                            "pyxll_py_version": "%s.%s" % (py_version[2:3], py_version[3:])})

    pyxll_cfg = _find_pyxll_config(pyxll_path)
    if not pyxll_cfg or not os.path.exists(pyxll_cfg):
        raise Error(("The PyXLL config file is missing.\n\n"
                     "The config file should be located here:\n" +
                     pyxll_cfg + "\n\n"
                     "You can re-install PyXLL by running:\n\n"
                     "pyxll install\n\n"
                     "or see the PyXLL website https://www.pyxll.com for installation instructions."))

    _log.debug("The PyXLL config file was found: '%s'." % pyxll_cfg)

    # Do some checks for common errors in the config
    _check_pyxll_config(pyxll_cfg)

    message = [
        "PyXLL appears to be installed correctly.\n\n"
    ]

    if pyxll_version:
        message += [
            "- The installed PyXLL version is '%s'.\n\n" % pyxll_version
        ]

    message += [
        "- The PyXLL add-in is located here:\n  ",
        pyxll_path + "\n\n",
        "- The PyXLL config file is located here:\n  ",
        pyxll_cfg + "\n\n",
        "- Excel and Python are both " + excel_bits + ".\n\n",
        "If you need additional help please contact support@pyxll.com."
    ]

    print(("".join(message)))
    return 0