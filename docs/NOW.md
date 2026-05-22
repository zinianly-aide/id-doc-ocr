# NOW

## 当前阶段
试点联调准备完成

## 当前主目标
未来30天内，把当前 SICK 试点从“技术 ready”推进到“可启动试点”，优先完成 integration freeze、指标采集责任与周度 review 机制冻结、试点 roster 与启动时间窗冻结。

## 当前技术增量
- 已新增 `leave_audit` 旁路审核业务域，使现有 OCR / plugin / pipeline / verify-attachment 能力可被假勤系统以 sidecar 模式接入。
- 新增 `/leave-audit/*` API、SQLite 任务/结果/复核存储、MockLeaveSystemAdapter 与 `fixtures/sample_leave_tasks.json`。
- 新增 React + Ant Design `ui/approval-verification/` 假勤材料旁路审核工作台，用于同步、核验、详情查看、人工复核与回写。
- 新增真实假勤系统 HTTP adapter 骨架与 adapter factory，可通过环境变量在 mock/http 间切换。
- 新增 `docs/demo-script.md`、`docs/pilot-acceptance-checklist.md` 与 `.env.leave-audit.example`，试点联调演示与验收材料已收口。
- 保持 `/health`、`/capabilities`、`/infer`、`/analyze-document`、`/verify-attachment` 兼容。

## 本周重点
- 当前进入“试点联调准备完成”阶段
- 使用 demo script 完成 mock 演示彩排
- 使用 pilot acceptance checklist 对齐假勤系统 sandbox 联调验收项
- 准备真实审批人 roster、调用方 owner 与首次 sandbox 联调窗口

## 当前风险
- request_id 技术链路已验证，但真实调用方接入人还需最终点名确认
- 周度 review 节奏已定义，但实际会议邀请与执行纪律仍需业务侧锁定
- 审批人名单当前仍为占位 roster，真实命名名单是最后启动 blocker
- 真实或脱敏真实 Normal 正样本占比仍可继续提高，但不再阻塞当前 go-live freeze

## 下一检查点
- 检查点类型：是否满足小范围 SICK 试点启动条件
- 关注事项：真实审批人名单、调用方接入责任人、weekly review 排期是否全部确认
- 建议时间：启动会前最终 go/no-go 检查
