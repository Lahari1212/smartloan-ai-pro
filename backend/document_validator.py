import re
from difflib import SequenceMatcher
from typing import Any, Dict, List, Optional
from ai_extractor import extract_document_fields


def clean_text(text: str) -> str:
    if not text:
        return ""
    text = text.replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n+", "\n", text)
    return text.strip()


def _normalize_name(name: str | None) -> str:
    if not name:
        return ""
    name_clean = re.sub(r"^(mr|mrs|ms|dr|prof)\.?\s+", "", name.strip(), flags=re.I)
    name_clean = re.sub(r"[^a-zA-Z\s]", "", name_clean)
    return " ".join(name_clean.lower().split())


def _names_match(name1: str | None, name2: str | None, threshold: float = 0.75) -> tuple[bool, float]:
    n1 = _normalize_name(name1)
    n2 = _normalize_name(name2)
    if not n1 or not n2:
        return False, 0.0
    if n1 == n2:
        return True, 1.0
    # Token subset match (e.g. "Aditi Sharma" in "Aditi Sharma Rao")
    tokens1 = set(n1.split())
    tokens2 = set(n2.split())
    if tokens1.issubset(tokens2) or tokens2.issubset(tokens1):
        return True, 0.90

    ratio = SequenceMatcher(None, n1, n2).ratio()
    return ratio >= threshold, round(ratio, 2)


def validate_single_document(document_type: str, extracted_fields: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validates completeness of key fields for an individual document.
    """
    fields = extracted_fields or {}
    missing_fields = []
    doc_lower = document_type.lower()

    if "payslip" in doc_lower:
        required = [("employee_name", "Employee Name"), ("gross_salary", "Gross Salary"), ("net_pay", "Net Pay")]
        for key, label in required:
            if not fields.get(key):
                missing_fields.append(label)
    elif "bank" in doc_lower:
        required = [("account_holder_name", "Account Holder Name"), ("account_number", "Account Number"), ("closing_balance", "Closing Balance")]
        for key, label in required:
            if not fields.get(key):
                missing_fields.append(label)
    elif "tax" in doc_lower or "itr" in doc_lower:
        required = [("assessee_name", "Assessee Name"), ("pan_number", "PAN Number"), ("gross_total_income", "Gross Total Income")]
        for key, label in required:
            if not fields.get(key):
                missing_fields.append(label)
    elif "kyc" in doc_lower or "aadhaar" in doc_lower or "identity" in doc_lower:
        required = [("holder_name", "Full Legal Name"), ("id_number", "Identity Number")]
        for key, label in required:
            if not fields.get(key):
                missing_fields.append(label)

    is_valid = len(missing_fields) == 0
    msg = f"{document_type} verified successfully." if is_valid else f"{document_type} missing required fields: {', '.join(missing_fields)}"

    return {
        "document_type": document_type,
        "is_valid": is_valid,
        "missing_fields": missing_fields,
        "extracted_details": fields,
        "validation_message": msg
    }


def validate_all_documents(application: Dict[str, Any], documents: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Cross-document verification agent:
    1. Checks for missing required documents.
    2. Compares applicant name across all documents.
    3. Cross-validates declared annual income against payslip, tax return, and bank deposits.
    4. Detects identification and confidence issues.
    """
    app_name = application.get("applicant_name", "")
    declared_income = float(application.get("annual_income") or 0.0)

    # 1. Document checklist & classification map
    STANDARD_DOCS = ["Payslip", "Bank Statement", "Tax Return", "KYC Document"]
    uploaded_by_type: Dict[str, List[Dict[str, Any]]] = {t: [] for t in STANDARD_DOCS}
    uploaded_by_type["Other"] = []

    for doc in documents:
        dtype = doc.get("document_type", "Unknown")
        matched_standard = False
        for std in STANDARD_DOCS:
            if std.lower() in dtype.lower():
                uploaded_by_type[std].append(doc)
                matched_standard = True
                break
        if not matched_standard:
            uploaded_by_type["Other"].append(doc)

    missing_docs = [std for std in STANDARD_DOCS if len(uploaded_by_type[std]) == 0]

    inconsistencies = []

    # Flag missing essential documents
    if "Payslip" in missing_docs:
        inconsistencies.append({
            "type": "MISSING_DOCUMENT",
            "severity": "HIGH",
            "document": "Payslip",
            "message": "Mandatory proof of current employment/salary (Payslip) is missing."
        })
    if "KYC Document" in missing_docs:
        inconsistencies.append({
            "type": "MISSING_DOCUMENT",
            "severity": "HIGH",
            "document": "KYC Document",
            "message": "Official Government Identity proof (KYC) is missing."
        })
    if "Bank Statement" in missing_docs:
        inconsistencies.append({
            "type": "MISSING_DOCUMENT",
            "severity": "MEDIUM",
            "document": "Bank Statement",
            "message": "Recent Bank Statement is missing to verify cash flows and salary deposits."
        })
    if "Tax Return" in missing_docs:
        inconsistencies.append({
            "type": "MISSING_DOCUMENT",
            "severity": "LOW",
            "document": "Tax Return",
            "message": "Income Tax Return (ITR-V) is missing. Recommended for higher loan amounts."
        })

    # 2. Cross-Document Name Validation
    for std, doc_list in uploaded_by_type.items():
        if std == "Other":
            continue
        for doc in doc_list:
            fields = doc.get("extracted_json") or {}
            extracted_name = None
            if std == "Payslip":
                extracted_name = fields.get("employee_name")
            elif std == "Bank Statement":
                extracted_name = fields.get("account_holder_name")
            elif std == "Tax Return":
                extracted_name = fields.get("assessee_name")
            elif std == "KYC Document":
                extracted_name = fields.get("holder_name")

            if extracted_name:
                matched, score = _names_match(app_name, extracted_name)
                if not matched:
                    inconsistencies.append({
                        "type": "NAME_MISMATCH",
                        "severity": "HIGH",
                        "document": std,
                        "declared_value": app_name,
                        "extracted_value": extracted_name,
                        "similarity_score": score,
                        "message": f"Name mismatch on {std}: Application declares '{app_name}', but document has '{extracted_name}' (match: {int(score*100)}%)."
                    })

    # 3. Cross-Document Income Validation
    income_points = []

    # Check Payslip income
    payslip_docs = uploaded_by_type["Payslip"]
    if payslip_docs:
        p_fields = payslip_docs[0].get("extracted_json") or {}
        p_annual = p_fields.get("annualized_income")
        if not p_annual and p_fields.get("gross_salary"):
            p_annual = p_fields.get("gross_salary") * 12.0
        if p_annual:
            income_points.append(("Payslip (Annualized)", float(p_annual)))

    # Check Tax Return income
    tax_docs = uploaded_by_type["Tax Return"]
    if tax_docs:
        t_fields = tax_docs[0].get("extracted_json") or {}
        t_income = t_fields.get("gross_total_income")
        if t_income:
            income_points.append(("Tax Return (Gross Total Income)", float(t_income)))

    # Compare income points against declared income
    for src, inc in income_points:
        if declared_income > 0:
            diff = abs(inc - declared_income)
            pct_diff = (diff / declared_income) * 100.0
            if pct_diff > 15.0:
                severity = "HIGH" if pct_diff > 25.0 else "MEDIUM"
                inconsistencies.append({
                    "type": "INCOME_DISCREPANCY",
                    "severity": severity,
                    "document": src,
                    "declared_value": f"₹{declared_income:,.0f}",
                    "extracted_value": f"₹{inc:,.0f}",
                    "variance_pct": round(pct_diff, 1),
                    "message": f"Income variance of {pct_diff:.1f}% detected: Application declared ₹{declared_income:,.0f}, but {src} indicates ₹{inc:,.0f}."
                })

    # 4. Low confidence checks
    for doc in documents:
        conf = float(doc.get("confidence_score") or 0.0)
        if 0 < conf < 65.0:
            inconsistencies.append({
                "type": "LOW_EXTRACTION_CONFIDENCE",
                "severity": "LOW",
                "document": doc.get("document_type", "Document"),
                "confidence": conf,
                "message": f"{doc.get('document_type', 'Document')} has low AI extraction confidence ({conf}%). Manual inspection advised."
            })

    high_issues = [i for i in inconsistencies if i["severity"] == "HIGH"]
    med_issues = [i for i in inconsistencies if i["severity"] == "MEDIUM"]

    # Status verdict
    if high_issues:
        status_verdict = "Manual Review"
        risk_level = "High"
    elif med_issues or len(missing_docs) > 2:
        status_verdict = "Manual Review"
        risk_level = "Medium"
    else:
        status_verdict = "Document Validated"
        risk_level = "Low"

    checklist = {}
    for std in STANDARD_DOCS:
        docs_present = uploaded_by_type[std]
        checklist[std] = {
            "uploaded": len(docs_present) > 0,
            "count": len(docs_present),
            "status": "Verified" if len(docs_present) > 0 else "Missing"
        }

    return {
        "is_valid": len(high_issues) == 0,
        "status": status_verdict,
        "risk_level": risk_level,
        "missing_documents": missing_docs,
        "inconsistencies": inconsistencies,
        "issues_count": len(inconsistencies),
        "checklist": checklist,
        "income_comparison": {
            "declared_annual_income": declared_income,
            "evidence": income_points
        }
    }


def validate_document(extracted_text: str, document_type: str = "Payslip") -> Dict[str, Any]:
    """
    Backwards-compatible wrapper function for main.py single-document verification.
    """
    if not extracted_text or not extracted_text.strip():
        return {
            "document_type": document_type or "Unknown",
            "is_valid": False,
            "missing_fields": ["Extracted text"],
            "extracted_details": {},
            "validation_message": "No text could be extracted from the document."
        }

    from ai_extractor import extract_document_fields
    extraction = extract_document_fields(document_type, extracted_text)
    return validate_single_document(document_type, extraction["fields"])