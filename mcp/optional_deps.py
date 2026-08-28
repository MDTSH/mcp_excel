# -*- coding: utf-8 -*-
"""Lazy loaders for numpy / pandas / requests.

Importing this module must not import those packages. Attribute access
or require() raises a bilingual error when a concrete function needs them.
"""

from __future__ import annotations

import importlib
import math


class MissingOptionalDependency(ImportError):
    """Raised when a UDF first needs a package that is not installed."""

    def __init__(self, package: str, feature: str | None = None) -> None:
        extra_zh = f"（当前函数：{feature}）" if feature else ""
        extra_en = f" (function: {feature})" if feature else ""
        super().__init__(
            f"缺少计算库 {package}{extra_zh}，此函数暂不可用。\n"
            f"请在该 Excel 使用的 Python 中运行: python -m pip install {package}\n"
            f"Missing package '{package}'{extra_en}. This function cannot run.\n"
            f"Install with: python -m pip install {package}"
        )
        self.package = package
        self.feature = feature


def require(name: str, feature: str | None = None):
    try:
        return importlib.import_module(name)
    except ImportError as exc:
        raise MissingOptionalDependency(name, feature) from exc


class LazyModule:
    """Stand-in for `import numpy as np`. Loads on first attribute access."""

    def __init__(self, name: str) -> None:
        object.__setattr__(self, "_name", name)
        object.__setattr__(self, "_mod", None)

    def _load(self, feature: str | None = None):
        mod = object.__getattribute__(self, "_mod")
        if mod is None:
            mod = require(object.__getattribute__(self, "_name"), feature)
            object.__setattr__(self, "_mod", mod)
        return mod

    def __getattr__(self, item: str):
        return getattr(self._load(), item)

    def __setattr__(self, key: str, value) -> None:
        if key in ("_name", "_mod"):
            object.__setattr__(self, key, value)
            return
        setattr(self._load(), key, value)


pandas = LazyModule("pandas")
numpy = LazyModule("numpy")
requests = LazyModule("requests")


def is_ndarray(val) -> bool:
    """True if val is a numpy array, without importing numpy for other types."""
    cls = type(val)
    return cls.__name__ == "ndarray" and getattr(cls, "__module__", "").startswith("numpy")


def is_dataframe(val) -> bool:
    cls = type(val)
    return cls.__name__ == "DataFrame" and getattr(cls, "__module__", "").startswith("pandas")


def is_timestamp(val) -> bool:
    cls = type(val)
    return cls.__name__ == "Timestamp" and getattr(cls, "__module__", "").startswith("pandas")


def is_na(val) -> bool:
    if val is None:
        return True
    if isinstance(val, float) and math.isnan(val):
        return True
    if type(val).__name__ in ("NaTType", "NaT"):
        return True
    if is_timestamp(val):
        return bool(require("pandas").isna(val))
    return False
