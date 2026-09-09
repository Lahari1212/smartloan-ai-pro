export default function ApplicationTable({ applications }) {
  return (
    <section className="panel table-panel">
      <div className="section-heading">
        <h2>Loan applications</h2>
        <p>Review the latest application records.</p>
      </div>

      <div className="table-wrapper">
        <table>
          <thead>
            <tr>
              <th>Applicant</th>
              <th>Income</th>
              <th>Loan Amount</th>
              <th>Status</th>
            </tr>
          </thead>

          <tbody>
            {applications.length === 0 ? (
              <tr>
                <td colSpan="4" className="no-data">
                  No applications found.
                </td>
              </tr>
            ) : (
              applications.map((application) => (
                <tr key={application.application_id}>
                  <td>
                    <strong>{application.applicant_name}</strong>
                    <small>{application.email}</small>
                  </td>

                  <td>
                    ₹
                    {Number(
                      application.annual_income
                    ).toLocaleString("en-IN")}
                  </td>

                  <td>
                    ₹
                    {Number(
                      application.loan_amount
                    ).toLocaleString("en-IN")}
                  </td>

                  <td>
                    <span
                      className={`status-badge ${
                        application.status === "Eligible"
                          ? "status-eligible"
                          : application.status === "Manual Review"
                          ? "status-review"
                          : "status-pending"
                      }`}
                    >
                      {application.status}
                    </span>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}