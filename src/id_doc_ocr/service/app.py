from __future__ import annotations

import os
from dataclasses import asdict, dataclass
from typing import Any

from fastapi import FastAPI, File, Form, HTTPException, UploadFile

from id_doc_ocr import __version__, plugins as _plugins  # noqa: F401
from id_doc_ocr.backbones.got_ocr import GOTOCRAdapter
from id_doc_ocr.backbones.mock import MockPaddleOCRAdapter, MockPaddleOCRVLAdapter
from id_doc_ocr.backbones.paddleocr import PaddleOCRAdapter
from id_doc_ocr.backbones.paddleocr_vl import PaddleOCRVLAdapter
from id_doc_ocr.backbones.rapidocr import RapidOCRAdapter
from id_doc_ocr.core.registry import registry
from id_doc_ocr.pipeline.runner import DemoPipelineRunner


@dataclass(slots=True)
class ServiceSettings:
    service_name: str = "id-doc-ocr"
    service_version: str = __version__
    default_failure_dir: str | None = None

    @classmethod
    def from_env(cls) -> "ServiceSettings":
        return cls(
            service_name=os.getenv("ID_DOC_OCR_SERVICE_NAME", "id-doc-ocr"),
            service_version=os.getenv("ID_DOC_OCR_SERVICE_VERSION", __version__),
            default_failure_dir=os.getenv("ID_DOC_OCR_FAILURE_DIR") or None,
        )


BACKBONE_SPECS = {
    "ocr": [MockPaddleOCRAdapter, RapidOCRAdapter, PaddleOCRAdapter, GOTOCRAdapter],
    "vlm": [MockPaddleOCRVLAdapter, PaddleOCRVLAdapter],
}


def build_capabilities(settings: ServiceSettings) -> dict[str, Any]:
    plugins: list[dict[str, Any]] = []
    for plugin_name in registry.list_plugins():
        plugin = registry.get(plugin_name)
        plugins.append(
            {
                "name": plugin.metadata.name,
                "version": plugin.metadata.version,
                "description": plugin.metadata.description,
                "supported_backbones": plugin.metadata.supported_backbones,
                "schema": plugin.get_schema_name(),
                "tags": plugin.metadata.tags,
            }
        )

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
                    "availability": availability,
                }
            )

    return {
        "service": asdict(settings),
        "plugins": plugins,
        "backbones": backbones,
    }


def create_app(settings: ServiceSettings | None = None) -> FastAPI:
    service_settings = settings or ServiceSettings.from_env()
    app = FastAPI(title=service_settings.service_name, version=service_settings.service_version)
    app.state.settings = service_settings

    @app.get("/health")
    def health() -> dict[str, object]:
        return {
            "ok": True,
            "service": service_settings.service_name,
            "version": service_settings.service_version,
            "plugins": registry.list_plugins(),
            "default_failure_dir": service_settings.default_failure_dir,
        }

    @app.get("/capabilities")
    def capabilities() -> dict[str, Any]:
        return build_capabilities(service_settings)

    @app.post("/infer")
    async def infer(
        plugin_name: str | None = Form(None),
        plugin: str | None = Form(None),
        file: UploadFile = File(...),
        ocr_backend: str = Form("mock"),
        vlm_backend: str = Form("auto"),
        failure_dir: str | None = Form(None),
    ) -> dict[str, object]:
        selected_plugin = plugin_name or plugin
        if not selected_plugin:
            raise HTTPException(status_code=422, detail="plugin_name is required")
        if selected_plugin not in registry.list_plugins():
            raise HTTPException(status_code=404, detail=f"Unknown plugin: {selected_plugin}")

        payload = await file.read()
        if not payload:
            raise HTTPException(status_code=400, detail="Uploaded file is empty")

        effective_failure_dir = failure_dir or service_settings.default_failure_dir
        runner = DemoPipelineRunner(
            ocr_backend=ocr_backend,
            vlm_backend=vlm_backend,
            failure_dir=effective_failure_dir,
        )
        try:
            result = runner.run(plugin_name=selected_plugin, image=payload)
        except RuntimeError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        except Exception as exc:  # pragma: no cover
            raise HTTPException(status_code=500, detail=f"Inference failed: {exc}") from exc
        return {
            "filename": file.filename,
            "content_type": file.content_type,
            "result": result,
        }

    return app


app = create_app()
