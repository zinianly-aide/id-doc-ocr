from __future__ import annotations

from importlib.util import find_spec


def module_available(module_name: str) -> bool:
    try:
        return find_spec(module_name) is not None
    except Exception:
        return False
