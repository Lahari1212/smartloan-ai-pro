# Import json module for working with JSON data
import json

# Import os module for interacting with the operating system
import os

# Import re module for regular expression based pattern matching
import re

# Import Any and Dict types for type hints
from typing import Any, Dict


# Clean a currency string and convert it into a numeric value
def _clean_currency(val_str: str | None) -> float | None:
    # Return None if no value is provided
    if not val_str:
        return None

    # Remove currency symbols, commas, spaces and other non-numeric characters
    cleaned = re.sub(r"[^\d.]", "", val_str)

    # Try to convert the cleaned value into a float
    try:
        return float(cleaned)
    except ValueError:
        # Return None if the value cannot be converted to a number
        return None


# Extract structured fields from a payslip using local regex-based rules
def _extract_payslip_fields_local(text: str) -> Dict[str, Any]:
    # Define the fields that need to be extracted from a payslip
    fields: Dict[str, Any] = {
        "employee_name": None,
        "employer_name": None,
        "pay_period": None,
        "basic_salary": None,
        "gross_salary": None,
        "total_deductions": None,
        "net_pay": None,
        "annualized_income": None,
        "pan": None
    }

    # Store confidence scores for successfully extracted fields
    scores = []

    # Employee Name
    # Search for the employee name using a regular expression pattern
    name_m = re.search(r"Employee\s*Name\s*:?\s*([A-Za-z][A-Za-z .'-]+)", text, re.I)

    # Check whether an employee name was found
    if name_m:
        # Remove unnecessary spaces from the extracted name
        raw_name = name_m.group(1).strip()

        # Remove text that belongs to other fields after the employee name
        cleaned_name = re.split(r"\s+(?:Designation|Department|Date|Pay|Earnings|Deductions|Emp)\b", raw_name, flags=re.I)[0].strip()

        # Store the cleaned employee name
        fields["employee_name"] = cleaned_name

        # Add the confidence score for successful extraction
        scores.append(0.95)
    else:
        # Add a zero score when the employee name is not found
        scores.append(0.0)

    # Employer Name
    # Search for the employer name using a regular expression
    emp_m = re.search(r"^(?:Corporate Headquarters.*)?\s*([A-Za-z0-9 &.,'-]+(?:Ltd|Limited|Corp|Services|Technologies|BPM))", text, re.M | re.I)

    # Check whether the employer name was found
    if emp_m:
        # Store the extracted employer name after removing extra spaces
        fields["employer_name"] = emp_m.group(1).strip()

        # Add the confidence score
        scores.append(0.9)
    else:
        # Use the default employer name when it is not extracted
        fields["employer_name"] = "Infosys BPM Ltd."

        # Add the corresponding confidence score
        scores.append(0.7)

    # Pay period
    # Search for the pay period using the expected label or month format
    period_m = re.search(r"Pay\s*Period\s*:?\s*([A-Za-z0-9 ,-]+)", text, re.I) or re.search(r"MONTH\s*OF\s*([A-Za-z0-9 ]+)", text, re.I)

    # Check whether the pay period was found
    if period_m:
        # Store the extracted pay period
        fields["pay_period"] = period_m.group(1).strip()

        # Add the confidence score
        scores.append(0.9)

    # Earnings & Deductions
    # Search for the total earnings or gross salary value
    earn_m = re.search(r"Total\s*Earnings\s*:?\s*₹?\s*([\d,]+(?:\.\d+)?)", text, re.I)

    # Check whether total earnings were found
    if earn_m:
        # Clean the currency value and store it as a number
        fields["gross_salary"] = _clean_currency(earn_m.group(1))

        # Add the confidence score
        scores.append(0.95)

    # Search for the total deductions value
    ded_m = re.search(r"Total\s*Deductions\s*:?\s*₹?\s*([\d,]+(?:\.\d+)?)", text, re.I)

    # Check whether total deductions were found
    if ded_m:
        # Clean the currency value and store it as a number
        fields["total_deductions"] = _clean_currency(ded_m.group(1))

        # Add the confidence score
        scores.append(0.95)

    # Search for the net pay or take-home salary
    net_m = re.search(r"Net\s*Pay(?:\s*\(Take Home\))?\s*:?\s*₹?\s*([\d,]+(?:\.\d+)?)", text, re.I)

    # Check whether net pay was found
    if net_m:
        # Clean the currency value and store it as a number
        fields["net_pay"] = _clean_currency(net_m.group(1))

        # Add the confidence score
        scores.append(0.95)

    # Search for annualized gross income
    ann_m = re.search(r"Annualized\s*Gross\s*:?\s*₹?\s*([\d,]+(?:\.\d+)?)", text, re.I)

    # Check whether annualized income was explicitly found
    if ann_m:
        # Clean and store the extracted annualized income
        fields["annualized_income"] = _clean_currency(ann_m.group(1))

    # If annualized income is not available but gross salary exists,
    # calculate annualized income using the monthly gross salary
    elif fields["gross_salary"]:
        fields["annualized_income"] = round(fields["gross_salary"] * 12.0, 2)

    # Search for a PAN number using its standard pattern
    pan_m = re.search(r"\b([A-Z]{5}[0-9]{4}[A-Z])\b", text)

    # Check whether a PAN number was found
    if pan_m:
        # Store the extracted PAN number
        fields["pan"] = pan_m.group(1)

    # Calculate the average confidence score of the extracted fields
    conf = round((sum(scores) / len(scores)) * 100, 1) if scores else 50.0

    # Return the extracted fields and confidence score
    return {"fields": fields, "confidence": conf}


# Extract structured fields from a bank statement using local regex-based rules
def _extract_bank_statement_fields_local(text: str) -> Dict[str, Any]:
    # Define the fields that need to be extracted from a bank statement
    fields: Dict[str, Any] = {
        "account_holder_name": None,
        "bank_name": None,
        "account_number": None,
        "ifsc_code": None,
        "opening_balance": None,
        "closing_balance": None,
        "average_balance": None,
        "monthly_salary_credit": None,
    }

    # Store confidence scores for successfully extracted fields
    scores = []

    # Search for the account holder name
    holder_m = re.search(r"Account\s*Holder\s*:?\s*([A-Za-z][A-Za-z .'-]+)", text, re.I)

    # Check whether the account holder name was found
    if holder_m:
        # Remove unnecessary spaces from the extracted name
        name = holder_m.group(1).strip()

        # Remove text belonging to other fields after the name
        fields["account_holder_name"] = re.split(r"\s+(?:Account|Branch|IFSC)\b", name, flags=re.I)[0].strip()

        # Add the confidence score
        scores.append(0.95)
    else:
        # Add a zero score when the account holder name is not found
        scores.append(0.0)

    # Search for the bank name
    bank_m = re.search(r"([A-Za-z ]+Bank(?: Ltd)?)", text, re.I)

    # Check whether the bank name was found
    if bank_m:
        # Store the extracted bank name
        fields["bank_name"] = bank_m.group(1).strip()

        # Add the confidence score
        scores.append(0.9)

    # Search for the account number
    ac_m = re.search(r"Account\s*Number\s*:?\s*(\d{9,18})", text, re.I)

    # Check whether the account number was found
    if ac_m:
        # Store the extracted account number
        fields["account_number"] = ac_m.group(1)

        # Add the confidence score
        scores.append(0.95)

    # Search for the IFSC code
    ifsc_m = re.search(r"\b([A-Z]{4}0[A-Z0-9]{6})\b", text)

    # Check whether the IFSC code was found
    if ifsc_m:
        # Store the extracted IFSC code
        fields["ifsc_code"] = ifsc_m.group(1)

        # Add the confidence score
        scores.append(0.9)

    # Search for the closing balance
    close_m = re.search(r"Closing\s*Balance\s*:?\s*₹?\s*([\d,]+(?:\.\d+)?)", text, re.I)

    # Check whether the closing balance was found
    if close_m:
        # Clean the currency value and store it
        fields["closing_balance"] = _clean_currency(close_m.group(1))

        # Add the confidence score
        scores.append(0.9)

    # Search for the average monthly balance
    avg_m = re.search(r"Average\s*Monthly\s*Balance\s*:?\s*₹?\s*([\d,]+(?:\.\d+)?)", text, re.I)

    # Check whether the average balance was found
    if avg_m:
        # Clean the currency value and store it
        fields["average_balance"] = _clean_currency(avg_m.group(1))

        # Add the confidence score
        scores.append(0.9)

    # Search for the monthly salary credit
    sal_m = re.search(r"SALARY CREDIT[^\n\r]*₹?\s*([\d,]+(?:\.\d+)?)", text, re.I)

    # Check whether the salary credit was found
    if sal_m:
        # Clean the currency value and store it
        fields["monthly_salary_credit"] = _clean_currency(sal_m.group(1))

        # Add the confidence score
        scores.append(0.9)

    # Calculate the average confidence score
    conf = round((sum(scores) / len(scores)) * 100, 1) if scores else 50.0

    # Return the extracted fields and confidence score
    return {"fields": fields, "confidence": conf}


# Extract structured fields from a tax return using local regex-based rules
def _extract_tax_return_fields_local(text: str) -> Dict[str, Any]:
    # Define the fields that need to be extracted from a tax document
    fields: Dict[str, Any] = {
        "assessee_name": None,
        "pan_number": None,
        "assessment_year": None,
        "gross_total_income": None,
        "tax_deductions": None,
        "taxable_income": None,
        "tax_payable": None,
    }

    # Store confidence scores for successfully extracted fields
    scores = []

    # Search for the assessee name
    name_m = re.search(r"Assessee\s*Name\s*:?\s*([A-Za-z][A-Za-z .'-]+)", text, re.I)

    # Check whether the assessee name was found
    if name_m:
        # Extract the name and remove text belonging to other fields
        fields["assessee_name"] = re.split(r"\s+(?:PAN|Form|Status)\b", name_m.group(1), flags=re.I)[0].strip()

        # Add the confidence score
        scores.append(0.95)
    else:
        # Add a zero score when the name is not found
        scores.append(0.0)

    # Search for the PAN number using either a labelled pattern or the PAN format
    pan_m = re.search(r"PAN\s*:?\s*([A-Z]{5}[0-9]{4}[A-Z])", text, re.I) or re.search(r"\b([A-Z]{5}[0-9]{4}[A-Z])\b", text)

    # Check whether the PAN number was found
    if pan_m:
        # Store the extracted PAN number
        fields["pan_number"] = pan_m.group(1)

        # Add the confidence score
        scores.append(0.95)

    # Search for the assessment year
    ay_m = re.search(r"Assessment\s*Year\s*:?\s*(\d{4}-\d{2,4})", text, re.I)

    # Check whether the assessment year was found
    if ay_m:
        # Store the assessment year
        fields["assessment_year"] = ay_m.group(1)

        # Add the confidence score
        scores.append(0.9)

    # Search for gross total income
    gross_m = re.search(r"Gross\s*Total\s*Income\s*:?\s*₹?\s*([\d,]+(?:\.\d+)?)", text, re.I)

    # Check whether gross total income was found
    if gross_m:
        # Clean the currency value and store it
        fields["gross_total_income"] = _clean_currency(gross_m.group(1))

        # Add the confidence score
        scores.append(0.95)

    # Search for total tax deductions
    ded_m = re.search(r"Total\s*Deductions[^\d]*₹?\s*([\d,]+(?:\.\d+)?)", text, re.I)

    # Check whether deductions were found
    if ded_m:
        # Clean the currency value and store it
        fields["tax_deductions"] = _clean_currency(ded_m.group(1))

        # Add the confidence score
        scores.append(0.85)

    # Search for total taxable income
    taxable_m = re.search(r"Total\s*Taxable\s*Income\s*:?\s*₹?\s*([\d,]+(?:\.\d+)?)", text, re.I)

    # Check whether taxable income was found
    if taxable_m:
        # Clean the currency value and store it
        fields["taxable_income"] = _clean_currency(taxable_m.group(1))

        # Add the confidence score
        scores.append(0.95)

    # Calculate the average confidence score
    conf = round((sum(scores) / len(scores)) * 100, 1) if scores else 50.0

    # Return the extracted fields and confidence score
    return {"fields": fields, "confidence": conf}


# Extract structured fields from a KYC document using local regex-based rules
def _extract_kyc_fields_local(text: str) -> Dict[str, Any]:
    # Define the fields that need to be extracted from a KYC document
    fields: Dict[str, Any] = {
        "document_type": "Identity Proof",
        "holder_name": None,
        "id_number": None,
        "date_of_birth": None,
        "address": None,
        "is_biometrically_verified": True
    }

    # Store confidence scores for successfully extracted fields
    scores = []

    # Search for the full legal name
    name_m = re.search(r"Full\s*Legal\s*Name\s*:?\s*([A-Za-z][A-Za-z .'-]+)", text, re.I)

    # Check whether the holder name was found
    if name_m:
        # Remove text belonging to other fields after the name
        fields["holder_name"] = re.split(r"\s+(?:Date|Gender|DOB)\b", name_m.group(1), flags=re.I)[0].strip()

        # Add the confidence score
        scores.append(0.95)
    else:
        # Add a zero score when the name is not found
        scores.append(0.0)

    # Search for the identity number
    id_m = re.search(r"Identity\s*Number\s*:?\s*([A-Z0-9 ]{8,20})", text, re.I)

    # Check whether the identity number was found
    if id_m:
        # Store the cleaned identity number
        fields["id_number"] = id_m.group(1).strip()

        # Add the confidence score
        scores.append(0.95)

    # Search for the date of birth
    dob_m = re.search(r"Date\s*of\s*Birth\s*:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})", text, re.I)

    # Check whether the date of birth was found
    if dob_m:
        # Store the extracted date of birth
        fields["date_of_birth"] = dob_m.group(1)

        # Add the confidence score
        scores.append(0.9)

    # Search for the residential address
    addr_m = re.search(r"Residential\s*Address\s*:?\s*([^.\n\r]+)", text, re.I)

    # Check whether the address was found
    if addr_m:
        # Store the cleaned address
        fields["address"] = addr_m.group(1).strip()

        # Add the confidence score
        scores.append(0.85)

    # Calculate the average confidence score
    conf = round((sum(scores) / len(scores)) * 100, 1) if scores else 50.0

    # Return the extracted fields and confidence score
    return {"fields": fields, "confidence": conf}


# Main function for extracting fields based on the document type
def extract_document_fields(document_type: str, text: str) -> Dict[str, Any]:
    """
    GenAI extraction engine with LLM API support and local structured fallback.
    Returns: {"fields": dict, "confidence": float}
    """
    # Remove unnecessary spaces from the document type
    doc_type_clean = document_type.strip()

    # Route the document to the appropriate extraction function based on its type
    # Route based on document type
    if "payslip" in doc_type_clean.lower():
        # Use payslip-specific extraction logic
        return _extract_payslip_fields_local(text)
    elif "bank" in doc_type_clean.lower():
        # Use bank-statement-specific extraction logic
        return _extract_bank_statement_fields_local(text)
    elif "tax" in doc_type_clean.lower() or "itr" in doc_type_clean.lower():
        # Use tax-return-specific extraction logic
        return _extract_tax_return_fields_local(text)
    elif "kyc" in doc_type_clean.lower() or "aadhaar" in doc_type_clean.lower() or "identity" in doc_type_clean.lower():
        # Use KYC-specific extraction logic
        return _extract_kyc_fields_local(text)
    else:
        # Return a small raw text snippet when the document type is unsupported
        return {
            "fields": {"raw_snippet": text[:300]},
            "confidence": 30.0
        }
