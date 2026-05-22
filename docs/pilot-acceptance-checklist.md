# 假勤材料旁路审核试点验收清单

## 1. 试点范围

本次试点覆盖以下假勤材料审核场景：

- 婚假：`MARRIAGE`，核心材料为结婚证 `marriage_certificate`
- 病假：`SICK`，核心材料为诊断证明 `diagnosis_proof`
- 出生证明相关假别：`MATERNITY` / `PATERNITY` / `PARENTAL`，核心材料为出生医学证明 `birth_certificate`

暂不把所有证照类型纳入首轮试点；超出范围的材料进入 REVIEW 或人工处理。

## 2. 接入方式

接入方式：旁路审核。

含义：

- 现有假勤系统仍负责请假申请、审批流、最终状态和业务归档。
- `id-doc-ocr` 通过 `leave_audit` 域拉取待审核附件，执行 OCR / analysis / verification。
- 审核结果通过 callback 回写给假勤系统。
- HR 可在旁路工作台中查看证据并提交人工复核结论。

管理摘要：验收重点是证明旁路审核链路可联通、可追踪、可人工兜底，且不破坏既有 OCR API。

## 3. 验收清单

| 验收项 | 验收方式 | 通过标准 | 负责人 | 备注 |
| --- | --- | --- | --- | --- |
| 假勤系统 pending 接口联通 | 设置 `ID_DOC_OCR_LEAVE_SYSTEM_ADAPTER=http` 后执行 `POST /leave-audit/sync` | HTTP adapter 能获取 pending 响应；非 2xx 能抛出明确错误；返回任务可转换为 `LeaveAuditTask` | 后端负责人 / 假勤系统接口负责人 | mock 模式先验证本地流程，真实模式使用 sandbox |
| 附件下载成功 | 对 pending 任务执行 `POST /leave-audit/tasks/{request_id}/run`，观察下载步骤 | `download_attachment()` 返回非空 bytes；下载失败时任务进入 `ERROR` 且错误可见 | 后端负责人 / 文件服务负责人 | 支持完整 URL 或 download API query 模式 |
| 任务入库成功 | sync 后查询 `GET /leave-audit/tasks` 与 SQLite 表 | 任务状态从 pending 源进入本地库，状态为 `PULLED`；request_id 唯一可查 | 后端负责人 | 数据库路径由 `ID_DOC_OCR_LEAVE_AUDIT_DB` 控制 |
| OCR/analysis 成功 | 运行任务后查看详情 Drawer 或 `GET /leave-audit/tasks/{request_id}` | `analysis_json` 存在，包含 doc_type、classification_evidence、extracted_fields、validation、risk 等关键字段 | OCR/算法负责人 | mock bytes 仅验证流程；真实材料需单独验收 OCR 质量 |
| verify_attachment 成功 | 运行任务后查看 `verification_json` | 输出 `verify_status`、risk_level、risk_score、rule_results、autoPassReadiness | 后端负责人 / 规则负责人 | 前端展示应优先使用中文 `display_message` |
| PASS / REVIEW / REJECT 状态正确 | 分别运行三类样例和真实试点样本 | PASS 仅用于低风险自动通过候选；REVIEW 进入人工复核；REJECT 有明确 blocker | 规则负责人 / HR 负责人 | 首轮以不误放行为优先，必要时 REVIEW 偏保守 |
| HR 复核可提交 | 在工作台详情 Drawer 的人工复核 Panel 提交 PASS / REVIEW / REJECT | `POST /leave-audit/tasks/{request_id}/review` 返回成功；review 记录可查询；任务状态更新 | HR 负责人 / 前端负责人 | reviewer 和 comment 必须可追踪 |
| callback 可回写 | 点击工作台“回写”或调用 callback API | HTTP adapter 向假勤系统发送 request_id、leave_request_id、verify_status、risk、summary、rule_results；假勤系统侧可查 | 后端负责人 / 假勤系统接口负责人 | mock 模式只记录内存，不代表真实回写成功 |
| 错误可追踪 | 人为触发 token 错误、pending 非 2xx、下载失败、callback 失败 | API 返回明确错误；任务进入 ERROR 或操作报错；日志可按 request_id 排查 | 后端负责人 / QA | 联调阶段保留失败样例和日志片段 |
| 原有接口兼容 | 执行 pytest，并抽查原有 API | `/health`、`/capabilities`、`/infer`、`/analyze-document`、`/verify-attachment` 均不受影响；全量测试通过 | 后端负责人 / QA | 当前基线：pytest 全量通过 |

## 4. 试点通过标准

试点联调可进入小范围试运行需同时满足：

1. mock 模式 PASS / REVIEW / REJECT 三类流程全部可演示。
2. HTTP adapter 能连通真实假勤系统 sandbox pending / download / callback。
3. 至少婚假、病假、出生证明相关假别各有一条真实或脱敏真实样例完成端到端验证。
4. HR 人工复核流程可用，且 reviewer/comment 可追踪。
5. callback 后假勤系统侧能看到审核摘要和规则证据。
6. 失败场景能定位到 request_id、接口、状态码和错误摘要。
7. 原有 OCR API 和现有前端构建不回归。

## 5. 验收记录模板

| 日期 | 场景 | request_id | 结果 | 验收人 | 问题编号/备注 |
| --- | --- | --- | --- | --- | --- |
| TBD | SICK | TBD | TBD | TBD | TBD |
| TBD | MARRIAGE | TBD | TBD | TBD | TBD |
| TBD | MATERNITY/PATERNITY/PARENTAL | TBD | TBD | TBD | TBD |
