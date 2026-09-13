import { useState } from "react";
import { loginUser, saveSession } from "../services/api";

export default function ApplicantLogin({ onLogin, onRegister, onBack }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const res = await loginUser({ email, password });
      const { access_token, user } = res.data;

      if (user.role !== "applicant") {
        setError("This portal is for applicants only. Please use the Loan Officer Portal.");
        return;
      }

      saveSession(access_token, user);
      onLogin(user);
    } catch (err) {
      const msg = err.response?.data?.detail || "Login failed. Please check your credentials.";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="auth-page applicant-auth-page">
      <form className="auth-card" onSubmit={handleSubmit}>
        <button type="button" className="back-btn" onClick={onBack}>
          ← Back
        </button>

        <div className="auth-brand">APPLICANT PORTAL</div>
        <h1 className="auth-title">Welcome back</h1>
        <p className="auth-subtitle">Sign in to manage your loan application.</p>

        {error && <div className="auth-error">{error}</div>}

        <div className="form-field">
          <label>Email address</label>
          <input
            type="email"
            placeholder="you@example.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            disabled={loading}
            autoComplete="email"
          />
        </div>

        <div className="form-field">
          <label>Password</label>
          <input
            type="password"
            placeholder="Enter your password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            disabled={loading}
            autoComplete="current-password"
          />
        </div>

        <button className="auth-submit-btn" type="submit" disabled={loading}>
          {loading ? "Signing in..." : "Login"}
        </button>

        <p className="auth-switch">
          Don&apos;t have an account?{" "}
          <button type="button" className="link-btn" onClick={onRegister}>
            Create Account
          </button>
        </p>
      </form>
    </main>
  );
}
