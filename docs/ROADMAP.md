# ROADMAP

## 当前阶段定义
试点联调准备完成

## 30天成功标准
- 病假场景可试点
- 婚假场景可灰度
- contract 冻结
- 周报机制跑通
- 管理层材料齐备
- 可启动小范围试点

## Milestone 1 — 核验链路 MVP 收口（已完成）
- `/analyze-document` 与 `/verify-attachment` 可联调
- Approval Verification UI 三栏结构可运行
- mock / real adapter 可切换
- mismatch / error / fallback / manual review 状态已可视化

## Milestone 2 — 文档治理与试点准备（已完成）
- 建立管理层版 / 执行版双层文档体系
- 建立 docs 生命周期治理与 archive 结构
- 建立试点执行总包、README 索引、PMO 文档

## Milestone 3 — P1 冻结真实试点 contract（已完成）
- 已产出并确认 `docs/contract-pilot-v1.md`
- 已完成 `docs/contract-review-checklist.md` 评审结论
- 已完成 `docs/contract-review-meeting.md` 对齐准备
- 已确认：业务 / HR / 产品 / 工程当前无 checklist blocker
- 已明确假勤系统输入字段、输出字段、错误码
- 已明确 REVIEW / PASS / REJECT 业务定义
- 已明确人工复核语义与系统边界

## Milestone 4 — P2 病假场景试点 readiness（已完成）
- 已产出 `docs/pilot-sick-leave-readiness-v1.md`
- 已建立并补充 `docs/pilot-sick-leave-samples-v1.md`
- 已新增 `docs/sick-leave-verification-gap-analysis-v1.md` 用于治理 `analysis reject/review vs verify PASS` 冲突
- 已新增 `docs/sick-leave-verification-fix-design-v1.md` 用于最小规则修复设计
- 已完成：SICK 场景 PASS gating 最小代码实现
- 已完成：关键弱样本回归（PASS=3 / REVIEW=9 / REJECT=0，Normal 控制 0 误伤）
- 已完成：Normal 样本补齐到 `11/10`
- 已完成：新增 8 个 Normal 生成样本的 PASS 稳定性验证（PASS=8 / REVIEW=0 / REJECT=0）
- 已完成：样本三分桶最低基线达标并形成 readiness 判断依据

## Milestone 5 — P3 小范围试点准备（Ready for Launch）
- 已新增 `leave_audit` 旁路审核中台能力：支持从假勤系统适配器同步任务、执行核验、保存结果、人工复核与回调
- 已新增 React + Ant Design 假勤材料旁路审核工作台，支持任务同步、运行核验、状态筛选、详情查看、人工复核与回写
- 已新增真实假勤系统 HTTP adapter 骨架与 adapter factory，支持从 mock 演示平滑切换到真实联调
- 已新增 `docs/demo-script.md`、`docs/pilot-acceptance-checklist.md`、`.env.leave-audit.example`，试点演示、验收和环境配置材料已收口
- 已新增 `docs/leave-audit-sidecar.md` 作为假勤系统 sidecar 接入说明
- 新增 `docs/pilot-launch-readiness-v1.md` 作为试点准备主文档
- 新增 `docs/METRICS.md`，冻结成功率 / REVIEW率 / P95耗时 / 人工复核占比口径
- 新增 `docs/RISKS.md`，冻结误放行 / REVIEW率异常 / 接口失败 / rollback 触发条件
- 已完成：request_id 由调用方生成并在 analyze / verify / response / log 中贯通验证
- 已完成：10 条首轮指标采集与最小采集口径验证
- 已完成：10 条审批 rehearsal，确认 PASS / REVIEW 与 fallback 语义可执行
- 已完成：integration freeze、metrics operation、weekly review cadence、pilot roster/schedule 形成 go-live baseline
- 当前唯一剩余启动前动作：将占位审批人 roster 替换为真实命名名单并完成启动会确认

## Milestone 6 — P4 婚假场景最小稳定闭环
- 输出 marriage rules gap list
- 补齐 fixture tests 与风险说明
- 明确婚假场景灰度边界

## Milestone 7 — P5 试点运营机制运行化
- 持续更新 `docs/WEEKLY-STATUS.md`
- 让 `docs/METRICS.md` 与 `docs/RISKS.md` 进入真实运营使用
- 让周报、问题台账、指标复盘可运行

## Milestone 8 — P6 管理层决策材料完备
- 一页纸摘要可直接汇报
- 试点启动会材料可直接使用
- 管理层汇报结构可直接转 PPT

## Milestone 9 — 小范围灰度试点
- 沙箱联调
- 小规模审批人灰度使用
- 采集成功率、耗时、REVIEW率、误判案例、业务反馈

## Milestone 10 — 试点评估与扩面决策
- 输出试点结论
- 判断 continue / expand / shrink / pause
- 若进入扩面前，优先补强规则、样本、误判治理
