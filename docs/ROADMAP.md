# ROADMAP

## 当前阶段定义
试点准备冲刺期（Pilot Readiness Sprint）

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

## Milestone 4 — P2 病假场景试点 readiness（Fix Design In Progress）
- 已产出 `docs/pilot-sick-leave-readiness-v1.md`
- 已建立并补充 `docs/pilot-sick-leave-samples-v1.md`
- 已新增 `docs/sick-leave-verification-gap-analysis-v1.md` 用于治理 `analysis reject/review vs verify PASS` 冲突
- 已新增 `docs/sick-leave-verification-fix-design-v1.md` 用于最小规则修复设计
- 待落地：病假场景 Normal 正样本继续补齐
- 待落地：SICK 场景 PASS 偏宽松问题的最小化代码实现
- 待落地：病假试点指标基线真实采集
- 待落地：病假试点 SOP 执行验证
- 目标：使病假场景成为首个稳定试点对象

## Milestone 5 — P3 婚假场景最小稳定闭环
- 输出 marriage rules gap list
- 补齐 fixture tests 与风险说明
- 明确婚假场景灰度边界

## Milestone 6 — P4 试点运营机制落地
- 持续更新 `docs/WEEKLY-STATUS.md`
- 建立 `docs/METRICS.md`
- 建立 `docs/RISKS.md`
- 让周报、问题台账、指标复盘可运行

## Milestone 7 — P5 管理层决策材料完备
- 一页纸摘要可直接汇报
- 试点启动会材料可直接使用
- 管理层汇报结构可直接转 PPT

## Milestone 8 — 小范围灰度试点
- 沙箱联调
- 小规模审批人灰度使用
- 采集成功率、耗时、REVIEW率、误判案例、业务反馈

## Milestone 9 — 试点评估与扩面决策
- 输出试点结论
- 判断 continue / expand / shrink / pause
- 若进入扩面前，优先补强规则、样本、误判治理
