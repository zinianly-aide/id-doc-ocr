import { useEffect, useMemo, useState } from "react";
import { ApprovalVerificationPage } from "./components/ApprovalVerificationPage";
import { ApprovalVerificationPageV1 } from "./components/ApprovalVerificationPageV1";
import {
  analyzeDocument,
  buildPageViewModel,
  getApprovalVerificationPageModel,
  verifyAttachment,
} from "./adapters/approvalVerification";
import type {
  ApprovalVerificationViewModel,
  DataSourceMode,
  MockScenario,
  RawApprovalVerificationPageModel,
  RawAnalyzeResponse,
  RawVerifyResponse,
} from "./types";

export default function App() {
  const [scenario, setScenario] = useState<MockScenario>("pass");
  const [mode, setMode] = useState<DataSourceMode>("mock");
  const [pageVersion, setPageVersion] = useState<"default" | "v1">("default");
  const [rawPageModel, setRawPageModel] = useState<RawApprovalVerificationPageModel | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError(null);
    getApprovalVerificationPageModel(mode, scenario)
      .then((payload) => {
        if (active) {
          setRawPageModel(payload);
          setLoading(false);
        }
      })
      .catch((caughtError) => {
        if (active) {
          setError(caughtError instanceof Error ? caughtError.message : "failed to load raw page model");
          setLoading(false);
        }
      });

    return () => {
      active = false;
    };
  }, [mode, scenario]);

  const initialViewModel: ApprovalVerificationViewModel | null = useMemo(() => {
    if (!rawPageModel) {
      return null;
    }
    return buildPageViewModel({ rawPageModel });
  }, [rawPageModel]);

  const buildNextViewModel = (input: {
    rawAnalyzeResponse?: RawAnalyzeResponse;
    rawVerifyResponse?: RawVerifyResponse;
  }): ApprovalVerificationViewModel => {
    if (!rawPageModel) {
      throw new Error("raw page model is missing");
    }
    return buildPageViewModel({ rawPageModel, ...input });
  };

  if (loading) {
    return <div className="app-loading">Loading page...</div>;
  }

  if (error || !rawPageModel || !initialViewModel) {
    return <div className="app-error">{error ?? "missing page model"}</div>;
  }

  return (
    <div className="app-frame">
      {pageVersion === "default" ? (
        <ApprovalVerificationPage
          initialViewModel={initialViewModel}
          mode={mode}
          scenario={scenario}
          pageVersion={pageVersion}
          onModeChange={setMode}
          onScenarioChange={setScenario}
          onPageVersionChange={setPageVersion}
          onAnalyze={(selectedFile) => analyzeDocument(mode, scenario, selectedFile)}
          onVerify={(selectedFile) => verifyAttachment(mode, scenario, selectedFile)}
          buildNextViewModel={buildNextViewModel}
        />
      ) : (
        <>
          <header className="app-topbar">
            <div>
              <strong>Page version</strong>
              <p>默认页为新审批工作台风格，原页面已保留为 V1。</p>
            </div>
            <div className="scenario-switcher">
              <button type="button" className="scenario-button" onClick={() => setPageVersion("default")}>Default page</button>
              <button type="button" className="scenario-button scenario-button--active" onClick={() => setPageVersion("v1")}>V1 page</button>
            </div>
          </header>

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

          <ApprovalVerificationPageV1
            initialViewModel={initialViewModel}
            mode={mode}
            onAnalyze={(selectedFile) => analyzeDocument(mode, scenario, selectedFile)}
            onVerify={(selectedFile) => verifyAttachment(mode, scenario, selectedFile)}
            buildNextViewModel={buildNextViewModel}
          />
        </>
      )}
    </div>
  );
}
