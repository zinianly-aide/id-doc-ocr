# Real OCR Demo for leave_audit

## 1. Purpose

This demo keeps the leave-system side mocked, but runs the document-processing chain with real local image bytes:

- OCR: `rapidocr`
- detector: `pil`
- rectify: `pil`
- VLM: `mock`
- callback: dry-run enabled

Management summary: this flow validates the real OCR/detector/rectify integration path without committing private sample images or calling a real leave-system callback.

## 2. Prepare a local sample image

Do not commit private or large real documents to the repository. Put the local demo image under `.local`, for example:

```bash
cd /Users/anshi/clawd/id-doc-ocr
mkdir -p .local/leave_audit_fixtures
cp /path/to/your/sick-diagnosis-proof.jpg .local/leave_audit_fixtures/sick-diagnosis-proof.jpg
```

The demo task file references the image as:

```text
fixture://sick-diagnosis-proof.jpg
```

When `ID_DOC_OCR_LEAVE_AUDIT_FIXTURE_DIR` is set, the mock adapter maps that URL to:

```text
${ID_DOC_OCR_LEAVE_AUDIT_FIXTURE_DIR}/sick-diagnosis-proof.jpg
```

If the file is missing, the adapter raises an explicit `FileNotFoundError`. Paths containing `../` are rejected to prevent path traversal.

## 3. Select the real-OCR demo task fixture

The repository includes task metadata only, not the image:

```text
src/id_doc_ocr/leave_audit/fixtures/real_ocr_leave_tasks.json
```

It contains three local-demo tasks:

- `sick-real-ocr-review-001`
- `sick-real-ocr-name-mismatch-001`
- `sick-real-ocr-date-check-001`

Set the fixture file and fixture directory:

```bash
export ID_DOC_OCR_LEAVE_AUDIT_FIXTURE_FILE=src/id_doc_ocr/leave_audit/fixtures/real_ocr_leave_tasks.json
export ID_DOC_OCR_LEAVE_AUDIT_FIXTURE_DIR=.local/leave_audit_fixtures
```

If `ID_DOC_OCR_LEAVE_AUDIT_FIXTURE_FILE` is not set, the mock adapter still uses the stable rule-demo file:

```text
fixtures/sample_leave_tasks.json
```

## 4. Start the backend

```bash
cd /Users/anshi/clawd/id-doc-ocr
source .venv/bin/activate

export ID_DOC_OCR_LEAVE_SYSTEM_ADAPTER=mock
export ID_DOC_OCR_LEAVE_AUDIT_DB=.local/leave_audit.db
export ID_DOC_OCR_LEAVE_AUDIT_DRY_RUN=true
export ID_DOC_OCR_LEAVE_AUDIT_FIXTURE_FILE=src/id_doc_ocr/leave_audit/fixtures/real_ocr_leave_tasks.json
export ID_DOC_OCR_LEAVE_AUDIT_FIXTURE_DIR=.local/leave_audit_fixtures

export ID_DOC_OCR_DEFAULT_OCR_BACKEND=rapidocr
export ID_DOC_OCR_DEFAULT_DETECTOR_BACKEND=pil
export ID_DOC_OCR_DEFAULT_RECTIFY_BACKEND=pil
export ID_DOC_OCR_DEFAULT_VLM_BACKEND=mock

python scripts/reset_leave_audit_demo.py
python -m uvicorn id_doc_ocr.service.app:app --host 127.0.0.1 --port 8000
```

Health check:

```bash
curl http://127.0.0.1:8000/health
```

Confirm the response shows:

```text
default_ocr_backend = rapidocr
default_detector_backend = pil
default_rectify_backend = pil
```

## 5. Start the frontend

```bash
cd /Users/anshi/clawd/id-doc-ocr/ui/approval-verification
npm run dev
```

Open the Vite URL, usually:

```text
http://127.0.0.1:5173
```

## 6. Demo flow

1. Click `同步待审核任务`.
2. Confirm the table shows the three `sick-real-ocr-*` tasks.
3. Click `运行核验` for each task.
4. Open `详情`.
5. Check:
   - `verify_status`
   - `risk_level`
   - extracted OCR fields
   - `autoPassReadiness`
   - `rule_results` Chinese explanations
6. For a REVIEW task, submit HR review:
   - `review_result`: `REVIEW`
   - `reviewer`: `hr01`
   - `review_comment`: real OCR demo review note
7. Click `回写`.
8. Confirm dry-run callback metadata is recorded and real callback is skipped.

Command-line equivalents:

```bash
curl -X POST http://127.0.0.1:8000/leave-audit/sync
curl -X POST http://127.0.0.1:8000/leave-audit/tasks/sick-real-ocr-review-001/run
curl http://127.0.0.1:8000/leave-audit/tasks/sick-real-ocr-review-001 | python -m json.tool
curl -X POST http://127.0.0.1:8000/leave-audit/tasks/sick-real-ocr-review-001/callback
```

## 7. Expected behavior

The real OCR demo is not intended to produce the stable PASS / REVIEW / REJECT three-branch matrix. Real OCR, image quality, detected dates, and extracted names can change the final status.

That difference is expected:

- Use `mock-rule-demo` for deterministic PASS / REVIEW / REJECT business-rule demonstrations.
- Use `real-ocr-demo` to validate the live OCR/detector/rectify path and REVIEW handling.

In real OCR mode, it is acceptable for all three tasks to enter REVIEW if the sample image, OCR confidence, name matching, or date matching does not meet auto-pass thresholds.

## 8. Troubleshooting

### `UnidentifiedImageError`

This means the adapter returned fake fixture bytes or the local file is not a valid image. Check:

```bash
echo $ID_DOC_OCR_LEAVE_AUDIT_FIXTURE_DIR
ls -lh .local/leave_audit_fixtures/sick-diagnosis-proof.jpg
```

### Missing fixture file

The adapter reports the original `fixture://...` URL and the resolved local path. Put the file in the fixture directory or update the task fixture JSON.

### Unexpected PASS/REVIEW/REJECT split

Real OCR output is data-dependent. Confirm the extracted fields in `analysis_json.extracted_fields` before changing rules or UI copy.
