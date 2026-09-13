import re


def classify_document(text: str) -> tuple[str, float]:
    """
    Classifies a document based on text features, keywords, and structural patterns.
    Returns: (document_type, confidence_score_0_to_100)
    """
    if not text or not text.strip():
        return "Unknown", 0.0

    text_lower = text.lower()

    # Weighted keyword dictionaries
    weights = {
        "Payslip": {
            "payslip": 10, "pay slip": 10, "salary slip": 10,
            "basic salary": 6, "gross salary": 6, "net salary": 6, "net pay": 8,
            "total earnings": 8, "total deductions": 8, "provident fund": 5,
            "pf number": 5, "hra": 4, "take home": 5, "pay period": 5, "employee id": 5
        },
        "Bank Statement": {
            "statement of account": 10, "bank statement": 10, "account number": 6,
            "opening balance": 8, "closing balance": 8, "average monthly balance": 8,
            "ifsc": 7, "branch": 4, "debit": 5, "credit": 5, "withdrawal": 4,
            "deposit": 4, "transaction date": 5, "narration": 4, "retail banking": 5
        },
        "Tax Return": {
            "income tax return": 10, "itr-v": 10, "itr-1": 8, "itr": 7,
            "assessment year": 8, "gross total income": 8, "taxable income": 8,
            "income tax department": 9, "assessee": 6, "pan": 5, "chapter vi-a": 6,
            "total tax payable": 7, "form 16": 9, "tds": 4
        },
        "KYC Document": {
            "unique identification authority": 10, "aadhaar": 10, "passport": 10,
            "election commission": 9, "voter id": 9, "identity proof": 8,
            "kyc document": 8, "date of birth": 6, "dob": 5, "residential address": 5,
            "nationality": 4, "pmla": 5, "gender": 4, "biometrically verified": 7
        }
    }

    scores = {doc_type: 0 for doc_type in weights}

    for doc_type, kw_dict in weights.items():
        for kw, score in kw_dict.items():
            if re.search(rf"\b{re.escape(kw)}\b", text_lower):
                scores[doc_type] += score

    highest_doc_type = max(scores, key=scores.get)
    max_score = scores[highest_doc_type]

    if max_score < 8:
        return "Unknown", 0.0

    # Calculate confidence as percentage relative to ideal score range
    confidence = min(99.0, max(60.0, round((max_score / 35.0) * 100, 1)))

    return highest_doc_type, confidence