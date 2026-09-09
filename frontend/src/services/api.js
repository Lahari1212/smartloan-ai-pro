import axios from "axios";

const api = axios.create({
  baseURL: "http://127.0.0.1:8000",
  timeout: 15000,
});

export const createApplication = (data) => {
  return api.post("/applications", data);
};

export const uploadDocument = (applicationId, file) => {
  const formData = new FormData();
  formData.append("file", file);

  return api.post(
    `/applications/${applicationId}/documents`,
    formData,
    {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    }
  );
};

export const validateDocument = (documentId) => {
  return api.post(`/documents/${documentId}/validate`);
};

export const checkEligibility = (applicationId) => {
  return api.post(
    `/applications/${applicationId}/eligibility`
  );
};

export const getApplications = () => {
  return api.get("/applications");
};

export default api;