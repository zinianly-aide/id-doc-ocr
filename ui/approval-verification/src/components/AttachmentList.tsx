import type { AsyncStatus, AttachmentViewModel, DataSourceMode, VerifyStatus } from "@/types";
import { RiskBadge } from "./RiskBadge";

interface AttachmentListProps {
  attachments: AttachmentViewModel[];
  selectedAttachmentId: string;
  onSelect: (attachmentId: string) => void;
  analyzeStatus: AsyncStatus;
  verifyStatus: VerifyStatus | null;
  mode: DataSourceMode;
  selectedFile: File | null;
  uploadInputError: string | null;
  onFileSelected: (file: File | null) => void;
}

function formatFileSize(size: number): string {
  if (size < 1024) return `${size} B`;
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`;
  return `${(size / (1024 * 1024)).toFixed(2)} MB`;
}

export function AttachmentList({
  attachments,
  selectedAttachmentId,
  onSelect,
  analyzeStatus,
  verifyStatus,
  mode,
  selectedFile,
  uploadInputError,
  onFileSelected,
}: AttachmentListProps) {
  return (
    <section className="panel">
      <div className="panel__header">
        <div>
          <h2>附件列表</h2>
          <p>先渲染选择与状态，不接真实上传。</p>
        </div>
        <div className="status-stack">
          <RiskBadge label={`analyze: ${analyzeStatus}`} tone="INFO" />
          {verifyStatus ? <RiskBadge label={`verify: ${verifyStatus}`} tone={verifyStatus} /> : null}
        </div>
      </div>

      <div className="upload-shell">
        <label className="action-button action-button--secondary upload-button">
          选择图片
          <input
            className="hidden-file-input"
            type="file"
            accept="image/*"
            onChange={(event) => onFileSelected(event.target.files?.[0] ?? null)}
          />
        </label>
        <p className="muted upload-hint">
          {mode === "real"
            ? selectedFile
              ? "当前 real adapter 将优先使用你选择的图片。"
              : "未选择文件时仍将 fallback 到 demo sample。"
            : "mock mode 不会真正上传文件，但你仍可预览本地图像壳层。"}
        </p>
        {selectedFile ? (
          <dl className="detail-kv upload-meta">
            <div><dt>文件名</dt><dd>{selectedFile.name}</dd></div>
            <div><dt>大小</dt><dd>{formatFileSize(selectedFile.size)}</dd></div>
            <div><dt>类型</dt><dd>{selectedFile.type || "-"}</dd></div>
          </dl>
        ) : null}
        {uploadInputError ? <p className="upload-error">{uploadInputError}</p> : null}
      </div>

      <div className="attachment-list">
        {attachments.map((attachment) => {
          const isSelected = attachment.id === selectedAttachmentId;
          return (
            <button
              key={attachment.id}
              type="button"
              className={`attachment-card ${isSelected ? "attachment-card--active" : ""}`}
              onClick={() => onSelect(attachment.id)}
            >
              <div className="attachment-card__top">
                <strong>{attachment.filename}</strong>
                {attachment.verifyStatus ? (
                  <RiskBadge label={attachment.verifyStatus} tone={attachment.verifyStatus} />
                ) : null}
              </div>
              <dl className="mini-kv">
                <div>
                  <dt>类型</dt>
                  <dd>{attachment.contentType}</dd>
                </div>
                <div>
                  <dt>大小</dt>
                  <dd>{attachment.sizeLabel}</dd>
                </div>
                <div>
                  <dt>文档</dt>
                  <dd>{attachment.docType ?? "-"}</dd>
                </div>
                <div>
                  <dt>标签</dt>
                  <dd>{attachment.attachmentLabel ?? "-"}</dd>
                </div>
              </dl>
            </button>
          );
        })}
      </div>
    </section>
  );
}
