from __future__ import annotations

import logging
import os
import platform
import sys
import time
from dataclasses import asdict, dataclass
from typing import Any

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from id_doc_ocr import __version__, plugins as _plugins  # noqa: F401
from id_doc_ocr.backbones.got_ocr import GOTOCRAdapter
from id_doc_ocr.backbones.mock import MockPaddleOCRAdapter, MockPaddleOCRVLAdapter
from id_doc_ocr.backbones.paddleocr import PaddleOCRAdapter
from id_doc_ocr.backbones.paddleocr_vl import PaddleOCRVLAdapter
from id_doc_ocr.backbones.rapidocr import RapidOCRAdapter
from id_doc_ocr.core.registry import registry
from id_doc_ocr.pipeline.runner import BackendSelectionError, DemoPipelineRunner
from id_doc_ocr.tools.plugin_inventory import build_plugin_inventory

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class ServiceSettings:
    service_name: str = "id-doc-ocr"
    service_version: str = __version__
    default_failure_dir: str | None = None
    default_ocr_backend: str = "paddleocr"
    default_vlm_backend: str = "mock"
    default_detector_backend: str = "pil"
    default_rectify_backend: str = "pil"

    @classmethod
    def from_env(cls) -> "ServiceSettings":
        return cls(
            service_name=os.getenv("ID_DOC_OCR_SERVICE_NAME", "id-doc-ocr"),
            service_version=os.getenv("ID_DOC_OCR_SERVICE_VERSION", __version__),
            default_failure_dir=os.getenv("ID_DOC_OCR_FAILURE_DIR") or None,
            default_ocr_backend=os.getenv("ID_DOC_OCR_DEFAULT_OCR_BACKEND", "paddleocr"),
            default_vlm_backend=os.getenv("ID_DOC_OCR_DEFAULT_VLM_BACKEND", "mock"),
            default_detector_backend=os.getenv("ID_DOC_OCR_DEFAULT_DETECTOR_BACKEND", "pil"),
            default_rectify_backend=os.getenv("ID_DOC_OCR_DEFAULT_RECTIFY_BACKEND", "pil"),
        )


BACKBONE_SPECS = {
    "ocr": [MockPaddleOCRAdapter, RapidOCRAdapter, PaddleOCRAdapter, GOTOCRAdapter],
    "vlm": [PaddleOCRVLAdapter, MockPaddleOCRVLAdapter],
}


def _runtime_info() -> dict[str, Any]:
    return {
        "python": {
            "version": platform.python_version(),
            "implementation": platform.python_implementation(),
            "executable": sys.executable,
        },
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
        },
    }


def _build_plugin_inventory() -> list[dict[str, Any]]:
    return build_plugin_inventory()


def _build_backbone_inventory() -> dict[str, list[dict[str, Any]]]:
    backbones: dict[str, list[dict[str, Any]]] = {}
    for kind, classes in BACKBONE_SPECS.items():
        backbones[kind] = []
        for backbone_cls in classes:
            info = getattr(backbone_cls, "info", None)
            availability_fn = getattr(backbone_cls, "availability_details", None)
            if callable(availability_fn):
                availability = availability_fn()
            else:
                availability = {"available": bool(getattr(backbone_cls, "is_available", lambda: True)())}
            backbones[kind].append(
                {
                    "name": info.name if info else backbone_cls.__name__,
                    "kind": info.kind if info else kind,
                    "description": info.description if info else "",
                    "available": bool(availability.get("available", False)),
                    "availability": availability,
                }
            )
    return backbones


def _build_availability_totals(items_by_kind: dict[str, list[dict[str, Any]]]) -> tuple[dict[str, dict[str, int]], int, int]:
    totals_by_kind: dict[str, dict[str, int]] = {}
    available_total = 0
    total = 0
    for kind, items in items_by_kind.items():
        kind_total = len(items)
        kind_available = sum(1 for item in items if item["available"])
        totals_by_kind[kind] = {
            "total": kind_total,
            "available": kind_available,
            "unavailable": kind_total - kind_available,
        }
        available_total += kind_available
        total += kind_total
    return totals_by_kind, total, available_total


def _build_summary(
    plugins: list[dict[str, Any]],
    backbones: dict[str, list[dict[str, Any]]],
    detectors: dict[str, list[dict[str, Any]]],
    rectify: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    backbone_totals, backbone_total, available_backbone_total = _build_availability_totals(backbones)
    detector_totals, detector_total, available_detector_total = _build_availability_totals(detectors)
    rectify_totals, rectify_total, available_rectify_total = _build_availability_totals(rectify)
    return {
        "plugin_count": len(plugins),
        "backbone_count": backbone_total,
        "available_backbone_count": available_backbone_total,
        "detector_count": detector_total,
        "available_detector_count": available_detector_total,
        "rectify_count": rectify_total,
        "available_rectify_count": available_rectify_total,
        "backbones": backbone_totals,
        "detectors": detector_totals,
        "rectify": rectify_totals,
    }


def build_capabilities(settings: ServiceSettings) -> dict[str, Any]:
    plugins = _build_plugin_inventory()
    backbones = _build_backbone_inventory()
    stage_inventory = DemoPipelineRunner.build_stage_inventory()
    detectors = {"detector": stage_inventory["detector"]}
    rectify = {"rectify": stage_inventory["rectify"]}
    summary = _build_summary(plugins, backbones, detectors, rectify)
    return {
        "ok": True,
        "service": asdict(settings),
        "runtime": _runtime_info(),
        "summary": summary,
        "availability": {
            "plugins": {"total": len(plugins)},
            "backbones": summary["backbones"],
            "detectors": summary["detectors"],
            "rectify": summary["rectify"],
        },
        "plugins": plugins,
        "backbones": backbones,
        "detectors": detectors,
        "rectify": rectify,
    }


def create_app(settings: ServiceSettings | None = None) -> FastAPI:
    service_settings = settings or ServiceSettings.from_env()
    app = FastAPI(title=service_settings.service_name, version=service_settings.service_version)
    app.state.settings = service_settings

    @app.on_event("startup")
    async def _on_startup() -> None:
        logger.info(
            "service_startup name=%s version=%s default_failure_dir=%s",
            service_settings.service_name,
            service_settings.service_version,
            service_settings.default_failure_dir,
        )

    @app.middleware("http")
    async def _request_logging(request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        logger.info(
            "request method=%s path=%s status=%s elapsed_ms=%.2f",
            request.method,
            request.url.path,
            response.status_code,
            elapsed_ms,
        )
        return response

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    def health() -> dict[str, object]:
        capabilities_payload = build_capabilities(service_settings)
        return {
            "ok": True,
            "status": "ok",
            "service": service_settings.service_name,
            "version": service_settings.service_version,
            "service_info": capabilities_payload["service"],
            "runtime": capabilities_payload["runtime"],
            "summary": capabilities_payload["summary"],
            "availability": capabilities_payload["availability"],
            "plugins": registry.list_plugins(),
            "plugin_names": registry.list_plugins(),
            "backbones": capabilities_payload["backbones"],
            "detectors": capabilities_payload["detectors"],
            "rectify": capabilities_payload["rectify"],
            "default_failure_dir": service_settings.default_failure_dir,
            "default_ocr_backend": service_settings.default_ocr_backend,
            "default_vlm_backend": service_settings.default_vlm_backend,
            "default_detector_backend": service_settings.default_detector_backend,
            "default_rectify_backend": service_settings.default_rectify_backend,
        }

    @app.get("/capabilities")
    def capabilities() -> dict[str, Any]:
        return build_capabilities(service_settings)

    @app.post("/infer")
    async def infer(
        plugin_name: str | None = Form(None),
        plugin: str | None = Form(None),
        file: UploadFile = File(...),
        ocr_backend: str | None = Form(None),
        vlm_backend: str | None = Form(None),
        detector_backend: str | None = Form(None),
        rectify_backend: str | None = Form(None),
        failure_dir: str | None = Form(None),
    ) -> JSONResponse:
        selected_plugin = plugin_name or plugin
        if not selected_plugin:
            raise HTTPException(status_code=422, detail="plugin_name is required")
        if selected_plugin not in registry.list_plugins():
            raise HTTPException(status_code=404, detail=f"Unknown plugin: {selected_plugin}")

        payload = await file.read()
        if not payload:
            raise HTTPException(status_code=400, detail="Uploaded file is empty")

        effective_failure_dir = failure_dir or service_settings.default_failure_dir
        effective_ocr_backend = ocr_backend or service_settings.default_ocr_backend
        effective_vlm_backend = vlm_backend or service_settings.default_vlm_backend
        effective_detector_backend = detector_backend or service_settings.default_detector_backend
        effective_rectify_backend = rectify_backend or service_settings.default_rectify_backend
        try:
            DemoPipelineRunner.validate_backend_selection(
                ocr_backend=effective_ocr_backend,
                vlm_backend=effective_vlm_backend,
                detector_backend=effective_detector_backend,
                rectify_backend=effective_rectify_backend,
            )
            runner = DemoPipelineRunner(
                ocr_backend=effective_ocr_backend,
                vlm_backend=effective_vlm_backend,
                detector_backend=effective_detector_backend,
                rectify_backend=effective_rectify_backend,
                failure_dir=effective_failure_dir,
            )
            result = runner.run(
                plugin_name=selected_plugin,
                image=payload,
                sample_id=os.path.splitext(file.filename or "in_memory_sample")[0],
                source_name=file.filename,
                source_kind="path",
            )
        except BackendSelectionError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        except RuntimeError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        except Exception as exc:  # pragma: no cover
            raise HTTPException(status_code=500, detail=f"Inference failed [{exc.__class__.__name__}]: {exc}") from exc
        return JSONResponse(
            content=jsonable_encoder(
                {
                    "filename": file.filename,
                    "content_type": file.content_type,
                    "result": result,
                }
            )
        )

    return app


app = create_app()
