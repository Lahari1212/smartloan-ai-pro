def classify_document(text: str) -> str:
    text_lower = text.lower()

    scores = {
        "Payslip": 0,
        "Bank Statement": 0,
        "Tax Document": 0,
        "KYC Document": 0,
        "Resume": 0
    }

    keyword_scores = {
        "Payslip": [
            "payslip",
            "pay slip",
            "basic salary",
            "gross salary",
            "net salary",
            "employee id",
            "earnings",
            "deductions",
            "pay period"
        ],
        "Bank Statement": [
            "bank statement",
            "account number",
            "transaction date",
            "closing balance",
            "opening balance",
            "debit",
            "credit",
            "withdrawal",
            "deposit",
            "available balance"
        ],
        "Tax Document": [
            "income tax",
            "tax return",
            "taxable income",
            "assessment year",
            "taxpayer",
            "tax deduction",
            "total income"
        ],
        "KYC Document": [
            "date of birth",
            "identity document",
            "nationality",
            "address proof",
            "government id",
            "aadhaar",
            "passport",
            "driving licence",
            "identity number"
        ],
        "Resume": [
            "professional summary",
            "technical skills",
            "work experience",
            "education",
            "projects",
            "certifications",
            "career objective",
            "employment history"
        ]
    }

    for document_type, keywords in keyword_scores.items():
        for keyword in keywords:
            if keyword in text_lower:
                scores[document_type] += 1

    highest_score = max(scores.values())

    if highest_score == 0:
        return "Unknown"

    detected_type = max(scores, key=scores.get)

    return detected_type