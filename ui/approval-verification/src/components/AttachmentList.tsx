import type { AsyncStatus, AttachmentViewModel, VerifyStatus } from "@/types";
import { RiskBadge } from "./RiskBadge";

interface AttachmentListProps {
  attachments: AttachmentViewModel[];
  selectedAttachmentId: string;
  onSelect: (attachmentId: string) => void;
  analyzeStatus: AsyncStatus;
  verifyStatus: VerifyStatus | null;
}

export function AttachmentList({
  attachments,
  selectedAttachmentId,
  onSelect,
  analyzeStatus,
  verifyStatus,
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
