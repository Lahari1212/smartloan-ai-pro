import shutil
import uuid
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field

from database import (
    create_tables,
    insert_application,
    get_all_applications,
    insert_document,
    get_documents_by_application,
    update_application_status,
    get_connection,
)

from pdf_reader import extract_text_from_pdf
from document_classifier import classify_document
from document_validator import validate_document
from eligibility_agent import calculate_eligibility


# --------------------------------------------------
# FastAPI application
# --------------------------------------------------

app = FastAPI(
    title="SmartLoan AI API",
    description="AI-powered loan application and document verification system",
    version="1.0.0",
)


# --------------------------------------------------
# CORS configuration
# --------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------
# Configuration
# --------------------------------------------------

UPLOAD_DIR = Path(__file__).parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)


# --------------------------------------------------
# Startup
# --------------------------------------------------

@app.on_event("startup")
def startup_event():
    create_tables()


# --------------------------------------------------
# Request models
# --------------------------------------------------

class ApplicationCreate(BaseModel):
    applicant_name: str = Field(..., min_length=2)
    email: EmailStr
    phone: str = Field(..., min_length=10)
    annual_income: float = Field(..., gt=0)
    loan_amount: float = Field(..., gt=0)
    loan_id: int | None = None


# --------------------------------------------------
# Helper functions
# --------------------------------------------------

def find_application(application_id: str):
    applications = get_all_applications()

    for application in applications:
        if application["application_id"] == application_id:
            return application

    return None


def find_document(document_id: str):
    connection = get_connection()

    row = connection.execute(
        """
        SELECT *
        FROM documents
        WHERE document_id = ?
        """,
        (document_id,),
    ).fetchone()

    connection.close()

    if row is None:
        return None

    return dict(row)


def get_document_file_path(document):
    return UPLOAD_DIR / document["saved_filename"]


# --------------------------------------------------
# Basic endpoints
# --------------------------------------------------

@app.get("/")
def root():
    return {
        "message": "SmartLoan AI backend is running",
        "docs": "http://127.0.0.1:8000/docs",
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "SmartLoan AI",
    }


# --------------------------------------------------
# Application endpoints
# --------------------------------------------------

@app.post("/applications")
def create_new_application(application: ApplicationCreate):
    application_id = str(uuid.uuid4())

    application_data = {
        "application_id": application_id,
        "loan_id": application.loan_id,
        "applicant_name": application.applicant_name,
        "email": str(application.email),
        "phone": application.phone,
        "annual_income": application.annual_income,
        "loan_amount": application.loan_amount,
        "status": "Document Pending",
    }

    insert_application(application_data)

    return {
        "message": "Application created successfully",
        "application_id": application_id,
        "loan_id": application.loan_id,
        "applicant_name": application.applicant_name,
        "status": "Document Pending",
    }


@app.get("/applications")
def get_applications():
    return {
        "applications": get_all_applications(),
    }


@app.get("/applications/{application_id}")
def get_single_application(application_id: str):
    application = find_application(application_id)

    if application is None:
        raise HTTPException(
            status_code=404,
            detail="Application not found",
        )

    return application


# --------------------------------------------------
# Document upload
# --------------------------------------------------

@app.post("/applications/{application_id}/documents")
async def upload_application_document(
    application_id: str,
    file: UploadFile = File(...),
):
    application = find_application(application_id)

    if application is None:
        raise HTTPException(
            status_code=404,
            detail="Application not found",
        )

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="No file selected",
        )

    file_extension = Path(file.filename).suffix.lower()

    if file_extension != ".pdf":
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported",
        )

    document_id = str(uuid.uuid4())
    saved_filename = f"{document_id}.pdf"
    saved_path = UPLOAD_DIR / saved_filename

    try:
        with saved_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to save document: {error}",
        )

    document_data = {
        "document_id": document_id,
        "application_id": application_id,
        "original_filename": file.filename,
        "saved_filename": saved_filename,
        "document_type": "Unknown",
        "extracted_text": "",
    }

    insert_document(document_data)

    update_application_status(
        application_id,
        "Document Uploaded",
    )

    return {
        "message": "Document uploaded successfully",
        "document_id": document_id,
        "application_id": application_id,
        "filename": file.filename,
        "status": "Document Uploaded",
    }


# --------------------------------------------------
# Document validation
# --------------------------------------------------

@app.post("/documents/{document_id}/validate")
def validate_uploaded_document(document_id: str):
    document = find_document(document_id)

    if document is None:
        raise HTTPException(
            status_code=404,
            detail="Document not found",
        )

    application_id = document["application_id"]
    file_path = get_document_file_path(document)

    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Uploaded file does not exist",
        )

    try:
        extracted_text = extract_text_from_pdf(str(file_path))

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to read PDF: {error}",
        )

    if not extracted_text.strip():
        update_application_status(
            application_id,
            "Manual Review",
        )

        return {
            "message": "Document validation completed",
            "document_id": document_id,
            "application_id": application_id,
            "document_type": "Unknown",
            "validation_result": {
                "document_type": "Unknown",
                "is_valid": False,
                "missing_fields": ["extracted_text"],
                "extracted_details": {},
                "validation_message": (
                    "No readable text was extracted from the PDF."
                ),
            },
            "extracted_text": "",
            "status": "Manual Review",
        }

    document_type = classify_document(extracted_text)

    # Important: validator receives only extracted text
    validation_result = validate_document(extracted_text)

    connection = get_connection()

    connection.execute(
        """
        UPDATE documents
        SET document_type = ?,
            extracted_text = ?
        WHERE document_id = ?
        """,
        (
            document_type,
            extracted_text,
            document_id,
        ),
    )

    connection.commit()
    connection.close()

    if validation_result.get("is_valid"):
        new_status = "Document Validated"
    else:
        new_status = "Manual Review"

    update_application_status(
        application_id,
        new_status,
    )

    return {
        "message": "Document validation completed",
        "document_id": document_id,
        "application_id": application_id,
        "document_type": document_type,
        "validation_result": validation_result,
        "extracted_text": extracted_text,
        "status": new_status,
    }


# --------------------------------------------------
# Eligibility calculation
# --------------------------------------------------

@app.post("/applications/{application_id}/eligibility")
def check_application_eligibility(application_id: str):
    application = find_application(application_id)

    if application is None:
        raise HTTPException(
            status_code=404,
            detail="Application not found",
        )

    documents = get_documents_by_application(application_id)

    if not documents:
        update_application_status(
            application_id,
            "Manual Review",
        )

        return {
            "application_id": application_id,
            "loan_id": application.get("loan_id"),
            "applicant_name": application["applicant_name"],
            "eligible": False,
            "risk_level": "High",
            "reason": "No documents uploaded",
            "status": "Manual Review",
        }

    latest_document = documents[0]
    file_path = get_document_file_path(latest_document)

    if not file_path.exists():
        update_application_status(
            application_id,
            "Manual Review",
        )

        return {
            "application_id": application_id,
            "loan_id": application.get("loan_id"),
            "applicant_name": application["applicant_name"],
            "eligible": False,
            "risk_level": "High",
            "reason": "Uploaded document file not found",
            "status": "Manual Review",
        }

    try:
        extracted_text = extract_text_from_pdf(str(file_path))

    except Exception as error:
        update_application_status(
            application_id,
            "Manual Review",
        )

        return {
            "application_id": application_id,
            "loan_id": application.get("loan_id"),
            "applicant_name": application["applicant_name"],
            "eligible": False,
            "risk_level": "High",
            "reason": f"Unable to read document: {error}",
            "status": "Manual Review",
        }

    document_type = classify_document(extracted_text)

    # Important: validator receives only extracted text
    validation_result = validate_document(extracted_text)

    eligibility_result = calculate_eligibility(
        annual_income=application["annual_income"],
        loan_amount=application["loan_amount"],
        validation_result=validation_result,
        applicant_name=application["applicant_name"],
        loan_id=application.get("loan_id"),
    )

    final_status = eligibility_result.get(
        "status",
        "Approved" if eligibility_result["eligible"] else "Manual Review",
    )

    update_application_status(
        application_id,
        final_status,
    )

    return {
        "application_id": application_id,
        "loan_id": application.get("loan_id"),
        "applicant_name": application["applicant_name"],
        "annual_income": application["annual_income"],
        "loan_amount": application["loan_amount"],
        "document_type": document_type,
        "validation_result": validation_result,
        "eligibility_result": eligibility_result,
        "eligible": eligibility_result["eligible"],
        "risk_level": eligibility_result.get("risk_level"),
        "reason": eligibility_result.get("reason"),
        "status": final_status,
    }


# --------------------------------------------------
# Application documents
# --------------------------------------------------

@app.get("/applications/{application_id}/documents")
def get_application_documents(application_id: str):
    application = find_application(application_id)

    if application is None:
        raise HTTPException(
            status_code=404,
            detail="Application not found",
        )

    return {
        "application_id": application_id,
        "documents": get_documents_by_application(application_id),
    }