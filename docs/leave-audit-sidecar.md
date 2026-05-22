# Leave Audit Sidecar / 假勤系统旁路审核模式

## 1. 定位

`leave_audit` 是新增的业务域，用于把现有 OCR / plugin / pipeline / `/verify-attachment` 能力封装成“旁路材料审核中台”。它不替代现有假勤系统，也不推翻现有接口，而是在假勤系统之外拉取待审核附件、执行 OCR + 规则核验、保存审核结果，并把结果回推给假勤系统。

管理摘要：本次重构让项目从单次上传核验工具升级为可被假勤系统接入的异步旁路审核服务，同时保留所有原有 API 兼容性。

## 2. 架构

新增目录：

```text
src/id_doc_ocr/leave_audit/
  domain/        # 枚举、任务/附件/结果/人工复核模型、leave_type -> plugin 映射
  adapters/      # 假勤系统适配器接口与 MockLeaveSystemAdapter
  repository/    # SQLiteRepository，保存 task/result/review
  service/       # sync、audit、review 业务服务
  worker/        # processor/poller，用于后续后台轮询或队列消费
  api/           # FastAPI router 与请求 schema
```

核心链路：

```text
假勤系统 / mock fixture
  -> LeaveSystemAdapter.fetch_pending_attachments()
  -> SQLiteRepository.save_task()
  -> AuditService.run_task()
  -> InferenceService -> DemoPipelineRunner
  -> verify_attachment()
  -> SQLiteRepository.save_result()
  -> LeaveSystemAdapter.push_audit_result()
```

## 3. 状态流转

`LeaveAuditStatus`：

- `PENDING`：待拉取或待处理
- `PULLED`：已从假勤系统同步到旁路库
- `PROCESSING`：正在 OCR / analysis / verification
- `PASS`：规则核验通过
- `REVIEW`：需要 HR 人工复核
- `REJECT`：规则核验拒绝
- `ERROR`：处理异常
- `IGNORED`：人工决定忽略
- `SYNCED`：结果已回推给假勤系统

典型流转：

```text
PENDING -> PULLED -> PROCESSING -> PASS/REVIEW/REJECT/ERROR -> SYNCED
                                      \-> HR review -> PASS/REVIEW/REJECT/IGNORED
```

## 4. leave_type 到 plugin 的映射

当前简单 resolver：`resolve_plugin_for_leave_task(task) -> str`

| leave_type | plugin |
| --- | --- |
| `MARRIAGE` | `marriage_certificate` |
| `SICK` | `diagnosis_proof` |
| `MATERNITY` | `birth_certificate` |
| `PATERNITY` | `birth_certificate` |
| `PARENTAL` | `birth_certificate` |
| `BEREAVEMENT` | `custody_relationship_certificate`（后续可扩展为 `hukou_booklet` fallback） |

如果附件中显式声明 `plugin_name`，优先使用附件级配置，便于 mock、灰度和异常样本测试。

## 5. Mock adapter 使用

Mock 数据文件：

```text
fixtures/sample_leave_tasks.json
```

Mock adapter：

```python
from id_doc_ocr.leave_audit.adapters.mock_leave_system import MockLeaveSystemAdapter

adapter = MockLeaveSystemAdapter()
tasks = adapter.fetch_pending_attachments()
content = adapter.download_attachment(tasks[0].attachments[0].attachment_url)
```

`fixture://...` URL 会生成本地 mock bytes；普通路径会按 fixture 文件所在目录解析。

## 6. SQLite 存储

默认数据库：

```text
.local/leave_audit.db
```

可通过环境变量覆盖：

```bash
export ID_DOC_OCR_LEAVE_AUDIT_DB=/path/to/leave_audit.db
```

表：

- `leave_audit_task`：任务、假别、员工、请假日期、附件 JSON、原始 payload
- `leave_audit_result`：analysis JSON、verification JSON、状态、回推标记
- `leave_audit_review`：HR 人工复核结论、复核人、备注

## 7. API 示例

### 7.1 同步 mock 任务

```bash
curl -X POST http://127.0.0.1:8000/leave-audit/sync
```

返回：

```json
{
  "synced": 3,
  "tasks": [
    {"request_id": "LV-MOCK-SICK-PASS-001", "status": "PULLED"}
  ]
}
```

### 7.2 执行单个任务核验

```bash
curl -X POST http://127.0.0.1:8000/leave-audit/tasks/LV-MOCK-SICK-PASS-001/run
```

返回核心字段：

```json
{
  "result": {
    "request_id": "LV-MOCK-SICK-PASS-001",
    "status": "PASS",
    "plugin_name": "diagnosis_proof",
    "verification_json": {
      "verify_status": "PASS",
      "autoPassReadiness": {
        "status": "ready",
        "label": "可自动通过",
        "reasons": [],
        "blockers": []
      }
    }
  }
}
```

### 7.3 查询任务列表

```bash
curl http://127.0.0.1:8000/leave-audit/tasks
```

可按状态过滤：

```bash
curl 'http://127.0.0.1:8000/leave-audit/tasks?status=REVIEW'
```

### 7.4 查询任务详情

```bash
curl http://127.0.0.1:8000/leave-audit/tasks/LV-MOCK-SICK-PASS-001
```

返回：

- `task`
- `result`
- `reviews`

### 7.5 提交 HR 人工复核

```bash
curl -X POST http://127.0.0.1:8000/leave-audit/tasks/LV-MOCK-SICK-PASS-001/review \
  -H 'Content-Type: application/json' \
  -d '{"decision":"REVIEW","reviewer":"hr01","comment":"抽检复核"}'
```

允许的 `decision`：

- `PASS`
- `REVIEW`
- `REJECT`
- `IGNORED`

### 7.6 回推审核结果

```bash
curl -X POST http://127.0.0.1:8000/leave-audit/tasks/LV-MOCK-SICK-PASS-001/callback
```

当前 mock adapter 仅把结果记录到内存 `pushed_results`；真实 adapter 应在这里调用假勤系统回调 API。

### 7.7 统计

```bash
curl http://127.0.0.1:8000/leave-audit/stats
```

## 8. verification 输出增强

`verify_attachment()` 现在在原有输出外增加：

```json
{
  "autoPassReadiness": {
    "status": "ready | blocked | unknown",
    "label": "可自动通过 | 禁止自动通过 | 需要人工确认",
    "reasons": [],
    "blockers": []
  }
}
```

含义：

- `ready`：可作为自动通过候选
- `blocked`：存在 error blocker 或拒绝类结论，禁止自动通过
- `unknown`：无硬阻断但需要人工确认

同时，`rule_results` 增加：

- `message_zh`
- `display_message`

前端应优先展示中文 `display_message`，不要直接把英文 `message` 作为审批文案。

## 9. 接入真实假勤系统 adapter

真实接入时替换 `LeaveSystemAdapter` 实现即可：

```python
class RealLeaveSystemAdapter(LeaveSystemAdapter):
    def fetch_pending_attachments(self) -> list[LeaveAuditTask]:
        # 调用假勤系统待审核材料接口
        ...

    def download_attachment(self, attachment_url: str) -> bytes:
        # 调用假勤系统或文件服务下载附件
        ...

    def push_audit_result(self, result: LeaveAuditResult) -> None:
        # 回写 PASS / REVIEW / REJECT / ERROR 和 evidence 摘要
        ...
```

替换建议：

1. 先保持 `SQLiteRepository` 不变，只替换 adapter。
2. 用真实假勤系统沙箱接口实现 `fetch_pending_attachments()`。
3. 确认 `request_id` 由调用方生成，并在假勤系统、旁路库、日志中一致。
4. 先只回推 `request_id/status/summary/autoPassReadiness`，再逐步回推完整 evidence。
5. 真实环境中不要把业务请求字段注入 OCR extracted_fields；业务字段应只进入 verification request/evidence。

## 10. 兼容性

本次新增 `/leave-audit/*` 路由，不改变以下既有接口：

- `GET /health`
- `GET /capabilities`
- `POST /infer`
- `POST /analyze-document`
- `POST /verify-attachment`

## 11. 验证命令

```bash
.venv/bin/python -m pytest -q \
  tests/test_leave_audit_adapter.py \
  tests/test_leave_audit_repository.py \
  tests/test_leave_audit_service.py \
  tests/test_leave_audit_api.py \
  tests/test_attachment_verification.py \
  tests/test_service_api.py
```

当前新增测试覆盖：

- mock adapter 拉取任务
- repository 保存 / 查询 task、result、review
- audit service 处理 PASS / REVIEW / REJECT
- API 查询任务列表与详情
- review API 提交 HR 复核结论
