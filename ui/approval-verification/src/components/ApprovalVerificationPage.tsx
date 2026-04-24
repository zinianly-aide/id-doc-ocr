import { useEffect, useMemo, useState } from "react";
import type {
  ApprovalVerificationViewModel,
  AsyncStatus,
  DataSourceMode,
  RawAnalyzeResponse,
  RawVerifyResponse,
} from "@/types";
import { AttachmentList } from "./AttachmentList";
import { DocumentPreview } from "./DocumentPreview";
import { AnalysisPanel } from "./AnalysisPanel";
import { VerificationPanel } from "./VerificationPanel";

interface ApprovalVerificationPageProps {
  initialViewModel: ApprovalVerificationViewModel;
  mode: DataSourceMode;
  onAnalyze: () => Promise<RawAnalyzeResponse>;
  onVerify: () => Promise<RawVerifyResponse>;
  buildNextViewModel: (input: {
    rawAnalyzeResponse?: RawAnalyzeResponse;
    rawVerifyResponse?: RawVerifyResponse;
  }) => ApprovalVerificationViewModel;
}

export function ApprovalVerificationPage({ initialViewModel, mode, onAnalyze, onVerify, buildNextViewModel }: ApprovalVerificationPageProps) {
  const [selectedAttachmentId, setSelectedAttachmentId] = useState(initialViewModel.selectedAttachmentId);
  const [analyzeStatus, setAnalyzeStatus] = useState<AsyncStatus>("success");
  const [verifyStatus, setVerifyStatus] = useState<AsyncStatus>("success");
  const [viewModel, setViewModel] = useState<ApprovalVerificationViewModel>(initialViewModel);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setSelectedAttachmentId(initialViewModel.selectedAttachmentId);
    setAnalyzeStatus("success");
    setVerifyStatus("success");
    setViewModel(initialViewModel);
    setError(null);
  }, [initialViewModel]);

  const selectedAttachment = useMemo(
    () => viewModel.attachments.find((item) => item.id === selectedAttachmentId) ?? viewModel.attachments[0],
    [viewModel.attachments, selectedAttachmentId],
  );

  const actionLabel = mode === "real" ? "API demo" : "mock";

  async function handleAnalyze() {
    setAnalyzeStatus("loading");
    setError(null);
    try {
      const rawAnalyzeResponse = await onAnalyze();
      setViewModel(buildNextViewModel({ rawAnalyzeResponse }));
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
      const rawVerifyResponse = await onVerify();
      setViewModel(buildNextViewModel({ rawVerifyResponse }));
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
            当前阶段不接真实上传；按钮使用 request builder + raw→viewModel 映射验证边界清晰度。
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
            attachments={viewModel.attachments}
            selectedAttachmentId={selectedAttachmentId}
            onSelect={setSelectedAttachmentId}
            analyzeStatus={analyzeStatus}
            verifyStatus={viewModel.verification.verifyStatus}
          />
        </div>

        <div className="column column--middle">
          <DocumentPreview
            header={viewModel.requestHeader}
            attachment={selectedAttachment}
            analysis={viewModel.analysis}
          />
          <AnalysisPanel analysis={viewModel.analysis} />
        </div>

        <div className="column column--right">
          <VerificationPanel verification={viewModel.verification} />
        </div>
      </div>
    </div>
  );
}
