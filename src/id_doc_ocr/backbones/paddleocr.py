from __future__ import annotations

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
        return PaddleOCR(**self.config)

    def infer(self, image: bytes | str | Path) -> dict[str, Any]:
        normalized_image = self.normalize_image_input(image)
        raw_result = self._engine.ocr(normalized_image, cls=bool(self.config.get("cls", True)))
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
