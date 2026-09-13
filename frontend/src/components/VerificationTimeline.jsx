const stages = [
  { id: 1, name: "Kaggle Dataset", desc: "Benchmark record selection" },
  { id: 2, name: "Create Application", desc: "Borrower financial profile" },
  { id: 3, name: "Upload Documents", desc: "Payslip, Bank, KYC, Tax" },
  { id: 4, name: "Document Classification", desc: "PyMuPDF text & type detection" },
  { id: 5, name: "AI Extraction", desc: "GenAI structured JSON parsing" },
  { id: 6, name: "Validation Agent", desc: "Cross-document verification" },
  { id: 7, name: "Check for Issues", desc: "Mismatches & missing docs" },
  { id: 8, name: "Generate Summary", desc: "AI audit memo & ML scoring" },
  { id: 9, name: "Human Review", desc: "Officer checks evidence & signs off" },
];

export default function VerificationTimeline({ currentStage = 3 }) {
  return (
    <section className="panel" style={{ padding: "20px" }}>
      <div className="section-heading" style={{ marginBottom: "16px" }}>
        <span style={{ color: "#2563eb", fontWeight: 700, fontSize: "12px" }}>n8n-STYLE AGENTIC ARCHITECTURE</span>
        <h3 style={{ margin: "4px 0", fontSize: "18px" }}>Intelligent Processing Pipeline</h3>
        <p style={{ color: "#64748b", margin: 0, fontSize: "13px" }}>
          End-to-end multi-document processing and underwriting flow.
        </p>
      </div>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(105px, 1fr))",
          gap: "8px",
          alignItems: "stretch"
        }}
      >
        {stages.map((stage) => {
          const isCompleted = stage.id < currentStage;
          const isCurrent = stage.id === currentStage;

          let bg = "#F8FAFC";
          let border = "#E2E8F0";
          let circleBg = "#E2E8F0";
          let textColor = "#64748B";

          if (isCompleted) {
            bg = "#F0FDF4";
            border = "#86EFAC";
            circleBg = "#22C55E";
            textColor = "#166534";
          } else if (isCurrent) {
            bg = "#EFF6FF";
            border = "#93C5FD";
            circleBg = "#2563EB";
            textColor = "#1E40AF";
          }

          return (
            <div
              key={stage.id}
              style={{
                padding: "10px 8px",
                background: bg,
                border: `1.5px solid ${border}`,
                borderRadius: "8px",
                textAlign: "center",
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                justifyContent: "flex-start",
                transition: "all 0.2s ease"
              }}
            >
              <div
                style={{
                  width: "24px",
                  height: "24px",
                  borderRadius: "50%",
                  background: circleBg,
                  color: (isCompleted || isCurrent) ? "white" : "#64748B",
                  fontSize: "11px",
                  fontWeight: 700,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  marginBottom: "6px"
                }}
              >
                {isCompleted ? "✓" : stage.id}
              </div>
              <strong style={{ fontSize: "11px", color: textColor, lineHeight: 1.2, marginBottom: "4px" }}>
                {stage.name}
              </strong>
              <span style={{ fontSize: "9px", color: "#64748B", lineHeight: 1.2 }}>
                {stage.desc}
              </span>
            </div>
          );
        })}
      </div>
    </section>
  );
}