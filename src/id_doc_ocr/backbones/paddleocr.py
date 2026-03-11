from __future__ import annotations

import inspect
import os
from pathlib import Path
from typing import Any

from id_doc_ocr.backbones.base import BackboneInfo, OCRBackboneAdapter


class PaddleOCRAdapter(OCRBackboneAdapter):
    info = BackboneInfo(name="paddleocr", kind="ocr", description="PaddleOCR backbone adapter")

    def __init__(
        self,
        lang: str | None = None,
        use_angle_cls: bool | None = None,
        enable_mkldnn: bool | None = None,
        det: bool = True,
        rec: bool = True,
        cls: bool | None = None,
        **kwargs: Any,
    ) -> None:
        self.lang = lang or os.getenv("ID_DOC_OCR_PADDLE_LANG", "ch")
        if use_angle_cls is None:
            use_angle_cls = os.getenv("ID_DOC_OCR_PADDLE_USE_ANGLE_CLS", "1") not in {"0", "false", "False"}
        if enable_mkldnn is None:
            enable_mkldnn = os.getenv("ID_DOC_OCR_PADDLE_ENABLE_MKLDNN", "0") in {"1", "true", "True"}
        if cls is None:
            cls = use_angle_cls
        self.config = {
            "use_angle_cls": use_angle_cls,
            "lang": self.lang,
            "enable_mkldnn": enable_mkldnn,
            "det": det,
            "rec": rec,
            "cls": cls,
            **kwargs,
        }
        self._engine = self._create_engine()

    @classmethod
    def is_available(cls) -> bool:
        try:
            from paddleocr import PaddleOCR as _PaddleOCR  # type: ignore
        except Exception:
            return False
        return _PaddleOCR is not None

    @classmethod
    def availability_details(cls) -> dict[str, Any]:
        details: dict[str, Any] = {
            "available": False,
            "package": "paddleocr",
            "env": {
                "ID_DOC_OCR_PADDLE_LANG": os.getenv("ID_DOC_OCR_PADDLE_LANG"),
                "ID_DOC_OCR_PADDLE_USE_ANGLE_CLS": os.getenv("ID_DOC_OCR_PADDLE_USE_ANGLE_CLS"),
                "ID_DOC_OCR_PADDLE_ENABLE_MKLDNN": os.getenv("ID_DOC_OCR_PADDLE_ENABLE_MKLDNN"),
            },
        }
        try:
            import paddleocr  # type: ignore
        except Exception as exc:
            details["reason"] = f"import_failed: {exc}"
            return details
        details["available"] = True
        details["version"] = getattr(paddleocr, "__version__", "unknown")
        return details

    def _create_engine(self) -> Any:
        try:
            from paddleocr import PaddleOCR  # type: ignore
        except Exception as exc:  # pragma: no cover
            raise RuntimeError(
                "paddleocr is not installed. See docs/paddleocr-setup.md for local setup instructions."
            ) from exc

        engine_config = dict(self.config)
        try:
            signature = inspect.signature(PaddleOCR.__init__)
        except (TypeError, ValueError):
            signature = None

        if signature is not None:
            supported = set(signature.parameters)
            if "use_angle_cls" not in supported:
                legacy_angle = bool(engine_config.pop("use_angle_cls", engine_config.get("cls", True)))
                if "use_textline_orientation" in supported and "use_textline_orientation" not in engine_config:
                    engine_config["use_textline_orientation"] = legacy_angle
                if "use_doc_orientation_classify" in supported and "use_doc_orientation_classify" not in engine_config:
                    engine_config["use_doc_orientation_classify"] = legacy_angle
                if "cls" not in supported:
                    engine_config.pop("cls", None)
            for key in ("det", "rec", "enable_mkldnn"):
                if key not in supported:
                    engine_config.pop(key, None)

        return PaddleOCR(**engine_config)

    def infer(self, image: bytes | str | Path) -> dict[str, Any]:
        normalized_image = self.normalize_image_input(image)
        ocr_kwargs: dict[str, Any] = {}
        try:
            ocr_signature = inspect.signature(self._engine.ocr)
        except (TypeError, ValueError, AttributeError):
            ocr_signature = None
        if ocr_signature is None or "cls" in ocr_signature.parameters:
            ocr_kwargs["cls"] = bool(self.config.get("cls", True))
        raw_result = self._engine.ocr(normalized_image, **ocr_kwargs)
        lines = self._normalize_lines(raw_result)
        avg_score = sum(x["score"] for x in lines) / len(lines) if lines else 0.0
        return {
            "engine": self.info.name,
            "text": "\n".join(x["text"] for x in lines),
            "lines": lines,
            "confidence": avg_score,
            "model_name": "PP-OCR",
            "config": dict(self.config),
            "availability": self.availability_details(),
        }

    def _normalize_lines(self, raw_result: Any) -> list[dict[str, Any]]:
        if raw_result is None:
            return []

        if isinstance(raw_result, list) and raw_result and isinstance(raw_result[0], dict):
            merged: list[dict[str, Any]] = []
            for page in raw_result:
                texts = page.get("rec_texts") or []
                scores = page.get("rec_scores") or []
                boxes = page.get("dt_polys") or page.get("rec_polys") or []
                for idx, text in enumerate(texts):
                    score = 0.0
                    if idx < len(scores):
                        try:
                            score = float(scores[idx])
                        except (TypeError, ValueError):
                            score = 0.0
                    box = boxes[idx].tolist() if idx < len(boxes) and hasattr(boxes[idx], "tolist") else (boxes[idx] if idx < len(boxes) else None)
                    merged.append({"box": box, "text": str(text), "score": score})
            return merged

        candidates = raw_result
        if isinstance(raw_result, list) and len(raw_result) == 1 and isinstance(raw_result[0], list):
            candidates = raw_result[0]

        lines: list[dict[str, Any]] = []
        for item in candidates or []:
            line = self._normalize_line(item)
            if line is not None:
                lines.append(line)
        return lines

    def _normalize_line(self, item: Any) -> dict[str, Any] | None:
        if not isinstance(item, (list, tuple)) or len(item) < 2:
            return None
        box = item[0]
        payload = item[1]
        text = ""
        score = 0.0
        if isinstance(payload, (list, tuple)) and payload:
            text = str(payload[0])
            if len(payload) > 1:
                try:
                    score = float(payload[1])
                except (TypeError, ValueError):
                    score = 0.0
        elif isinstance(payload, str):
            text = payload
        return {"box": box, "text": text, "score": score}
