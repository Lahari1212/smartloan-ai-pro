import { useState, useEffect } from "react";
import { getApplications } from "../services/api";
import ApplicationForm from "./ApplicationForm";
import DocumentUpload from "./DocumentUpload";
import EligibilityResult from "./EligibilityResult";

const PIPELINE_STAGES = [
  { id: 1, label: "Application Created", key: "created" },
  { id: 2, label: "Documents Uploaded", key: "uploaded" },
  { id: 3, label: "AI Processing", key: "processing" },
  { id: 4, label: "Document Validation", key: "validated" },
  { id: 5, label: "Eligibility Check", key: "eligibility" },
  { id: 6, label: "Officer Review", key: "review" },
  { id: 7, label: "Final Decision", key: "decision" },
];

function getPipelineStage(status) {
  if (!status) return 1;
  const s = status.toLowerCase();
  if (s.includes("document pending")) return 1;
  if (s.includes("document uploaded")) return 2;
  if (s.includes("processing") || s.includes("validated")) return 4;
  if (s.includes("manual review")) return 6;
  if (s.includes("approved") || s.includes("rejected")) return 7;
  return 3;
}

function StatusBadge({ status }) {
  const s = (status || "").toLowerCase();
  let cls = "status-badge-dash";
  if (s.includes("approved")) cls += " status-approved";
  else if (s.includes("rejected")) cls += " status-rejected";
  else if (s.includes("review")) cls += " status-review";
  else if (s.includes("pending")) cls += " status-pending";
  else cls += " status-default";
  return <span className={cls}>{status || "Pending"}</span>;
}

export default function ApplicantDashboard({ user, onLogout }) {
  const [view, setView] = useState("dashboard"); // dashboard | create | upload | result
  const [applications, setApplications] = useState([]);
  const [selectedApp, setSelectedApp] = useState(null);
  const [eligibilityResult, setEligibilityResult] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadApplications = async () => {
    try {
      setLoading(true);
      const res = await getApplications();
      setApplications(res.data.applications || []);
    } catch {
      setError("Unable to load your applications.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadApplications();
  }, []);

  const handleApplicationCreated = (app) => {
    setSelectedApp(app);
    setView("upload");
    loadApplications();
  };

  const handleDocumentsCompleted = (result) => {
    setEligibilityResult(result);
    setView("result");
    loadApplications();
  };

  const handleNewApplication = () => {
    setSelectedApp(null);
    setEligibilityResult(null);
    setView("create");
  };

  const handleContinueApp = (app) => {
    setSelectedApp(app);
    setEligibilityResult(null);
    setView("upload");
  };

  const handleViewResult = (app) => {
    setSelectedApp(app);
    setView("result");
  };

  const firstName = user?.full_name?.split(" ")[0] || "Applicant";

  // ── Stats calculation ────────────────────────────────────────────
  const totalApps = applications.length;
  const docsSubmitted = applications.filter(
    (a) => !a.status?.toLowerCase().includes("pending")
  ).length;
  const activeApp = applications[0] || null;
  const approvedCount = applications.filter(
    (a) => a.status?.toLowerCase() === "approved"
  ).length;

  if (view === "create") {
    return (
      <main className="dash-page">
        <header className="dash-header">
          <div className="dash-header-brand">
            <span className="header-brand-label">SMARTLOAN AI</span>
            <span className="header-dash-name">Applicant Portal</span>
          </div>
          <div className="dash-header-actions">
            <button className="btn-outline" onClick={() => setView("dashboard")}>
              ← Dashboard
            </button>
            <button className="btn-outline" onClick={onLogout}>Logout</button>
          </div>
        </header>
        <div className="dash-body">
          <ApplicationForm onCreated={handleApplicationCreated} />
        </div>
      </main>
    );
  }

  if (view === "upload" && selectedApp) {
    return (
      <main className="dash-page">
        <header className="dash-header">
          <div className="dash-header-brand">
            <span className="header-brand-label">SMARTLOAN AI</span>
            <span className="header-dash-name">Document Center</span>
          </div>
          <div className="dash-header-actions">
            <button className="btn-outline" onClick={() => setView("dashboard")}>
              ← Dashboard
            </button>
            <button className="btn-outline" onClick={onLogout}>Logout</button>
          </div>
        </header>
        <div className="dash-body">
          <DocumentUpload
            applicationId={selectedApp.application_id}
            onCompleted={handleDocumentsCompleted}
          />
        </div>
      </main>
    );
  }

  if (view === "result") {
    return (
      <main className="dash-page">
        <header className="dash-header">
          <div className="dash-header-brand">
            <span className="header-brand-label">SMARTLOAN AI</span>
            <span className="header-dash-name">AI Assessment</span>
          </div>
          <div className="dash-header-actions">
            <button className="btn-outline" onClick={() => setView("dashboard")}>
              ← Dashboard
            </button>
            <button className="btn-outline" onClick={onLogout}>Logout</button>
          </div>
        </header>
        <div className="dash-body">
          <EligibilityResult
            result={eligibilityResult || selectedApp}
            onReset={() => setView("dashboard")}
          />
        </div>
      </main>
    );
  }

  // ── Main Dashboard View ──────────────────────────────────────────
  return (
    <main className="dash-page">
      <header className="dash-header">
        <div className="dash-header-brand">
          <span className="header-brand-label">SMARTLOAN AI</span>
          <span className="header-dash-name">Applicant Dashboard</span>
        </div>
        <div className="dash-header-actions">
          <button className="btn-primary" onClick={handleNewApplication}>
            + New Application
          </button>
          <button className="btn-outline" onClick={onLogout}>Logout</button>
        </div>
      </header>

      <div className="dash-body">
        {/* Welcome Banner */}
        <div className="welcome-banner">
          <div>
            <p className="welcome-label">Welcome back,</p>
            <h1 className="welcome-name">{firstName} 👋</h1>
            <p className="welcome-email">{user?.email}</p>
          </div>
          <div className="welcome-badge">
            <span>Applicant</span>
          </div>
        </div>

        {/* Stats Row */}
        <div className="stats-row">
          {[
            { label: "Applications", value: totalApps, icon: "📋" },
            { label: "Docs Submitted", value: docsSubmitted, icon: "📁" },
            { label: "Approved", value: approvedCount, icon: "✅" },
            {
              label: "Active Status",
              value: activeApp?.status || "—",
              icon: "🔄",
              isText: true,
            },
          ].map((s) => (
            <div className="stat-card-new" key={s.label}>
              <span className="stat-icon">{s.icon}</span>
              <div>
                <p className="stat-label-new">{s.label}</p>
                <p className={`stat-value-new ${s.isText ? "stat-value-sm" : ""}`}>
                  {s.value}
                </p>
              </div>
            </div>
          ))}
        </div>

        {error && <div className="alert-error">{error}</div>}

        {/* Applications List */}
        <div className="section-card">
          <div className="section-card-header">
            <h2>Your Applications</h2>
            <button className="btn-primary" onClick={handleNewApplication}>
              + New
            </button>
          </div>

          {loading ? (
            <div className="skeleton-list">
              {[1, 2].map((i) => (
                <div key={i} className="skeleton-row" />
              ))}
            </div>
          ) : applications.length === 0 ? (
            <div className="empty-state">
              <div className="empty-icon">📋</div>
              <h3>No applications yet</h3>
              <p>Start your loan journey by creating your first application.</p>
              <button className="btn-primary" onClick={handleNewApplication}>
                Create Application
              </button>
            </div>
          ) : (
            <div className="app-list">
              {applications.map((app) => {
                const stage = getPipelineStage(app.status);
                const isComplete =
                  app.status === "Approved" || app.status === "Rejected";
                return (
                  <div className="app-card" key={app.application_id}>
                    <div className="app-card-top">
                      <div>
                        <p className="app-id-label">
                          Application ID
                        </p>
                        <p className="app-id-val">
                          {app.application_id.slice(0, 8).toUpperCase()}
                        </p>
                      </div>
                      <StatusBadge status={app.status} />
                    </div>

                    <div className="app-card-meta">
                      <span>💰 ₹{Number(app.loan_amount).toLocaleString("en-IN")}</span>
                      <span>📅 {new Date(app.created_at).toLocaleDateString("en-IN")}</span>
                      <span>🏦 CIBIL {app.cibil_score}</span>
                    </div>

                    {/* Pipeline Progress */}
                    <div className="pipeline-row">
                      {PIPELINE_STAGES.map((ps) => (
                        <div
                          key={ps.id}
                          className={`pipeline-dot ${
                            ps.id < stage
                              ? "pipeline-done"
                              : ps.id === stage
                              ? "pipeline-active"
                              : "pipeline-future"
                          }`}
                          title={ps.label}
                        >
                          {ps.id < stage ? "✓" : ps.id}
                        </div>
                      ))}
                    </div>
                    <p className="pipeline-current-label">
                      Stage {stage}: {PIPELINE_STAGES[stage - 1]?.label}
                    </p>

                    <div className="app-card-actions">
                      {isComplete ? (
                        <button
                          className="btn-secondary"
                          onClick={() => handleViewResult(app)}
                        >
                          View Result
                        </button>
                      ) : (
                        <>
                          {app.status === "Document Pending" && (
                            <button
                              className="btn-primary"
                              onClick={() => handleContinueApp(app)}
                            >
                              Upload Documents →
                            </button>
                          )}
                          {app.status === "Document Uploaded" && (
                            <button
                              className="btn-primary"
                              onClick={() => handleContinueApp(app)}
                            >
                              Continue Processing →
                            </button>
                          )}
                          {app.status === "Manual Review" && (
                            <button
                              className="btn-secondary"
                              onClick={() => handleViewResult(app)}
                            >
                              View AI Report
                            </button>
                          )}
                        </>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Disclaimer */}
        <div className="disclaimer-box">
          <p>
            ⚠️ <strong>Important:</strong> AI assessments are for guidance only.
            All final loan decisions are made exclusively by a qualified Loan Officer.
          </p>
        </div>
      </div>
    </main>
  );
}
