# WEEKLY STATUS

## 本次完成事项
- 已完成假勤系统旁路审核模式重构：新增 `leave_audit` 业务域、MockLeaveSystemAdapter、SQLiteRepository、AuditService/ReviewService、worker skeleton 与 `/leave-audit/*` API
- 已完成 React + Ant Design 假勤材料旁路审核工作台：统计卡、筛选/搜索、任务表格、详情 Drawer、人工复核 Panel、回写按钮均已接入 `/leave-audit/*` API
- 已完成真实假勤系统 HTTP adapter 骨架：支持 Bearer Token、超时、非 2xx 明确异常、pending/download/callback 三类接口与 adapter factory 环境变量切换
- 已完成 dry-run callback 模式与联调日志追踪，sandbox 联调可在不真实回写的情况下检查 callback payload
- 已新增 `scripts/reset_leave_audit_demo.py`，mock 演示可一键重置本地 SQLite 数据
- 已完成试点联调准备材料：`docs/demo-script.md`、`docs/pilot-acceptance-checklist.md`、`.env.leave-audit.example`，并进一步进入“Sandbox dry-run 联调准备阶段”
- 已新增 `docs/sandbox-integration-log.md`，用于逐项记录联调日期、环境、adapter 模式、dry-run、pending/download、OCR/verify、callback payload、真实回写、问题与结论
- 已新增 `docs/leave-system-api-contract.md`，用于与真实假勤系统 owner 对齐 pending/download/callback、鉴权、字段映射、错误码、超时与重试约定
- 已新增 `docs/callback-field-mapping-design.md`，预留未来 callback payload 字段名不一致时的配置化映射方案（本轮不实现代码）
- 已将 FastAPI startup 从 `@app.on_event("startup")` 迁移到 lifespan，消除 deprecation warning 且保持既有 API 兼容
- 已在 Vite 配置中增加 `antd` / `icons` / `vendor` manualChunks，降低试点演示构建 warning 噪音
- 已增强 verification 输出：新增 `autoPassReadiness` 与规则中文展示文案，前端可优先展示 `display_message`
- 已新增 `docs/leave-audit-sidecar.md`，说明架构、接入方式、mock adapter、API 示例、状态流转与真实 adapter 替换路径
- 已从 P3.1 Pre-Launch Validation 进入 P3.2 Go-Live Freeze
- 已冻结 request_id 真实接入责任边界
- 已明确：request_id 由调用方 / 假勤系统接入层或 pilot gateway 生成，不由验证服务首生成
- 已冻结 request_id 格式规范：`LV-SICK-YYYYMMDD-XXXXXX`
- 已把 request_id integration freeze 写入 `docs/pilot-launch-readiness-v1.md`
- 已冻结 metrics operation ownership：
  - QA + Pilot Operations Support 负责每日记录
  - Pilot Operations Support 负责每周汇总
  - Business Owner 负责 go / hold / rollback 决策
- 已冻结 weekly review cadence：每周三 `16:00 CST`
- 已确认 `docs/WEEKLY-STATUS.md` 为唯一周报源
- 已把 metrics operational ownership 写入 `docs/METRICS.md`
- 已冻结 pilot roster baseline、试点部门、启动时间窗、第一次周报时间
- 已明确 fallback / rollback 拍板人：Business Owner
- 已新增最终 Go-Live Checklist 并形成 go-live freeze baseline

## 遗留问题
- 审批人名单目前仍为占位 roster，真实命名名单还需在启动会前最终确认
- request_id 的组织责任边界已冻结，但真实调用方接入 owner 仍需最终点名确认
- 真实或脱敏真实的 Normal 正样本占比仍可继续提高，但不再阻塞当前 go-live 冻结
- sandbox pending/download/callback 的真实接口结果仍需按 `docs/sandbox-integration-log.md` 落表确认
- 真实假勤系统 callback 目标字段名仍待 owner 确认；当前仅冻结配置化映射设计，不改回写代码

## 下周建议
- 第一优先：按 `docs/demo-script.md` 完成一次 mock 演示彩排
- 第二优先：按 `docs/leave-system-api-contract.md` 与假勤系统 owner 对齐接口契约，尤其是 pending 原始字段与 callback 目标字段
- 第三优先：按 `docs/sandbox-integration-log.md` 记录 sandbox pending/download/callback dry-run 联调结果
- 第四优先：dry-run payload 被业务侧确认后，再关闭 dry-run 做一次真实 callback 回写演练
- 第五优先：在启动会前把占位审批人 roster 替换为真实命名名单，并确认 weekly review 邀请对象

## Management Summary Implication
- 当前状态从“材料 ready”推进为“sandbox dry-run 联调可执行、可审计、可决定是否真实回写”。
