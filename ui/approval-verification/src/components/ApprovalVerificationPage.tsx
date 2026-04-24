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

export function ApprovalVerificationPage({ initialViewModel, mode, onAnalyze, onVerify, buildNextViewModel }: ApprovalVerificationPageProps) {
  const [selectedAttachmentId, setSelectedAttachmentId] = useState(initialViewModel.selectedAttachmentId);
  const [analyzeStatus, setAnalyzeStatus] = useState<AsyncStatus>("success");
  const [verifyStatus, setVerifyStatus] = useState<AsyncStatus>("success");
  const [viewModel, setViewModel] = useState<ApprovalVerificationViewModel>(initialViewModel);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [uploadInputError, setUploadInputError] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setSelectedAttachmentId(initialViewModel.selectedAttachmentId);
    setAnalyzeStatus("success");
    setVerifyStatus("success");
    setViewModel(initialViewModel);
    setSelectedFile(null);
    setUploadInputError(null);
    setError(null);
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

  const actionLabel = mode === "real" ? "API demo" : "mock";

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
      setError(imageSelectionError);
      return;
    }

    setSelectedFile(file);
    setUploadInputError(null);
    setError(null);
  }

  async function handleAnalyze() {
    if (mode === "real" && uploadInputError) {
      setAnalyzeStatus("error");
      setError(uploadInputError);
      return;
    }

    setAnalyzeStatus("loading");
    setError(null);
    try {
      const rawAnalyzeResponse = await onAnalyze(selectedFile);
      setViewModel(buildNextViewModel({ rawAnalyzeResponse }));
      setAnalyzeStatus("success");
    } catch (caughtError) {
      setAnalyzeStatus("error");
      setError(caughtError instanceof Error ? caughtError.message : `${actionLabel} analyze failed`);
    }
  }

  async function handleVerify() {
    if (mode === "real" && uploadInputError) {
      setVerifyStatus("error");
      setError(uploadInputError);
      return;
    }

    setVerifyStatus("loading");
    setError(null);
    try {
      const rawVerifyResponse = await onVerify(selectedFile);
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
        <span>mode: {mode}</span>
        <span>selectedAttachmentId: {selectedAttachmentId}</span>
        <span>selectedFile: {selectedFile?.name ?? "none"}</span>
        <span>previewUrl: {previewUrl ? "ready" : "none"}</span>
        <span>uploadInputError: {uploadInputError ?? "none"}</span>
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
          <AnalysisPanel analysis={viewModel.analysis} />
        </div>

        <div className="column column--right">
          <VerificationPanel verification={viewModel.verification} />
        </div>
      </div>
    </div>
  );
}
