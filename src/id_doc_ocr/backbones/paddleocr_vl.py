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

        errors: list[str] = []
        for class_name in ("PaddleOCRVL", "PaddleOCR"):
            candidate = getattr(paddleocr, class_name, None)
            if candidate is None:
                continue
            try:
                kwargs = self._filter_kwargs(candidate, self._default_init_kwargs(class_name))
                engine = candidate(**kwargs)
                self._runtime_class = class_name
                self._runtime_error = None
                return engine
            except Exception as exc:
                errors.append(f"{class_name} init failed: {exc}")

        if errors:
            self._runtime_error = " | ".join(errors)
        return None

    def _default_init_kwargs(self, runtime_class: str) -> dict[str, Any]:
        defaults = {
            "use_doc_orientation_classify": False,
            "use_doc_unwarping": False,
            "use_textline_orientation": False,
        }
        if runtime_class == "PaddleOCRVL":
            defaults["model_name"] = self.model_name
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
        normalized_image = str(image) if isinstance(image, Path) else image
        for method_name in ("predict", "ocr"):
            method = getattr(self._engine, method_name, None)
            if callable(method):
                return method(normalized_image)
        raise RuntimeError("PaddleOCR-VL engine does not expose a supported inference method (predict/ocr).")

    def _normalize_output(self, raw: Any) -> dict[str, Any]:
        texts: list[str] = []
        layout: list[dict[str, Any]] = []
        kv_pairs: dict[str, Any] = {}
        self._walk(raw, texts, layout, kv_pairs)
        deduped_texts: list[str] = []
        seen_texts: set[str] = set()
        for text in texts:
            normalized = self.normalize_text(text)
            if not normalized or normalized in seen_texts:
                continue
            seen_texts.add(normalized)
            deduped_texts.append(normalized)

        confidence = self.average_confidence(layout)
        return {
            "text": "\n".join(deduped_texts).strip(),
            "layout": layout,
            "kv": kv_pairs,
            "confidence": confidence,
        }

    def _walk(self, node: Any, texts: list[str], layout: list[dict[str, Any]], kv_pairs: dict[str, Any]) -> None:
        if node is None:
            return
        if isinstance(node, str):
            value = self.normalize_text(node)
            if value:
                texts.append(value)
            return
        if isinstance(node, (int, float, bool)):
            return
        if isinstance(node, dict):
            text = self.normalize_text(node.get("text") or node.get("transcription") or node.get("label"))
            if text:
                texts.append(text)
                entry = {"text": text}
                for key in ("bbox", "box", "type", "label"):
                    if key in node:
                        entry[key] = node[key]
                if "score" in node:
                    entry["score"] = self.normalize_score(node.get("score"))
                layout.append(entry)
            key = node.get("key") or node.get("field") or node.get("name")
            value = node.get("value")
            if isinstance(key, str) and value is not None and key not in {"text", "label"}:
                kv_pairs[key] = value
            for child_key, child in node.items():
                if child_key in {"text", "transcription", "label", "score", "bbox", "box", "type"}:
                    continue
                self._walk(child, texts, layout, kv_pairs)
            return
        if isinstance(node, (list, tuple, set)):
            if len(node) >= 2 and isinstance(node[1], str):
                text = self.normalize_text(node[1])
                if text:
                    entry: dict[str, Any] = {"text": text}
                    texts.append(text)
                    if len(node) >= 1:
                        entry["box"] = node[0]
                    if len(node) >= 3:
                        entry["score"] = self.normalize_score(node[2])
                    layout.append(entry)
                return
            for item in node:
                self._walk(item, texts, layout, kv_pairs)


__all__ = ["PaddleOCRVLAdapter"]
