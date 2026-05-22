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

## 9. Adapter factory 与真实 HTTP adapter

`leave_audit` API 通过 adapter factory 创建假勤系统适配器：

```text
ID_DOC_OCR_LEAVE_SYSTEM_ADAPTER=mock -> MockLeaveSystemAdapter
ID_DOC_OCR_LEAVE_SYSTEM_ADAPTER=http -> HttpLeaveSystemAdapter
未配置 -> mock
```

默认 `mock`，因此 `/leave-audit/sync` 的本地演示行为保持不变。

### 9.1 mock adapter 用法

```bash
unset ID_DOC_OCR_LEAVE_SYSTEM_ADAPTER
# 或
export ID_DOC_OCR_LEAVE_SYSTEM_ADAPTER=mock
```

Mock 数据仍来自：

```text
fixtures/sample_leave_tasks.json
```

适用场景：

- 本地演示
- CI / pytest
- 前端工作台联调
- 不依赖真实假勤系统的 PASS / REVIEW / REJECT 链路验证

### 9.2 http adapter 环境变量

启用真实假勤系统 HTTP adapter：

```bash
export ID_DOC_OCR_LEAVE_SYSTEM_ADAPTER=http
export ID_DOC_OCR_LEAVE_SYSTEM_BASE_URL=https://leave-system.example.com
export ID_DOC_OCR_LEAVE_SYSTEM_TOKEN=replace-with-token
export ID_DOC_OCR_LEAVE_SYSTEM_PENDING_API=/api/leave-audit/pending
export ID_DOC_OCR_LEAVE_SYSTEM_DOWNLOAD_API=/api/leave-audit/download
export ID_DOC_OCR_LEAVE_SYSTEM_CALLBACK_API=/api/leave-audit/callback
export ID_DOC_OCR_LEAVE_SYSTEM_TIMEOUT_SECONDS=10
export ID_DOC_OCR_LEAVE_AUDIT_DRY_RUN=true
```

说明：

- `BASE_URL`：真实假勤系统或 pilot gateway 地址，http adapter 必填
- `TOKEN`：可选；配置后会发送 `Authorization: Bearer <token>`
- `PENDING_API`：拉取待审核任务接口，默认 `/leave-audit/pending`
- `DOWNLOAD_API`：下载附件接口，默认 `/leave-audit/download`
- `CALLBACK_API`：回写审核结果接口，默认 `/leave-audit/callback`
- `TIMEOUT_SECONDS`：HTTP 超时秒数，默认 `10`
- `ID_DOC_OCR_LEAVE_AUDIT_DRY_RUN`：callback dry-run 开关，默认 `false`；sandbox 首轮联调建议先设为 `true`

HTTP adapter 使用 `httpx`，并显式 `trust_env=False`，避免本机代理环境变量影响联调行为。

### 9.3 真实假勤系统接口约定

#### 拉取待审核任务

请求：

```http
GET {BASE_URL}{PENDING_API}
Authorization: Bearer <token>
Accept: application/json
```

响应可以是数组，也可以是包含 `tasks` 或 `data` 的对象：

```json
{
  "tasks": [
    {
      "request_id": "LV-SICK-20260522-000001",
      "leave_request_id": "LR-20260522-000001",
      "leave_type": "SICK",
      "employee_id": "E001",
      "employee_name": "张三",
      "leave_start_date": "2026-05-22",
      "leave_end_date": "2026-05-24",
      "attachments": [
        {
          "attachment_id": "ATT-001",
          "attachment_url": "file-001",
          "filename": "diagnosis.jpg",
          "content_type": "image/jpeg",
          "plugin_name": "diagnosis_proof",
          "metadata": {}
        }
      ]
    }
  ]
}
```

字段兼容别名：

- task id：`request_id` / `id` / `leave_request_id`
- employee name：`employee_name` / `applicant_name` / `applicant`
- date：`leave_start_date` / `start_date`，`leave_end_date` / `end_date`
- attachments：`attachments` / `attachment_list`
- attachment url：`attachment_url` / `url` / `download_url`
- filename：`filename` / `attachment_name` / `name`

#### 下载附件

如果 `attachment_url` 是完整 `http://` 或 `https://` URL，adapter 会直接 GET 该 URL。

否则会调用：

```http
GET {BASE_URL}{DOWNLOAD_API}?attachment_url=<attachment_url>
Authorization: Bearer <token>
```

响应 body 直接作为附件 bytes。

#### 回写结果 callback

请求：

```http
POST {BASE_URL}{CALLBACK_API}
Authorization: Bearer <token>
Content-Type: application/json
```

payload 示例：

```json
{
  "request_id": "LV-SICK-20260522-000001",
  "leave_request_id": "LR-20260522-000001",
  "verify_status": "REVIEW",
  "risk_level": "MEDIUM",
  "risk_score": 45,
  "needs_manual_review": true,
  "summary": "REVIEW: MEDICAL_CERTIFICATE vs expected ['MEDICAL_CERTIFICATE']",
  "rule_results": [
    {
      "rule_code": "applicant_name_match",
      "passed": false,
      "severity": "warning",
      "display_message": "申请人与材料中的人员信息不一致"
    }
  ]
}
```

### 9.4 HTTP 错误处理

- 非 2xx 响应会抛出 `LeaveSystemHttpError`
- 异常信息包含 action、HTTP status 和最多 500 字符响应 body
- pending 响应不是 JSON 或不包含 list 时会抛出明确异常

### 9.5 联调步骤

1. 保持默认 mock，先验证本地链路：

```bash
unset ID_DOC_OCR_LEAVE_SYSTEM_ADAPTER
.venv/bin/python -m pytest -q tests/test_leave_audit_api.py
```

2. 配置 HTTP adapter 环境变量。

3. 启动 API：

```bash
.venv/bin/python -m uvicorn id_doc_ocr.service.app:app --host 127.0.0.1 --port 8000
```

4. 拉取真实待审核任务：

```bash
curl -X POST http://127.0.0.1:8000/leave-audit/sync
```

5. 运行单条核验：

```bash
curl -X POST http://127.0.0.1:8000/leave-audit/tasks/<request_id>/run
```

6. 打开 `ui/approval-verification/` 工作台，确认任务列表、详情 Drawer、人工复核与回写按钮可用。

7. 回写结果：

```bash
curl -X POST http://127.0.0.1:8000/leave-audit/tasks/<request_id>/callback
```

8. 在假勤系统侧确认 request_id / leave_request_id / verify_status / summary / rule_results 已正确入库或进入审批流。

替换建议：

1. 先保持 `SQLiteRepository` 不变，只切换 adapter。
2. 用真实假勤系统沙箱接口验证 `fetch_pending_attachments()`。
3. 确认 `request_id` 由调用方生成，并在假勤系统、旁路库、日志中一致。
4. 先只回推 callback payload 摘要，再逐步扩展完整 evidence。
5. 真实环境中不要把业务请求字段注入 OCR extracted_fields；业务字段应只进入 verification request/evidence。

## 10. 试点推荐流程

试点建议分四步推进：

1. 本地 mock 演示
   - 使用 `ID_DOC_OCR_LEAVE_SYSTEM_ADAPTER=mock`
   - 运行 `POST /leave-audit/sync`
   - 跑通 PASS / REVIEW / REJECT 三条 mock 链路
   - 在 React 工作台中确认详情 Drawer、autoPassReadiness、rule_results 中文解释、HR 复核和 callback 操作

2. 假勤系统 sandbox 联调
   - 切换到 `ID_DOC_OCR_LEAVE_SYSTEM_ADAPTER=http`
   - 使用 `.env.leave-audit.example` 复制出本地 `.env` 或 shell export
   - 先只验证 pending / download / callback 三个接口连通
   - 每个失败都记录 request_id、HTTP status、body preview

3. 小样本端到端验证
   - 病假、婚假、出生证明相关假别各至少一条真实或脱敏真实样例
   - 确认任务入库、附件下载、OCR/analysis、verify_attachment、HR review、callback 全链路可用
   - 对 REVIEW / REJECT 保留截图或 JSON 证据

4. 试点验收
   - 使用 `docs/pilot-acceptance-checklist.md` 逐项确认
   - 明确负责人、通过标准和未解决备注
   - 验收后再进入小范围审批人灰度

## 11. mock -> http adapter 切换方式

默认 mock：

```bash
export ID_DOC_OCR_LEAVE_SYSTEM_ADAPTER=mock
```

切换真实 HTTP adapter：

```bash
cp .env.leave-audit.example .env.leave-audit.local
# 编辑 .env.leave-audit.local 后 export 对应变量，或用 shell/source 工具加载
export ID_DOC_OCR_LEAVE_SYSTEM_ADAPTER=http
export ID_DOC_OCR_LEAVE_SYSTEM_BASE_URL=http://localhost:8080
export ID_DOC_OCR_LEAVE_SYSTEM_TOKEN=replace-me
export ID_DOC_OCR_LEAVE_SYSTEM_PENDING_API=/api/leave/attachments/pending
export ID_DOC_OCR_LEAVE_SYSTEM_DOWNLOAD_API=/api/leave/attachments/{attachment_id}/download
export ID_DOC_OCR_LEAVE_SYSTEM_CALLBACK_API=/api/leave/audit-result
export ID_DOC_OCR_LEAVE_SYSTEM_TIMEOUT_SECONDS=10
export ID_DOC_OCR_LEAVE_AUDIT_DB=.local/leave_audit.db
```

切换后无需改前端，工作台仍调用同一组 `/leave-audit/*` API。

## 12. Dry-run callback 模式

`sandbox` 首轮联调建议开启：

```bash
export ID_DOC_OCR_LEAVE_AUDIT_DRY_RUN=true
```

开启后：

- `/leave-audit/sync` 正常拉取任务
- 附件下载正常执行
- OCR / analysis 正常执行
- `verify_attachment` 正常执行
- 任务状态正常更新为 PASS / REVIEW / REJECT / ERROR
- `POST /leave-audit/tasks/{request_id}/callback` 不调用真实假勤系统 callback
- callback payload 会保存到 `result.verification_json.callback_dry_run.payload`
- API 响应会包含：

```json
{
  "dry_run": true,
  "callback_skipped": true,
  "callback_payload": {
    "request_id": "LV-SICK-20260522-000001",
    "leave_request_id": "LR-20260522-000001",
    "verify_status": "REVIEW"
  }
}
```

检查 payload：

```bash
curl http://127.0.0.1:8000/leave-audit/tasks/<request_id> | python -m json.tool
```

关闭 dry-run 后才会真实回写：

```bash
export ID_DOC_OCR_LEAVE_AUDIT_DRY_RUN=false
curl -X POST http://127.0.0.1:8000/leave-audit/tasks/<request_id>/callback
```

## 13. 联调日志追踪

`leave_audit` service 与 HTTP adapter 会输出结构化 key/value 日志，常用字段包括：

- `request_id`
- `leave_request_id`
- `attachment_id`
- `adapter_type`
- `adapter_action`
- `http_status`
- `elapsed_ms`
- `dry_run`
- `error_type`
- `error_message`

建议联调时按 `request_id` 过滤日志，并对 pending / download / run / callback 四段分别确认耗时与错误。

## 14. 演示前重置 demo 数据

使用脚本重建本地 demo SQLite：

```bash
cd /Users/anshi/clawd/id-doc-ocr
source .venv/bin/activate
python scripts/reset_leave_audit_demo.py
```

或指定数据库路径：

```bash
python scripts/reset_leave_audit_demo.py --db-path .local/leave_audit.db
```

脚本会删除并重建目标 SQLite schema，然后输出下一步演示命令。它只操作指定 `.db` 文件，不会清理源码目录。

## 15. 联调排障清单

| 问题 | 检查点 | 处理建议 |
| --- | --- | --- |
| sync 无任务 | adapter 是否为 http、pending API 是否正确 | 先 curl 假勤系统 pending API；确认响应是 list 或包含 `tasks/data` |
| 任务入库失败 | SQLite 路径、目录权限、request_id 是否为空 | 检查 `ID_DOC_OCR_LEAVE_AUDIT_DB`，确认父目录可写 |
| run 失败 | 附件 URL、download API、插件映射 | 查看任务详情 error_message；确认附件 bytes 非空 |
| OCR/analysis 异常 | backend 环境、插件名、文件内容 | 本地先用 mock backend；真实 OCR 问题单独记录样本 |
| verify 结果不符合预期 | leave_type、employee_name、日期、rule_results | 查看 `verification_json.evidence.request` 与 `rule_results` |
| callback 失败 | callback API、token、payload 字段 | 检查 HTTP status/body preview；确认假勤系统接受字段名 |
| 前端无数据 | 后端端口、Vite proxy、浏览器 console | 确认后端在 127.0.0.1:8000，前端 `/api` proxy 生效 |

## 16. 常见错误

### token 缺失

现象：pending/download/callback 返回 401 或 403。

处理：

- 确认 `ID_DOC_OCR_LEAVE_SYSTEM_TOKEN` 已设置
- 确认真实假勤系统接受 `Authorization: Bearer <token>`
- 如果 sandbox 暂不需要 token，可清空该变量并确认服务端允许匿名测试

### pending 接口非 2xx

现象：`/leave-audit/sync` 报错，日志包含 `leave system fetch pending leave attachments failed`。

处理：

- 检查 `ID_DOC_OCR_LEAVE_SYSTEM_BASE_URL`
- 检查 `ID_DOC_OCR_LEAVE_SYSTEM_PENDING_API`
- 用 curl 直接请求 pending API
- 确认响应结构是数组或 `{ "tasks": [...] }` / `{ "data": [...] }`

### 附件下载失败

现象：任务运行时进入 `ERROR`，或 error_message 指向 download。

处理：

- 如果 `attachment_url` 是完整 http(s) URL，确认该 URL 可直接 GET
- 如果是相对 id，确认 `DOWNLOAD_API` 支持 `attachment_url` query 参数
- 若真实接口使用 `{attachment_id}` path 模板，需在真实联调阶段与 adapter 约定字段替换策略或让 pending 返回完整下载 URL

### callback 失败

现象：点击“回写”失败，HTTP adapter 抛出 `push leave audit result failed`。

处理：

- 检查 `ID_DOC_OCR_LEAVE_SYSTEM_CALLBACK_API`
- 检查 token 和权限
- 对照 callback payload 示例确认假勤系统字段名
- 在假勤系统侧查看 request_id / leave_request_id 是否存在

### 本机代理干扰

现象：HTTP client 走了本机代理、报 socksio 或代理连接错误。

处理：

- 当前 `HttpLeaveSystemAdapter` 默认 `trust_env=False`，不会读取系统代理环境变量
- 如果仍出现代理问题，确认测试是否手动传入了自定义 httpx client
- 真实联调如必须走代理，应显式构造 client 并注入 adapter，而不是依赖环境变量

### 数据库路径不可写

现象：sync 或 run 时 SQLite 报 unable to open database file / permission denied。

处理：

- 检查 `ID_DOC_OCR_LEAVE_AUDIT_DB`
- 确认父目录存在且当前用户可写
- 本地建议使用 `.local/leave_audit.db`
- CI 或容器环境建议使用临时目录或挂载卷

## 17. 兼容性

本次新增 `/leave-audit/*` 路由，不改变以下既有接口：

- `GET /health`
- `GET /capabilities`
- `POST /infer`
- `POST /analyze-document`
- `POST /verify-attachment`

## 18. 验证命令

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
