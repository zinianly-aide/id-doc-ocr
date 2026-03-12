from __future__ import annotations

from fastapi import FastAPI, File, Form, HTTPException, UploadFile

from id_doc_ocr import plugins as _plugins  # noqa: F401
from id_doc_ocr.core.registry import registry
from id_doc_ocr.pipeline.runner import DemoPipelineRunner

app = FastAPI(title="id-doc-ocr", version="0.1.0")


@app.get("/health")
def health() -> dict[str, object]:
    return {
        "ok": True,
        "service": "id-doc-ocr",
        "plugins": registry.list_plugins(),
    }


@app.post("/infer")
async def infer(
    plugin_name: str = Form(...),
    file: UploadFile = File(...),
    ocr_backend: str = Form("mock"),
    vlm_backend: str = Form("auto"),
    failure_dir: str | None = Form(None),
) -> dict[str, object]:
    if plugin_name not in registry.list_plugins():
        raise HTTPException(status_code=404, detail=f"Unknown plugin: {plugin_name}")

    payload = await file.read()
    if not payload:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    runner = DemoPipelineRunner(
        ocr_backend=ocr_backend,
        vlm_backend=vlm_backend,
        failure_dir=failure_dir,
    )
    result = runner.run(plugin_name=plugin_name, image=payload)
    return {
        "filename": file.filename,
        "content_type": file.content_type,
        "result": result,
    }
