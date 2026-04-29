import type { AnalysisViewModel, AttachmentViewModel, RequestHeader } from "@/types";

interface DocumentPreviewProps {
  header: RequestHeader;
  attachment?: AttachmentViewModel;
  analysis?: AnalysisViewModel | null;
  previewUrl: string | null;
  selectedFile: File | null;
  mode: "mock" | "real";
}

export function DocumentPreview({ header, attachment, analysis, previewUrl, selectedFile, mode }: DocumentPreviewProps) {
  const usingDemoSample = mode === "real" && !selectedFile;
  const usingSelectedFile = mode === "real" && Boolean(selectedFile);

  return (
    <section className="panel panel--preview">
      <div className="panel__header">
        <div>
          <h2>DocumentPreview</h2>
          <p>本阶段增加本地图片预览壳；未选文件时仍可使用 demo sample。</p>
          <p className="muted">
            {mode === "mock"
              ? "当前为 mock 展示态。"
              : usingSelectedFile
                ? "当前使用用户选择文件。"
                : "当前使用 demo sample。"}
          </p>
        </div>
      </div>

      <div className="preview-placeholder">
        {previewUrl ? (
          <>
            <img className="preview-image" src={previewUrl} alt={selectedFile?.name ?? "selected preview"} />
            <div className="preview-placeholder__file">{selectedFile?.name ?? attachment?.filename ?? "未选择附件"}</div>
            <div className="preview-placeholder__meta">{selectedFile?.type ?? attachment?.contentType ?? "-"}</div>
          </>
        ) : (
          <>
            <div className="preview-placeholder__file">{attachment?.filename ?? "未选择附件"}</div>
            <div className="preview-placeholder__meta">{attachment?.contentType ?? "-"}</div>
            <div className="preview-placeholder__hint">
              {usingDemoSample ? "当前未选择文件，因此本次展示与调用都将使用 demo sample。" : "后续接真实上传/图片预览时，优先替换这一块。"}
            </div>
          </>
        )}
      </div>

      <div className="info-card">
        <h3>请求头摘要</h3>
        <dl className="detail-kv">
          <div><dt>requestId</dt><dd>{header.requestId}</dd></div>
          <div><dt>applicant</dt><dd>{header.applicantName}</dd></div>
          <div><dt>department</dt><dd>{header.department}</dd></div>
          <div><dt>leaveType</dt><dd>{header.leaveType}</dd></div>
          <div><dt>dateRange</dt><dd>{header.leaveDateRange}</dd></div>
          <div><dt>status</dt><dd>{header.approvalStatus}</dd></div>
        </dl>
      </div>

      <div className="info-card">
        <h3>可解释信息优先级</h3>
        <ul>
          <li>doc_type: {analysis?.docType ?? "-"}</li>
          <li>attachment_label: {analysis?.attachmentLabel ?? "-"}</li>
          <li>extracted_fields: {analysis?.extractedFields.length ?? 0}</li>
        </ul>
      </div>
    </section>
  );
}
