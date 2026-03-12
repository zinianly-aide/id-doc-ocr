from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _json_safe(value: Any) -> Any:
    if isinstance(value, bytes):
        return {"type": "bytes", "size": len(value)}
    if isinstance(value, Path):
        return str(value)
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def write_failure_case(out_dir: str | Path, payload: dict[str, Any], name: str) -> Path:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"{name}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=_json_safe))
    return path
