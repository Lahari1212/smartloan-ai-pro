import { useEffect, useState } from "react";
import { getApplications } from "../services/api";
import OfficerApplicationView from "./OfficerApplicationView";

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

function RiskBadge({ risk }) {
  const r = (risk || "").toLowerCase();
  const cls =
    r === "low" ? "risk-low" : r === "high" ? "risk-high" : "risk-medium";
  return <span className={`risk-badge ${cls}`}>{risk || "—"}</span>;
}

export default function OfficerDashboard({ user, onLogout }) {
  const [applications, setApplications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");
  const [filterStatus, setFilterStatus] = useState("all");
  const [selectedApp, setSelectedApp] = useState(null);

  const loadApplications = async () => {
    try {
      setLoading(true);
      const res = await getApplications();
      setApplications(res.data.applications || []);
    } catch {
      setError("Unable to load applications.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadApplications();
  }, []);

  // ─── Stats ────────────────────────────────────────────────────────
  const stats = {
    total: applications.length,
    pending: applications.filter((a) =>
      a.status?.toLowerCase().includes("pending")
    ).length,
    manualReview: applications.filter((a) =>
      a.status?.toLowerCase().includes("review")
    ).length,
    approved: applications.filter((a) =>
      a.status?.toLowerCase() === "approved"
    ).length,
    rejected: applications.filter((a) =>
      a.status?.toLowerCase() === "rejected"
    ).length,
    docUploaded: applications.filter(
      (a) => a.status === "Document Uploaded"
    ).length,
  };

  // ─── Filter & Search ──────────────────────────────────────────────
  const filtered = applications.filter((app) => {
    const matchSearch =
      !search ||
      app.applicant_name?.toLowerCase().includes(search.toLowerCase()) ||
      app.application_id?.toLowerCase().includes(search.toLowerCase()) ||
      app.email?.toLowerCase().includes(search.toLowerCase());

    const matchStatus =
      filterStatus === "all" ||
      app.status?.toLowerCase().includes(filterStatus.toLowerCase());

    return matchSearch && matchStatus;
  });

  if (selectedApp) {
    return (
      <OfficerApplicationView
        applicationId={selectedApp.application_id}
        onBack={() => {
          setSelectedApp(null);
          loadApplications();
        }}
        user={user}
      />
    );
  }

  return (
    <main className="dash-page">
      {/* Header */}
      <header className="dash-header officer-header-dark">
        <div className="dash-header-brand">
          <span className="header-brand-label-light">SMARTLOAN AI</span>
          <span className="header-dash-name-light">Loan Officer Dashboard</span>
        </div>
        <div className="dash-header-actions">
          <span className="officer-welcome-name">
            👤 {user?.full_name || "Loan Officer"}
          </span>
          <button className="btn-outline-light" onClick={onLogout}>
            Logout
          </button>
        </div>
      </header>

      <div className="dash-body">
        {/* Stats Grid */}
        <div className="officer-stats-grid">
          {[
            { label: "Total Applications", value: stats.total, color: "#2563eb" },
            { label: "Pending Review", value: stats.manualReview, color: "#d97706" },
            { label: "AI Verified", value: stats.docUploaded, color: "#7c3aed" },
            { label: "Approved", value: stats.approved, color: "#059669" },
            { label: "Rejected", value: stats.rejected, color: "#dc2626" },
            { label: "Doc Pending", value: stats.pending, color: "#64748b" },
          ].map((s) => (
            <div className="officer-stat-card" key={s.label}>
              <p className="officer-stat-label">{s.label}</p>
              <p
                className="officer-stat-value"
                style={{ color: s.color }}
              >
                {s.value}
              </p>
            </div>
          ))}
        </div>

        {/* Search & Filter Bar */}
        <div className="section-card">
          <div className="filter-bar">
            <div className="search-wrapper">
              <span className="search-icon">🔍</span>
              <input
                className="search-input"
                placeholder="Search applicant name, ID, or email..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>

            <select
              className="filter-select"
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
            >
              <option value="all">All Status</option>
              <option value="pending">Document Pending</option>
              <option value="uploaded">Document Uploaded</option>
              <option value="review">Manual Review</option>
              <option value="approved">Approved</option>
              <option value="rejected">Rejected</option>
            </select>

            <button
              className="btn-outline"
              onClick={loadApplications}
              title="Refresh"
            >
              ↻ Refresh
            </button>
          </div>

          {error && <div className="alert-error">{error}</div>}

          {/* Applications Table */}
          <div className="table-scroll">
            <table className="app-table">
              <thead>
                <tr>
                  <th>Applicant</th>
                  <th>Loan Amount</th>
                  <th>CIBIL</th>
                  <th>Status</th>
                  <th>Date</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr>
                    <td colSpan={6} className="table-loading">
                      Loading applications...
                    </td>
                  </tr>
                ) : filtered.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="table-empty">
                      {search || filterStatus !== "all"
                        ? "No applications match your filter."
                        : "No applications found."}
                    </td>
                  </tr>
                ) : (
                  filtered.map((app) => (
                    <tr key={app.application_id}>
                      <td>
                        <p className="table-name">{app.applicant_name}</p>
                        <p className="table-email">{app.email}</p>
                      </td>
                      <td className="table-amount">
                        ₹{Number(app.loan_amount).toLocaleString("en-IN")}
                      </td>
                      <td>
                        <span
                          className={`cibil-badge ${
                            app.cibil_score >= 750
                              ? "cibil-good"
                              : app.cibil_score >= 650
                              ? "cibil-fair"
                              : "cibil-poor"
                          }`}
                        >
                          {app.cibil_score}
                        </span>
                      </td>
                      <td>
                        <StatusBadge status={app.status} />
                      </td>
                      <td className="table-date">
                        {new Date(app.created_at).toLocaleDateString("en-IN")}
                      </td>
                      <td>
                        <button
                          className="btn-primary btn-sm"
                          onClick={() => setSelectedApp(app)}
                        >
                          Review →
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          <div className="table-footer">
            Showing {filtered.length} of {applications.length} applications
          </div>
        </div>
      </div>
    </main>
  );
}