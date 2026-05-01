import { useEffect, useMemo, useState } from "react";
import type {
  ApprovalVerificationViewModel,
  AsyncStatus,
  DataSourceMode,
  RawAnalyzeResponse,
  RawVerifyResponse,
  VerifyStatus,
} from "@/types";
import { AttachmentList } from "./AttachmentList";
import { DocumentPreview } from "./DocumentPreview";
import { AnalysisPanel } from "./AnalysisPanel";
import { VerificationPanel } from "./VerificationPanel";

interface ApprovalVerificationPageProps {
  initialViewModel: ApprovalVerificationViewModel;
  mode: DataSourceMode;
  onAnalyze: (selectedFile: File | null) => Promise<RawAnalyzeResponse>;
  onVerify: (selectedFile: File | null) => Promise<RawVerifyResponse>;
  buildNextViewModel: (input: {
    rawAnalyzeResponse?: RawAnalyzeResponse;
    rawVerifyResponse?: RawVerifyResponse;
  }) => ApprovalVerificationViewModel;
}

function getImageSelectionError(file: File): string | null {
  if (!file.type.startsWith("image/")) {
    return "当前仅支持 image/*，暂不支持 PDF 或其他文件类型。";
  }
  return null;
}

function normalizeAnalysisAction(action: string): "PASS" | "REVIEW" | "REJECT" {
  const normalized = action.trim().toUpperCase();
  if (normalized === "AUTO_ACCEPT" || normalized === "PASS") return "PASS";
  if (normalized === "REJECT") return "REJECT";
  return "REVIEW";
}

function buildInconsistencyMessage(analysisAction: string, verifyStatus: VerifyStatus): string | null {
  const normalizedAnalysisAction = normalizeAnalysisAction(analysisAction);
  if (normalizedAnalysisAction === verifyStatus) {
    return null;
  }

  return `识别分析建议 (${analysisAction}) 与业务核验结论 (${verifyStatus}) 不一致，请以业务核验结论为主，并人工复核分析风险。`;
}

export function ApprovalVerificationPageV1({ initialViewModel, mode, onAnalyze, onVerify, buildNextViewModel }: ApprovalVerificationPageProps) {
  const [selectedAttachmentId, setSelectedAttachmentId] = useState(initialViewModel.selectedAttachmentId);
  const [analyzeStatus, setAnalyzeStatus] = useState<AsyncStatus>("success");
  const [verifyStatus, setVerifyStatus] = useState<AsyncStatus>("success");
  const [viewModel, setViewModel] = useState<ApprovalVerificationViewModel>(initialViewModel);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [uploadInputError, setUploadInputError] = useState<string | null>(null);
  const [analyzeError, setAnalyzeError] = useState<string | null>(null);
  const [verifyError, setVerifyError] = useState<string | null>(null);
  const [simulateAnalyzeError, setSimulateAnalyzeError] = useState(false);
  const [simulateVerifyError, setSimulateVerifyError] = useState(false);

  useEffect(() => {
    setSelectedAttachmentId(initialViewModel.selectedAttachmentId);
    setAnalyzeStatus("success");
    setVerifyStatus("success");
    setViewModel(initialViewModel);
    setSelectedFile(null);
    setUploadInputError(null);
    setAnalyzeError(null);
    setVerifyError(null);
    setSimulateAnalyzeError(false);
    setSimulateVerifyError(false);
  }, [initialViewModel]);

  useEffect(() => {
    if (!selectedFile) {
      setPreviewUrl(null);
      return undefined;
    }

    const objectUrl = URL.createObjectURL(selectedFile);
    setPreviewUrl(objectUrl);

    return () => {
      URL.revokeObjectURL(objectUrl);
    };
  }, [selectedFile]);

  const selectedAttachment = useMemo(
    () => viewModel.attachments.find((item) => item.id === selectedAttachmentId) ?? viewModel.attachments[0],
    [viewModel.attachments, selectedAttachmentId],
  );

  const inconsistencyMessage = useMemo(
    () => buildInconsistencyMessage(viewModel.analysis.reviewAction, viewModel.verification.verifyStatus),
    [viewModel.analysis.reviewAction, viewModel.verification.verifyStatus],
  );

  const analysisErrorMessage = analyzeStatus === "error" ? analyzeError : null;
  const verificationErrorMessage = verifyStatus === "error" ? verifyError : null;

  const actionLabel = mode === "real" ? "API demo" : "mock";
  const inputSourceLabel = mode === "mock" ? "mock sample" : selectedFile ? `用户选择文件：${selectedFile.name}` : "demo sample（未选择文件）";

  function handleFileSelected(file: File | null) {
    if (!file) {
      setSelectedFile(null);
      setUploadInputError(null);
      return;
    }

    const imageSelectionError = getImageSelectionError(file);
    if (imageSelectionError) {
      setSelectedFile(null);
      setUploadInputError(imageSelectionError);
      setAnalyzeError(imageSelectionError);
      setVerifyError(imageSelectionError);
      return;
    }

    setSelectedFile(file);
    setUploadInputError(null);
    setAnalyzeError(null);
    setVerifyError(null);
  }

  async function handleAnalyze() {
    if (mode === "real" && uploadInputError) {
      setAnalyzeStatus("error");
      setAnalyzeError(uploadInputError);
      return;
    }

    setAnalyzeStatus("loading");
    setAnalyzeError(null);
    try {
      if (simulateAnalyzeError) {
        throw new Error("模拟 analyze 失败：用于演示错误提示与旧结果回退状态。");
      }
      const rawAnalyzeResponse = await onAnalyze(selectedFile);
      setViewModel(buildNextViewModel({ rawAnalyzeResponse }));
      setAnalyzeStatus("success");
    } catch (caughtError) {
      setAnalyzeStatus("error");
      setAnalyzeError(caughtError instanceof Error ? caughtError.message : `${actionLabel} analyze failed`);
    }
  }

  async function handleVerify() {
    if (mode === "real" && uploadInputError) {
      setVerifyStatus("error");
      setVerifyError(uploadInputError);
      return;
    }

    setVerifyStatus("loading");
    setVerifyError(null);
    try {
      if (simulateVerifyError) {
        throw new Error("模拟 verify 失败：用于演示错误提示与旧结果仅供参考状态。");
      }
      const rawVerifyResponse = await onVerify(selectedFile);
      setViewModel(buildNextViewModel({ rawVerifyResponse }));
      setVerifyStatus("success");
    } catch (caughtError) {
      setVerifyStatus("error");
      setVerifyError(caughtError instanceof Error ? caughtError.message : `${actionLabel} verify failed`);
    }
  }

  return (
    <div className="page-shell">
      <section className="hero-card">
        <div>
          <p className="eyebrow">审批附件核验页 / {mode === "real" ? "real-adapter demo" : "mock-first"}</p>
          <h1>ApprovalVerificationPage</h1>
          <p className="hero-copy">
            当前阶段仅增加单图选择、本地预览和上传壳；未选文件时 real adapter 继续 fallback 到 demo sample。
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
        <span>inputSource: {inputSourceLabel}</span>
        <span>mode: {mode}</span>
        <span>selectedAttachmentId: {selectedAttachmentId}</span>
        <span>selectedFile: {selectedFile?.name ?? "none"}</span>
        <span>previewUrl: {previewUrl ? "ready" : "none"}</span>
        <span>uploadInputError: {uploadInputError ?? "none"}</span>
        <span>analyzeStatus: {analyzeStatus}</span>
        <span>verifyStatus: {verifyStatus}</span>
        <span>analyzeError: {analyzeError ?? "none"}</span>
        <span>verifyError: {verifyError ?? "none"}</span>
        <span>simulateAnalyzeError: {simulateAnalyzeError ? "on" : "off"}</span>
        <span>simulateVerifyError: {simulateVerifyError ? "on" : "off"}</span>
        <button type="button" className="scenario-button" onClick={() => setSimulateAnalyzeError((value) => !value)}>
          {simulateAnalyzeError ? "Disable analyze error demo" : "Enable analyze error demo"}
        </button>
        <button type="button" className="scenario-button" onClick={() => setSimulateVerifyError((value) => !value)}>
          {simulateVerifyError ? "Disable verify error demo" : "Enable verify error demo"}
        </button>
      </section>

      <div className="three-column-layout">
        <div className="column column--left">
          <AttachmentList
            attachments={viewModel.attachments}
            selectedAttachmentId={selectedAttachmentId}
            onSelect={setSelectedAttachmentId}
            analyzeStatus={analyzeStatus}
            verifyStatus={viewModel.verification.verifyStatus}
            mode={mode}
            selectedFile={selectedFile}
            uploadInputError={uploadInputError}
            onFileSelected={handleFileSelected}
          />
        </div>

        <div className="column column--middle">
          <DocumentPreview
            header={viewModel.requestHeader}
            attachment={selectedAttachment}
            analysis={viewModel.analysis}
            previewUrl={previewUrl}
            selectedFile={selectedFile}
            mode={mode}
          />
          <AnalysisPanel
            analysis={viewModel.analysis}
            analyzeStatus={analyzeStatus}
            errorMessage={analysisErrorMessage}
          />
        </div>

        <div className="column column--right">
          <VerificationPanel
            verification={viewModel.verification}
            verifyStatus={verifyStatus}
            errorMessage={verificationErrorMessage}
            inconsistencyMessage={inconsistencyMessage}
          />
        </div>
      </div>
    </div>
  );
}
