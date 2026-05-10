import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { buildApprovalPageModel } from "../src/adapters/viewModelBuilders.ts";

const TEST_DIR = dirname(fileURLToPath(import.meta.url));

function loadPageModel() {
  const fixturePath = resolve(TEST_DIR, "../../../examples/mock-ui/approval-verification-page.pass.json");
  return JSON.parse(readFileSync(fixturePath, "utf-8"));
}

test("buildApprovalPageModel uses latest analyze request_id in request header when analyze response is refreshed", () => {
  const rawPageModel = loadPageModel();
  const rawAnalyzeResponse = {
    ...rawPageModel.analyzeResponse,
    request_id: "LV-SICK-ANALYZE-123",
  };

  const viewModel = buildApprovalPageModel({
    rawPageModel,
    rawAnalyzeResponse,
  });

  assert.equal(viewModel.requestHeader.requestId, "LV-SICK-ANALYZE-123");
});

test("buildApprovalPageModel uses latest verify request payload in header and attachment metadata", () => {
  const rawPageModel = loadPageModel();
  const rawVerifyResponse = {
    ...rawPageModel.verifyResponse,
    request_id: "LV-SICK-VERIFY-456",
    filename: "diagnosis_generated_001.png",
    verification: {
      ...rawPageModel.verifyResponse.verification,
      evidence: {
        ...rawPageModel.verifyResponse.verification.evidence,
        request: {
          ...rawPageModel.verifyResponse.verification.evidence.request,
          applicant_name: "张三",
          leave_type: "SICK",
          leave_start_date: "2026-03-10",
          leave_end_date: "2026-03-16",
        },
      },
    },
  };

  const viewModel = buildApprovalPageModel({
    rawPageModel,
    rawVerifyResponse,
  });

  assert.equal(viewModel.requestHeader.requestId, "LV-SICK-VERIFY-456");
  assert.equal(viewModel.requestHeader.applicantName, "张三");
  assert.equal(viewModel.requestHeader.leaveType, "SICK");
  assert.equal(viewModel.requestHeader.leaveDateRange, "2026-03-10 ~ 2026-03-16");
  assert.equal(viewModel.attachments[0]?.filename, "diagnosis_generated_001.png");
});

test("buildApprovalPageModel derives quality review reason when review has no warnings but still needs manual review", () => {
  const rawPageModel = loadPageModel();
  const rawVerifyResponse = {
    ...rawPageModel.verifyResponse,
    verification: {
      ...rawPageModel.verifyResponse.verification,
      verify_status: "REVIEW",
      warnings: [],
      needs_manual_review: true,
      rule_results: rawPageModel.verifyResponse.verification.rule_results.map((rule: { passed: boolean }) => ({
        ...rule,
        passed: true,
      })),
    },
  };

  const viewModel = buildApprovalPageModel({
    rawPageModel,
    rawVerifyResponse,
  });

  assert.equal(
    viewModel.verification.reviewReasonHint,
    "业务字段已基本匹配，但材料质量门控/识别置信度仍未达到自动通过标准，建议人工复核。",
  );
});

test("buildApprovalPageModel classifies analysis risk separately from verification risk", () => {
  const rawPageModel = loadPageModel();
  const rawVerifyResponse = {
    ...rawPageModel.verifyResponse,
    analysis: {
      ...rawPageModel.verifyResponse.analysis,
      validation: {
        ...rawPageModel.verifyResponse.analysis.validation,
        accepted: true,
        issues: [],
      },
      review: {
        ...rawPageModel.verifyResponse.analysis.review,
        decision: {
          ...rawPageModel.verifyResponse.analysis.review.decision,
          review_recommended: true,
          quality_passed: false,
          validation_accepted: true,
        },
      },
      risk: {
        ...rawPageModel.verifyResponse.analysis.risk,
        review_recommended: true,
        quality_passed: false,
        validation_accepted: true,
      },
    },
    verification: {
      ...rawPageModel.verifyResponse.verification,
      verify_status: "REVIEW",
      risk_level: "LOW",
      warnings: [],
      needs_manual_review: true,
      rule_results: rawPageModel.verifyResponse.verification.rule_results.map((rule: { passed: boolean }) => ({
        ...rule,
        passed: true,
      })),
    },
  };

  const viewModel = buildApprovalPageModel({
    rawPageModel,
    rawVerifyResponse,
  });

  assert.equal(viewModel.analysis.riskCategory.label, "识别/材料风险");
  assert.equal(viewModel.analysis.riskCategory.level, "HIGH");
  assert.match(viewModel.analysis.riskCategory.summary, /质量门控|自动通过/);
  assert.equal(viewModel.verification.riskCategory.label, "业务核验风险");
  assert.equal(viewModel.verification.riskCategory.level, "LOW");
  assert.match(viewModel.verification.riskCategory.summary, /业务字段已基本匹配|规则/);
});

test("buildApprovalPageModel derives layered explainability buckets for quality integrity and rule mismatch", () => {
  const rawPageModel = loadPageModel();
  const rawVerifyResponse = {
    ...rawPageModel.verifyResponse,
    analysis: {
      ...rawPageModel.verifyResponse.analysis,
      review: {
        ...rawPageModel.verifyResponse.analysis.review,
        warnings: [
          {
            code: "low_blur_score",
            severity: "warning",
            message: "blur_score is below the preferred threshold.",
            stage: "quality",
          },
        ],
      },
      validation: {
        ...rawPageModel.verifyResponse.analysis.validation,
        issues: [
          {
            code: "missing_seal",
            severity: "warning",
            message: "missing seal",
          },
        ],
      },
    },
    verification: {
      ...rawPageModel.verifyResponse.verification,
      warnings: ["leave dates do not align with extracted document dates"],
      rule_results: rawPageModel.verifyResponse.verification.rule_results.map((rule: { rule_code: string }) =>
        rule.rule_code === "leave_date_match"
          ? {
              ...rule,
              passed: false,
              severity: "warning",
              message: "leave dates do not align with extracted document dates",
            }
          : rule,
      ),
    },
  };

  const viewModel = buildApprovalPageModel({
    rawPageModel,
    rawVerifyResponse,
  });

  assert.deepEqual(
    viewModel.verification.explainabilityGroups.map((group) => group.key),
    ["ocr_quality", "document_integrity", "rule_mismatch"],
  );
  assert.match(viewModel.verification.explainabilityGroups[0]?.items.join(" "), /blur|质量|低/);
  assert.match(viewModel.verification.explainabilityGroups[1]?.items.join(" "), /seal|盖章/);
  assert.match(viewModel.verification.explainabilityGroups[2]?.items.join(" "), /leave dates|日期/);
});

test("buildApprovalPageModel derives review reason taxonomy and localized explainability copy", () => {
  const rawPageModel = loadPageModel();
  const rawVerifyResponse = {
    ...rawPageModel.verifyResponse,
    analysis: {
      ...rawPageModel.verifyResponse.analysis,
      review: {
        ...rawPageModel.verifyResponse.analysis.review,
        warnings: [
          {
            code: "low_blur_score",
            severity: "warning",
            message: "blur_score is below the preferred threshold.",
            stage: "quality",
          },
        ],
      },
      validation: {
        ...rawPageModel.verifyResponse.analysis.validation,
        issues: [
          {
            code: "missing_seal",
            severity: "warning",
            message: "missing seal",
          },
        ],
      },
    },
    verification: {
      ...rawPageModel.verifyResponse.verification,
      verify_status: "REVIEW",
      warnings: ["leave dates do not align with extracted document dates"],
      needs_manual_review: true,
      rule_results: rawPageModel.verifyResponse.verification.rule_results.map((rule: { rule_code: string }) =>
        rule.rule_code === "leave_date_match"
          ? {
              ...rule,
              passed: false,
              severity: "warning",
              message: "leave dates do not align with extracted document dates",
            }
          : rule,
      ),
    },
  };

  const viewModel = buildApprovalPageModel({ rawPageModel, rawVerifyResponse });

  assert.deepEqual(viewModel.verification.reviewReasonTags, [
    "ocr_quality_risk",
    "document_integrity_risk",
    "rule_mismatch_risk",
  ]);
  assert.equal(viewModel.verification.explainabilityGroups[0]?.label, "OCR质量");
  assert.match(viewModel.verification.explainabilityGroups[0]?.items.join(" "), /清晰度|质量门控|模糊/);
  assert.equal(viewModel.verification.explainabilityGroups[1]?.label, "材料完整性");
  assert.match(viewModel.verification.explainabilityGroups[1]?.items.join(" "), /盖章|完整性/);
  assert.equal(viewModel.verification.explainabilityGroups[2]?.label, "规则不匹配");
  assert.match(viewModel.verification.explainabilityGroups[2]?.items.join(" "), /日期|规则/);
});

test("buildApprovalPageModel fails closed with clear message for partial verify response", () => {
  const rawPageModel = loadPageModel();
  const rawVerifyResponse = {
    request_id: "LV-SICK-PARTIAL-789",
    verification: rawPageModel.verifyResponse.verification,
  };

  assert.throws(
    () => buildApprovalPageModel({
      rawPageModel,
      rawVerifyResponse: rawVerifyResponse as never,
    }),
    /verify response is missing analysis payload/i,
  );
});
