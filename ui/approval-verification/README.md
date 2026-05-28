# Approval verification mock React UI

## Goal

A mock-first React skeleton for the approval attachment verification page.

Current scope:
- render PASS and REVIEW scenarios from `examples/mock-ui/*.json`
- validate three-column layout
- validate component decomposition
- validate page state and adapter flow
- support both `mock` mode and `real adapter` mode

Not included yet:
- real upload
- parser expansion
- new document types
- rules backend / management UI

## Local run

```bash
cd ui/approval-verification
npm install
npm run dev
```

Default local URL from Vite:
- `http://127.0.0.1:5173/`

If you want an explicit host/port:

```bash
npm run dev -- --host 127.0.0.1 --port 4173
```

## Mode switching

The page now has two topbar controls.

### Data source mode
- `Mock mode`
- `Real adapter mode`

Behavior:
- `Mock mode` reads only local mock JSON
- `Real adapter mode` keeps the same page shell, but the analyze / verify buttons call the real backend adapters

### Scenario switching
- `PASS mock`
- `REVIEW mock`

Those buttons still drive:
- `examples/mock-ui/approval-verification-page.pass.json`
- `examples/mock-ui/approval-verification-page.review.json`

In `real adapter mode`, the same scenario also controls which demo request payload is sent to the backend.

Current adapter files:
- `src/adapters/mockApprovalVerification.ts`
- `src/adapters/realApprovalVerification.ts`
- `src/adapters/demoRequestBuilders.ts`
- `src/adapters/viewModelBuilders.ts`
- `src/adapters/approvalVerification.ts`

## Real adapter mode requirements

For local integration testing, start the backend first:

```bash
cd /Users/anshi/clawd/id-doc-ocr
source .venv/bin/activate
python -m uvicorn id_doc_ocr.service.app:app --host 127.0.0.1 --port 8000
```

Then start the frontend:

```bash
cd ui/approval-verification
npm run dev -- --host 127.0.0.1 --port 4173
```

Notes:
- Vite dev server proxies `/api/*` to `http://127.0.0.1:8000`
- `real adapter mode` uses a built-in sample image under `public/samples/`
- it will first probe backend demo path `/api/demo/samples/simple/*` so both Docker and local runs can reuse the shared `simple` sample folder when available
- it also supports probing `/api/demo/samples/by-path?path=...` for repo-relative sample paths (for example paths listed in demo manifest JSON files under `examples/assets`)
- this is only for adapter integration; it is not real upload UI yet
- OpenAI 按钮支持两种后端 LLM Provider：`openai`（默认）与 `dify`；可通过前端环境变量 `VITE_LLM_PROVIDER` 切换，并在后端分别配置 `OPENAI_API_KEY` 或 `DIFY_API_KEY`（可选 `DIFY_BASE_URL`，默认 `http://127.0.0.1/v1`）

## Raw response vs ViewModel boundary

The page now separates raw API shapes from UI-facing shapes.

Raw types:
- `RawAnalyzeResponse`
- `RawVerifyResponse`
- `RawApprovalVerificationPageModel`

UI ViewModel types:
- `ApprovalVerificationViewModel`
- `AttachmentViewModel`
- `AnalysisViewModel`
- `VerificationViewModel`

Builder functions:
- `buildApprovalPageModel()`
- `buildAnalyzeDemoFormData()`
- `buildVerifyDemoFormData()`

Meaning:
- adapter layer reads raw backend response
- builder layer maps raw response into a stable page ViewModel
- components consume only ViewModel fields
- `/verify-attachment` returns the latest `analysis` for that verification run
- when the frontend receives `rawVerifyResponse`, it should refresh both the analysis panel and verification panel from that same response
- when real upload is added later, only the request builder should need to change first

## Build

```bash
npm run build
```

## Main files

- `src/App.tsx`
- `src/components/ApprovalVerificationPage.tsx`
- `src/adapters/mockApprovalVerification.ts`
- `src/types.ts`

## Scenarios

- PASS mock
- REVIEW mock
