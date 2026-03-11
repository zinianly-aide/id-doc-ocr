from __future__ import annotations

from pathlib import Path
from typing import Any

from id_doc_ocr.backbones.base import BackboneInfo, OCRBackboneAdapter


class RapidOCRAdapter(OCRBackboneAdapter):
    info = BackboneInfo(name="rapidocr", kind="ocr", description="RapidOCR ONNXRuntime adapter")

    def __init__(self) -> None:
        try:
            from rapidocr_onnxruntime import RapidOCR  # type: ignore
        except Exception as e:  # pragma: no cover
            raise RuntimeError(
                "rapidocr_onnxruntime is not installed. Install extras or use the project venv."
            ) from e
        self._engine = RapidOCR()

    def infer(self, image: bytes | str | Path) -> dict[str, Any]:
        result, _ = self._engine(image)
        lines: list[dict[str, Any]] = []
        full_text: list[str] = []
        for item in result or []:
            box, text, score = item
            lines.append({"box": box, "text": text, "score": float(score)})
            full_text.append(text)
        avg_score = sum(x["score"] for x in lines) / len(lines) if lines else 0.0
        return {
            "engine": self.info.name,
            "text": "\n".join(full_text),
            "lines": lines,
            "confidence": avg_score,
        }
