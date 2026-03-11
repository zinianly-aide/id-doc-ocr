from __future__ import annotations

import inspect
from pathlib import Path
from typing import Any

from id_doc_ocr.backbones.base import BackboneInfo, OCRBackboneAdapter
from id_doc_ocr.utils.runtime import module_available


class PaddleOCRVLAdapter(OCRBackboneAdapter):
    info = BackboneInfo(name="paddleocr_vl", kind="vlm", description="PaddleOCR-VL fallback/backbone adapter")

    def __init__(
        self,
        model_name: str = "PaddleOCR-VL-0.9B",
        *,
        auto_init: bool = True,
        engine: Any | None = None,
        **engine_kwargs: Any,
    ) -> None:
        self.model_name = model_name
        self.engine_kwargs = engine_kwargs
        self._engine = engine
        self._runtime_error: str | None = None
        self._runtime_module = "paddleocr"
        self._runtime_class = "unknown"
        if auto_init and self._engine is None:
            self._engine = self._build_engine()

    @classmethod
    def is_runtime_available(cls) -> bool:
        return module_available("paddleocr")

    @classmethod
    def runtime_status(cls) -> dict[str, Any]:
        return {
            "engine": cls.info.name,
            "available": cls.is_runtime_available(),
            "required_modules": ["paddleocr"],
            "recommended_extras": "pip install -e .[paddle-vl]",
        }

    def _build_engine(self) -> Any | None:
        try:
            import paddleocr  # type: ignore
        except Exception as exc:
            self._runtime_error = f"paddleocr import failed: {exc}"
            return None

        for class_name in ("PaddleOCRVL", "PaddleOCR"):
            candidate = getattr(paddleocr, class_name, None)
            if candidate is None:
                continue
            try:
                kwargs = self._filter_kwargs(candidate, self._default_init_kwargs())
                engine = candidate(**kwargs)
                self._runtime_class = class_name
                return engine
            except Exception as exc:
                self._runtime_error = f"{class_name} init failed: {exc}"
        return None

    def _default_init_kwargs(self) -> dict[str, Any]:
        defaults = {
            "model_name": self.model_name,
            "use_doc_orientation_classify": False,
            "use_doc_unwarping": False,
            "use_textline_orientation": False,
        }
        defaults.update(self.engine_kwargs)
        return defaults

    def _filter_kwargs(self, fn: Any, kwargs: dict[str, Any]) -> dict[str, Any]:
        try:
            sig = inspect.signature(fn)
        except (TypeError, ValueError):
            return kwargs
        accepted = set(sig.parameters)
        if any(p.kind == inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values()):
            return kwargs
        return {k: v for k, v in kwargs.items() if k in accepted}

    def infer(self, image: bytes | str | Path) -> dict[str, Any]:
        if self._engine is None:
            return {
                "engine": self.info.name,
                "model_name": self.model_name,
                "status": "unavailable",
                "message": "PaddleOCR-VL runtime not available. Install optional dependencies to enable real inference.",
                "runtime": self.runtime_status(),
                "error": self._runtime_error,
            }

        raw = self._invoke_engine(image)
        normalized = self._normalize_output(raw)
        normalized.update(
            {
                "engine": self.info.name,
                "model_name": self.model_name,
                "status": "ok",
                "runtime": {
                    "module": self._runtime_module,
                    "class": self._runtime_class,
                    "available": True,
                },
                "raw": raw,
            }
        )
        return normalized

    def _invoke_engine(self, image: bytes | str | Path) -> Any:
        for method_name in ("predict", "ocr"):
            method = getattr(self._engine, method_name, None)
            if callable(method):
                return method(image)
        raise RuntimeError("PaddleOCR-VL engine does not expose a supported inference method (predict/ocr).")

    def _normalize_output(self, raw: Any) -> dict[str, Any]:
        texts: list[str] = []
        layout: list[dict[str, Any]] = []
        kv_pairs: dict[str, Any] = {}
        self._walk(raw, texts, layout, kv_pairs)
        confidence_values = [float(item.get("score", 0.0)) for item in layout if isinstance(item.get("score"), (int, float))]
        confidence = sum(confidence_values) / len(confidence_values) if confidence_values else 0.0
        return {
            "text": "\n".join(x for x in texts if x).strip(),
            "layout": layout,
            "kv": kv_pairs,
            "confidence": confidence,
        }

    def _walk(self, node: Any, texts: list[str], layout: list[dict[str, Any]], kv_pairs: dict[str, Any]) -> None:
        if node is None:
            return
        if isinstance(node, str):
            value = node.strip()
            if value:
                texts.append(value)
            return
        if isinstance(node, (int, float, bool)):
            return
        if isinstance(node, dict):
            text = node.get("text") or node.get("transcription") or node.get("label")
            if isinstance(text, str) and text.strip():
                texts.append(text.strip())
                entry = {"text": text.strip()}
                for key in ("score", "bbox", "box", "type", "label"):
                    if key in node:
                        entry[key] = node[key]
                layout.append(entry)
            key = node.get("key") or node.get("field") or node.get("name")
            value = node.get("value")
            if isinstance(key, str) and value is not None and key not in {"text", "label"}:
                kv_pairs[key] = value
            for child in node.values():
                self._walk(child, texts, layout, kv_pairs)
            return
        if isinstance(node, (list, tuple, set)):
            if len(node) >= 2 and isinstance(node[1], str):
                entry: dict[str, Any] = {"text": node[1].strip()}
                texts.append(node[1].strip())
                if len(node) >= 1:
                    entry["box"] = node[0]
                if len(node) >= 3 and isinstance(node[2], (int, float)):
                    entry["score"] = float(node[2])
                layout.append(entry)
            for item in node:
                self._walk(item, texts, layout, kv_pairs)


__all__ = ["PaddleOCRVLAdapter"]
