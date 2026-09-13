import { useState } from "react";
import { registerApplicant, saveSession } from "../services/api";

export default function ApplicantRegister({ onLogin, onBack }) {
  const [form, setForm] = useState({
    full_name: "",
    email: "",
    password: "",
    confirm_password: "",
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleChange = (e) => {
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    if (form.password.length < 8) {
      setError("Password must be at least 8 characters.");
      return;
    }

    if (form.password !== form.confirm_password) {
      setError("Passwords do not match.");
      return;
    }

    setLoading(true);
    try {
      const res = await registerApplicant(form);
      const { access_token, user } = res.data;
      saveSession(access_token, user);
      onLogin(user);
    } catch (err) {
      const msg = err.response?.data?.detail || "Registration failed. Please try again.";
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
        <h1 className="auth-title">Create your account</h1>
        <p className="auth-subtitle">Join SmartLoan AI and apply for a loan in minutes.</p>

        {error && <div className="auth-error">{error}</div>}

        <div className="form-field">
          <label>Full Name</label>
          <input
            type="text"
            name="full_name"
            placeholder="e.g. Aditi Sharma"
            value={form.full_name}
            onChange={handleChange}
            required
            disabled={loading}
            autoComplete="name"
          />
        </div>

        <div className="form-field">
          <label>Email address</label>
          <input
            type="email"
            name="email"
            placeholder="you@example.com"
            value={form.email}
            onChange={handleChange}
            required
            disabled={loading}
            autoComplete="email"
          />
        </div>

        <div className="form-field">
          <label>Password <span className="field-hint">(min. 8 characters)</span></label>
          <input
            type="password"
            name="password"
            placeholder="Create a strong password"
            value={form.password}
            onChange={handleChange}
            required
            minLength={8}
            disabled={loading}
            autoComplete="new-password"
          />
        </div>

        <div className="form-field">
          <label>Confirm Password</label>
          <input
            type="password"
            name="confirm_password"
            placeholder="Repeat your password"
            value={form.confirm_password}
            onChange={handleChange}
            required
            disabled={loading}
            autoComplete="new-password"
          />
        </div>

        <button className="auth-submit-btn" type="submit" disabled={loading}>
          {loading ? "Creating account..." : "Create Account"}
        </button>

        <p className="auth-switch">
          Already have an account?{" "}
          <button type="button" className="link-btn" onClick={onBack}>
            Login
          </button>
        </p>
      </form>
    </main>
  );
}
