# Leave Audit Demo Runbook

## 1. Demo 路线总览

| Demo 路线 | 目的 | 特点 | 适用场景 | 预期 |
| --- | --- | --- | --- | --- |
| mock-rule-demo | 稳定演示 PASS / REVIEW / REJECT 三分支 | 使用 mock adapter 和 mock fixture bytes；依赖 fixture 中的 mock_fields | 管理层演示、规则分支演示、前端状态展示 | 三条 mock 任务分别进入 PASS / REVIEW / REJECT |
| real-ocr-demo | 验证真实 OCR / detector / rectify 链路 | 使用本地真实图片 + rapidocr + pil detector + pil rectify；VLM 保持 mock | 技术联调、OCR 链路验证、sandbox 前自检 | 结果可能进入 REVIEW，不要求稳定复现 PASS / REVIEW / REJECT 三分支 |

管理摘要：mock-rule-demo 用于“稳定讲清业务分支”，real-ocr-demo 用于“确认真实 OCR 链路可跑通”；两者用途不同，演示前应先选路线。

## 2. 通用准备

### Python 环境

```bash
cd /Users/anshi/clawd/id-doc-ocr
source .venv/bin/activate
```

### 前端依赖

```bash
cd /Users/anshi/clawd/id-doc-ocr/ui/approval-verification
npm install
```

### 端口约定

- 后端端口：`8001`
- 前端端口：`5173`

如端口被占用，先检查并释放：

```bash
lsof -nP -iTCP:8001 -sTCP:LISTEN
lsof -nP -iTCP:5173 -sTCP:LISTEN
```

### 清理 demo DB

```bash
cd /Users/anshi/clawd/id-doc-ocr
source .venv/bin/activate
python scripts/reset_leave_audit_demo.py
```

### 验证命令

```bash
cd /Users/anshi/clawd/id-doc-ocr
source .venv/bin/activate
python -m pytest

cd /Users/anshi/clawd/id-doc-ocr/ui/approval-verification
npm run build
```

## 3. mock-rule-demo 操作步骤

### 环境变量示例

```bash
cd /Users/anshi/clawd/id-doc-ocr
source .venv/bin/activate

export ID_DOC_OCR_LEAVE_SYSTEM_ADAPTER=mock
export ID_DOC_OCR_LEAVE_AUDIT_DRY_RUN=true
export ID_DOC_OCR_LEAVE_AUDIT_DB=.local/leave_audit.db
unset ID_DOC_OCR_LEAVE_AUDIT_FIXTURE_FILE
unset ID_DOC_OCR_LEAVE_AUDIT_FIXTURE_DIR
```

### 后端启动命令

```bash
python scripts/reset_leave_audit_demo.py
python -m uvicorn id_doc_ocr.service.app:app --host 127.0.0.1 --port 8001
```

### 前端启动命令

```bash
cd /Users/anshi/clawd/id-doc-ocr/ui/approval-verification
VITE_API_BASE_URL=http://127.0.0.1:8001 npm run dev -- --host 127.0.0.1 --port 5173
```

### 页面操作步骤

1. 打开工作台：`http://127.0.0.1:5173`
2. 点击“同步待审核任务”
3. 查看 3 条 mock 任务
4. 分别点击“运行核验”
5. 验证 PASS / REVIEW / REJECT
6. 打开详情
7. 查看 `autoPassReadiness`
8. 查看 `rule_results` 中文解释
9. 提交 HR 复核
10. 点击 dry-run 回写

### 预期结果表格

| request_id | 预期 status | 预期 verify_status | 预期 risk_level | 说明 |
| --- | --- | --- | --- | --- |
| `LV-MOCK-SICK-PASS-001` | PASS | PASS | LOW | 申请人、材料类型、日期均匹配 |
| `LV-MOCK-SICK-REVIEW-001` | REVIEW | REVIEW | MEDIUM | 申请人与材料人员信息不一致，需要 HR 复核 |
| `LV-MOCK-SICK-REJECT-001` | REJECT | REJECT | HIGH | 病假申请上传婚假/结婚证类材料，材料类型不匹配 |

## 4. real-ocr-demo 操作步骤

### 本地准备真实图片

不要提交真实隐私图片到仓库。将真实或脱敏样本放到本地 `.local`：

```bash
cd /Users/anshi/clawd/id-doc-ocr
mkdir -p .local/leave_audit_fixtures
cp /path/to/your/sick-diagnosis-proof.jpg .local/leave_audit_fixtures/sick-diagnosis-proof.jpg
```

### 环境变量示例

```bash
cd /Users/anshi/clawd/id-doc-ocr
source .venv/bin/activate

export ID_DOC_OCR_LEAVE_SYSTEM_ADAPTER=mock
export ID_DOC_OCR_LEAVE_AUDIT_DRY_RUN=true
export ID_DOC_OCR_LEAVE_AUDIT_DB=.local/leave_audit.db
export ID_DOC_OCR_LEAVE_AUDIT_FIXTURE_FILE=src/id_doc_ocr/leave_audit/fixtures/real_ocr_leave_tasks.json
export ID_DOC_OCR_LEAVE_AUDIT_FIXTURE_DIR=.local/leave_audit_fixtures
export ID_DOC_OCR_DEFAULT_OCR_BACKEND=rapidocr
export ID_DOC_OCR_DEFAULT_DETECTOR_BACKEND=pil
export ID_DOC_OCR_DEFAULT_RECTIFY_BACKEND=pil
export ID_DOC_OCR_DEFAULT_VLM_BACKEND=mock
```

### 后端启动命令

```bash
python scripts/reset_leave_audit_demo.py
python -m uvicorn id_doc_ocr.service.app:app --host 127.0.0.1 --port 8001
```

健康检查：

```bash
curl http://127.0.0.1:8001/health
```

确认 health 中显示：

- `default_ocr_backend: rapidocr`
- `default_detector_backend: pil`
- `default_rectify_backend: pil`

### 前端启动命令

```bash
cd /Users/anshi/clawd/id-doc-ocr/ui/approval-verification
VITE_API_BASE_URL=http://127.0.0.1:8001 npm run dev -- --host 127.0.0.1 --port 5173
```

### 页面操作步骤

1. 打开工作台：`http://127.0.0.1:5173`
2. 点击“同步待审核任务”
3. 查看 `sick-real-ocr-*` 三条任务
4. 分别点击“运行核验”
5. 打开 REVIEW 任务详情
6. 查看真实 OCR 提取字段
7. 查看 `autoPassReadiness`
8. 查看 `rule_results.message_zh` / `display_message`
9. 提交 HR 复核
10. 点击 dry-run 回写
11. 检查 `callback_dry_run.payload`

### 预期结果说明

真实 OCR 结果受图片质量、OCR 识别、字段抽取、质量门控影响，可能全部进入 REVIEW，这是正常现象。real-ocr-demo 的目标是验证真实 OCR / detector / rectify 链路、详情展示、HR 复核和 dry-run callback 是否跑通，不要求稳定复现 PASS / REVIEW / REJECT 三分支。

### 需要重点确认

- `hospital_name`
- `certificate_title`
- `patient_name`
- `issue_date`
- `rest_start_date`
- `rest_end_date`
- `seal_present`
- `seal_text`
- `autoPassReadiness`
- `rule_results.message_zh`
- `callback_dry_run.payload`

## 5. dry-run callback 检查

### 行为说明

当 `ID_DOC_OCR_LEAVE_AUDIT_DRY_RUN=true` 时，系统不会真实调用假勤系统 callback。API 应返回：

```json
{
  "dry_run": true,
  "callback_skipped": true,
  "callback_payload": {
    "request_id": "...",
    "leave_request_id": "...",
    "verify_status": "..."
  }
}
```

同时，`result.verification_json.callback_dry_run.payload` 应保存同一份 payload，便于联调记录和业务侧确认。

### payload 应包含

- `request_id`
- `leave_request_id`
- `verify_status`
- `risk_level`
- `risk_score`
- `needs_manual_review`
- `summary`
- `rule_results`

### 检查命令示例

```bash
curl -X POST http://127.0.0.1:8001/leave-audit/tasks/LV-MOCK-SICK-REVIEW-001/callback
curl http://127.0.0.1:8001/leave-audit/tasks/LV-MOCK-SICK-REVIEW-001 | python -m json.tool
```

## 6. 常见问题

### fixture:// 返回假字节导致真实 OCR 失败

现象：真实 OCR / PIL 报 `UnidentifiedImageError`。

解决：配置 `ID_DOC_OCR_LEAVE_AUDIT_FIXTURE_DIR`，并放入真实图片：

```bash
export ID_DOC_OCR_LEAVE_AUDIT_FIXTURE_DIR=.local/leave_audit_fixtures
ls -lh .local/leave_audit_fixtures/sick-diagnosis-proof.jpg
```

未配置 fixture dir 时，mock adapter 会保持旧行为，返回 mock fixture bytes，仅适合 mock-rule-demo。

### 真实 OCR 不复现 PASS / REVIEW / REJECT 三分支

这是预期。real-ocr-demo 验证 OCR 链路，不验证规则分支稳定性。需要稳定三分支演示时，请使用 mock-rule-demo。

### pytest 命令 import path 问题

建议统一使用：

```bash
python -m pytest
```

不要只运行裸 `pytest`，否则在部分本地环境中可能出现 `ModuleNotFoundError: scripts`。

### 前端无数据

检查：

1. 后端是否在 `8001` 启动
2. 前端 `VITE_API_BASE_URL` 是否指向 `http://127.0.0.1:8001`
3. `/leave-audit` API 是否可访问
4. 是否已点击“同步待审核任务”
5. `.local/leave_audit.db` 是否刚被 reset 但尚未 sync

### callback 没有真实回写

检查 `ID_DOC_OCR_LEAVE_AUDIT_DRY_RUN` 是否为 `true`。dry-run=true 时不会真实回写，这是安全模式预期行为。

如需真实回写 sandbox，必须先确认 callback payload，并显式切换 dry-run=false。

### 字段名不匹配

检查字段映射配置：

```text
configs/leave_system_field_mapping.yaml
```

重点核对 pending 原始字段、download 标识字段、callback 目标字段是否与真实假勤系统 sandbox 契约一致。

## 7. 演示完成后的收尾

1. 停止前端进程
2. 停止后端进程
3. 清理 `.local` demo DB：

```bash
cd /Users/anshi/clawd/id-doc-ocr
rm -f .local/leave_audit.db .local/leave_audit.db-*
```

4. 不提交真实隐私图片：

```bash
git status --short
```

确认 `.local/leave_audit_fixtures/`、真实样本图片、临时 DB 均未进入 git。

5. 确认工作区 clean：

```bash
git status --short
```

Management summary implication: runbook 将“能跑通”固化为“一页可交接、可复现、可自检”的操作手册，降低 sandbox dry-run 前的人为遗漏风险。
