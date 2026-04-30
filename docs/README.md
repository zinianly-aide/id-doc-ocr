# Docs Index

## Purpose

This `docs/` directory is governed with two reading layers and four lifecycle statuses.

### Reading layers

1. Executive layer — fast decision reading for business owners and HR managers
2. Execution layer — detailed planning and delivery tracking for product, engineering, QA, and pilot operations

### Lifecycle statuses

- `[CURRENT]` current primary document and default reading entry
- `[ACTIVE]` currently valid topic document that is still useful in delivery or operations
- `[ARCHIVE]` historical material kept only for traceability or historical reference
- `[PENDING ARCHIVE]` older, duplicate, draft-like, or transitional material moved out of the main reading path but still kept for possible reference before final retirement

Use this index before opening individual documents.

---

## Default Reading Entry

### PMO / 项目推进常驻文档

- `[CURRENT]` `docs/NOW.md`
  - 当前阶段、主目标、本周重点、风险、下一检查点
- `[CURRENT]` `docs/WEEKLY-STATUS.md`
  - 最近一轮完成事项、遗留问题、下周建议
- `[CURRENT]` `docs/ROADMAP.md`
  - 当前里程碑状态与下一阶段路线图
- `[CURRENT]` `docs/pilot-launch-readiness-v1.md`
  - P3 试点准备主文档：readiness 总结、试点范围冻结、运行方式、request_id、风险与启动清单
- `[CURRENT]` `docs/METRICS.md`
  - 小范围试点启动期核心指标定义：成功率、REVIEW率、P95耗时、人工复核占比
- `[CURRENT]` `docs/RISKS.md`
  - 小范围试点启动期风险与回滚文档：误放行、REVIEW率异常、接口失败、traceability 失败
- `[CURRENT]` `docs/pilot-sick-leave-samples-v1.md`
  - 病假样本台账、分类结构、最小样本规模、联调/回归/误判分析使用方式
- `[CURRENT]` `docs/sick-leave-verification-gap-analysis-v1.md`
  - 病假场景 `analysis reject/review vs verify PASS` 冲突专项文档、误判清单、修复方向与回归范围
- `[CURRENT]` `docs/sick-leave-verification-fix-design-v1.md`
  - SICK 场景最小规则修复设计：gating、字段门槛、执行顺序、影响评估与回归方案
- `[ACTIVE]` `docs/contract-review-checklist.md`
  - contract 候选版评审检查清单
- `[ACTIVE]` `docs/contract-review-meeting.md`
  - contract review 会议简版材料
- `[ACTIVE]` `docs/contract-review-execution.md`
  - contract review 会议执行版
- `[ACTIVE]` `docs/contract-review-blockers.md`
  - contract review blocker 台账


### Executive / management readers

1. `[CURRENT]` `docs/01-executive/pilot-summary-v1.md`
2. `[CURRENT]` `docs/pilot-execution-package-v1.md` (only if more detail is needed)

### Delivery / implementation readers

1. `[CURRENT]` `docs/pilot-execution-package-v1.md`
2. Relevant `[ACTIVE]` topic documents based on role and task

---

## Role-Based Recommended Reading Order

### If you are a business owner or HR manager

1. `[CURRENT]` `docs/01-executive/pilot-summary-v1.md`
2. `[CURRENT]` `docs/contract-pilot-v1.md`
3. `[CURRENT]` `docs/pilot-sick-leave-readiness-v1.md`
4. `[CURRENT]` `docs/pilot-sick-leave-samples-v1.md`
5. `[CURRENT]` `docs/sick-leave-verification-gap-analysis-v1.md`
6. `[CURRENT]` `docs/sick-leave-verification-fix-design-v1.md`
7. `[CURRENT]` `docs/pilot-execution-package-v1.md`
8. `[ACTIVE]` `docs/leave-verification-matrix-and-demo.md` (only if rule scope detail is needed)

### If you are a product / process lead

1. `[CURRENT]` `docs/contract-pilot-v1.md`
2. `[CURRENT]` `docs/pilot-sick-leave-readiness-v1.md`
3. `[CURRENT]` `docs/pilot-sick-leave-samples-v1.md`
4. `[CURRENT]` `docs/sick-leave-verification-gap-analysis-v1.md`
5. `[CURRENT]` `docs/sick-leave-verification-fix-design-v1.md`
6. `[CURRENT]` `docs/pilot-execution-package-v1.md`
7. `[ACTIVE]` `docs/frontend-api-contract.md`
8. `[ACTIVE]` `docs/frontend-binding-guide.md`
9. `[ACTIVE]` `docs/approval-verification-ui.md`
10. `[ACTIVE]` `docs/leave-verification-matrix-and-demo.md`

### If you are a backend / frontend engineer

1. `[CURRENT]` `docs/contract-pilot-v1.md`
2. `[CURRENT]` `docs/pilot-execution-package-v1.md`
3. `[ACTIVE]` `docs/frontend-api-contract.md`
4. `[ACTIVE]` `docs/frontend-binding-guide.md`
5. `[ACTIVE]` `docs/api.md`
6. `[ACTIVE]` `docs/architecture.md`
7. `[ACTIVE]` `docs/approval-verification-ui.md`
8. `[ACTIVE]` `docs/regression.md`

### If you are QA or pilot operations support

1. `[CURRENT]` `docs/contract-pilot-v1.md`
2. `[CURRENT]` `docs/pilot-sick-leave-readiness-v1.md`
3. `[CURRENT]` `docs/pilot-sick-leave-samples-v1.md`
4. `[CURRENT]` `docs/sick-leave-verification-gap-analysis-v1.md`
5. `[CURRENT]` `docs/sick-leave-verification-fix-design-v1.md`
6. `[CURRENT]` `docs/pilot-execution-package-v1.md`
7. `[ACTIVE]` `docs/leave-verification-matrix-and-demo.md`
8. `[ACTIVE]` `docs/regression.md`
9. `[ACTIVE]` `docs/frontend-api-contract.md`

---

## Two-Layer Document Structure

### Layer 1 — Executive Edition

Folder:
- `docs/01-executive/`

Documents:
- `[CURRENT]` `docs/01-executive/pilot-summary-v1.md`
  - 5-minute management summary for pilot approval and governance

### Layer 2 — Execution Edition

Primary document:
- `[CURRENT]` `docs/pilot-execution-package-v1.md`
  - source of truth for pilot implementation plan, weekly schedule, RACI, reporting templates, kickoff package, and management briefing structure

### Archive Layer

Folders:
- `docs/archive/`
- `docs/archive/presentations/`
- `docs/archive/plans/`
- `docs/archive/prototypes/`

These folders keep documents that are no longer part of the default reading path.

---

## Lifecycle Classification by Topic

### A. Pilot governance and primary reading entry

- `[CURRENT]` `docs/01-executive/pilot-summary-v1.md`
- `[CURRENT]` `docs/pilot-execution-package-v1.md`
- `[CURRENT]` `docs/contract-pilot-v1.md`
- `[CURRENT]` `docs/pilot-sick-leave-readiness-v1.md`
- `[CURRENT]` `docs/pilot-launch-readiness-v1.md`
- `[CURRENT]` `docs/METRICS.md`
- `[CURRENT]` `docs/RISKS.md`
- `[CURRENT]` `docs/pilot-sick-leave-samples-v1.md`
- `[CURRENT]` `docs/sick-leave-verification-gap-analysis-v1.md`
- `[CURRENT]` `docs/sick-leave-verification-fix-design-v1.md`
- `[CURRENT]` `docs/README.md`
- `[CURRENT]` `docs/NOW.md`
- `[CURRENT]` `docs/WEEKLY-STATUS.md`
- `[CURRENT]` `docs/ROADMAP.md`

### B. Active approval-verification topic documents

- `[ACTIVE]` `docs/frontend-api-contract.md`
- `[ACTIVE]` `docs/frontend-binding-guide.md`
- `[ACTIVE]` `docs/approval-verification-ui.md`
- `[ACTIVE]` `docs/leave-verification-matrix-and-demo.md`
- `[ACTIVE]` `docs/api.md`
- `[ACTIVE]` `docs/architecture.md`
- `[ACTIVE]` `docs/regression.md`

### C. Active supporting technical references

- `[ACTIVE]` `docs/deployment.md`
- `[ACTIVE]` `docs/platform-architecture.md`
- `[ACTIVE]` `docs/plugin-maturity.md`
- `[ACTIVE]` `docs/plugin-onboarding.md`
- `[ACTIVE]` `docs/accuracy-sop.md`
- `[ACTIVE]` `docs/paddleocr-vl.md`
- `[ACTIVE]` `docs/paddleocr-setup.md`

### D. Pending archive — older, overlapping, or transitional materials

These documents are physically moved out of the docs root, but may still contain useful context.

- `[PENDING ARCHIVE]` `docs/archive/approval-verification-react-skeleton.md`
  - older scaffold-level UI planning; partially superseded by current execution package and implemented UI docs
- `[PENDING ARCHIVE]` `docs/archive/paddleocr-vl-progress.md`
  - progress-style note rather than stable reference
- `[PENDING ARCHIVE]` `docs/archive/presentations/id-doc-ocr-presentation.md`
  - older presentation draft
- `[PENDING ARCHIVE]` `docs/archive/presentations/id-doc-ocr-presentation-marp.md`
  - presentation source, likely superseded by later deck variants
- `[PENDING ARCHIVE]` `docs/archive/presentations/id-doc-ocr-presentation-feishu.md`
  - channel-specific presentation version, not a canonical source
- `[PENDING ARCHIVE]` `docs/archive/plans/2026-03-11-accuracy-implementation.md`
  - historical implementation plan
- `[PENDING ARCHIVE]` `docs/archive/plans/2026-04-17-p1-p5-hardening.md`
  - historical hardening plan
- `[PENDING ARCHIVE]` `docs/archive/plans/2026-03-11-platform-design.md`
  - historical platform design plan

### E. Archive — historical or trace-only assets

- `[ARCHIVE]` `docs/archive/prototypes/approval-verification-page.html`
  - historical prototype artifact for UI traceability
- `[ARCHIVE]` `docs/archive/README.zh-CN.md`
  - localized historical overview; useful for reference only unless actively maintained again
- `[ARCHIVE]` `docs/archive/accuracy-sop.zh-CN.md`
  - localized SOP reference; not the primary maintained source
- `[ARCHIVE]` `docs/archive/id-doc-ocr-arch.mmd`
  - diagram source artifact
- `[ARCHIVE]` `docs/archive/id-doc-ocr-arch.png`
  - diagram export artifact
- `[ARCHIVE]` `docs/archive/presentations/id-doc-ocr-presentation.pptx`
  - historical binary presentation artifact
- `[ARCHIVE]` `docs/archive/presentations/id-doc-ocr-presentation-v2.pptx`
  - historical binary presentation artifact
- `[ARCHIVE]` `docs/archive/presentations/id-doc-ocr-presentation-v3.pptx`
  - historical binary presentation artifact

---

## Suggested Long-Term Maintenance Set

The following files should be maintained as the long-term living set for the current approval-verification and pilot track:

- `docs/README.md`
- `docs/01-executive/pilot-summary-v{n}.md`
- `docs/pilot-execution-package-v{n}.md`
- `docs/contract-pilot-v{n}.md`
- `docs/pilot-sick-leave-readiness-v{n}.md`
- `docs/pilot-launch-readiness-v{n}.md`
- `docs/METRICS.md`
- `docs/RISKS.md`
- `docs/pilot-sick-leave-samples-v{n}.md`
- `docs/sick-leave-verification-gap-analysis-v{n}.md`
- `docs/sick-leave-verification-fix-design-v{n}.md`
- `docs/frontend-api-contract.md`
- `docs/frontend-binding-guide.md`
- `docs/approval-verification-ui.md`
- `docs/leave-verification-matrix-and-demo.md`
- `docs/api.md`
- `docs/architecture.md`
- `docs/regression.md`

Everything else should be maintained only when it has an active operational or delivery reason.

---

## Docs Root Retention Rule

Files should remain in the docs root only if they are:

1. `[CURRENT]` default reading entries, or
2. `[ACTIVE]` topic documents used in ongoing delivery, integration, QA, or pilot operations.

Historical, duplicate, presentation-specific, prototype, or transitional planning materials should be moved under `docs/archive/`.

---

## Governance Rules for Future Planning Documents

1. Executive-facing pilot summaries go under `docs/01-executive/` and must be versioned.
2. Detailed pilot governance stays centralized in `docs/pilot-execution-package-v{n}.md` unless a split is clearly justified.
3. If a planning topic changes materially, create a new versioned document instead of silently rewriting decision history.
4. New documents should be added only if existing `[CURRENT]` or `[ACTIVE]` documents cannot reasonably absorb the content.
5. If a document becomes duplicate, obsolete, or draft-like, move it into `docs/archive/` and reflect its lifecycle state in this index.
6. Avoid using `[PENDING ARCHIVE]` or `[ARCHIVE]` files as the default reading entry in meetings or implementation tasks.

---

## Suggested Reading Path by Current Task

### Task: decide whether to approve the pilot
- Read `[CURRENT]` `docs/01-executive/pilot-summary-v1.md`
- Then `[CURRENT]` `docs/contract-pilot-v1.md`
- Then `[CURRENT]` `docs/pilot-sick-leave-readiness-v1.md`
- Then `[CURRENT]` `docs/sick-leave-verification-gap-analysis-v1.md`
- Then `[CURRENT]` `docs/sick-leave-verification-fix-design-v1.md`

### Task: prepare kickoff meeting or weekly pilot operation
- Read `[CURRENT]` `docs/contract-pilot-v1.md`
- Then `[CURRENT]` `docs/pilot-sick-leave-readiness-v1.md`
- Then `[CURRENT]` `docs/sick-leave-verification-gap-analysis-v1.md`
- Then `[CURRENT]` `docs/sick-leave-verification-fix-design-v1.md`
- Then read `[CURRENT]` `docs/pilot-execution-package-v1.md`

### Task: implement or debug approval verification UI/API integration
- Read `[CURRENT]` `docs/contract-pilot-v1.md`
- Then `[ACTIVE]` `docs/frontend-api-contract.md`
- Then `[ACTIVE]` `docs/frontend-binding-guide.md`
- Then `[ACTIVE]` `docs/approval-verification-ui.md`
- Then `[ACTIVE]` `docs/api.md`

### Task: understand the minimal business rule scope
- Read `[ACTIVE]` `docs/leave-verification-matrix-and-demo.md`

### Task: understand historical technical planning context
- Read archive materials only when traceability is needed:
  - `docs/archive/plans/`
  - `docs/archive/presentations/`
  - `docs/archive/prototypes/`
