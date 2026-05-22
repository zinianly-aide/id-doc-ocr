# NOW

## 当前阶段
Sandbox dry-run 联调准备阶段

## 当前主目标
在不新增大功能的前提下，完成试点联调前小收口：消除已知非业务 warning、冻结 sandbox 联调记录模板，并用 dry-run callback 验证 pending/download/OCR/verify/callback payload 全链路后再进入真实回写。

## 当前技术增量
- 已新增 `leave_audit` 旁路审核业务域，使现有 OCR / plugin / pipeline / verify-attachment 能力可被假勤系统以 sidecar 模式接入。
- 新增 `/leave-audit/*` API、SQLite 任务/结果/复核存储、MockLeaveSystemAdapter 与 `fixtures/sample_leave_tasks.json`。
- 新增 React + Ant Design `ui/approval-verification/` 假勤材料旁路审核工作台，用于同步、核验、详情查看、人工复核与回写。
- 新增真实假勤系统 HTTP adapter 骨架与 adapter factory，可通过环境变量在 mock/http 间切换。
- 新增 dry-run callback 模式、联调结构化日志与 `scripts/reset_leave_audit_demo.py`，真实 sandbox 联调可先验 payload 再实际回写。
- 新增 `docs/demo-script.md`、`docs/pilot-acceptance-checklist.md` 与 `.env.leave-audit.example`，试点联调演示与验收材料已收口。
- 新增 `docs/sandbox-integration-log.md`，用于记录 sandbox pending/download/OCR/verify/callback dry-run/真实回写结果。
- FastAPI startup 已迁移到 lifespan，避免 `@app.on_event("startup")` deprecation warning，同时保持 `/health`、`/capabilities`、`/infer`、`/analyze-document`、`/verify-attachment`、`/leave-audit/*` 兼容。
- 前端 Vite build 已增加 `antd` / `icons` / `vendor` manualChunks，用于降低试点演示构建 warning 噪音。

## 本周重点
- 当前进入“Sandbox dry-run 联调准备阶段”
- 使用 demo script 完成 mock 演示彩排
- 使用 `docs/sandbox-integration-log.md` 逐项记录 sandbox pending/download/callback 联调结果
- 先开启 dry-run 核对 callback payload，再关闭 dry-run 进行真实回写演练
- 准备真实审批人 roster、调用方 owner 与首次 sandbox 联调窗口

## 当前风险
- request_id 技术链路已验证，但真实调用方接入人还需最终点名确认
- 周度 review 节奏已定义，但实际会议邀请与执行纪律仍需业务侧锁定
- 审批人名单当前仍为占位 roster，真实命名名单是最后启动 blocker
- 真实或脱敏真实 Normal 正样本占比仍可继续提高，但不再阻塞当前 go-live freeze

## 下一检查点
- 检查点类型：sandbox dry-run 联调记录是否完整、callback payload 是否被业务侧确认
- 关注事项：pending/download/callback 接口返回、dry-run payload 字段、真实回写结果、request_id 日志可追踪性
- 建议时间：首次 sandbox 联调完成后立即复盘

## Management Summary Implication
- 当前收口把项目从“演示材料 ready”推进到“sandbox dry-run 联调可记录、可复盘、可决定是否真实回写”的操作态。
