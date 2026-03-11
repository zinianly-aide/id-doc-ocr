# id-doc-ocr 中文说明

`id-doc-ocr` 是一个面向多类型文档的可扩展识别平台，目标不是只做 OCR，而是做**结构化抽取 + 校验 + 可扩展插件化接入**。

## 当前方向

已支持或已建骨架：
- 中国身份证
- 护照
- 登机牌
- 车票
- 病例
- 户口本

## 架构思路

项目按三层设计：

1. **平台层**
   - registry
   - pipeline
   - internal annotation schema
   - eval/report

2. **backbone 层**
   - RapidOCR（已接入真实链路）
   - PaddleOCR（占位）
   - PaddleOCR-VL（占位）
   - GOT-OCR（占位）

3. **plugin 层**
   - 每种文档一个 plugin
   - plugin 内维护 schema / parser / validator / config / label spec / train recipe

## 当前能力

- 真实 OCR 已通过 RapidOCR 接入
- demo runner 支持 mock / rapidocr
- OCR line 可映射到 internal annotation
- boarding_pass 已完成第一版结构化抽取

## 推荐阅读顺序

1. `docs/platform-architecture.md`
2. `docs/accuracy-sop.md`
3. `docs/zh/accuracy-sop.zh-CN.md`
4. `docs/plugin-onboarding.md`
