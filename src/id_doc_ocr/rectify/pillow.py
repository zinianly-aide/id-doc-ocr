from __future__ import annotations

from io import BytesIO
from math import hypot
from pathlib import Path
from typing import Any

from id_doc_ocr.rectify.base import BaseRectifyPipeline, OrientationCorrector, PerspectiveCorrector, QualityScorer
from id_doc_ocr.rectify.contracts import OrientationDecision, PerspectiveTransform
from id_doc_ocr.schemas.types import BoundingBox, DocumentDetection, Point, QualityReport
from id_doc_ocr.utils.runtime import module_available


def _clamp_score(value: float) -> float:
    return round(min(1.0, max(0.0, value)), 3)


class PillowPerspectiveCorrector(PerspectiveCorrector):
    @classmethod
    def is_available(cls) -> bool:
        return module_available("PIL")

    def correct(
        self,
        image: bytes | str | Path,
        *,
        detection: DocumentDetection | None = None,
    ) -> tuple[bytes | str, PerspectiveTransform]:
        if not self.is_available() or detection is None:
            return image, self._passthrough_transform(detection, method="pil_passthrough")
        try:
            pil_image = self._open_image(image)
        except Exception:
            return image, self._passthrough_transform(detection, method="pil_passthrough_invalid_image")

        corners = list(detection.corners) if detection and len(detection.corners) >= 4 else self._bbox_corners(detection.bbox if detection else None)
        if len(corners) < 4:
            return image, self._passthrough_transform(detection, method="pil_passthrough_no_corners")

        ordered = self._order_points(corners[:4])
        width = max(1, int(max(hypot(ordered[1].x - ordered[0].x, ordered[1].y - ordered[0].y), hypot(ordered[2].x - ordered[3].x, ordered[2].y - ordered[3].y))))
        height = max(1, int(max(hypot(ordered[3].x - ordered[0].x, ordered[3].y - ordered[0].y), hypot(ordered[2].x - ordered[1].x, ordered[2].y - ordered[1].y))))
        data = (
            ordered[0].x, ordered[0].y,
            ordered[3].x, ordered[3].y,
            ordered[2].x, ordered[2].y,
            ordered[1].x, ordered[1].y,
        )
        from PIL import Image

        rectified = pil_image.transform((width, height), Image.Transform.QUAD, data, resample=Image.Resampling.BICUBIC)
        payload = self._encode_image(rectified)
        target_corners = [Point(x=0, y=0), Point(x=width, y=0), Point(x=width, y=height), Point(x=0, y=height)]
        return payload, PerspectiveTransform(
            source_corners=ordered,
            target_corners=target_corners,
            applied=True,
            confidence=_clamp_score((detection.confidence if detection else 0.6) * 0.95),
            method="pil_quad_transform",
        )

    def _open_image(self, image: bytes | str | Path):
        from PIL import Image, ImageOps

        opened = Image.open(BytesIO(image)) if isinstance(image, (bytes, bytearray)) else Image.open(str(image))
        return ImageOps.exif_transpose(opened).convert("RGB")

    def _encode_image(self, image) -> bytes:
        output = BytesIO()
        image.save(output, format="PNG")
        return output.getvalue()

    def _bbox_corners(self, bbox: BoundingBox | None) -> list[Point]:
        if bbox is None:
            return []
        return [
            Point(x=bbox.x1, y=bbox.y1),
            Point(x=bbox.x2, y=bbox.y1),
            Point(x=bbox.x2, y=bbox.y2),
            Point(x=bbox.x1, y=bbox.y2),
        ]

    def _order_points(self, corners: list[Point]) -> list[Point]:
        summed = sorted(corners, key=lambda point: point.x + point.y)
        diffed = sorted(corners, key=lambda point: point.y - point.x)
        top_left = summed[0]
        bottom_right = summed[-1]
        top_right = diffed[0]
        bottom_left = diffed[-1]
        return [top_left, top_right, bottom_right, bottom_left]

    def _passthrough_transform(self, detection: DocumentDetection | None, *, method: str) -> PerspectiveTransform:
        corners = list(detection.corners)[:4] if detection else []
        return PerspectiveTransform(
            source_corners=corners,
            target_corners=corners,
            applied=False,
            confidence=_clamp_score((detection.confidence if detection else 0.5) * 0.8),
            method=method,
        )


class PillowOrientationCorrector(OrientationCorrector):
    def correct(self, image: bytes | str | Path) -> tuple[bytes | str, OrientationDecision]:
        return image, OrientationDecision(angle=0, applied=False, confidence=0.96, method="pil_exif_transpose")


class PillowQualityScorer(QualityScorer):
    @classmethod
    def is_available(cls) -> bool:
        return module_available("PIL")

    def score(self, image: bytes | str | Path) -> QualityReport:
        if not self.is_available():
            return QualityReport(blur_score=0.75, glare_score=0.75, occlusion_score=0.75, shadow_score=0.75, crop_integrity_score=0.75, passed=True, reasons=[])
        try:
            pil_image = self._open_image(image)
        except Exception:
            return QualityReport(blur_score=0.4, glare_score=0.5, occlusion_score=0.5, shadow_score=0.5, crop_integrity_score=0.4, passed=False, reasons=["image_decode_failed"])

        from PIL import ImageFilter, ImageStat

        gray = pil_image.convert("L")
        stat = ImageStat.Stat(gray.filter(ImageFilter.FIND_EDGES))
        edge_mean = stat.mean[0] if stat.mean else 0.0
        histogram = gray.histogram()
        total_pixels = max(sum(histogram), 1)
        glare_fraction = sum(histogram[245:]) / total_pixels
        dark_fraction = sum(histogram[:24]) / total_pixels

        blur_score = _clamp_score(edge_mean / 42.0)
        glare_score = _clamp_score(1.0 - (glare_fraction * 4.0))
        occlusion_score = _clamp_score(1.0 - (dark_fraction * 3.0))
        shadow_score = _clamp_score(1.0 - (dark_fraction * 1.8))
        crop_integrity_score = self._crop_integrity_score(gray)
        scores = [blur_score, glare_score, occlusion_score, shadow_score, crop_integrity_score]
        passed = min(scores) >= 0.35
        reasons = []
        if blur_score < 0.45:
            reasons.append("blur_detected")
        if glare_score < 0.45:
            reasons.append("glare_detected")
        if occlusion_score < 0.45:
            reasons.append("occlusion_detected")
        if shadow_score < 0.45:
            reasons.append("shadow_detected")
        if crop_integrity_score < 0.45:
            reasons.append("crop_integrity_low")
        return QualityReport(
            blur_score=blur_score,
            glare_score=glare_score,
            occlusion_score=occlusion_score,
            shadow_score=shadow_score,
            crop_integrity_score=crop_integrity_score,
            passed=passed,
            reasons=reasons,
        )

    def _open_image(self, image: bytes | str | Path):
        from PIL import Image, ImageOps

        opened = Image.open(BytesIO(image)) if isinstance(image, (bytes, bytearray)) else Image.open(str(image))
        return ImageOps.exif_transpose(opened).convert("RGB")

    def _crop_integrity_score(self, gray) -> float:
        width, height = gray.size
        border = max(1, min(width, height) // 25)
        top = gray.crop((0, 0, width, border))
        bottom = gray.crop((0, max(height - border, 0), width, height))
        left = gray.crop((0, 0, border, height))
        right = gray.crop((max(width - border, 0), 0, width, height))
        from PIL import ImageStat

        border_mean = sum(
            ImageStat.Stat(region).mean[0]
            for region in (top, bottom, left, right)
        ) / 4.0
        return _clamp_score(border_mean / 220.0)


class PillowRectifyPipeline(BaseRectifyPipeline):
    @classmethod
    def is_available(cls) -> bool:
        return PillowPerspectiveCorrector.is_available() and PillowQualityScorer.is_available()

    @classmethod
    def availability_details(cls) -> dict[str, Any]:
        available = cls.is_available()
        return {
            "available": available,
            "package": "Pillow",
            "reason": None if available else "module_spec_not_found",
        }

    def __init__(self) -> None:
        super().__init__(
            perspective_corrector=PillowPerspectiveCorrector(),
            orientation_corrector=PillowOrientationCorrector(),
            quality_scorer=PillowQualityScorer(),
        )