export default function EligibilityResult({ result }) {
  if (!result) {
    return (
      <section className="panel empty-panel">
        <span>STEP 3</span>
        <h2>AI decision</h2>
        <p>
          Upload and validate a document to see the eligibility result.
        </p>
      </section>
    );
  }

  const status = result.status || (result.eligible ? "Approved" : "Manual Review");

  const isApproved =
    result.eligible === true ||
    status.toLowerCase() === "approved";

  const isRejected =
    status.toLowerCase() === "rejected";

  const decisionClass = isApproved
    ? "eligible-panel"
    : isRejected
    ? "rejected-panel"
    : "review-panel";

  const badgeClass = isApproved
    ? "eligible"
    : isRejected
    ? "rejected"
    : "review";

  const badgeText = isApproved
    ? "✓ Approved"
    : isRejected
    ? "✕ Rejected"
    : "⚠ Manual Review";

  return (
    <section className={`panel result-panel ${decisionClass}`}>
      <div className="section-heading">
        <span>STEP 3</span>
        <h2>AI decision</h2>
        <p>The AI has completed the application review.</p>
      </div>

      <div className={`decision-badge ${badgeClass}`}>
        {badgeText}
      </div>

      <div className="result-details">
        <p>
          <strong>Status:</strong> {status}
        </p>

        <p>
          <strong>Risk level:</strong>{" "}
          {result.risk_level || "Not available"}
        </p>

        <p>
          <strong>Reason:</strong>{" "}
          {result.reason || "No reason provided"}
        </p>

        {result.income_limit && (
          <p>
            <strong>Income limit:</strong>{" "}
            ₹{Number(result.income_limit).toLocaleString("en-IN")}
          </p>
        )}

        {result.applicant_name && (
          <p>
            <strong>Applicant:</strong> {result.applicant_name}
          </p>
        )}

        {result.payslip_employee_name && (
          <p>
            <strong>Payslip employee:</strong>{" "}
            {result.payslip_employee_name}
          </p>
        )}

        {result.loan_id !== undefined && (
          <p>
            <strong>Dataset Loan ID:</strong> {result.loan_id}
          </p>
        )}
      </div>
    </section>
  );
}