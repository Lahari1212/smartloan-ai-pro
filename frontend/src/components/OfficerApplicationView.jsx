import { useEffect, useState } from "react";
import {
  getSingleApplication,
  processAllDocuments,
  submitOfficerReview,
  getDocumentDownloadUrl,
  downloadPdfReport,
  chatWithAiAnalyst,
} from "../services/api";

function SectionCard({ title, icon, children }) {
  return (
    <div className="dossier-section">
      <h3 className="dossier-section-title">
        <span>{icon}</span> {title}
      </h3>
      <div className="dossier-section-body">{children}</div>
    </div>
  );
}

function InfoRow({ label, value, highlight }) {
  return (
    <div className={`info-row ${highlight ? "info-row-highlight" : ""}`}>
      <span className="info-label">{label}</span>
      <span className="info-value">{value || "—"}</span>
    </div>
  );
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

export default function OfficerApplicationView({ applicationId, onBack, user }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState("");

  // Officer review state
  const [decision, setDecision] = useState("");
  const [notes, setNotes] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [reviewSuccess, setReviewSuccess] = useState("");
  const [reviewError, setReviewError] = useState("");

  // AI Summary toggle
  const [showSummary, setShowSummary] = useState(false);

  // PDF Export state
  const [exportingPdf, setExportingPdf] = useState(false);

  // Context-Aware AI Loan Analyst Chatbot state
  const [chatMessages, setChatMessages] = useState([
    {
      role: "model",
      content: "Hello Officer! I have analyzed this borrower's financial profile, uploaded documents, and risk indicators. How can I assist your underwriting review?",
    },
  ]);
  const [chatInput, setChatInput] = useState("");
  const [chatLoading, setChatLoading] = useState(false);

  const handleExportPdf = async () => {
    try {
      setExportingPdf(true);
      await downloadPdfReport(applicationId, data?.applicant_name || "Applicant");
    } catch (err) {
      alert("Failed to export PDF report: " + (err.response?.data?.detail || err.message));
    } finally {
      setExportingPdf(false);
    }
  };

  const handleSendQuery = async (queryText) => {
    const q = queryText || chatInput;
    if (!q.trim() || chatLoading) return;

    const newHistory = [...chatMessages, { role: "user", content: q }];
    setChatMessages(newHistory);
    setChatInput("");
    setChatLoading(true);

    try {
      const res = await chatWithAiAnalyst(applicationId, q, newHistory);
      setChatMessages((prev) => [...prev, { role: "model", content: res.data.reply }]);
    } catch (err) {
      setChatMessages((prev) => [
        ...prev,
        { role: "model", content: "⚠️ Analyst agent error: " + (err.response?.data?.detail || err.message) },
      ]);
    } finally {
      setChatLoading(false);
    }
  };

  const handleUseAiNoteInReview = (aiContent) => {
    // Extract text in quotes if present or use full content
    const match = aiContent.match(/"([^"]+)"/);
    const textToUse = match ? match[1] : aiContent;
    setNotes(textToUse);
  };

  const load = async () => {
    try {
      setLoading(true);
      const res = await getSingleApplication(applicationId);
      setData(res.data);
    } catch (err) {
      setError("Failed to load application: " + (err.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, [applicationId]);

  const handleRunProcessing = async () => {
    try {
      setProcessing(true);
      setError("");
      const res = await processAllDocuments(applicationId);
      setData((prev) => ({ ...prev, ...res.data }));
      await load();
    } catch (err) {
      setError("Processing failed: " + (err.response?.data?.detail || err.message));
    } finally {
      setProcessing(false);
    }
  };

  const handleSubmitReview = async (e) => {
    e.preventDefault();
    if (!decision) {
      setReviewError("Please select a decision.");
      return;
    }
    if (!notes.trim()) {
      setReviewError("Please add review notes.");
      return;
    }
    try {
      setSubmitting(true);
      setReviewError("");
      await submitOfficerReview(applicationId, { decision, notes });
      setReviewSuccess(`Decision "${decision}" submitted successfully.`);
      await load();
    } catch (err) {
      setReviewError(err.response?.data?.detail || "Failed to submit review.");
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <main className="dash-page">
        <header className="dash-header officer-header-dark">
          <div className="dash-header-brand">
            <span className="header-brand-label-light">SMARTLOAN AI</span>
            <span className="header-dash-name-light">Application Dossier</span>
          </div>
          <button className="btn-outline-light" onClick={onBack}>
            ← Back to Dashboard
          </button>
        </header>
        <div className="dash-body">
          <div className="loading-state">Loading application dossier...</div>
        </div>
      </main>
    );
  }

  if (error && !data) {
    return (
      <main className="dash-page">
        <header className="dash-header officer-header-dark">
          <button className="btn-outline-light" onClick={onBack}>← Back</button>
        </header>
        <div className="dash-body">
          <div className="alert-error">{error}</div>
        </div>
      </main>
    );
  }

  const app = data || {};
  const documents = app.documents || [];
  const auditLog = app.audit_log || [];
  const appStatus = app.status || "Unknown";

  return (
    <main className="dash-page">
      {/* Header */}
      <header className="dash-header officer-header-dark">
        <div className="dash-header-brand">
          <span className="header-brand-label-light">SMARTLOAN AI</span>
          <span className="header-dash-name-light">Application Dossier</span>
        </div>
        <div className="dash-header-actions">
          <StatusBadge status={appStatus} />
          <button
            className="btn-primary btn-sm"
            onClick={handleExportPdf}
            disabled={exportingPdf}
            title="Download official PDF report"
          >
            {exportingPdf ? "Generating PDF..." : "📥 Export PDF Report"}
          </button>
          <button className="btn-outline-light" onClick={onBack}>
            ← Dashboard
          </button>
        </div>
      </header>

      <div className="dash-body dossier-body">
        {error && <div className="alert-error">{error}</div>}

        {/* 1. Applicant Profile */}
        <SectionCard title="Applicant Profile" icon="👤">
          <div className="info-grid-2">
            <InfoRow label="Full Name" value={app.applicant_name} />
            <InfoRow label="Email" value={app.email} />
            <InfoRow label="Phone" value={app.phone} />
            <InfoRow label="Application ID" value={app.application_id} />
            <InfoRow
              label="Submitted"
              value={app.created_at ? new Date(app.created_at).toLocaleString("en-IN") : "—"}
            />
            <InfoRow label="Current Status" value={appStatus} />
          </div>
        </SectionCard>

        {/* 2. Application Information */}
        <SectionCard title="Loan Application Details" icon="💼">
          <div className="info-grid-2">
            <InfoRow
              label="Requested Loan Amount"
              value={`₹${Number(app.loan_amount || 0).toLocaleString("en-IN")}`}
              highlight
            />
            <InfoRow
              label="Declared Annual Income"
              value={`₹${Number(app.annual_income || 0).toLocaleString("en-IN")}`}
              highlight
            />
            <InfoRow label="CIBIL Score" value={app.cibil_score} />
            <InfoRow label="Loan Term" value={app.loan_term ? `${app.loan_term} years` : "—"} />
            <InfoRow label="Education" value={app.education} />
            <InfoRow label="Self Employed" value={app.self_employed} />
            <InfoRow
              label="Loan-to-Income Ratio"
              value={
                app.annual_income
                  ? `${((app.loan_amount / app.annual_income) * 100).toFixed(1)}%`
                  : "—"
              }
            />
            <InfoRow
              label="Residential Assets"
              value={`₹${Number(app.residential_assets_value || 0).toLocaleString("en-IN")}`}
            />
            <InfoRow
              label="Commercial Assets"
              value={`₹${Number(app.commercial_assets_value || 0).toLocaleString("en-IN")}`}
            />
            <InfoRow
              label="Bank Asset Value"
              value={`₹${Number(app.bank_asset_value || 0).toLocaleString("en-IN")}`}
            />
          </div>
        </SectionCard>

        {/* 3. Documents */}
        <SectionCard title={`Documents (${documents.length})`} icon="📁">
          {documents.length === 0 ? (
            <div className="empty-small">No documents uploaded yet.</div>
          ) : (
            <div className="doc-grid">
              {documents.map((doc) => {
                const conf = doc.confidence_score || doc.classification_confidence || 0;
                const fields = doc.extracted_json || {};
                return (
                  <div className="doc-card-officer" key={doc.document_id}>
                    <div className="doc-card-header">
                      <span className="doc-type-badge">{doc.document_type}</span>
                      <a
                        href={getDocumentDownloadUrl(doc.document_id)}
                        target="_blank"
                        rel="noreferrer"
                        className="doc-download-link"
                      >
                        📄 PDF
                      </a>
                    </div>
                    <p className="doc-filename">{doc.original_filename}</p>
                    <div className="doc-conf-bar">
                      <div className="doc-conf-fill" style={{ width: `${conf}%` }} />
                    </div>
                    <p className="doc-conf-label">
                      Extraction confidence: <strong>{conf.toFixed(1)}%</strong>
                    </p>
                    {/* Show key extracted fields */}
                    <div className="doc-fields">
                      {Object.entries(fields)
                        .filter(([, v]) => v)
                        .slice(0, 4)
                        .map(([k, v]) => (
                          <div className="doc-field-row" key={k}>
                            <span className="doc-field-key">
                              {k.replace(/_/g, " ")}
                            </span>
                            <span className="doc-field-val">{String(v)}</span>
                          </div>
                        ))}
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          {documents.length > 0 && (
            <button
              className="btn-primary"
              onClick={handleRunProcessing}
              disabled={processing}
              style={{ marginTop: 16 }}
            >
              {processing ? "⚙️ Processing..." : "⚙️ Re-run AI Processing"}
            </button>
          )}
        </SectionCard>

        {/* 4. Cross-Document Verification */}
        {app.validation_report && (
          <SectionCard title="Cross-Document Verification" icon="🔍">
            <CrossDocSection validation={app.validation_report} />
          </SectionCard>
        )}

        {/* 5. Missing Documents */}
        {app.validation_report?.missing_documents?.length > 0 && (
          <SectionCard title="Missing Documents" icon="⚠️">
            <div className="missing-docs-list">
              {app.validation_report.missing_documents.map((doc) => (
                <div className="missing-doc-item" key={doc}>
                  <span className="missing-icon">✗</span>
                  <span>{doc}</span>
                  <span className="missing-required">Required</span>
                </div>
              ))}
            </div>
          </SectionCard>
        )}

        {/* 6. ML Eligibility */}
        {app.ml_result && (
          <SectionCard title="ML Eligibility Assessment" icon="🤖">
            <MLSection ml={app.ml_result} />
          </SectionCard>
        )}

        {/* 7. AI Summary */}
        {app.ai_summary && (
          <SectionCard title="AI Loan Processing Summary" icon="📜">
            <button
              className="btn-outline"
              onClick={() => setShowSummary(!showSummary)}
            >
              {showSummary ? "Hide Summary" : "View Full AI Summary"}
            </button>
            {showSummary && (
              <pre className="ai-summary-pre">{app.ai_summary}</pre>
            )}
          </SectionCard>
        )}

        {/* 8. Context-Aware AI Loan Analyst Assistant */}
        <SectionCard title="AI Loan Analyst Assistant (Context-Aware Agent)" icon="🤖">
          <div className="ai-assistant-wrapper">
            <p className="ai-assistant-desc">
              Ask questions directly about this applicant&apos;s income verification, cross-document inconsistencies, credit risk rating, or ask the agent to draft custom underwriting notes.
            </p>

            {/* Quick Prompt Chips */}
            <div className="prompt-chips">
              {[
                { label: "📊 Summarize Risk", query: "Summarize this loan application, key risks, and verification findings." },
                { label: "🚨 Explain Anomalies", query: "Are there any document discrepancies or income mismatches?" },
                { label: "💳 CIBIL & Credit Analysis", query: "Explain this applicant's CIBIL score and default probability." },
                { label: "📝 Draft Approval Note", query: "Draft an officer approval decision note for this loan." },
                { label: "❌ Draft Rejection Note", query: "Draft an officer rejection decision note explaining the reasons." },
              ].map((chip) => (
                <button
                  key={chip.label}
                  type="button"
                  className="chip-btn"
                  onClick={() => handleSendQuery(chip.query)}
                  disabled={chatLoading}
                >
                  {chip.label}
                </button>
              ))}
            </div>

            {/* Chat History View */}
            <div className="ai-chat-box">
              {chatMessages.map((msg, i) => (
                <div
                  key={i}
                  className={`chat-bubble-row ${msg.role === "user" ? "chat-row-user" : "chat-row-agent"}`}
                >
                  <div className={`chat-bubble ${msg.role === "user" ? "bubble-user" : "bubble-agent"}`}>
                    <div className="chat-bubble-header">
                      <strong>{msg.role === "user" ? "Officer Inquiry" : "🤖 SmartLoan AI Analyst"}</strong>
                    </div>
                    <div className="chat-bubble-text" style={{ whiteSpace: "pre-wrap" }}>
                      {msg.content}
                    </div>

                    {msg.role === "model" && i > 0 && (
                      <button
                        type="button"
                        className="btn-use-note"
                        onClick={() => handleUseAiNoteInReview(msg.content)}
                        title="Copy suggested note into review decision notes form"
                      >
                        ✍️ Use as Officer Note
                      </button>
                    )}
                  </div>
                </div>
              ))}

              {chatLoading && (
                <div className="chat-bubble-row chat-row-agent">
                  <div className="chat-bubble bubble-agent chat-typing">
                    🤖 Analyzing underwriting data & synthesis...
                  </div>
                </div>
              )}
            </div>

            {/* Chat Input Bar */}
            <form
              className="chat-input-bar"
              onSubmit={(e) => {
                e.preventDefault();
                handleSendQuery();
              }}
            >
              <input
                type="text"
                placeholder="Ask the AI Analyst (e.g. 'Compare income to bank statements', 'What is the asset coverage?')..."
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                disabled={chatLoading}
              />
              <button type="submit" className="btn-primary" disabled={chatLoading || !chatInput.trim()}>
                {chatLoading ? "Thinking..." : "Ask Agent →"}
              </button>
            </form>
          </div>
        </SectionCard>

        {/* 9. Officer Review Panel */}
        <SectionCard title="Officer Decision" icon="⚖️">
          {reviewSuccess && (
            <div className="alert-success">{reviewSuccess}</div>
          )}
          {app.review_notes && (
            <div className="previous-review">
              <p className="prev-review-label">Previous Review</p>
              <p>
                <strong>Decision:</strong> {app.status}
              </p>
              <p>
                <strong>Notes:</strong> {app.review_notes}
              </p>
              <p>
                <strong>Reviewed by:</strong> {app.reviewed_by} on{" "}
                {app.reviewed_at
                  ? new Date(app.reviewed_at).toLocaleString("en-IN")
                  : "—"}
              </p>
            </div>
          )}

          <form className="review-form" onSubmit={handleSubmitReview}>
            <div className="decision-buttons">
              {["Approved", "Rejected", "Manual Review", "Request Re-upload"].map(
                (d) => (
                  <button
                    key={d}
                    type="button"
                    className={`decision-btn ${
                      d === "Approved"
                        ? "decision-approve"
                        : d === "Rejected"
                        ? "decision-reject"
                        : "decision-neutral"
                    } ${decision === d ? "decision-active" : ""}`}
                    onClick={() => setDecision(d)}
                  >
                    {d === "Approved"
                      ? "✓ Approve"
                      : d === "Rejected"
                      ? "✗ Reject"
                      : d === "Manual Review"
                      ? "⚠ Manual Review"
                      : "📋 Request More Info"}
                  </button>
                )
              )}
            </div>

            <div className="form-field" style={{ marginTop: 16 }}>
              <label>
                Officer Notes{" "}
                <span className="field-hint">(required)</span>
              </label>
              <textarea
                className="review-textarea"
                placeholder="Add your review notes, observations, and reasoning..."
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                rows={4}
                required
              />
            </div>

            {reviewError && <div className="alert-error">{reviewError}</div>}

            <div className="officer-disclaimer">
              ⚖️ <strong>Reminder:</strong> As Loan Officer, you are solely responsible
              for the final loan decision. The AI provides analysis to support — not
              replace — your professional judgment.
            </div>

            <button
              className="btn-primary"
              type="submit"
              disabled={submitting || !decision}
              style={{ marginTop: 12, width: "100%" }}
            >
              {submitting ? "Submitting..." : `Submit Decision: ${decision || "Select above"}`}
            </button>
          </form>
        </SectionCard>

        {/* 9. Audit Trail */}
        <SectionCard title="Audit Trail" icon="📋">
          {auditLog.length === 0 ? (
            <div className="empty-small">No audit events recorded yet.</div>
          ) : (
            <div className="audit-timeline">
              {auditLog.map((event, i) => (
                <div className="audit-item" key={i}>
                  <div className="audit-dot" />
                  <div className="audit-content">
                    <p className="audit-event">{event.event}</p>
                    {event.details && (
                      <p className="audit-details">{event.details}</p>
                    )}
                    <p className="audit-meta">
                      {event.user_email || "System"} •{" "}
                      {event.created_at
                        ? new Date(event.created_at).toLocaleString("en-IN")
                        : "—"}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </SectionCard>
      </div>
    </main>
  );
}

// ─── Sub-components ────────────────────────────────────────────────────

function CrossDocSection({ validation }) {
  const inconsistencies = validation.inconsistencies || [];
  const checklist = validation.checklist || {};

  return (
    <div>
      {/* Document Checklist */}
      <div className="cross-doc-checklist">
        {Object.entries(checklist).map(([docType, info]) => (
          <div
            className={`checklist-item ${
              info.uploaded ? "checklist-ok" : "checklist-missing"
            }`}
            key={docType}
          >
            <span>{info.uploaded ? "✓" : "✗"}</span>
            <span>{docType}</span>
            <span className="checklist-status">
              {info.uploaded ? "Verified" : "Missing"}
            </span>
          </div>
        ))}
      </div>

      {/* Inconsistencies */}
      {inconsistencies.length === 0 ? (
        <div className="cross-doc-clean">
          ✅ Zero discrepancies detected. All document data matches application declarations.
        </div>
      ) : (
        <div className="inconsistency-list">
          <p className="inconsistency-title">
            {inconsistencies.length} Anomaly Indicator(s) Detected:
          </p>
          {inconsistencies.map((issue, i) => {
            const isHigh = issue.severity === "HIGH";
            const isMed = issue.severity === "MEDIUM";
            return (
              <div
                className={`inconsistency-item ${
                  isHigh
                    ? "issue-high"
                    : isMed
                    ? "issue-medium"
                    : "issue-low"
                }`}
                key={i}
              >
                <div className="issue-header">
                  <span
                    className={`severity-tag ${
                      isHigh ? "sev-high" : isMed ? "sev-med" : "sev-low"
                    }`}
                  >
                    {issue.severity}
                  </span>
                  <strong>{issue.type?.replace(/_/g, " ")}</strong>
                </div>
                <p className="issue-message">{issue.message}</p>
                {issue.declared_value && (
                  <div className="issue-values">
                    <span>
                      Application: <strong>{issue.declared_value}</strong>
                    </span>
                    <span>
                      Document: <strong>{issue.extracted_value}</strong>
                    </span>
                  </div>
                )}
                {issue.variance_pct && (
                  <p className="issue-variance">
                    Variance: {issue.variance_pct}%
                  </p>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Income Comparison */}
      {validation.income_comparison?.evidence?.length > 0 && (
        <div className="income-compare">
          <p className="income-compare-title">Income Cross-Validation:</p>
          <div className="info-row">
            <span className="info-label">Declared Income</span>
            <span className="info-value">
              ₹{Number(validation.income_comparison.declared_annual_income || 0).toLocaleString("en-IN")}
            </span>
          </div>
          {validation.income_comparison.evidence.map(([src, amt]) => (
            <div className="info-row" key={src}>
              <span className="info-label">{src}</span>
              <span className="info-value">
                ₹{Number(amt).toLocaleString("en-IN")}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function MLSection({ ml }) {
  const isApproved = ml.status === "Approved";
  const isRejected = ml.status === "Rejected";

  return (
    <div>
      <div
        className={`ml-verdict ${
          isApproved
            ? "ml-approved"
            : isRejected
            ? "ml-rejected"
            : "ml-review"
        }`}
      >
        <div>
          <p className="ml-verdict-label">AI Recommendation</p>
          <p className="ml-verdict-status">{ml.status}</p>
          <p className="ml-reason">{ml.reason}</p>
        </div>
        <div className="ml-metrics">
          <div className="ml-metric">
            <span className="ml-metric-label">Confidence</span>
            <span className="ml-metric-value">{ml.confidence?.toFixed(1)}%</span>
          </div>
          <div className="ml-metric">
            <span className="ml-metric-label">Risk Level</span>
            <span className="ml-metric-value">{ml.risk_level}</span>
          </div>
          <div className="ml-metric">
            <span className="ml-metric-label">CIBIL Score</span>
            <span className="ml-metric-value">{ml.cibil_score}</span>
          </div>
        </div>
      </div>
      <p className="ml-disclaimer">
        ℹ️ This is an AI-assisted assessment. The final loan decision is the exclusive
        responsibility of the Loan Officer.
      </p>
    </div>
  );
}
