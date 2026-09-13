import json
import os
import shutil
import uuid
from pathlib import Path
from typing import Optional, List

# Load environment variables from .env file (for local development)
from dotenv import load_dotenv
load_dotenv()

import numpy as np
from fastapi import FastAPI, File, HTTPException, UploadFile, Query, Depends, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, EmailStr, Field


class _NumpyEncoder(json.JSONEncoder):
    """JSON encoder that converts numpy scalars to native Python types."""
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.bool_):
            return bool(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)


class NumpySafeResponse(JSONResponse):
    def render(self, content) -> bytes:
        return json.dumps(content, cls=_NumpyEncoder, ensure_ascii=False).encode("utf-8")


from database import (
    create_tables,
    insert_application,
    get_all_applications,
    get_applications_by_user,
    get_application_by_id,
    insert_document,
    get_documents_by_application,
    get_document_by_id,
    update_document_extraction,
    update_application_status,
    update_application_summary,
    record_officer_review,
    insert_user,
    get_user_by_email,
    email_exists,
    upsert_officer,
    log_audit_event,
    get_audit_log,
    create_notification,
    get_notifications_by_user,
    mark_notification_as_read,
)

from auth import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
    require_applicant,
    require_officer,
    require_authenticated,
)

from pdf_reader import extract_text_from_pdf
from document_classifier import classify_document
from ai_extractor import extract_document_fields
from document_validator import validate_single_document, validate_all_documents, validate_document
from eligibility_agent import calculate_eligibility, generate_loan_processing_summary
from database_loader import load_loan_dataset
from dummy_generator import generate_document_bundle
from report_generator import generate_underwriting_pdf
from ai_assistant import run_loan_analyst_agent


# --------------------------------------------------
# App setup
# --------------------------------------------------

app = FastAPI(
    title="SmartLoan AI API",
    description="GenAI-enabled loan application, document verification & agentic decision system",
    version="3.0.0",
    default_response_class=NumpySafeResponse,
)

# CORS — allow all local dev ports + Vercel/Render production domains
_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get(
        "ALLOWED_ORIGINS",
        "http://localhost:5173,http://localhost:5174,http://127.0.0.1:5173,http://127.0.0.1:5174,https://smartloan-ai.vercel.app"
    ).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_ALLOWED_ORIGINS,
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$|^https://.*\.vercel\.app$|^https://.*\.onrender\.com$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = Path(__file__).parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB


# --------------------------------------------------
# Startup: create DB tables + initialize officer account
# --------------------------------------------------

@app.on_event("startup")
def startup_event():
    create_tables()
    _initialize_officer_account()


def _initialize_officer_account():
    """
    Create (or update) the loan officer account from environment variables.
    SMARTLOAN_OFFICER_EMAIL and SMARTLOAN_OFFICER_PASSWORD must be set.
    """
    officer_email = os.environ.get("SMARTLOAN_OFFICER_EMAIL", "").strip()
    officer_password = os.environ.get("SMARTLOAN_OFFICER_PASSWORD", "").strip()

    if not officer_email or not officer_password:
        print("[SmartLoan] WARNING: SMARTLOAN_OFFICER_EMAIL or SMARTLOAN_OFFICER_PASSWORD not set.")
        print("[SmartLoan] Officer login will be unavailable until these are configured.")
        return

    officer_id = "officer-" + str(uuid.uuid5(uuid.NAMESPACE_URL, officer_email))
    hashed = hash_password(officer_password)
    upsert_officer(
        user_id=officer_id,
        full_name="Loan Officer",
        email=officer_email,
        password_hash=hashed,
    )
    print(f"[SmartLoan] Officer account initialized for: {officer_email}")


# --------------------------------------------------
# Request & Response Models
# --------------------------------------------------

class RegisterRequest(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    confirm_password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1)


class ApplicationCreate(BaseModel):
    applicant_name: str = Field(..., min_length=2)
    email: EmailStr
    phone: str = Field(..., min_length=10)
    annual_income: float = Field(..., gt=0)
    loan_amount: float = Field(..., gt=0)
    loan_id: Optional[int] = None
    cibil_score: Optional[int] = 750
    loan_term: Optional[int] = 10
    education: Optional[str] = "Graduate"
    self_employed: Optional[str] = "No"
    residential_assets_value: Optional[float] = 0.0
    commercial_assets_value: Optional[float] = 0.0
    luxury_assets_value: Optional[float] = 0.0
    bank_asset_value: Optional[float] = 0.0


class DummyDocsRequest(BaseModel):
    scenario: str = "clean"  # "clean" or "discrepancy"


class OfficerReviewRequest(BaseModel):
    decision: str  # "Approved", "Rejected", "Manual Review", "Request Re-upload"
    notes: str
    officer_id: Optional[str] = None


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    history: Optional[List[dict]] = []



# --------------------------------------------------
# Helper: check application ownership
# --------------------------------------------------

def _get_app_or_404(application_id: str):
    """Fetch application or raise 404."""
    app_record = get_application_by_id(application_id)
    if not app_record:
        raise HTTPException(status_code=404, detail="Application not found")
    return app_record


def _assert_ownership(app_record: dict, current_user: dict):
    """
    Ensure the current applicant owns this application.
    Officers bypass this check.
    """
    if current_user.get("role") == "officer":
        return  # officers can access all

    app_user_id = app_record.get("user_id")
    if app_user_id and app_user_id != current_user.get("sub"):
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to access this application."
        )


# --------------------------------------------------
# System & Health Endpoints (public)
# --------------------------------------------------

@app.get("/")
def root():
    return {
        "message": "SmartLoan AI agent backend is online",
        "docs": "/docs",
        "version": "3.0.0"
    }


@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "SmartLoan AI Agent"}


@app.get("/dataset/samples")
def get_dataset_samples(limit: int = Query(25, ge=1, le=100), status: Optional[str] = None):
    """Returns sample loan profiles from the Kaggle dataset for one-click selection."""
    df = load_loan_dataset()
    if status:
        df = df[df["loan_status"].str.lower() == status.lower()]
    samples = df.head(limit).to_dict(orient="records")
    return {"total_records": len(df), "samples": samples}


# --------------------------------------------------
# Authentication Endpoints (public)
# --------------------------------------------------

@app.post("/auth/register", status_code=201)
def register_applicant(request: RegisterRequest):
    """Register a new applicant account."""
    if request.password != request.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match.")

    if len(request.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters.")

    normalized_email = str(request.email).lower().strip()

    if email_exists(normalized_email):
        raise HTTPException(
            status_code=409,
            detail="An account with this email already exists. Please log in."
        )

    user_id = str(uuid.uuid4())
    hashed = hash_password(request.password)

    insert_user({
        "user_id": user_id,
        "full_name": request.full_name.strip(),
        "email": normalized_email,
        "password_hash": hashed,
        "role": "applicant",
    })

    token = create_access_token(
        user_id=user_id,
        email=normalized_email,
        role="applicant",
        full_name=request.full_name.strip(),
    )

    return {
        "message": "Account created successfully.",
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "user_id": user_id,
            "full_name": request.full_name.strip(),
            "email": normalized_email,
            "role": "applicant",
        }
    }


@app.post("/auth/login")
def login(request: LoginRequest):
    """Authenticate and return a JWT token."""
    normalized_email = str(request.email).lower().strip()
    user = get_user_by_email(normalized_email)

    if not user or not verify_password(request.password, user["password_hash"]):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password."
        )

    token = create_access_token(
        user_id=user["user_id"],
        email=user["email"],
        role=user["role"],
        full_name=user["full_name"],
    )

    return {
        "message": "Login successful.",
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "user_id": user["user_id"],
            "full_name": user["full_name"],
            "email": user["email"],
            "role": user["role"],
        }
    }


@app.get("/auth/me")
def get_me(current_user: dict = Depends(get_current_user)):
    """Return the current authenticated user's profile."""
    return {
        "user_id": current_user["sub"],
        "email": current_user["email"],
        "role": current_user["role"],
        "full_name": current_user["name"],
    }


# --------------------------------------------------
# Application Endpoints (protected)
# --------------------------------------------------

@app.post("/applications")
def create_new_application(
    application: ApplicationCreate,
    current_user: dict = Depends(require_applicant),
):
    application_id = str(uuid.uuid4())

    app_dict = {
        "application_id": application_id,
        "user_id": current_user["sub"],
        "loan_id": application.loan_id,
        "applicant_name": application.applicant_name,
        "email": str(application.email),
        "phone": application.phone,
        "annual_income": application.annual_income,
        "loan_amount": application.loan_amount,
        "loan_term": application.loan_term,
        "cibil_score": application.cibil_score,
        "education": application.education,
        "self_employed": application.self_employed,
        "residential_assets_value": application.residential_assets_value,
        "commercial_assets_value": application.commercial_assets_value,
        "luxury_assets_value": application.luxury_assets_value,
        "bank_asset_value": application.bank_asset_value,
        "status": "Document Pending",
    }

    insert_application(app_dict)

    log_audit_event(
        application_id=application_id,
        event="Application Created",
        details=f"Loan application submitted for ₹{application.loan_amount:,.0f}",
        user_id=current_user["sub"],
        user_email=current_user["email"],
    )

    return {
        "message": "Application registered successfully",
        "application_id": application_id,
        "applicant_name": application.applicant_name,
        "status": "Document Pending",
        "details": app_dict,
    }


@app.get("/applications")
def get_applications(current_user: dict = Depends(get_current_user)):
    """
    Officers see all applications.
    Applicants see only their own applications.
    """
    if current_user.get("role") == "officer":
        return {"applications": get_all_applications()}
    else:
        return {"applications": get_applications_by_user(current_user["sub"])}


@app.get("/applications/{application_id}")
def get_single_application(
    application_id: str,
    current_user: dict = Depends(get_current_user),
):
    app_record = _get_app_or_404(application_id)
    _assert_ownership(app_record, current_user)

    docs = get_documents_by_application(application_id)
    audit = get_audit_log(application_id)
    return {
        **app_record,
        "documents": docs,
        "audit_log": audit,
    }


# --------------------------------------------------
# Document Upload & Processing (protected)
# --------------------------------------------------

@app.post("/applications/{application_id}/documents")
async def upload_application_document(
    application_id: str,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    app_record = _get_app_or_404(application_id)
    _assert_ownership(app_record, current_user)

    if not file.filename:
        raise HTTPException(status_code=400, detail="No file selected")

    # Validate file type
    file_extension = Path(file.filename).suffix.lower()
    if file_extension != ".pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    # Safe filename
    document_id = str(uuid.uuid4())
    saved_filename = f"{document_id}.pdf"
    saved_path = UPLOAD_DIR / saved_filename

    try:
        contents = await file.read()
        if len(contents) > MAX_FILE_SIZE_BYTES:
            raise HTTPException(status_code=413, detail="File too large. Maximum size is 10 MB.")
        with saved_path.open("wb") as buffer:
            buffer.write(contents)
        file_size = saved_path.stat().st_size
    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Unable to save document: {error}")

    # 1. PyMuPDF text extraction
    try:
        extracted_text = extract_text_from_pdf(str(saved_path))
    except Exception:
        extracted_text = ""

    # 2. Classification
    doc_type, class_conf = classify_document(extracted_text)

    # 3. GenAI structured extraction
    extraction = extract_document_fields(doc_type, extracted_text)

    document_data = {
        "document_id": document_id,
        "application_id": application_id,
        "original_filename": file.filename,
        "saved_filename": saved_filename,
        "document_type": doc_type,
        "extracted_text": extracted_text,
        "extracted_json": extraction["fields"],
        "confidence_score": extraction["confidence"],
        "classification_confidence": class_conf,
        "file_size": file_size,
    }

    insert_document(document_data)
    update_application_status(application_id, "Document Uploaded")

    log_audit_event(
        application_id=application_id,
        event="Document Uploaded",
        details=f"{doc_type} uploaded: {file.filename} (confidence: {class_conf:.1f}%)",
        user_id=current_user["sub"],
        user_email=current_user["email"],
    )

    return {
        "message": "Document uploaded, classified, and extracted successfully",
        "document_id": document_id,
        "application_id": application_id,
        "filename": file.filename,
        "document_type": doc_type,
        "classification_confidence": class_conf,
        "extraction": extraction,
        "status": "Document Uploaded",
    }


@app.get("/documents/{document_id}/download")
def download_document(
    document_id: str,
    current_user: dict = Depends(get_current_user),
):
    doc = get_document_by_id(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document record not found")

    # Verify ownership of the parent application
    app_record = get_application_by_id(doc["application_id"])
    if app_record:
        _assert_ownership(app_record, current_user)

    file_path = UPLOAD_DIR / doc["saved_filename"]
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found on disk")

    return FileResponse(
        path=file_path,
        filename=doc["original_filename"],
        media_type="application/pdf",
    )


# --------------------------------------------------
# Auto-Generate Dummy Document Suite (protected)
# --------------------------------------------------

@app.post("/applications/{application_id}/generate-dummy-docs")
def generate_and_attach_dummy_documents(
    application_id: str,
    payload: DummyDocsRequest = DummyDocsRequest(),
    current_user: dict = Depends(get_current_user),
):
    """
    One-click instant demo generator:
    Generates Payslip, Bank Statement, Tax Return, and KYC documents,
    extracts them, and executes the full agentic verification workflow.
    """
    app_record = _get_app_or_404(application_id)
    _assert_ownership(app_record, current_user)

    scenario = payload.scenario.lower()
    app_temp_dir = UPLOAD_DIR / f"dummy_{application_id}_{scenario}"

    # Generate all 4 PDFs
    docs_dict = generate_document_bundle(
        app_temp_dir,
        applicant_name=app_record["applicant_name"],
        annual_income=app_record["annual_income"],
        scenario=scenario,
    )

    created_docs = []
    for doc_label, src_path in docs_dict.items():
        doc_id = str(uuid.uuid4())
        dest_filename = f"{doc_id}.pdf"
        dest_path = UPLOAD_DIR / dest_filename
        shutil.copyfile(src_path, dest_path)

        text = extract_text_from_pdf(str(dest_path))
        doc_type, class_conf = classify_document(text)
        extraction = extract_document_fields(doc_type, text)

        doc_data = {
            "document_id": doc_id,
            "application_id": application_id,
            "original_filename": src_path.name,
            "saved_filename": dest_filename,
            "document_type": doc_type,
            "extracted_text": text,
            "extracted_json": extraction["fields"],
            "confidence_score": extraction["confidence"],
            "classification_confidence": class_conf,
            "file_size": dest_path.stat().st_size,
        }
        insert_document(doc_data)
        created_docs.append(doc_data)

    log_audit_event(
        application_id=application_id,
        event="Demo Documents Generated",
        details=f"Scenario: {scenario}. {len(created_docs)} documents generated.",
        user_id=current_user["sub"],
        user_email=current_user["email"],
    )

    # Process all documents & evaluate eligibility
    return process_all_application_documents(application_id, current_user)


# --------------------------------------------------
# Agentic Verification & Summary Generation (protected)
# --------------------------------------------------

@app.post("/applications/{application_id}/process-all")
def process_all_application_documents(
    application_id: str,
    current_user: dict = Depends(get_current_user),
):
    """
    Full agentic workflow:
    1. Fetches all documents for the application.
    2. Runs cross-document validation & inconsistency detection.
    3. Runs Kaggle ML credit risk model prediction.
    4. Synthesizes GenAI Loan Processing Summary & Audit Memo.
    5. Updates application status.
    """
    app_record = _get_app_or_404(application_id)
    _assert_ownership(app_record, current_user)

    documents = get_documents_by_application(application_id)
    if not documents:
        raise HTTPException(status_code=400, detail="No documents uploaded yet.")

    # 1. Cross-Document Validation Agent
    validation_report = validate_all_documents(app_record, documents)

    log_audit_event(
        application_id=application_id,
        event="Cross-Document Verification Completed",
        details=f"{len(validation_report.get('inconsistencies', []))} issue(s) detected.",
        user_id=current_user["sub"],
        user_email=current_user["email"],
    )

    # 2. Kaggle ML Model Scoring
    ml_result = calculate_eligibility(
        annual_income=app_record["annual_income"],
        loan_amount=app_record["loan_amount"],
        validation_result=validation_report,
        applicant_name=app_record["applicant_name"],
        loan_id=app_record.get("loan_id"),
        cibil_score=app_record.get("cibil_score", 750),
        loan_term=app_record.get("loan_term", 10),
        education=app_record.get("education", "Graduate"),
        self_employed=app_record.get("self_employed", "No"),
        residential_assets=app_record.get("residential_assets_value", 0),
        commercial_assets=app_record.get("commercial_assets_value", 0),
        luxury_assets=app_record.get("luxury_assets_value", 0),
        bank_asset=app_record.get("bank_asset_value", 0),
    )

    log_audit_event(
        application_id=application_id,
        event="ML Eligibility Calculated",
        details=f"Prediction: {ml_result.get('model_prediction')}, confidence: {ml_result.get('confidence'):.1f}%",
        user_id=current_user["sub"],
        user_email=current_user["email"],
    )

    # 3. GenAI Loan Processing Summary
    ai_summary = generate_loan_processing_summary(
        application=app_record,
        validation_result=validation_report,
        ml_result=ml_result,
        documents=documents,
    )

    # Determine final application status
    if validation_report["is_valid"] and ml_result["eligible"] and len(validation_report["inconsistencies"]) == 0:
        new_status = "Approved"
    elif not ml_result["eligible"] and ml_result.get("status") == "Rejected":
        new_status = "Rejected"
    else:
        new_status = "Manual Review"

    update_application_summary(application_id, ai_summary=ai_summary, status=new_status)

    log_audit_event(
        application_id=application_id,
        event="AI Summary Generated",
        details=f"Application status set to: {new_status}",
        user_id=current_user["sub"],
        user_email=current_user["email"],
    )

    return {
        "message": "AI Agent verification completed",
        "application_id": application_id,
        "applicant_name": app_record["applicant_name"],
        "status": new_status,
        "risk_level": ml_result.get("risk_level", "Medium"),
        "validation_report": validation_report,
        "ml_result": ml_result,
        "ai_summary": ai_summary,
        "documents": documents,
    }


@app.post("/applications/{application_id}/eligibility")
def check_application_eligibility(
    application_id: str,
    current_user: dict = Depends(get_current_user),
):
    return process_all_application_documents(application_id, current_user)


@app.post("/documents/{document_id}/validate")
def validate_uploaded_document(
    document_id: str,
    current_user: dict = Depends(get_current_user),
):
    doc = get_document_by_id(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # Ownership check via parent application
    app_record = get_application_by_id(doc["application_id"])
    if app_record:
        _assert_ownership(app_record, current_user)

    file_path = UPLOAD_DIR / doc["saved_filename"]
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    text = extract_text_from_pdf(str(file_path))
    doc_type, class_conf = classify_document(text)
    extraction = extract_document_fields(doc_type, text)
    validation_res = validate_single_document(doc_type, extraction["fields"])

    update_document_extraction(
        document_id,
        doc_type,
        text,
        extraction["fields"],
        extraction["confidence"],
        class_conf,
    )

    return {
        "message": "Document validated",
        "document_id": document_id,
        "document_type": doc_type,
        "validation_result": validation_res,
        "extracted_details": extraction["fields"],
        "confidence": extraction["confidence"],
        "extracted_text": text,
    }


# --------------------------------------------------
# Loan Officer Review Station (officer only)
# --------------------------------------------------

@app.post("/applications/{application_id}/officer-review")
def submit_officer_review(
    application_id: str,
    review: OfficerReviewRequest,
    current_user: dict = Depends(require_officer),
):
    app_record = _get_app_or_404(application_id)

    valid_decisions = ["Approved", "Rejected", "Manual Review", "Request Re-upload"]
    if review.decision not in valid_decisions:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid decision. Must be one of: {', '.join(valid_decisions)}"
        )

    officer_identifier = current_user.get("email", "Loan Officer")

    record_officer_review(
        application_id=application_id,
        decision=review.decision,
        notes=review.notes,
        officer_id=officer_identifier,
    )

    log_audit_event(
        application_id=application_id,
        event=f"Officer Decision: {review.decision}",
        details=f"Notes: {review.notes[:200] if review.notes else 'None'}",
        user_id=current_user["sub"],
        user_email=officer_identifier,
    )

    # Dispatch notification to applicant if application has associated user_id
    if app_record.get("user_id"):
        create_notification(
            user_id=app_record["user_id"],
            title=f"Loan Application {review.decision}",
            message=f"Your loan application #{application_id[:8].upper()} has been updated to '{review.decision}'. Officer Notes: {review.notes}",
            application_id=application_id,
        )

    return {
        "message": f"Officer review saved: {review.decision}",
        "application_id": application_id,
        "new_status": review.decision,
        "notes": review.notes,
        "reviewed_by": officer_identifier,
    }


@app.get("/applications/{application_id}/summary")
def get_application_summary(
    application_id: str,
    current_user: dict = Depends(get_current_user),
):
    app_record = _get_app_or_404(application_id)
    _assert_ownership(app_record, current_user)

    docs = get_documents_by_application(application_id)
    validation_report = validate_all_documents(app_record, docs) if docs else None
    audit = get_audit_log(application_id)

    return {
        "application": app_record,
        "documents": docs,
        "validation_report": validation_report,
        "ai_summary": app_record.get("ai_summary"),
        "audit_log": audit,
    }


@app.get("/applications/{application_id}/audit")
def get_application_audit(
    application_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Return the audit trail for an application."""
    app_record = _get_app_or_404(application_id)
    _assert_ownership(app_record, current_user)
    return {"audit_log": get_audit_log(application_id)}


# --------------------------------------------------
# PDF Report Export Endpoint
# --------------------------------------------------

@app.get("/applications/{application_id}/export-pdf")
def export_application_pdf(
    application_id: str,
    current_user: dict = Depends(get_current_user),
):
    """
    Generates and downloads a formal Underwriting & Decision PDF Report.
    """
    app_record = _get_app_or_404(application_id)
    _assert_ownership(app_record, current_user)

    docs = get_documents_by_application(application_id)
    validation_report = validate_all_documents(app_record, docs) if docs else {}
    ml_result = calculate_eligibility(
        annual_income=app_record["annual_income"],
        loan_amount=app_record["loan_amount"],
        validation_result=validation_report,
        applicant_name=app_record["applicant_name"],
        loan_id=app_record.get("loan_id"),
        cibil_score=app_record.get("cibil_score", 750),
        loan_term=app_record.get("loan_term", 10),
        education=app_record.get("education", "Graduate"),
        self_employed=app_record.get("self_employed", "No"),
        residential_assets=app_record.get("residential_assets_value", 0),
        commercial_assets=app_record.get("commercial_assets_value", 0),
        luxury_assets=app_record.get("luxury_assets_value", 0),
        bank_asset=app_record.get("bank_asset_value", 0),
    ) if docs else {}
    audit = get_audit_log(application_id)

    pdf_buffer = generate_underwriting_pdf(
        application=app_record,
        documents=docs,
        validation_report=validation_report,
        ml_result=ml_result,
        audit_log=audit,
    )

    filename = f"SmartLoan_Report_{app_record['applicant_name'].replace(' ', '_')}_{application_id[:8].upper()}.pdf"

    log_audit_event(
        application_id=application_id,
        event="PDF Dossier Exported",
        details=f"Official Underwriting Report downloaded by {current_user.get('email', 'User')}",
        user_id=current_user["sub"],
        user_email=current_user.get("email"),
    )

    return Response(
        content=pdf_buffer.getvalue(),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=\"{filename}\""},
    )


# --------------------------------------------------
# Context-Aware AI Loan Analyst Chatbot Endpoint
# --------------------------------------------------

@app.post("/applications/{application_id}/chat")
def chat_with_loan_analyst(
    application_id: str,
    req: ChatRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Context-aware interactive AI assistant for loan officers.
    """
    app_record = _get_app_or_404(application_id)
    _assert_ownership(app_record, current_user)

    docs = get_documents_by_application(application_id)
    validation_report = validate_all_documents(app_record, docs) if docs else {}
    ml_result = calculate_eligibility(
        annual_income=app_record["annual_income"],
        loan_amount=app_record["loan_amount"],
        validation_result=validation_report,
        applicant_name=app_record["applicant_name"],
        loan_id=app_record.get("loan_id"),
        cibil_score=app_record.get("cibil_score", 750),
        loan_term=app_record.get("loan_term", 10),
        education=app_record.get("education", "Graduate"),
        self_employed=app_record.get("self_employed", "No"),
        residential_assets=app_record.get("residential_assets_value", 0),
        commercial_assets=app_record.get("commercial_assets_value", 0),
        luxury_assets=app_record.get("luxury_assets_value", 0),
        bank_asset=app_record.get("bank_asset_value", 0),
    ) if docs else {}

    ai_reply = run_loan_analyst_agent(
        application=app_record,
        documents=docs,
        validation_report=validation_report,
        ml_result=ml_result,
        user_query=req.message,
        chat_history=req.history,
    )

    return {
        "reply": ai_reply,
        "application_id": application_id,
    }


# --------------------------------------------------
# In-App Notifications Endpoints
# --------------------------------------------------

@app.get("/notifications")
def get_user_notifications_endpoint(
    current_user: dict = Depends(get_current_user),
):
    """Get latest in-app notifications for current user."""
    notifs = get_notifications_by_user(current_user["sub"])
    return {"notifications": notifs}


@app.post("/notifications/{notification_id}/read")
def mark_read_endpoint(
    notification_id: int,
    current_user: dict = Depends(get_current_user),
):
    """Mark a notification as read."""
    mark_notification_as_read(notification_id, current_user["sub"])
    return {"status": "success", "notification_id": notification_id}