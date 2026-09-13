import { useState, useEffect } from "react";
import { createApplication, getDatasetSamples } from "../services/api";

export default function ApplicationForm({ onCreated }) {
  const [formData, setFormData] = useState({
    applicant_name: "Aditi Sharma",
    email: "aditi.sharma@example.com",
    phone: "9876543210",
    annual_income: "8500000",
    loan_amount: "25000000",
    loan_id: "1",
    cibil_score: "778",
    loan_term: "12",
    education: "Graduate",
    self_employed: "No",
    residential_assets_value: "2400000",
    commercial_assets_value: "17600000",
    luxury_assets_value: "22700000",
    bank_asset_value: "8000000",
  });

  const [datasetSamples, setDatasetSamples] = useState([]);
  const [loadingSamples, setLoadingSamples] = useState(false);
  const [showDatasetPicker, setShowDatasetPicker] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    fetchSamples();
  }, []);

  const fetchSamples = async () => {
    setLoadingSamples(true);
    try {
      const res = await getDatasetSamples(15);
      setDatasetSamples(res.data.samples || []);
    } catch (err) {
      console.error("Failed to load dataset samples:", err);
    } finally {
      setLoadingSamples(false);
    }
  };

  const handleSelectSample = (sample) => {
    // Generate realistic names based on loan_id
    const sampleNames = [
      "Aditi Sharma", "Rahul Verma", "Priya Patel", "Vikram Malhotra",
      "Neha Kulkarni", "Amitabh Sen", "Deepika Reddy", "Karan Johar",
      "Ananya Deshmukh", "Rohan Mehra", "Pooja Hegde", "Suresh Nair"
    ];
    const pickedName = sampleNames[(sample.loan_id - 1) % sampleNames.length] || `Applicant #${sample.loan_id}`;

    setFormData({
      applicant_name: pickedName,
      email: `${pickedName.toLowerCase().replace(/\s+/g, ".")}@example.com`,
      phone: `98765${String(sample.loan_id).padStart(5, "0")}`,
      annual_income: String(sample.income_annum),
      loan_amount: String(sample.loan_amount),
      loan_id: String(sample.loan_id),
      cibil_score: String(sample.cibil_score),
      loan_term: String(sample.loan_term),
      education: sample.education,
      self_employed: sample.self_employed,
      residential_assets_value: String(sample.residential_assets_value || 0),
      commercial_assets_value: String(sample.commercial_assets_value || 0),
      luxury_assets_value: String(sample.luxury_assets_value || 0),
      bank_asset_value: String(sample.bank_asset_value || 0),
    });
    setShowDatasetPicker(false);
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    if (!formData.applicant_name || !formData.annual_income || !formData.loan_amount) {
      setError("Please fill in all mandatory fields.");
      return;
    }

    setLoading(true);
    try {
      const payload = {
        applicant_name: formData.applicant_name,
        email: formData.email,
        phone: formData.phone || "9876543210",
        annual_income: Number(formData.annual_income),
        loan_amount: Number(formData.loan_amount),
        loan_id: formData.loan_id ? Number(formData.loan_id) : null,
        cibil_score: Number(formData.cibil_score || 750),
        loan_term: Number(formData.loan_term || 10),
        education: formData.education,
        self_employed: formData.self_employed,
        residential_assets_value: Number(formData.residential_assets_value || 0),
        commercial_assets_value: Number(formData.commercial_assets_value || 0),
        luxury_assets_value: Number(formData.luxury_assets_value || 0),
        bank_asset_value: Number(formData.bank_asset_value || 0),
      };

      const res = await createApplication(payload);
      if (onCreated) {
        onCreated(res.data.details || res.data);
      }
    } catch (err) {
      console.error("Creation error:", err);
      setError(err.response?.data?.detail || err.message || "Failed to create application");
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="panel application-panel">
      <div className="section-heading" style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "10px" }}>
        <div>
          <span style={{ color: "#2563eb", fontWeight: 700 }}>STAGE 1 & 2 • WORKFLOW START</span>
          <h2 style={{ margin: "4px 0" }}>Loan Application & Kaggle Dataset Record</h2>
          <p style={{ color: "#64748b", margin: 0 }}>
            Select a Kaggle benchmark record or enter custom borrower credentials.
          </p>
        </div>

        <button
          type="button"
          onClick={() => setShowDatasetPicker(!showDatasetPicker)}
          style={{
            padding: "8px 16px",
            background: "#EFF6FF",
            border: "1px solid #BFDBFE",
            color: "#1D4ED8",
            borderRadius: "8px",
            fontWeight: 600,
            cursor: "pointer",
            display: "flex",
            alignItems: "center",
            gap: "8px"
          }}
        >
          📂 {showDatasetPicker ? "Close Dataset Browser" : "Browse Kaggle Dataset"}
        </button>
      </div>

      {showDatasetPicker && (
        <div style={{ margin: "20px 0", padding: "16px", background: "#F8FAFC", borderRadius: "12px", border: "1px solid #E2E8F0" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px" }}>
            <h4 style={{ margin: 0, color: "#1E293B" }}>Select Benchmark Record from Kaggle Dataset:</h4>
            <span style={{ fontSize: "12px", color: "#64748B" }}>Total 4,269 Records</span>
          </div>

          {loadingSamples ? (
            <p style={{ color: "#64748B" }}>Loading records...</p>
          ) : (
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))", gap: "10px", maxHeight: "250px", overflowY: "auto" }}>
              {datasetSamples.map((s) => (
                <div
                  key={s.loan_id}
                  onClick={() => handleSelectSample(s)}
                  style={{
                    padding: "10px 14px",
                    background: formData.loan_id === String(s.loan_id) ? "#DBEAFE" : "white",
                    border: formData.loan_id === String(s.loan_id) ? "1.5px solid #2563EB" : "1px solid #E2E8F0",
                    borderRadius: "8px",
                    cursor: "pointer",
                    transition: "all 0.15s ease"
                  }}
                >
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <strong style={{ color: "#0F172A" }}>Loan #{s.loan_id}</strong>
                    <span
                      style={{
                        padding: "2px 8px",
                        borderRadius: "12px",
                        fontSize: "11px",
                        fontWeight: 700,
                        background: s.loan_status === "Approved" ? "#DCFCE7" : "#FEE2E2",
                        color: s.loan_status === "Approved" ? "#166534" : "#991B1B"
                      }}
                    >
                      {s.loan_status}
                    </span>
                  </div>
                  <div style={{ fontSize: "12px", color: "#475569", marginTop: "4px" }}>
                    Income: ₹{(s.income_annum / 100000).toFixed(1)}L | Loan: ₹{(s.loan_amount / 100000).toFixed(1)}L
                  </div>
                  <div style={{ fontSize: "11px", color: "#64748B" }}>
                    CIBIL: <b>{s.cibil_score}</b> | Edu: {s.education}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      <form onSubmit={handleSubmit} style={{ marginTop: "16px" }}>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: "16px" }}>
          <div>
            <label style={{ display: "block", fontSize: "13px", fontWeight: 600, color: "#334155", marginBottom: "6px" }}>
              Applicant Full Name *
            </label>
            <input
              type="text"
              name="applicant_name"
              placeholder="e.g. Aditi Sharma"
              value={formData.applicant_name}
              onChange={handleChange}
              disabled={loading}
              style={{ width: "100%", padding: "10px 12px", borderRadius: "8px", border: "1px solid #CBD5E1" }}
              required
            />
          </div>

          <div>
            <label style={{ display: "block", fontSize: "13px", fontWeight: 600, color: "#334155", marginBottom: "6px" }}>
              Email Address
            </label>
            <input
              type="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              disabled={loading}
              style={{ width: "100%", padding: "10px 12px", borderRadius: "8px", border: "1px solid #CBD5E1" }}
            />
          </div>

          <div>
            <label style={{ display: "block", fontSize: "13px", fontWeight: 600, color: "#334155", marginBottom: "6px" }}>
              Phone Number
            </label>
            <input
              type="tel"
              name="phone"
              value={formData.phone}
              onChange={handleChange}
              disabled={loading}
              style={{ width: "100%", padding: "10px 12px", borderRadius: "8px", border: "1px solid #CBD5E1" }}
            />
          </div>

          <div>
            <label style={{ display: "block", fontSize: "13px", fontWeight: 600, color: "#334155", marginBottom: "6px" }}>
              Declared Annual Income (₹) *
            </label>
            <input
              type="number"
              name="annual_income"
              value={formData.annual_income}
              onChange={handleChange}
              disabled={loading}
              style={{ width: "100%", padding: "10px 12px", borderRadius: "8px", border: "1px solid #CBD5E1" }}
              required
            />
          </div>

          <div>
            <label style={{ display: "block", fontSize: "13px", fontWeight: 600, color: "#334155", marginBottom: "6px" }}>
              Requested Loan Amount (₹) *
            </label>
            <input
              type="number"
              name="loan_amount"
              value={formData.loan_amount}
              onChange={handleChange}
              disabled={loading}
              style={{ width: "100%", padding: "10px 12px", borderRadius: "8px", border: "1px solid #CBD5E1" }}
              required
            />
          </div>

          <div>
            <label style={{ display: "block", fontSize: "13px", fontWeight: 600, color: "#334155", marginBottom: "6px" }}>
              CIBIL Credit Score (300 - 900)
            </label>
            <input
              type="number"
              name="cibil_score"
              value={formData.cibil_score}
              onChange={handleChange}
              disabled={loading}
              style={{ width: "100%", padding: "10px 12px", borderRadius: "8px", border: "1px solid #CBD5E1" }}
            />
          </div>

          <div>
            <label style={{ display: "block", fontSize: "13px", fontWeight: 600, color: "#334155", marginBottom: "6px" }}>
              Loan Term (Years)
            </label>
            <input
              type="number"
              name="loan_term"
              value={formData.loan_term}
              onChange={handleChange}
              disabled={loading}
              style={{ width: "100%", padding: "10px 12px", borderRadius: "8px", border: "1px solid #CBD5E1" }}
            />
          </div>

          <div>
            <label style={{ display: "block", fontSize: "13px", fontWeight: 600, color: "#334155", marginBottom: "6px" }}>
              Benchmark Kaggle Loan ID
            </label>
            <input
              type="number"
              name="loan_id"
              value={formData.loan_id}
              onChange={handleChange}
              disabled={loading}
              style={{ width: "100%", padding: "10px 12px", borderRadius: "8px", border: "1px solid #CBD5E1" }}
            />
          </div>
        </div>

        {error && (
          <div style={{ marginTop: "16px", padding: "12px", background: "#FEF2F2", border: "1px solid #FCA5A5", borderRadius: "8px", color: "#B91C1C", fontSize: "14px" }}>
            ⚠ {error}
          </div>
        )}

        <button
          type="submit"
          disabled={loading}
          style={{
            marginTop: "24px",
            width: "100%",
            padding: "14px",
            background: "#1E3A8A",
            color: "white",
            border: "none",
            borderRadius: "10px",
            fontSize: "15px",
            fontWeight: 700,
            cursor: loading ? "not-allowed" : "pointer"
          }}
        >
          {loading ? "Creating Application..." : "Save Application & Proceed to Document Upload →"}
        </button>
      </form>
    </section>
  );
}