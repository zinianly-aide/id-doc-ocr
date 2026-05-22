# Sandbox Integration Log

## Purpose

This template records each leave-system sandbox dry-run integration session before real callback writeback is enabled. Keep one filled copy per session, or duplicate the checklist blocks under dated headings.

## Session Metadata

- 联调日期：2026-05-23
- 联调环境：sandbox / 待填写
- 参与方：OCR sidecar / 假勤系统 adapter owner / QA / Pilot Operations Support
- 记录人：待填写
- 关联 request_id：待填写
- 关联 leave_request_id：待填写

## Adapter Configuration

- adapter 模式：mock / http / 待填写
- `ID_DOC_OCR_LEAVE_SYSTEM_ADAPTER`：待填写
- `ID_DOC_OCR_LEAVE_SYSTEM_BASE_URL`：待填写
- `ID_DOC_OCR_LEAVE_SYSTEM_FIELD_MAPPING_FILE`：默认 `configs/leave_system_field_mapping.yaml` / 自定义路径 / 未配置
- `ID_DOC_OCR_LEAVE_AUDIT_DB`：待填写
- dry-run 是否开启：是 / 否 / 待填写
- `ID_DOC_OCR_LEAVE_AUDIT_DRY_RUN`：true / false / 待填写

## Integration Checklist

| 项目 | 记录内容 | 结果 |
| --- | --- | --- |
| pending 接口结果 | 请求时间、HTTP status、返回任务数、关键 request_id | 待填写 |
| pending 字段映射结果 | 外部字段名、是否被映射为内部 canonical field、是否需更新 mapping 文件 | 待填写 |
| download 接口结果 | attachment_id、HTTP status、文件大小、content-type、耗时 | 待填写 |
| OCR/verify 结果 | plugin、analysis.doc_type、analysis.review.action、verify_status、risk_level、needs_manual_review | 待填写 |
| callback dry-run payload 检查 | `dry_run=true` 时 payload 是否含 request_id、leave_request_id、verify_status、risk_level、summary、rule_results | 待填写 |
| callback 真实回写结果 | `dry_run=false` 时 HTTP status、对方响应摘要、是否标记 SYNCED | 待填写 |
| 结构化日志检查 | 是否可按 request_id 检索 pending/download/OCR/verify/callback 全链路日志 | 待填写 |

## Detailed Notes

### 1. Pending 接口结果

- 请求命令或调用入口：待填写
- HTTP status：待填写
- 返回任务数：待填写
- 样例 request_id：待填写
- 样例 leave_request_id：待填写
- 外部原始字段名示例：如 `applyNo` / `empName` / `absenceType` / `fileUrl` / 待填写
- 字段映射文件：`configs/leave_system_field_mapping.yaml` / 自定义路径 / 未使用
- 字段差异记录：无 / 待填写
- 需要新增或调整的别名：无 / 待填写
- 异常或非预期字段：无 / 待填写

#### Pending response 原始样例记录区

粘贴 pending 原始响应样例，必要时先脱敏：

```json
{
  "tasks": []
}
```

字段映射检查表：

| 原始字段名 | 原始样例值 | 内部字段名 | 是否已配置 mapping | 是否需要代码改动 | 备注 |
| --- | --- | --- | --- | --- | --- |
| `applyNo` | `LR-...` | `leave_request_id` | 是 / 否 | 否 | 示例 |
| `empName` | `张三` | `employee_name` | 是 / 否 | 否 | 示例 |
| `fileUrl` | `https://...` | `attachment_url` | 是 / 否 | 否 | 示例 |

处理规则：字段名差异优先更新 `configs/leave_system_field_mapping.yaml` 或 `ID_DOC_OCR_LEAVE_SYSTEM_FIELD_MAPPING_FILE` 指向的外部 mapping 文件；只有 response 结构无法通过 mapping 表达时，才评估代码改动。

### 2. Download 接口结果

- attachment_id：待填写
- attachment_url：待填写
- HTTP status：待填写
- 文件大小：待填写
- content-type：待填写
- 下载耗时：待填写
- 异常或非预期字段：无 / 待填写

### 3. OCR / Verify 结果

- plugin：待填写
- OCR backend：待填写
- detector / rectify：待填写
- `analysis.doc_type`：待填写
- `analysis.validation.accepted`：待填写
- `analysis.risk.review_action`：待填写
- `verification.verify_status`：待填写
- `verification.risk_level`：待填写
- `verification.needs_manual_review`：待填写
- `autoPassReadiness`：待填写
- 关键 rule_results：待填写

### 4. Callback Dry-Run Payload 检查

- API 响应是否包含 `dry_run: true`：是 / 否 / 待填写
- API 响应是否包含 `callback_skipped: true`：是 / 否 / 待填写
- `callback_payload.request_id`：待填写
- `callback_payload.leave_request_id`：待填写
- `callback_payload.verify_status`：待填写
- `callback_payload.risk_level`：待填写
- `callback_payload.summary`：待填写
- `callback_payload.rule_results` 条数：待填写
- payload 是否已持久化到 `result.verification_json.callback_dry_run.payload`：是 / 否 / 待填写

### 5. Callback 真实回写结果

仅在 dry-run 关闭后填写。

- `ID_DOC_OCR_LEAVE_AUDIT_DRY_RUN=false` 是否确认：是 / 否 / 待填写
- 回写 API HTTP status：待填写
- 对方响应摘要：待填写
- 本地 task status 是否更新为 `SYNCED`：是 / 否 / 待填写
- 本地 result.synced 是否为 true：是 / 否 / 待填写
- 回写失败时错误类型 / 错误信息：无 / 待填写

## 问题记录

| 编号 | 时间 | request_id | 问题描述 | 影响 | owner | 处理状态 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 待填写 | 待填写 | 待填写 | 待填写 | 待填写 | Open / Closed |

## 处理结论

- 本次联调结论：通过 / 条件通过 / 不通过 / 待填写
- 是否允许进入真实 callback 回写：是 / 否 / 待填写
- 阻塞项：无 / 待填写
- 非阻塞 warning：如 Vite chunk warning，仅前端构建体积提示，不影响 sandbox API 联调；如已通过 manualChunks 消除则记录为已处理。

## 下一步动作

| 动作 | owner | 截止时间 | 状态 |
| --- | --- | --- | --- |
| 完成 pending/download/callback sandbox 凭据确认 | 待填写 | 待填写 | Open |
| 完成 dry-run payload 复核 | 待填写 | 待填写 | Open |
| 完成一次 dry-run=false 真实回写演练 | 待填写 | 待填写 | Open |
| 更新 `docs/WEEKLY-STATUS.md` 联调结论 | Pilot Operations Support | 待填写 | Open |
