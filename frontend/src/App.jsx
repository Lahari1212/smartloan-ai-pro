import { useState, useEffect } from "react";
import RoleSelection from "./components/RoleSelection";
import ApplicantLogin from "./components/ApplicantLogin";
import ApplicantRegister from "./components/ApplicantRegister";
import OfficerLogin from "./components/OfficerLogin";
import ApplicantDashboard from "./components/ApplicantDashboard";
import OfficerDashboard from "./components/OfficerDashboard";
import { getStoredUser, clearSession } from "./services/api";

export default function App() {
  const [page, setPage] = useState("roles");
  const [currentUser, setCurrentUser] = useState(null);

  // Restore session on page load
  useEffect(() => {
    const stored = getStoredUser();
    if (stored) {
      setCurrentUser(stored);
      setPage(stored.role === "applicant" ? "applicantDashboard" : "officerDashboard");
    }
  }, []);

  const handleLogin = (user) => {
    setCurrentUser(user);
    setPage(user.role === "applicant" ? "applicantDashboard" : "officerDashboard");
  };

  const handleLogout = () => {
    clearSession();
    setCurrentUser(null);
    setPage("roles");
  };

  if (page === "roles") {
    return (
      <RoleSelection
        onSelectRole={(role) => {
          if (role === "applicant") setPage("applicantLogin");
          else setPage("officerLogin");
        }}
      />
    );
  }

  if (page === "applicantLogin") {
    return (
      <ApplicantLogin
        onLogin={handleLogin}
        onRegister={() => setPage("applicantRegister")}
        onBack={() => setPage("roles")}
      />
    );
  }

  if (page === "applicantRegister") {
    return (
      <ApplicantRegister
        onLogin={handleLogin}
        onBack={() => setPage("applicantLogin")}
      />
    );
  }

  if (page === "officerLogin") {
    return (
      <OfficerLogin
        onLogin={handleLogin}
        onBack={() => setPage("roles")}
      />
    );
  }

  if (page === "applicantDashboard") {
    return (
      <ApplicantDashboard
        user={currentUser}
        onLogout={handleLogout}
      />
    );
  }

  if (page === "officerDashboard") {
    return (
      <OfficerDashboard
        user={currentUser}
        onLogout={handleLogout}
      />
    );
  }

  return null;
}