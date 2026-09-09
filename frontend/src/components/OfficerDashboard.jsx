import { useEffect, useState } from "react";
import DashboardStats from "./DashboardStats";
import ApplicationTable from "./ApplicationTable";
import { getApplications } from "../services/api";

export default function OfficerDashboard({ user, onLogout }) {
  const [applications, setApplications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadApplications = async () => {
    try {
      const response = await getApplications();
      setApplications(response.data.applications || []);
    } catch {
      setError("Unable to load applications.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadApplications();
  }, []);

  return (
    <main className="dashboard-page">
      <header className="dashboard-header officer-header">
        <div>
          <p className="brand-label">SMARTLOAN AI</p>
          <h1>Loan Officer Dashboard</h1>
        </div>

        <button className="outline-button" onClick={onLogout}>
          Logout
        </button>
      </header>

      <div className="dashboard-container">
        <div className="welcome-section">
          <p>Officer workspace</p>
          <h2>Application overview</h2>
          <span>
            Logged in as {user?.employeeId || "Loan Officer"}
          </span>
        </div>

        {error && <div className="error-message">{error}</div>}

        {loading ? (
          <div className="panel">Loading applications...</div>
        ) : (
          <>
            <DashboardStats applications={applications} />

            <div className="table-space">
              <ApplicationTable applications={applications} />
            </div>
          </>
        )}
      </div>
    </main>
  );
}