# id-doc-ocr 中文项目引导

[English README](../../README.md)

`id-doc-ocr` 是一个面向身份证件与弱模板文档的**自托管 OCR / KIE / 校验**系统。

目标不是只输出一段 OCR 文本，而是构建一条更接近生产可用的结构化抽取链路：

- 文档检测与分类
- 几何矫正与图像质量检查
- 字段级 OCR
- KIE / VLM 兜底
- MRZ / 条码 / 规则校验
- 低置信度人工复核

## 当前目标

- 提升证件字段级精确抽取率
- 保持链路可解释、可审计
- 用插件化方式逐步扩展文档类型
- 保持本地部署 / 自托管友好

## 当前技术路线

- **主 OCR backbone**：PaddleOCR 系列
- **复杂版式 / 弱模板增强**：PaddleOCR-VL
- **区域兜底 OCR**：GOT-OCR 2.0
- **校验层**：日期、证件号、MRZ、跨字段一致性规则

## 当前仓库状态

### 1) 架构骨架已建立

核心目录：

```text
src/id_doc_ocr/
  detector/     # 文档检测、角点检测、文档分类
  rectify/      # 透视矫正、方向校正、质量评分
  ocr/          # OCR 适配器与字段级识别
  kie/          # KIE / VLM 兜底
  validator/    # MRZ、校验码、规则一致性校验
  review/       # 人工复核能力
  pipeline/     # 流水线编排与阶段组合
  schemas/      # 结构化结果 schema
  utils/        # 公共工具
```

### 2) OCR / VLM backbone 现状

- `mock`：默认轻量 stub，便于开发流水线
- `rapidocr`：本地 smoke test 的可用基线
- `paddleocr`：已接入真实 adapter，支持懒加载运行时、结果归一化、demo wiring
- `paddleocr_vl`：已接入真实集成路径，支持运行时检测、归一化输出、`vlm_backend="auto"` 自动接入

### 3) 已补充的工程化能力

- parser regression fixtures
- public smoke-regression assets
- demo runner 对 OCR / VLM backend 的切换支持
- Paddle runtime 缺失时的 graceful fallback

## 关键文档

### 架构

- 平台 / 总体设计：`docs/architecture.md`
- 平台视角补充：`docs/platform-architecture.md`

### OCR / VLM

- PaddleOCR 本地安装与环境变量：`docs/paddleocr-setup.md`
- PaddleOCR-VL 集成说明：`docs/paddleocr-vl.md`
- PaddleOCR-VL 进展记录：`docs/paddleocr-vl-progress.md`

### 回归与质量

- 回归测试轨道：`docs/regression.md`
- 准确率操作规范：`docs/accuracy-sop.md`
- 中文版准确率规范：`docs/zh/accuracy-sop.zh-CN.md`

### 插件扩展

- plugin 接入说明：`docs/plugin-onboarding.md`

## 推荐阅读顺序

如果你是第一次进入这个 repo，建议按下面顺序看：

1. `README.md`（英文主页）
2. `docs/zh/README.zh-CN.md`（本文）
3. `docs/architecture.md`
4. `docs/regression.md`
5. `docs/paddleocr-setup.md`
6. `docs/paddleocr-vl.md`
7. `docs/plugin-onboarding.md`

## 当前阶段重点

当前更偏向于把“可扩展、可验证、可替换 backbone”的主链路先搭稳，包括：

1. repository scaffold
2. architecture and interfaces
3. OCR / VLM adapter wiring
4. regression track
5. 面向具体文档 plugin 的持续增强

## 后续方向

- 完善第一批端到端文档抽取链路
- 扩展中国身份证、护照等文档 schema / validator
- 将 VLM 输出更深地回灌到 plugin parser 与置信度融合
- 增加服务化 API 与部署清单

## 语言入口

- English: `README.md`
- 中文：`docs/zh/README.zh-CN.md`
