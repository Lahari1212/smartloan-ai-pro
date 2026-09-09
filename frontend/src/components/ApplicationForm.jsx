import { useState } from "react";
import { createApplication } from "../services/api";

export default function ApplicationForm({ onCreated }) {
  const [formData, setFormData] = useState({
    applicant_name: "",
    email: "",
    phone: "",
    annual_income: "",
    loan_amount: "",
    loan_id: "",
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleChange = (event) => {
    const { name, value } = event.target;

    setFormData((previousData) => ({
      ...previousData,
      [name]: value,
    }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();

    setError("");

    if (
      !formData.applicant_name ||
      !formData.email ||
      !formData.phone ||
      !formData.annual_income ||
      !formData.loan_amount ||
      !formData.loan_id
    ) {
      setError("Please fill in all fields.");
      return;
    }

    setLoading(true);

    try {
      const payload = {
        applicant_name: formData.applicant_name,
        email: formData.email,
        phone: formData.phone,
        annual_income: Number(formData.annual_income),
        loan_amount: Number(formData.loan_amount),
        loan_id: Number(formData.loan_id),
      };

      const response = await createApplication(payload);

      if (onCreated) {
        onCreated(response.data);
      }
    } catch (error) {
      console.error("Application creation error:", error);

      setError(
        error.response?.data?.detail ||
          error.message ||
          "Unable to create the application."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="panel application-panel">
      <div className="section-heading">
        <span>STEP 1</span>

        <h2>Loan application</h2>

        <p>Enter the applicant's financial details.</p>
      </div>

      <form onSubmit={handleSubmit}>
        <div className="form-grid">
          <input
            type="text"
            name="applicant_name"
            placeholder="Applicant name"
            value={formData.applicant_name}
            onChange={handleChange}
            disabled={loading}
          />

          <input
            type="email"
            name="email"
            placeholder="Email address"
            value={formData.email}
            onChange={handleChange}
            disabled={loading}
          />

          <input
            type="tel"
            name="phone"
            placeholder="Phone number"
            value={formData.phone}
            onChange={handleChange}
            disabled={loading}
          />

          <input
            type="number"
            name="annual_income"
            placeholder="Annual income"
            value={formData.annual_income}
            onChange={handleChange}
            disabled={loading}
          />

          <input
            type="number"
            name="loan_amount"
            placeholder="Loan amount"
            value={formData.loan_amount}
            onChange={handleChange}
            disabled={loading}
          />

          <input
            type="number"
            name="loan_id"
            placeholder="Loan ID"
            value={formData.loan_id}
            onChange={handleChange}
            disabled={loading}
          />
        </div>

        {error && (
          <div className="error-message">
            {error}
          </div>
        )}

        <button
          type="submit"
          className="primary-button full-width"
          disabled={loading}
        >
          {loading ? "Creating..." : "Create Application"}
        </button>
      </form>
    </section>
  );
}