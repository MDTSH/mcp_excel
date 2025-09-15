"""
Copyright (c) 2009-2012, All Rights Reserved, http://www.pyxll.com/

THIS CODE AND INFORMATION ARE PROVIDED "AS IS" WITHOUT WARRANTY OF ANY
KIND, EITHER EXPRESSED OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND/OR FITNESS FOR A
PARTICULAR PURPOSE.
"""
import sys

# Don't even try and import anything unless we're on Windows
if sys.platform != "win32":
    print("ERROR: PyXLL is only available for Microsoft Windows.")
    sys.exit(1)

from . import __version__
from ._errors import Error, Help
from ._utils import (
    _print,
    _get_latest_pyxll_version,
    _compare_pyxll_versions,
    _input,
    _set_non_interactive,
    _is_non_interactive,
    _set_forced
)
import logging
import sys

_log = logging.getLogger(__name__)

def print_help(msg=None):
    if msg:
        print((">>>> " + msg + """ <<<<
"""))

    _print("""PyXLL command line utility.

Available commands:
    - install [--version={pyxll-version}] [--install-first] [pyxll-zip-file]
    - update [--version={pyxll-version}] [pyxll-zip-file]
    - activate [--install-first] [folder]
    - install-certificate
    - uninstall  [--dry-run/-n] [--force/-f]
    - configure
    - status
 
General options:
    --debug or -d to enable debug logging
    --non-interactive or -ni to not prompt the user for input
    --force to force changes to Excel options even if Excel is running
 
Example usage:
>> pyxll install

See https://www.pyxll.com for more details about PyXLL.
""")

def main():
    if sys.version_info[:2] < (2, 5):
        print("""The PyXLL command line tool requires Python >= 2.5.""")
        return 1

    args = []
    log_level = logging.INFO
    for arg in sys.argv[1:]:
        if arg == "--debug" or arg == "-d":
            log_level = logging.DEBUG
            continue
        if arg == "--non-interactive" or arg == "-ni":
            _set_non_interactive(True)
            continue
        if arg == "--force" or arg == "-f":
            _set_forced(True)
            continue
        args.append(arg)

    logging.basicConfig(level=log_level)

    if len(args) < 1:
        print_help()
        return 1

    def check_latest():
        if _is_non_interactive():
            return

        try:
            latest_version = _get_latest_pyxll_version()
        except Exception:
            _log.debug("Unable to get latest PyXLL version", exc_info=True)
            return

        if _compare_pyxll_versions(latest_version, __version__) > 0:
            _print("\nYou are using an out of date version of this tool (%s)." % __version__)
            _print("A newer version %s is available to install." % latest_version)
            response = None
            while response not in ("y", "n"):
                response = _input("Do you want to install the new version now ([y]/n)? ").lower()
                if not response:
                    response = "y"

            if response == "y":
                _print("\nTo install the latest version run the following command:")
                _print("pip install --upgrade pyxll")
                _print("Followed by 'pyxll install' or 'pyxll update'.")
                sys.exit(1)

    try:
        cmd = args[0]
        if cmd == "install":
            from . import _install
            check_latest()
            return _install.install(*args[1:])

        elif cmd in ("update", "upgrade"):
            from . import _update
            check_latest()
            return _update.update(*args[1:])

        elif cmd == "activate":
            from . import _activate
            check_latest()
            return _activate.activate(*args[1:])

        elif cmd == "uninstall":
            from . import _uninstall
            return _uninstall.uninstall(*args[1:])

        elif cmd in ("configure", "config"):
            from . import _config
            check_latest()
            return _config.configure(*args[1:])

        elif cmd in ("check", "status"):
            from . import _check
            check_latest()
            return _check.check(*args[1:])

        elif cmd == "install-certificate":
            from . import _cert
            if _cert._install_certificate(*args[1:]):
                print("PyXLL certificate added to Trusted Publishers certificate store.")
            return 0

        else:
            print_help("Unrecognized command '%s'." % cmd)
            return 1
    except Error:
        exc_type, exc_value, exc_tb = sys.exc_info()
        _print(("\nERROR: " + str(exc_value).strip() +
                "\n\nIf you need additional help please contact support@pyxll.com"))
        return 1
    except Help:
        exc_type, exc_value, exc_tb = sys.exc_info()
        print_help(str(exc_value))
        return 1

    return 1

if __name__ == "__main__":
    sys.exit(main())