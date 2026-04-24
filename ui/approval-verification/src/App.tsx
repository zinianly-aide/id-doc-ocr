import { useEffect, useState } from "react";
import { ApprovalVerificationPage } from "./components/ApprovalVerificationPage";
import {
  analyzeDocument,
  getApprovalVerificationPageModel,
  verifyAttachment,
} from "./adapters/approvalVerification";
import type {
  ApprovalVerificationMockPage,
  DataSourceMode,
  MockScenario,
} from "./types";

export default function App() {
  const [scenario, setScenario] = useState<MockScenario>("pass");
  const [mode, setMode] = useState<DataSourceMode>("mock");
  const [pageModel, setPageModel] = useState<ApprovalVerificationMockPage | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError(null);
    getApprovalVerificationPageModel(mode, scenario)
      .then((payload) => {
        if (active) {
          setPageModel(payload);
          setLoading(false);
        }
      })
      .catch((caughtError) => {
        if (active) {
          setError(caughtError instanceof Error ? caughtError.message : "failed to load page model");
          setLoading(false);
        }
      });

    return () => {
      active = false;
    };
  }, [mode, scenario]);

  if (loading) {
    return <div className="app-loading">Loading page...</div>;
  }

  if (error || !pageModel) {
    return <div className="app-error">{error ?? "missing page model"}</div>;
  }

  return (
    <div className="app-frame">
      <header className="app-topbar">
        <div>
          <strong>Data source</strong>
          <p>mock 用于页面验收；real 用于最小真实 adapter 联调，不接真实上传。</p>
        </div>
        <div className="scenario-switcher">
          <button
            type="button"
            className={mode === "mock" ? "scenario-button scenario-button--active" : "scenario-button"}
            onClick={() => setMode("mock")}
          >
            Mock mode
          </button>
          <button
            type="button"
            className={mode === "real" ? "scenario-button scenario-button--active" : "scenario-button"}
            onClick={() => setMode("real")}
          >
            Real adapter mode
          </button>
        </div>
      </header>

      <header className="app-topbar">
        <div>
          <strong>Mock scenario</strong>
          <p>PASS / REVIEW 页面态都保留，用来驱动 request header、附件信息和 demo 请求场景。</p>
        </div>
        <div className="scenario-switcher">
          <button
            type="button"
            className={scenario === "pass" ? "scenario-button scenario-button--active" : "scenario-button"}
            onClick={() => setScenario("pass")}
          >
            PASS mock
          </button>
          <button
            type="button"
            className={scenario === "review" ? "scenario-button scenario-button--active" : "scenario-button"}
            onClick={() => setScenario("review")}
          >
            REVIEW mock
          </button>
        </div>
      </header>

      <ApprovalVerificationPage
        pageModel={pageModel}
        mode={mode}
        onAnalyze={() => analyzeDocument(mode, scenario)}
        onVerify={() => verifyAttachment(mode, scenario)}
      />
    </div>
  );
}
