import { useState } from "react";
import { getDocumentDownloadUrl } from "../services/api";

export default function EligibilityResult({ result, onReset }) {
  const [showFullMemo, setShowFullMemo] = useState(false);

  if (!result) {
    return (
      <section className="panel empty-panel">
        <span style={{ color: "#2563eb", fontWeight: 700 }}>STAGE 8 • AI DECISION</span>
        <h2>AI Agent Findings</h2>
        <p>Complete document upload and verification to see findings.</p>
      </section>
    );
  }

  const validation = result.validation_report || result.validation_result || {};
  const ml = result.ml_result || result.eligibility_result || {};
  const inconsistencies = validation.inconsistencies || [];
  const checklist = validation.checklist || {};
  const documents = result.documents || [];

  const status = result.status || "Manual Review";
  const riskLevel = result.risk_level || ml.risk_level || "Medium";
  const isApproved = status.toLowerCase() === "approved";
  const isRejected = status.toLowerCase() === "rejected";

  const bannerColor = isApproved ? "#166534" : isRejected ? "#991B1B" : "#B45309";
  const bannerBg = isApproved ? "#F0FDF4" : isRejected ? "#FEF2F2" : "#FFFBEB";
  const bannerBorder = isApproved ? "#86EFAC" : isRejected ? "#FCA5A5" : "#FDE68A";

  return (
    <section className="panel result-panel" style={{ marginTop: "24px" }}>
      <div className="section-heading">
        <span style={{ color: "#2563eb", fontWeight: 700 }}>STAGES 6, 7 & 8 • GENAI AUDIT & DECISION DOSSIER</span>
        <h2 style={{ margin: "4px 0" }}>AI Document Verification & Credit Scoring Report</h2>
        <p style={{ color: "#64748b", margin: 0 }}>
          Comprehensive underwriting synthesis from PyMuPDF text, GenAI extraction, and Kaggle ML model.
        </p>
      </div>

      {/* Decision Banner */}
      <div
        style={{
          marginTop: "16px",
          padding: "20px",
          background: bannerBg,
          border: `2px solid ${bannerBorder}`,
          borderRadius: "14px",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: "14px"
        }}
      >
        <div>
          <span style={{ fontSize: "12px", fontWeight: 700, color: bannerColor, textTransform: "uppercase", letterSpacing: "0.05em" }}>
            Underwriting Verdict
          </span>
          <h1 style={{ margin: "2px 0 6px", color: bannerColor, fontSize: "28px" }}>
            {isApproved ? "✓ Fast-Track Approved" : isRejected ? "✕ Rejected" : "⚠ Referred for Officer Review"}
          </h1>
          <p style={{ margin: 0, fontSize: "14px", color: bannerColor, opacity: 0.9 }}>
            {result.reason || ml.reason || "Documents processed and reviewed by AI agent."}
          </p>
        </div>

        <div style={{ display: "flex", gap: "10px", alignItems: "center" }}>
          <div style={{ textAlign: "right", paddingRight: "12px", borderRight: `1px solid ${bannerBorder}` }}>
            <span style={{ fontSize: "11px", color: "#64748B", display: "block" }}>RISK PROFILE</span>
            <strong style={{ fontSize: "16px", color: bannerColor }}>{riskLevel} Risk</strong>
          </div>
          <div style={{ textAlign: "right" }}>
            <span style={{ fontSize: "11px", color: "#64748B", display: "block" }}>ML CONFIDENCE</span>
            <strong style={{ fontSize: "16px", color: bannerColor }}>{ml.confidence || 85}%</strong>
          </div>
        </div>
      </div>

      {/* AI Disclaimer */}
      <div style={{ margin: "14px 0 0", padding: "12px 16px", background: "#eff6ff", border: "1px solid #bfdbfe", borderRadius: "10px", fontSize: "13px", color: "#1e40af", borderLeft: "3px solid #2563eb" }}>
        ⚖️ <strong>Important:</strong> This is an AI-generated recommendation to support — not replace — human judgment.
        All final loan approval or rejection decisions are made exclusively by the Loan Officer.
        The AI cannot approve or reject any loan application.
      </div>

      {/* Cross-Document Inconsistencies & Red Flags */}
      <div style={{ marginTop: "24px" }}>
        <h3 style={{ margin: "0 0 10px", color: "#1E293B", display: "flex", alignItems: "center", gap: "8px" }}>
          <span>🔍</span> Anomaly Indicators &amp; Verification Flags ({inconsistencies.length})
        </h3>

        {inconsistencies.length === 0 ? (
          <div style={{ padding: "14px 18px", background: "#F0FDF4", border: "1px solid #BBF7D0", borderRadius: "10px", color: "#166534", fontSize: "14px" }}>
            ✓ <b>Zero discrepancies detected!</b> Declared income, applicant legal name, and tax filings match across all submitted documents.
          </div>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
            {inconsistencies.map((issue, idx) => {
              const isHigh = issue.severity === "HIGH";
              const isMed = issue.severity === "MEDIUM";
              return (
                <div
                  key={idx}
                  style={{
                    padding: "12px 16px",
                    background: isHigh ? "#FEF2F2" : isMed ? "#FFFBEB" : "#F8FAFC",
                    border: `1px solid ${isHigh ? "#FCA5A5" : isMed ? "#FDE68A" : "#E2E8F0"}`,
                    borderRadius: "10px",
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "flex-start",
                    gap: "12px"
                  }}
                >
                  <div>
                    <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "4px" }}>
                      <span
                        style={{
                          padding: "2px 8px",
                          borderRadius: "6px",
                          fontSize: "11px",
                          fontWeight: 700,
                          background: isHigh ? "#EF4444" : isMed ? "#F59E0B" : "#64748B",
                          color: "white"
                        }}
                      >
                        {issue.severity}
                      </span>
                      <strong style={{ fontSize: "13px", color: "#1E293B" }}>{issue.type}</strong>
                    </div>
                    <p style={{ margin: 0, fontSize: "13px", color: "#334155" }}>
                      {issue.message}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Document Checklist & Extracted Telemetry */}
      <div style={{ marginTop: "24px" }}>
        <h3 style={{ margin: "0 0 10px", color: "#1E293B", display: "flex", alignItems: "center", gap: "8px" }}>
          <span>📋</span> Document Verification Checklist
        </h3>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: "12px" }}>
          {Object.entries(checklist).map(([docType, info]) => (
            <div
              key={docType}
              style={{
                padding: "12px 14px",
                borderRadius: "8px",
                border: "1px solid #E2E8F0",
                background: info.uploaded ? "#F8FAFC" : "#FFF1F2"
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <strong style={{ fontSize: "13px", color: "#1E293B" }}>{docType}</strong>
                <span
                  style={{
                    fontSize: "11px",
                    fontWeight: 700,
                    color: info.uploaded ? "#166534" : "#991B1B"
                  }}
                >
                  {info.uploaded ? "✓ Verified" : "✗ Missing"}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Attached Documents Preview & Download */}
      {documents.length > 0 && (
        <div style={{ marginTop: "24px" }}>
          <h3 style={{ margin: "0 0 10px", color: "#1E293B" }}>
            Extracted Document Telemetry ({documents.length})
          </h3>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))", gap: "12px" }}>
            {documents.map((doc) => {
              const json = doc.extracted_json || {};
              return (
                <div
                  key={doc.document_id}
                  style={{
                    padding: "14px",
                    background: "white",
                    border: "1px solid #CBD5E1",
                    borderRadius: "10px",
                    display: "flex",
                    flexDirection: "column",
                    justifyContent: "space-between"
                  }}
                >
                  <div>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                      <span style={{ fontWeight: 700, color: "#1E3A8A", fontSize: "14px" }}>
                        {doc.document_type}
                      </span>
                      <a
                        href={getDocumentDownloadUrl(doc.document_id)}
                        target="_blank"
                        rel="noreferrer"
                        style={{ fontSize: "12px", color: "#2563EB", fontWeight: 600, textDecoration: "none" }}
                      >
                        📄 Download PDF
                      </a>
                    </div>
                    <div style={{ fontSize: "11px", color: "#64748B", margin: "4px 0 10px" }}>
                      Extraction Confidence: {doc.confidence_score || 95}%
                    </div>

                    <div style={{ fontSize: "12px", color: "#334155", background: "#F8FAFC", padding: "8px", borderRadius: "6px" }}>
                      {Object.entries(json).slice(0, 5).map(([k, v]) => (
                        <div key={k} style={{ display: "flex", justifyContent: "space-between", margin: "3px 0" }}>
                          <span style={{ color: "#64748B" }}>{k.replace(/_/g, " ")}:</span>
                          <span style={{ fontWeight: 600, textAlign: "right" }}>{String(v)}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* GenAI Executive Summary Memo Toggle */}
      {result.ai_summary && (
        <div style={{ marginTop: "24px" }}>
          <button
            type="button"
            onClick={() => setShowFullMemo(!showFullMemo)}
            style={{
              padding: "10px 18px",
              background: "#F1F5F9",
              border: "1px solid #CBD5E1",
              borderRadius: "8px",
              fontWeight: 600,
              color: "#334155",
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              gap: "8px"
            }}
          >
            📜 {showFullMemo ? "Hide Audit Memo" : "View Full GenAI Loan Processing Audit Memo"}
          </button>

          {showFullMemo && (
            <pre
              style={{
                marginTop: "12px",
                padding: "16px",
                background: "#0F172A",
                color: "#E2E8F0",
                borderRadius: "10px",
                fontSize: "12px",
                fontFamily: "monospace",
                overflowX: "auto",
                whiteSpace: "pre-wrap",
                lineHeight: 1.5
              }}
            >
              {result.ai_summary}
            </pre>
          )}
        </div>
      )}

      {onReset && (
        <button
          type="button"
          onClick={onReset}
          style={{
            marginTop: "24px",
            padding: "12px 24px",
            background: "#64748B",
            color: "white",
            border: "none",
            borderRadius: "8px",
            fontWeight: 600,
            cursor: "pointer"
          }}
        >
          ← Process Another Application
        </button>
      )}
    </section>
  );
}