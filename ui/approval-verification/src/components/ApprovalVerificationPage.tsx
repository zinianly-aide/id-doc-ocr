import { useEffect, useMemo, useState } from "react";
import type {
  AnalysisResponse,
  ApprovalVerificationMockPage,
  AsyncStatus,
  DataSourceMode,
  VerificationResponse,
} from "@/types";
import { AttachmentList } from "./AttachmentList";
import { DocumentPreview } from "./DocumentPreview";
import { AnalysisPanel } from "./AnalysisPanel";
import { VerificationPanel } from "./VerificationPanel";

interface ApprovalVerificationPageProps {
  pageModel: ApprovalVerificationMockPage;
  mode: DataSourceMode;
  onAnalyze: () => Promise<AnalysisResponse>;
  onVerify: () => Promise<VerificationResponse>;
}

export function ApprovalVerificationPage({ pageModel, mode, onAnalyze, onVerify }: ApprovalVerificationPageProps) {
  const [selectedAttachmentId, setSelectedAttachmentId] = useState(pageModel.selectedAttachmentId);
  const [analyzeStatus, setAnalyzeStatus] = useState<AsyncStatus>("success");
  const [verifyStatus, setVerifyStatus] = useState<AsyncStatus>("success");
  const [currentAnalysis, setCurrentAnalysis] = useState<AnalysisResponse["analysis"] | null>(pageModel.analyzeResponse.analysis);
  const [currentVerification, setCurrentVerification] = useState<VerificationResponse["verification"] | null>(pageModel.verifyResponse.verification);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setSelectedAttachmentId(pageModel.selectedAttachmentId);
    setAnalyzeStatus("success");
    setVerifyStatus("success");
    setCurrentAnalysis(pageModel.analyzeResponse.analysis);
    setCurrentVerification(pageModel.verifyResponse.verification);
    setError(null);
  }, [pageModel]);

  const selectedAttachment = useMemo(
    () => pageModel.attachments.find((item) => item.id === selectedAttachmentId) ?? pageModel.attachments[0],
    [pageModel.attachments, selectedAttachmentId],
  );

  const actionLabel = mode === "real" ? "API demo" : "mock";

  async function handleAnalyze() {
    setAnalyzeStatus("loading");
    setError(null);
    try {
      const response = await onAnalyze();
      setCurrentAnalysis(response.analysis);
      setAnalyzeStatus("success");
    } catch (caughtError) {
      setAnalyzeStatus("error");
      setError(caughtError instanceof Error ? caughtError.message : `${actionLabel} analyze failed`);
    }
  }

  async function handleVerify() {
    setVerifyStatus("loading");
    setError(null);
    try {
      const response = await onVerify();
      setCurrentAnalysis(response.analysis);
      setCurrentVerification(response.verification);
      setVerifyStatus("success");
    } catch (caughtError) {
      setVerifyStatus("error");
      setError(caughtError instanceof Error ? caughtError.message : `${actionLabel} verify failed`);
    }
  }

  return (
    <div className="page-shell">
      <section className="hero-card">
        <div>
          <p className="eyebrow">审批附件核验页 / {mode === "real" ? "real-adapter demo" : "mock-first"}</p>
          <h1>ApprovalVerificationPage</h1>
          <p className="hero-copy">
            当前阶段不接真实上传；按钮使用内置 demo 样本或 mock 数据验证页面编排和字段绑定。
          </p>
        </div>
        <div className="toolbar">
          <button type="button" className="action-button" onClick={handleAnalyze} disabled={analyzeStatus === "loading"}>
            {analyzeStatus === "loading" ? "Analyzing..." : `Run ${actionLabel} analyze`}
          </button>
          <button type="button" className="action-button action-button--secondary" onClick={handleVerify} disabled={verifyStatus === "loading"}>
            {verifyStatus === "loading" ? "Verifying..." : `Run ${actionLabel} verify`}
          </button>
        </div>
      </section>

      <section className="state-bar">
        <span>mode: {mode}</span>
        <span>selectedAttachmentId: {selectedAttachmentId}</span>
        <span>analyzeStatus: {analyzeStatus}</span>
        <span>verifyStatus: {verifyStatus}</span>
        <span>error: {error ?? "none"}</span>
      </section>

      <div className="three-column-layout">
        <div className="column column--left">
          <AttachmentList
            attachments={pageModel.attachments}
            selectedAttachmentId={selectedAttachmentId}
            onSelect={setSelectedAttachmentId}
            analyzeStatus={analyzeStatus}
            verifyStatus={currentVerification?.verify_status}
          />
        </div>

        <div className="column column--middle">
          <DocumentPreview
            header={pageModel.requestHeader}
            attachment={selectedAttachment}
            analysis={currentAnalysis}
          />
          <AnalysisPanel analysis={currentAnalysis} />
        </div>

        <div className="column column--right">
          <VerificationPanel verification={currentVerification} />
        </div>
      </div>
    </div>
  );
}
