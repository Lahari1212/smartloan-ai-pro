import { useState } from "react";

import {
  uploadDocument,
  validateDocument,
  checkEligibility,
} from "../services/api";

export default function DocumentUpload({
  applicationId,
  onCompleted,
}) {
  const [file, setFile] = useState(null);
  const [documentId, setDocumentId] = useState("");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const handleFileChange = (event) => {
    const selectedFile = event.target.files?.[0] || null;

    setFile(null);
    setDocumentId("");
    setMessage("");
    setError("");

    if (!selectedFile) {
      return;
    }

    const isPdf =
      selectedFile.type === "application/pdf" ||
      selectedFile.name.toLowerCase().endsWith(".pdf");

    if (!isPdf) {
      setError("Please select a PDF file only.");
      return;
    }

    setFile(selectedFile);
  };

  const handleUpload = async () => {
    if (!applicationId) {
      setError(
        "Application ID is missing. Please create an application first."
      );
      return;
    }

    if (!file) {
      setError("Please select a PDF file.");
      return;
    }

    setLoading(true);
    setError("");
    setMessage("");
    setDocumentId("");

    try {
      // Step 1: Upload document
      setMessage("Uploading document...");

      const uploadResponse = await uploadDocument(
        applicationId,
        file
      );

      console.log(
        "Upload response:",
        uploadResponse.data
      );

      const uploadedDocumentId =
        uploadResponse.data?.document_id;

      if (!uploadedDocumentId) {
        throw new Error(
          "The backend did not return a document ID."
        );
      }

      setDocumentId(uploadedDocumentId);

      // Step 2: Validate document
      setMessage(
        "Document uploaded successfully. Validating..."
      );

      const validationResponse = await validateDocument(
        uploadedDocumentId
      );

      console.log(
        "Validation response:",
        validationResponse.data
      );

      const validation =
        validationResponse.data?.validation_result;

      if (!validation) {
        throw new Error(
          "The backend did not return a validation result."
        );
      }

      if (!validation.is_valid) {
        setError(
          validation.validation_message ||
            "The document could not be validated."
        );
        setMessage("");
        return;
      }

      // Step 3: Check eligibility
      setMessage(
        "Document validated successfully. Checking eligibility..."
      );

      const eligibilityResponse =
        await checkEligibility(applicationId);

      console.log(
        "Eligibility response:",
        eligibilityResponse.data
      );

      setMessage(
        "Eligibility check completed successfully."
      );

      if (onCompleted) {
        onCompleted(eligibilityResponse.data);
      }
    } catch (error) {
      console.error(
        "Upload, validation, or eligibility error:",
        error
      );

      const backendError =
        error.response?.data?.detail;

      let errorMessage =
        "Unable to upload, validate, or check eligibility.";

      if (typeof backendError === "string") {
        errorMessage = backendError;
      } else if (Array.isArray(backendError)) {
        errorMessage = backendError
          .map((item) => item.msg || JSON.stringify(item))
          .join(", ");
      } else if (error.message) {
        errorMessage = error.message;
      }

      setError(errorMessage);
      setMessage("");
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="panel document-upload-panel">
      <div className="section-heading">
        <span>STEP 2</span>

        <h2>Upload document</h2>

        <p>
          Upload the applicant's payslip for verification.
        </p>
      </div>

      <div className="upload-box">
        <div className="upload-icon">📄</div>

        <h3>Select payslip PDF</h3>

        <p>
          Upload a clear, text-based PDF document.
        </p>

        <input
          type="file"
          accept=".pdf,application/pdf"
          onChange={handleFileChange}
          disabled={loading}
        />

        {file && (
          <p className="file-name">
            Selected file: {file.name}
          </p>
        )}
      </div>

      {message && (
        <div className="success-message">
          {message}
        </div>
      )}

      {error && (
        <div className="error-message">
          {error}
        </div>
      )}

      <button
        type="button"
        className="primary-button full-width"
        onClick={handleUpload}
        disabled={
          loading ||
          !file ||
          !applicationId
        }
      >
        {loading
          ? "Processing..."
          : "Upload and Check Eligibility"}
      </button>

      {documentId && (
        <p className="document-id">
          Document ID: {documentId}
        </p>
      )}
    </section>
  );
}