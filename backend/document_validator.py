import re


def clean_text(text: str) -> str:
    if not text:
        return ""

    text = text.replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n+", "\n", text)

    return text.strip()


def extract_employee_name(text: str):
    patterns = [
        r"Employee\s*Name\s*:?\s*([A-Za-z][A-Za-z .'-]+)",
        r"Employee\s*:?\s*([A-Za-z][A-Za-z .'-]+)",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)

        if match:
            name = match.group(1).strip()

            name = re.split(
                r"\s+(?:Designation|Department|Date|Pay|Earnings|Deductions)\b",
                name,
                flags=re.IGNORECASE,
            )[0].strip()

            return name

    return None


def extract_summary_values(text: str):
    """
    Extract values from the payslip summary.

    For the uploaded payslip, the values appear after
    Total Earnings in this order:

    Total Earnings -> Total Deductions -> Net Pay
    """

    summary_match = re.search(
        r"Total\s+Earnings(.*)",
        text,
        re.IGNORECASE | re.DOTALL,
    )

    if summary_match:
        summary_text = summary_match.group(1)

        numbers = re.findall(
            r"\b\d[\d,]*(?:\.\d+)?\b",
            summary_text,
        )

        numbers = [
            number.replace(",", "")
            for number in numbers
        ]

        if len(numbers) >= 3:
            return {
                "total_earnings": float(numbers[0]),
                "total_deductions": float(numbers[1]),
                "net_pay": float(numbers[2]),
            }

    return {
        "total_earnings": None,
        "total_deductions": None,
        "net_pay": None,
    }


def validate_payslip(extracted_text: str):
    text = clean_text(extracted_text)

    employee_name = extract_employee_name(text)
    summary_values = extract_summary_values(text)

    missing_fields = []

    if not employee_name:
        missing_fields.append("Employee Name")

    if summary_values["total_earnings"] is None:
        missing_fields.append("Total Earnings")

    if summary_values["total_deductions"] is None:
        missing_fields.append("Total Deductions")

    if summary_values["net_pay"] is None:
        missing_fields.append("Net Pay")

    is_valid = len(missing_fields) == 0

    if is_valid:
        validation_message = "Payslip validated successfully."
    else:
        validation_message = (
            "Payslip validation failed. Missing fields: "
            + ", ".join(missing_fields)
        )

    return {
        "document_type": "Payslip",
        "is_valid": is_valid,
        "missing_fields": missing_fields,
        "extracted_details": {
            "employee_name": employee_name,
            "total_earnings": summary_values["total_earnings"],
            "total_deductions": summary_values["total_deductions"],
            "net_pay": summary_values["net_pay"],
        },
        "validation_message": validation_message,
    }


def validate_document(
    extracted_text: str,
    document_type: str = "Payslip",
):
    """
    Function imported by main.py.
    Supports both one and two arguments.
    """

    if not extracted_text or not extracted_text.strip():
        return {
            "document_type": document_type or "Unknown",
            "is_valid": False,
            "missing_fields": ["Extracted text"],
            "extracted_details": {},
            "validation_message": (
                "No text could be extracted from the document."
            ),
        }

    if document_type and "payslip" not in document_type.lower():
        return {
            "document_type": document_type,
            "is_valid": False,
            "missing_fields": [],
            "extracted_details": {},
            "validation_message": (
                "This document is not recognized as a payslip."
            ),
        }

    return validate_payslip(extracted_text)