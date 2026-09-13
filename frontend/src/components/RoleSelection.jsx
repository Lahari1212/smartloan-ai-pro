export default function RoleSelection({ onSelectRole }) {
  return (
    <main className="role-page">
      <div className="role-container">
        <p className="brand-label">SMARTLOAN AI</p>
        <h1>Intelligent Loan Processing</h1>
        <p className="subtitle">
          AI-powered document verification, eligibility assessment, and loan officer review.
        </p>

        <div className="role-grid">
          <button
            className="role-card applicant-card"
            onClick={() => onSelectRole("applicant")}
          >
            <div className="role-icon">👤</div>
            <h2>Applicant Portal</h2>
            <p>
              Apply for a loan, upload documents, track AI processing, and
              monitor your application status.
            </p>
            <span>Continue as Applicant →</span>
          </button>

          <button
            className="role-card officer-card"
            onClick={() => onSelectRole("officer")}
          >
            <div className="role-icon">🧑‍💼</div>
            <h2>Loan Officer Portal</h2>
            <p>
              Review applications, inspect AI findings, cross-document
              analysis, and make final decisions.
            </p>
            <span>Continue as Loan Officer →</span>
          </button>
        </div>

        <p className="role-footer">
          SmartLoan AI — AI assists, humans decide.
        </p>
      </div>
    </main>
  );
}