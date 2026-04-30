# WEEKLY STATUS

## 本次完成事项
- 已 push P1 / P1.5 / P1.6 文档治理与 contract 确认成果
- 已正式进入 P2：Sick Leave Pilot Readiness
- 新增 `docs/pilot-sick-leave-readiness-v1.md`
- 已定义病假场景样本体系、指标基线、运行 SOP、风险说明、验收标准
- 已建立病假样本结构：Normal / Abnormal / Edge
- 新增 `docs/pilot-sick-leave-samples-v1.md` 作为样本台账基线
- 已补录 19 条可证明来源的病假样本案例
- 已标记 10 个关键样本，真实来源占比 68.4%（13/19）
- 当前样本填充进度：Normal 3/10，Abnormal 10/10，Edge 6/5
- 已抓取一批 Wikimedia Commons 公开医疗文档图到 `examples/assets/sick_leave_public/commons/`
- 已对其中 9 张公开样本跑真实接口验证，并确认存在 `analysis=reject` 但 `verify_status=PASS` 的偏宽松冲突

## 遗留问题
- Normal 桶仍明显不足，尚未达到 10 条目标
- 公开样本虽补足了 Abnormal / Edge，但与真实病假正样本仍有语义差距
- `verify-attachment` 对弱质医疗文书样本存在 PASS 偏宽松问题，需后续单独收口
- request_id 仍需在真实接入实现中按 contract 落地
- 指标基线尚未开始真实采集
- 试点运营文档 `docs/METRICS.md`、`docs/RISKS.md` 尚未建立

## 下周建议
- 第一优先：继续补充更接近标准病假证明的公开或脱敏真实 Normal 样本
- 第二优先：围绕 `analysis reject` vs `verify PASS` 冲突建立专项误判清单
- 第三优先：建立试点指标采集文档
