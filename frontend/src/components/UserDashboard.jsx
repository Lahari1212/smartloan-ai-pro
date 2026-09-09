import { useState } from "react";
import ApplicationForm from "./ApplicationForm";
import DocumentUpload from "./DocumentUpload";
import EligibilityResult from "./EligibilityResult";

export default function UserDashboard() {
  const [application, setApplication] = useState(null);
  const [eligibilityResult, setEligibilityResult] = useState(null);

  return (
    <main className="dashboard">
      <div className="section-heading">
        <span>USER DASHBOARD</span>
        <h1>SmartLoan AI</h1>
        <p>Apply for a loan and verify your eligibility.</p>
      </div>

      {!application && (
        <ApplicationForm onCreated={setApplication} />
      )}

      {application && !eligibilityResult && (
        <DocumentUpload
          applicationId={application.application_id}
          onCompleted={setEligibilityResult}
        />
      )}

      {eligibilityResult && (
        <EligibilityResult result={eligibilityResult} />
      )}
    </main>
  );
}