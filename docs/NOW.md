# NOW

## 当前阶段
Sick Leave Pilot Readiness

## 当前主目标
未来30天内，把项目推进到“可启动小范围业务试点”的状态，优先完成真实试点 contract 冻结、病假场景 readiness、婚假场景灰度准备、运营机制落地和管理层材料齐备。

## 本周重点
- 进入“P2.3 最小规则修复实现（SICK PASS gating） / Fix Implementation”阶段
- 已实现 SICK 场景 PASS gating，阻断 weak PASS 输出
- 已完成关键回归与全量 pytest 验证
- 仅推进病假场景，不扩展到婚假，并保持 contract v1 不变

## 当前风险
- Normal 病假正样本仍不足，当前样本池偏向 Abnormal / Edge
- 最小修复已收紧 PASS，短期可能提高 REVIEW 率
- request_id 仍需在真实接入实现中按 contract 落地
- 指标口径已定义，但尚未进入真实采集
- 试点部门、审批人名单、业务侧实际运行安排尚未冻结

## 下一检查点
- 检查点类型：病假试点 readiness 是否具备启动条件
- 关注事项：样本三分桶、指标基线、审批 SOP、人工兜底是否可执行
- 建议时间：进入样本准备或试点启动会前立即检查
