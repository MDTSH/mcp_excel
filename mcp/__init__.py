import importlib.util
import os
import sys

# Compiled extension lives under lib\\X64 as ABI-tagged pyds:
#   _mcp.cp39-win_amd64.pyd ... _mcp.cp313-win_amd64.pyd
_current_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(_current_dir)
_lib_x64_dir = os.path.join(_project_root, "lib", "X64")
_SUPPORTED_TAGS = ("cp39", "cp310", "cp311", "cp312", "cp313")


def _abi_tag():
    return "cp%d%d" % (sys.version_info.major, sys.version_info.minor)


def _available_pyds():
    if not os.path.isdir(_lib_x64_dir):
        return []
    names = []
    for name in os.listdir(_lib_x64_dir):
        lower = name.lower()
        if lower.startswith("_mcp") and lower.endswith(".pyd"):
            names.append(name)
    return sorted(names)


def _candidate_paths():
    tag = _abi_tag()
    tagged = os.path.join(_lib_x64_dir, "_mcp.%s-win_amd64.pyd" % tag)
    if os.path.isfile(tagged):
        return [tagged]
    return []


def _load_extension():
    if "mcp._mcp" in sys.modules:
        return sys.modules["mcp._mcp"]

    if os.path.isdir(_lib_x64_dir):
        os.environ["PATH"] = _lib_x64_dir + os.pathsep + os.environ.get("PATH", "")
        if hasattr(os, "add_dll_directory"):
            os.add_dll_directory(_lib_x64_dir)
        if _lib_x64_dir not in sys.path:
            sys.path.insert(0, _lib_x64_dir)
        if _lib_x64_dir not in __path__:
            __path__.append(_lib_x64_dir)

    candidates = _candidate_paths()
    if not candidates:
        tag = _abi_tag()
        available = _available_pyds()
        supported = ", ".join(_SUPPORTED_TAGS)
        have = ", ".join(available) if available else "(none)"
        raise ImportError(
            "MCP Excel has no _mcp extension for this Python (%s, %s).\n"
            "Supported: 64-bit CPython %s.\n"
            "Found in lib\\X64: %s"
            % (sys.version.split()[0], tag, supported, have)
        )

    last_error = None
    for path in candidates:
        spec = importlib.util.spec_from_file_location("mcp._mcp", path)
        if spec is None or spec.loader is None:
            continue
        module = importlib.util.module_from_spec(spec)
        sys.modules["mcp._mcp"] = module
        sys.modules["_mcp"] = module
        try:
            spec.loader.exec_module(module)
            return module
        except Exception as exc:
            last_error = exc
            sys.modules.pop("mcp._mcp", None)
            sys.modules.pop("_mcp", None)

    raise ImportError(
        "Failed to load %s: %s" % (candidates[0], last_error)
    )


_mcp = _load_extension()
