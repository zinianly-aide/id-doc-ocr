# 假勤材料旁路审核演示脚本

## 1. 演示目标

本脚本用于演示 `leave_audit` 旁路审核模式：系统从 mock 假勤系统同步待审核附件，执行 OCR / analysis / verify_attachment，展示 PASS / REVIEW / REJECT 三类结果，支持 HR 人工复核，并可 callback 回写审核结果。

管理摘要：演示重点不是替代现有假勤系统，而是证明 OCR 审核服务可以作为旁路中台接入既有假勤审批流。

## 2. 本地启动后端

在仓库根目录执行：

```bash
cd /Users/anshi/clawd/id-doc-ocr
source .venv/bin/activate
export ID_DOC_OCR_LEAVE_SYSTEM_ADAPTER=mock
export ID_DOC_OCR_LEAVE_AUDIT_DB=.local/leave_audit.db
python -m uvicorn id_doc_ocr.service.app:app --host 127.0.0.1 --port 8000
```

健康检查：

```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/leave-audit/stats
```

## 3. 本地启动前端

另开终端：

```bash
cd /Users/anshi/clawd/id-doc-ocr/ui/approval-verification
npm install
npm run dev
```

浏览器打开 Vite 输出地址，通常为：

```text
http://127.0.0.1:5173
```

前端默认通过 Vite proxy 将 `/api/*` 转发到：

```text
http://127.0.0.1:8000
```

## 4. Mock adapter 演示流程

Mock 数据来自：

```text
fixtures/sample_leave_tasks.json
```

包含三条代表性链路：

- `LV-MOCK-SICK-PASS-001`：病假材料，预期 PASS
- `LV-MOCK-SICK-REVIEW-001`：病假材料，预期 REVIEW
- `LV-MOCK-SICK-REJECT-001`：材料类型不匹配，预期 REJECT

## 5. 同步待审核任务

### 前端操作

点击工作台顶部操作区：

```text
同步待审核任务
```

预期：任务表格出现 mock 任务。

### 命令行操作

```bash
curl -X POST http://127.0.0.1:8000/leave-audit/sync
```

预期返回：

```json
{
  "synced": 3,
  "tasks": []
}
```

实际 `tasks` 中应包含三条 mock request_id。

演示话术：

```text
这一步模拟从现有假勤系统拉取待审核附件。当前使用 mock adapter，不依赖真实假勤系统；真实联调时只需要切换 HTTP adapter。
```

## 6. 运行 PASS / REVIEW / REJECT 三类案例

### PASS 案例

```bash
curl -X POST http://127.0.0.1:8000/leave-audit/tasks/LV-MOCK-SICK-PASS-001/run
```

预期：

```text
status = PASS
verification_json.verify_status = PASS
autoPassReadiness.status = ready
```

演示话术：

```text
PASS 表示材料类型、申请人、日期等核心规则都满足自动审核条件，可作为自动通过候选。
```

### REVIEW 案例

```bash
curl -X POST http://127.0.0.1:8000/leave-audit/tasks/LV-MOCK-SICK-REVIEW-001/run
```

预期：

```text
status = REVIEW
verification_json.verify_status = REVIEW
autoPassReadiness.status = unknown
```

演示话术：

```text
REVIEW 表示系统没有直接拒绝，但存在人员、日期、证据完整性或规则风险，需要 HR 人工复核。
```

### REJECT 案例

```bash
curl -X POST http://127.0.0.1:8000/leave-audit/tasks/LV-MOCK-SICK-REJECT-001/run
```

预期：

```text
status = REJECT
verification_json.verify_status = REJECT
autoPassReadiness.status = blocked
```

演示话术：

```text
REJECT 表示存在硬阻断，例如假别要求的材料类型与上传材料明显不一致，应建议驳回或要求补充正确材料。
```

## 7. 查看 autoPassReadiness

前端：点击任务行“详情”，在 Drawer 中查看：

```text
autoPassReadiness
```

字段说明：

- `ready`：可自动通过
- `blocked`：禁止自动通过
- `unknown`：需要人工确认
- `reasons`：需要人工确认的原因
- `blockers`：阻断自动通过的原因

命令行查看：

```bash
curl http://127.0.0.1:8000/leave-audit/tasks/LV-MOCK-SICK-PASS-001 | python -m json.tool
```

演示话术：

```text
autoPassReadiness 是给自动化审批闸门使用的摘要字段。它不替代完整规则证据，但能让假勤系统快速判断是否允许自动通过。
```

## 8. 查看 rule_results 中文解释

前端：详情 Drawer 中查看：

```text
rule_results
```

重点字段：

- `rule_code`：规则编号
- `passed`：是否通过
- `severity`：info / warning / error
- `display_message`：中文展示文案
- `evidence`：规则证据

演示话术：

```text
规则结果保留 rule_code 便于工程追踪，同时提供中文 display_message 给 HR 和审批人阅读，避免前端直接暴露英文技术提示。
```

## 9. HR 提交人工复核

### 前端操作

1. 打开 REVIEW 任务详情
2. 在“人工复核 Panel”选择：
   - PASS
   - REVIEW
   - REJECT
3. 输入 review_comment
4. 点击“提交复核按钮”

### 命令行操作

```bash
curl -X POST http://127.0.0.1:8000/leave-audit/tasks/LV-MOCK-SICK-REVIEW-001/review \
  -H 'Content-Type: application/json' \
  -d '{"decision":"PASS","reviewer":"hr01","comment":"材料补充说明已确认，人工通过"}'
```

预期：

```text
review.decision = PASS
任务状态更新为 PASS
```

演示话术：

```text
旁路审核不会取消 HR 的最终判断权。系统给出建议结论，HR 可以基于业务解释和补充材料提交最终复核意见。
```

## 10. callback 回写结果

### 前端操作

点击任务行或详情 Drawer 中的：

```text
回写
```

### 命令行操作

```bash
curl -X POST http://127.0.0.1:8000/leave-audit/tasks/LV-MOCK-SICK-PASS-001/callback
```

Mock adapter 下 callback 只写入内存；HTTP adapter 下会调用真实假勤系统 callback API。

预期 callback payload 包含：

- request_id
- leave_request_id
- verify_status
- risk_level
- risk_score
- needs_manual_review
- summary
- rule_results

演示话术：

```text
回写步骤用于把旁路审核结果送回现有假勤系统。真实接入时，假勤系统仍是主流程和最终状态归属方，OCR 服务只提供材料审核建议和证据。
```

## 11. 演示顺序建议

1. 打开工作台首页，说明“旁路审核，不替代假勤系统”。
2. 点击“同步待审核任务”，展示 mock 任务进入列表。
3. 依次运行 PASS / REVIEW / REJECT 三条任务。
4. 打开 PASS 详情，展示 autoPassReadiness=ready。
5. 打开 REVIEW 详情，展示 rule_results 中文说明和 HR 复核 Panel。
6. 打开 REJECT 详情，展示 blocker 与红色状态。
7. 对 REVIEW 任务提交 HR 复核。
8. 点击 callback，说明真实模式会回写假勤系统。
9. 最后说明 mock -> http adapter 只需切换环境变量，不需要改前端或 API 路由。

## 12. 演示风险提示

- 当前 mock 图片 bytes 仅用于流程演示，不代表真实 OCR 质量。
- 真正试点前必须使用真实或脱敏真实附件完成联调。
- HTTP adapter 已有骨架，但接口字段仍需与真实假勤系统 sandbox 对齐。
- 若浏览器请求失败，优先确认后端端口、Vite proxy、数据库路径和 adapter 环境变量。
