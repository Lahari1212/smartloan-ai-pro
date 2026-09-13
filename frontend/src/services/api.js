import axios from "axios";

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8002";

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60000,
});

// ─── Auth token injection ───────────────────────────────────────────────────
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("smartloan_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// ─── Global 401 handler ─────────────────────────────────────────────────────
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem("smartloan_token");
      localStorage.removeItem("smartloan_user");
    }
    return Promise.reject(error);
  }
);

// ─── Auth ────────────────────────────────────────────────────────────────────
export const registerApplicant = (data) => api.post("/auth/register", data);
export const loginUser = (data) => api.post("/auth/login", data);
export const getMe = () => api.get("/auth/me");

// ─── Session helpers ─────────────────────────────────────────────────────────
export const saveSession = (token, user) => {
  localStorage.setItem("smartloan_token", token);
  localStorage.setItem("smartloan_user", JSON.stringify(user));
};

export const clearSession = () => {
  localStorage.removeItem("smartloan_token");
  localStorage.removeItem("smartloan_user");
};

export const getStoredUser = () => {
  try {
    const raw = localStorage.getItem("smartloan_user");
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
};

export const isAuthenticated = () => !!localStorage.getItem("smartloan_token");

// ─── Dataset ─────────────────────────────────────────────────────────────────
export const getDatasetSamples = (limit = 25, status = "") => {
  const params = { limit };
  if (status) params.status = status;
  return api.get("/dataset/samples", { params });
};

// ─── Applications ─────────────────────────────────────────────────────────────
export const createApplication = (data) => api.post("/applications", data);
export const getApplications = () => api.get("/applications");
export const getSingleApplication = (applicationId) =>
  api.get(`/applications/${applicationId}`);
export const getApplicationSummary = (applicationId) =>
  api.get(`/applications/${applicationId}/summary`);
export const getApplicationAudit = (applicationId) =>
  api.get(`/applications/${applicationId}/audit`);

// ─── Documents ───────────────────────────────────────────────────────────────
export const uploadDocument = (applicationId, file) => {
  const formData = new FormData();
  formData.append("file", file);
  return api.post(`/applications/${applicationId}/documents`, formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
};

export const generateDummyDocs = (applicationId, scenario = "clean") =>
  api.post(`/applications/${applicationId}/generate-dummy-docs`, { scenario });

export const processAllDocuments = (applicationId) =>
  api.post(`/applications/${applicationId}/process-all`);

export const validateDocument = (documentId) =>
  api.post(`/documents/${documentId}/validate`);

export const checkEligibility = (applicationId) =>
  api.post(`/applications/${applicationId}/eligibility`);

export const getDocumentDownloadUrl = (documentId) =>
  `${API_BASE_URL}/documents/${documentId}/download`;

// ─── Officer & AI Assistant ──────────────────────────────────────────────────
export const submitOfficerReview = (applicationId, reviewData) =>
  api.post(`/applications/${applicationId}/officer-review`, reviewData);

export const chatWithAiAnalyst = (applicationId, message, history = []) =>
  api.post(`/applications/${applicationId}/chat`, { message, history });

export const downloadPdfReport = async (applicationId, applicantName = "Applicant") => {
  const response = await api.get(`/applications/${applicationId}/export-pdf`, {
    responseType: "blob",
  });
  const url = window.URL.createObjectURL(new Blob([response.data], { type: "application/pdf" }));
  const link = document.createElement("a");
  link.href = url;
  link.setAttribute("download", `SmartLoan_Report_${applicantName.replace(/\s+/g, "_")}_${applicationId.slice(0, 8)}.pdf`);
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
};

// ─── In-App Notifications ────────────────────────────────────────────────────
export const getNotifications = () => api.get("/notifications");
export const markNotificationRead = (notificationId) =>
  api.post(`/notifications/${notificationId}/read`);

export default api;