import { useState } from "react";
import { uploadDocument, generateDummyDocs, processAllDocuments, getDocumentDownloadUrl } from "../services/api";

export default function DocumentUpload({ applicationId, onCompleted }) {
  const [uploadedDocs, setUploadedDocs] = useState([]);
  const [fileToUpload, setFileToUpload] = useState(null);
  const [loading, setLoading] = useState(false);
  const [actionMessage, setActionMessage] = useState("");
  const [error, setError] = useState("");

  const docTypesList = [
    { type: "Payslip", label: "Payslip / Salary Certificate", icon: "💰", req: "Mandatory" },
    { type: "Bank Statement", label: "Bank Account Statement (3 Mo)", icon: "🏦", req: "Mandatory" },
    { type: "KYC Document", label: "Official Identity Proof (KYC)", icon: "🪪", req: "Mandatory" },
    { type: "Tax Return", label: "Income Tax Return (ITR-V / Form 16)", icon: "📑", req: "Recommended" },
  ];

  const handleManualUpload = async (e) => {
    e.preventDefault();
    if (!fileToUpload) {
      setError("Please select a PDF file.");
      return;
    }

    setLoading(true);
    setError("");
    setActionMessage("Extracting text and running AI classification...");

    try {
      const res = await uploadDocument(applicationId, fileToUpload);
      setUploadedDocs((prev) => [...prev, res.data]);
      setFileToUpload(null);
      setActionMessage("Document uploaded and classified successfully!");
    } catch (err) {
      console.error(err);
      setError(err.response?.data?.detail || err.message || "Failed to upload document");
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateDummySuite = async (scenario) => {
    setLoading(true);
    setError("");
    setActionMessage(
      scenario === "clean"
        ? "Generating 4 clean matching documents (Payslip, Bank Statement, Tax Return, KYC) and running AI validation agent..."
        : "Generating documents with intentional income discrepancy to demonstrate anomaly detection..."
    );

    try {
      const res = await generateDummyDocs(applicationId, scenario);
      setUploadedDocs(res.data.documents || []);
      setActionMessage("Full agentic verification workflow completed!");
      if (onCompleted) {
        onCompleted(res.data);
      }
    } catch (err) {
      console.error("Dummy generation error:", err);
      setError(err.response?.data?.detail || err.message || "Failed to generate demo document bundle");
    } finally {
      setLoading(false);
    }
  };

  const handleRunVerification = async () => {
    setLoading(true);
    setError("");
    setActionMessage("Executing cross-document consistency agent & Kaggle ML underwriting model...");

    try {
      const res = await processAllDocuments(applicationId);
      if (onCompleted) {
        onCompleted(res.data);
      }
    } catch (err) {
      console.error("Verification error:", err);
      setError(err.response?.data?.detail || err.message || "Failed to complete verification");
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="panel document-upload-panel">
      <div className="section-heading">
        <span style={{ color: "#2563eb", fontWeight: 700 }}>STAGE 3 • DOCUMENT REPOSITORY</span>
        <h2 style={{ margin: "4px 0" }}>Upload Required Documents & Instant Generator</h2>
        <p style={{ color: "#64748b", margin: 0 }}>
          Upload PDF proofs or use the built-in generator to create test documents on the fly.
        </p>
      </div>

      {/* Instant Demo Generator Toolbar */}
      <div style={{ padding: "16px", background: "#F0FDF4", border: "1.5px solid #86EFAC", borderRadius: "12px", margin: "14px 0" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "10px" }}>
          <div>
            <strong style={{ color: "#166534", fontSize: "15px" }}>⚡ One-Click GenAI Test Generator:</strong>
            <p style={{ margin: "4px 0 0", fontSize: "13px", color: "#15803D" }}>
              Automatically generate all 4 standard PDFs (Payslip, Bank Statement, Tax Return, KYC) and execute the agent pipeline.
            </p>
          </div>

          <div style={{ display: "flex", gap: "10px", flexWrap: "wrap" }}>
            <button
              type="button"
              onClick={() => handleGenerateDummySuite("clean")}
              disabled={loading}
              style={{
                padding: "10px 16px",
                background: "#15803D",
                color: "white",
                border: "none",
                borderRadius: "8px",
                fontWeight: 600,
                cursor: loading ? "not-allowed" : "pointer"
              }}
            >
              ✓ Generate Clean Suite (Match)
            </button>

            <button
              type="button"
              onClick={() => handleGenerateDummySuite("discrepancy")}
              disabled={loading}
              style={{
                padding: "10px 16px",
                background: "#B45309",
                color: "white",
                border: "none",
                borderRadius: "8px",
                fontWeight: 600,
                cursor: loading ? "not-allowed" : "pointer"
              }}
            >
              ⚠ Generate Anomaly Suite (Mismatch)
            </button>
          </div>
        </div>
      </div>

      {/* Manual Upload Section */}
      <div style={{ padding: "16px", background: "#F8FAFC", border: "1px dashed #CBD5E1", borderRadius: "12px", margin: "10px 0" }}>
        <h4 style={{ margin: "0 0 10px", color: "#334155" }}>Or Upload Custom PDF Document:</h4>
        <div style={{ display: "flex", gap: "12px", alignItems: "center", flexWrap: "wrap" }}>
          <input
            type="file"
            accept=".pdf,application/pdf"
            onChange={(e) => setFileToUpload(e.target.files?.[0] || null)}
            disabled={loading}
            style={{ fontSize: "13px" }}
          />

          <button
            type="button"
            onClick={handleManualUpload}
            disabled={loading || !fileToUpload}
            style={{
              padding: "8px 18px",
              background: "#2563EB",
              color: "white",
              border: "none",
              borderRadius: "6px",
              fontWeight: 600,
              cursor: (!fileToUpload || loading) ? "not-allowed" : "pointer"
            }}
          >
            Upload & Classify PDF
          </button>
        </div>
      </div>

      {/* Document Checklist & Uploaded Cards */}
      <div style={{ marginTop: "16px" }}>
        <h4 style={{ margin: "0 0 12px", color: "#1E293B" }}>Required Documents Verification Grid:</h4>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: "12px" }}>
          {docTypesList.map((docItem) => {
            const uploaded = uploadedDocs.find(
              (d) => d.document_type?.toLowerCase().includes(docItem.type.toLowerCase())
            );
            return (
              <div
                key={docItem.type}
                style={{
                  padding: "14px",
                  borderRadius: "10px",
                  border: uploaded ? "1.5px solid #22C55E" : "1px solid #E2E8F0",
                  background: uploaded ? "#F0FDF4" : "white",
                  display: "flex",
                  flexDirection: "column",
                  justifyContent: "space-between"
                }}
              >
                <div>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                    <span style={{ fontSize: "24px" }}>{docItem.icon}</span>
                    <span
                      style={{
                        padding: "2px 8px",
                        borderRadius: "10px",
                        fontSize: "11px",
                        fontWeight: 700,
                        background: uploaded ? "#DCFCE7" : "#F1F5F9",
                        color: uploaded ? "#166534" : "#64748B"
                      }}
                    >
                      {uploaded ? "✓ Verified" : docItem.req}
                    </span>
                  </div>
                  <strong style={{ display: "block", marginTop: "8px", fontSize: "14px", color: "#1E293B" }}>
                    {docItem.label}
                  </strong>
                  {uploaded && (
                    <div style={{ fontSize: "12px", color: "#166534", marginTop: "4px" }}>
                      Classified: <b>{uploaded.document_type}</b> ({uploaded.classification_confidence || 95}%)
                    </div>
                  )}
                </div>

                {uploaded && (
                  <div style={{ marginTop: "10px", paddingTop: "8px", borderTop: "1px solid #DCFCE7", fontSize: "11px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <span style={{ color: "#475569" }}>Conf: {uploaded.confidence_score || 95}%</span>
                    <a
                      href={getDocumentDownloadUrl(uploaded.document_id)}
                      target="_blank"
                      rel="noreferrer"
                      style={{ color: "#2563EB", textDecoration: "none", fontWeight: 600 }}
                    >
                      View PDF ↗
                    </a>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {actionMessage && (
        <div style={{ marginTop: "16px", padding: "12px", background: "#EFF6FF", border: "1px solid #BFDBFE", borderRadius: "8px", color: "#1D4ED8", fontSize: "13px" }}>
          ℹ {actionMessage}
        </div>
      )}

      {error && (
        <div style={{ marginTop: "16px", padding: "12px", background: "#FEF2F2", border: "1px solid #FCA5A5", borderRadius: "8px", color: "#B91C1C", fontSize: "13px" }}>
          ⚠ {error}
        </div>
      )}

      {uploadedDocs.length > 0 && (
        <button
          type="button"
          onClick={handleRunVerification}
          disabled={loading}
          style={{
            marginTop: "20px",
            width: "100%",
            padding: "14px",
            background: "#2563EB",
            color: "white",
            border: "none",
            borderRadius: "10px",
            fontSize: "15px",
            fontWeight: 700,
            cursor: loading ? "not-allowed" : "pointer"
          }}
        >
          {loading ? "Analyzing Inconsistencies & ML Scoring..." : "Run AI Validation Agent & Synthesize Summary →"}
        </button>
      )}
    </section>
  );
}