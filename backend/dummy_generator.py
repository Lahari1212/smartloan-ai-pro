import os
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT


def _create_header(title: str, subtitle: str, styles):
    title_style = ParagraphStyle(
        'HeaderTitle',
        parent=styles['Heading1'],
        fontSize=18,
        leading=22,
        textColor=colors.HexColor('#1E3A8A'),
        alignment=TA_CENTER
    )
    sub_style = ParagraphStyle(
        'HeaderSubtitle',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#4B5563'),
        alignment=TA_CENTER
    )
    return [
        Paragraph(title, title_style),
        Spacer(1, 4),
        Paragraph(subtitle, sub_style),
        Spacer(1, 10),
        HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#1E3A8A'), spaceBefore=5, spaceAfter=15)
    ]


def generate_payslip_pdf(file_path: str, applicant_name: str, annual_income: float, employer_name: str = "Infosys BPM Ltd.", pay_period: str = "August 2026", discrepancy: bool = False):
    """
    Generates a professional corporate salary payslip.
    If discrepancy=True, salary is significantly reduced (-35%) to trigger an income discrepancy flag.
    """
    doc = SimpleDocTemplate(file_path, pagesize=letter, leftMargin=40, rightMargin=40, topMargin=40, bottomMargin=40)
    styles = getSampleStyleSheet()
    story = []

    # Title
    story.extend(_create_header(employer_name, "Corporate Headquarters: Electronic City, Bengaluru - 560100 | PAYSLIP FOR THE MONTH OF " + pay_period.upper(), styles))

    employee_name_val = applicant_name
    if discrepancy:
        # Subtle name discrepancy or income discrepancy
        annual_val = annual_income * 0.65  # 35% lower than declared
    else:
        annual_val = annual_income

    monthly_gross = round(annual_val / 12.0, 2)
    basic_salary = round(monthly_gross * 0.50, 2)
    hra = round(monthly_gross * 0.30, 2)
    special_allowance = round(monthly_gross * 0.20, 2)

    pf_deduction = round(basic_salary * 0.12, 2)
    prof_tax = 200.0
    tds = round(monthly_gross * 0.05, 2)
    total_deductions = round(pf_deduction + prof_tax + tds, 2)
    net_pay = round(monthly_gross - total_deductions, 2)

    # Employee info table
    emp_data = [
        [
            Paragraph("<b>Employee Name:</b>", styles['Normal']),
            Paragraph(employee_name_val, styles['Normal']),
            Paragraph("<b>Employee ID:</b>", styles['Normal']),
            Paragraph("EMP-98241", styles['Normal'])
        ],
        [
            Paragraph("<b>Designation:</b>", styles['Normal']),
            Paragraph("Senior Associate / Consultant", styles['Normal']),
            Paragraph("<b>Department:</b>", styles['Normal']),
            Paragraph("Technology & Operations", styles['Normal'])
        ],
        [
            Paragraph("<b>Pay Period:</b>", styles['Normal']),
            Paragraph(pay_period, styles['Normal']),
            Paragraph("<b>Bank A/C:</b>", styles['Normal']),
            Paragraph("HDFC Bank - 9918234891", styles['Normal'])
        ],
        [
            Paragraph("<b>PAN:</b>", styles['Normal']),
            Paragraph("ABCDE1234F", styles['Normal']),
            Paragraph("<b>PF Number:</b>", styles['Normal']),
            Paragraph("BGPF-887319-X", styles['Normal'])
        ]
    ]
    t1 = Table(emp_data, colWidths=[110, 150, 110, 150])
    t1.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8FAFC')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t1)
    story.append(Spacer(1, 15))

    # Salary breakdown table
    sal_data = [
        [Paragraph("<b>Earnings</b>", styles['Normal']), Paragraph("<b>Amount (INR)</b>", styles['Normal']),
         Paragraph("<b>Deductions</b>", styles['Normal']), Paragraph("<b>Amount (INR)</b>", styles['Normal'])],
        ["Basic Salary", f"₹ {basic_salary:,.2f}", "Provident Fund (PF)", f"₹ {pf_deduction:,.2f}"],
        ["House Rent Allowance (HRA)", f"₹ {hra:,.2f}", "Professional Tax", f"₹ {prof_tax:,.2f}"],
        ["Special Allowance", f"₹ {special_allowance:,.2f}", "Tax Deducted at Source (TDS)", f"₹ {tds:,.2f}"],
        [Paragraph("<b>Total Earnings</b>", styles['Normal']), f"₹ {monthly_gross:,.2f}",
         Paragraph("<b>Total Deductions</b>", styles['Normal']), f"₹ {total_deductions:,.2f}"],
        [Paragraph("<b>Net Pay (Take Home):</b>", styles['Normal']), Paragraph(f"<b>₹ {net_pay:,.2f}</b>", styles['Normal']),
         Paragraph("<b>Annualized Gross:</b>", styles['Normal']), Paragraph(f"<b>₹ {annual_val:,.2f}</b>", styles['Normal'])]
    ]
    t2 = Table(sal_data, colWidths=[150, 110, 150, 110])
    t2.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#E0E7FF')),
        ('BACKGROUND', (0,4), (-1,4), colors.HexColor('#F1F5F9')),
        ('BACKGROUND', (0,5), (-1,5), colors.HexColor('#ECFDF5')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t2)
    story.append(Spacer(1, 20))

    footer_text = Paragraph("<font size=8 color='#64748B'>* This is a computer generated salary slip and requires no physical signature. Verified under payroll batch #2026-08.</font>", styles['Normal'])
    story.append(footer_text)

    doc.build(story)
    return file_path


def generate_bank_statement_pdf(file_path: str, applicant_name: str, annual_income: float, bank_name: str = "HDFC Bank Ltd.", discrepancy: bool = False):
    """
    Generates a 3-month bank account statement showing salary credits.
    """
    doc = SimpleDocTemplate(file_path, pagesize=letter, leftMargin=40, rightMargin=40, topMargin=40, bottomMargin=40)
    styles = getSampleStyleSheet()
    story = []

    story.extend(_create_header(f"{bank_name} - Retail Banking", "STATEMENT OF ACCOUNT | Period: 01-Jun-2026 to 31-Aug-2026 | Currency: INR", styles))

    holder_name = applicant_name
    if discrepancy:
        # Typo discrepancy in name
        parts = applicant_name.split()
        if len(parts) > 1:
            holder_name = f"{parts[0]} Kumar {parts[1]}"
        else:
            holder_name = f"{applicant_name} Kumar"

    monthly_sal = round(annual_income / 12.0 * 0.85, 2)
    open_bal = 125400.00
    close_bal = round(open_bal + (monthly_sal * 3) - 180000.0, 2)

    meta_data = [
        [
            Paragraph("<b>Account Holder:</b>", styles['Normal']),
            Paragraph(holder_name, styles['Normal']),
            Paragraph("<b>Account Number:</b>", styles['Normal']),
            Paragraph("50100482910482", styles['Normal'])
        ],
        [
            Paragraph("<b>Branch:</b>", styles['Normal']),
            Paragraph("Koramangala 4th Block, Bangalore", styles['Normal']),
            Paragraph("<b>IFSC Code:</b>", styles['Normal']),
            Paragraph("HDFC0001244", styles['Normal'])
        ],
        [
            Paragraph("<b>Opening Balance:</b>", styles['Normal']),
            Paragraph(f"₹ {open_bal:,.2f}", styles['Normal']),
            Paragraph("<b>Closing Balance:</b>", styles['Normal']),
            Paragraph(f"₹ {close_bal:,.2f}", styles['Normal'])
        ],
        [
            Paragraph("<b>Average Monthly Balance:</b>", styles['Normal']),
            Paragraph(f"₹ {round((open_bal + close_bal)/2, 2):,.2f}", styles['Normal']),
            Paragraph("<b>Account Type:</b>", styles['Normal']),
            Paragraph("Salary Savings Account", styles['Normal'])
        ]
    ]
    t_meta = Table(meta_data, colWidths=[130, 140, 110, 140])
    t_meta.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8FAFC')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_meta)
    story.append(Spacer(1, 15))

    tx_data = [
        [Paragraph("<b>Date</b>", styles['Normal']), Paragraph("<b>Description / Narration</b>", styles['Normal']),
         Paragraph("<b>Debit (INR)</b>", styles['Normal']), Paragraph("<b>Credit (INR)</b>", styles['Normal']), Paragraph("<b>Balance</b>", styles['Normal'])],
        ["01-Jun-2026", "SALARY CREDIT - INFOSYS BPM", "-", f"₹ {monthly_sal:,.2f}", f"₹ {open_bal + monthly_sal:,.2f}"],
        ["05-Jun-2026", "ATM CASH WITHDRAWAL", "₹ 15,000.00", "-", f"₹ {open_bal + monthly_sal - 15000:,.2f}"],
        ["18-Jun-2026", "UPI/SWIGGY/GROCERIES", "₹ 12,450.00", "-", f"₹ {open_bal + monthly_sal - 27450:,.2f}"],
        ["01-Jul-2026", "SALARY CREDIT - INFOSYS BPM", "-", f"₹ {monthly_sal:,.2f}", f"₹ {open_bal + 2*monthly_sal - 27450:,.2f}"],
        ["10-Jul-2026", "NEFT - HOUSE RENT", "₹ 35,000.00", "-", f"₹ {open_bal + 2*monthly_sal - 62450:,.2f}"],
        ["01-Aug-2026", "SALARY CREDIT - INFOSYS BPM", "-", f"₹ {monthly_sal:,.2f}", f"₹ {close_bal:,.2f}"]
    ]
    t_tx = Table(tx_data, colWidths=[75, 180, 85, 85, 95])
    t_tx.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#E0E7FF')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_tx)
    story.append(Spacer(1, 20))

    story.append(Paragraph("<font size=8 color='#64748B'>* Bank statement certified electronically by HDFC Bank CBS. No alterations permitted.</font>", styles['Normal']))
    doc.build(story)
    return file_path


def generate_tax_return_pdf(file_path: str, applicant_name: str, annual_income: float, pan: str = "ABCDE1234F", assessment_year: str = "2025-26", discrepancy: bool = False):
    """
    Generates an Indian Income Tax Return Acknowledgement (ITR-V).
    """
    doc = SimpleDocTemplate(file_path, pagesize=letter, leftMargin=40, rightMargin=40, topMargin=40, bottomMargin=40)
    styles = getSampleStyleSheet()
    story = []

    story.extend(_create_header("INCOME TAX DEPARTMENT - GOVT OF INDIA", f"INDIAN INCOME TAX RETURN ACKNOWLEDGEMENT [ITR-V] | Assessment Year: {assessment_year}", styles))

    tax_income = annual_income
    if discrepancy:
        tax_income = annual_income * 0.50  # drastic mismatch

    deductions_80c = 150000.00
    taxable_income = max(0.0, tax_income - deductions_80c)
    tax_payable = round(taxable_income * 0.10, 2)

    data = [
        [Paragraph("<b>Assessee Name:</b>", styles['Normal']), Paragraph(applicant_name, styles['Normal']),
         Paragraph("<b>PAN:</b>", styles['Normal']), Paragraph(pan, styles['Normal'])],
        [Paragraph("<b>Form Type:</b>", styles['Normal']), Paragraph("ITR-1 (Sahaj)", styles['Normal']),
         Paragraph("<b>Status:</b>", styles['Normal']), Paragraph("Individual - Resident", styles['Normal'])],
        [Paragraph("<b>Assessment Year:</b>", styles['Normal']), Paragraph(assessment_year, styles['Normal']),
         Paragraph("<b>Filing Date:</b>", styles['Normal']), Paragraph("15-Jul-2025", styles['Normal'])],
        [Paragraph("<b>Gross Total Income:</b>", styles['Normal']), Paragraph(f"<b>₹ {tax_income:,.2f}</b>", styles['Normal']),
         Paragraph("<b>Total Deductions (Chapter VI-A):</b>", styles['Normal']), Paragraph(f"₹ {deductions_80c:,.2f}", styles['Normal'])],
        [Paragraph("<b>Total Taxable Income:</b>", styles['Normal']), Paragraph(f"<b>₹ {taxable_income:,.2f}</b>", styles['Normal']),
         Paragraph("<b>Total Tax & Cess Payable:</b>", styles['Normal']), Paragraph(f"₹ {tax_payable:,.2f}", styles['Normal'])],
        [Paragraph("<b>Taxes Paid / TDS:</b>", styles['Normal']), Paragraph(f"₹ {tax_payable:,.2f}", styles['Normal']),
         Paragraph("<b>Refund / Balance Payable:</b>", styles['Normal']), Paragraph("₹ 0.00 (Nil)", styles['Normal'])]
    ]

    t = Table(data, colWidths=[140, 130, 130, 120])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8FAFC')),
        ('BACKGROUND', (0,3), (1,3), colors.HexColor('#FEF3C7')),
        ('BACKGROUND', (0,4), (1,4), colors.HexColor('#DCFCE7')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t)
    story.append(Spacer(1, 20))

    story.append(Paragraph("<font size=8 color='#64748B'>Verification: e-Filed under Digital Signature Certificate. Verified and Processed under section 143(1) of the Income-tax Act, 1961.</font>", styles['Normal']))
    doc.build(story)
    return file_path


def generate_kyc_pdf(file_path: str, applicant_name: str, id_type: str = "Aadhaar Card", id_number: str = "7821 4490 1203", dob: str = "14/05/1992", discrepancy: bool = False):
    """
    Generates a Government Issued KYC Document (e.g. Aadhaar Card / Identity Proof).
    """
    doc = SimpleDocTemplate(file_path, pagesize=letter, leftMargin=40, rightMargin=40, topMargin=40, bottomMargin=40)
    styles = getSampleStyleSheet()
    story = []

    story.extend(_create_header("GOVERNMENT OF INDIA - UNIQUE IDENTIFICATION AUTHORITY", f"OFFICIAL IDENTITY PROOF (KYC DOCUMENT) - {id_type.upper()}", styles))

    kyc_name = applicant_name
    if discrepancy:
        # Different spelling in KYC
        kyc_name = applicant_name + " Rao"

    kyc_data = [
        [Paragraph("<b>Document Type:</b>", styles['Normal']), Paragraph(id_type, styles['Normal']),
         Paragraph("<b>Identity Number:</b>", styles['Normal']), Paragraph(id_number, styles['Normal'])],
        [Paragraph("<b>Full Legal Name:</b>", styles['Normal']), Paragraph(f"<b>{kyc_name}</b>", styles['Normal']),
         Paragraph("<b>Date of Birth:</b>", styles['Normal']), Paragraph(dob, styles['Normal'])],
        [Paragraph("<b>Gender:</b>", styles['Normal']), Paragraph("Male / Transgender / Female", styles['Normal']),
         Paragraph("<b>Nationality:</b>", styles['Normal']), Paragraph("Indian", styles['Normal'])],
        [Paragraph("<b>Residential Address:</b>", styles['Normal']),
         Paragraph("Flat 402, Lotus Residency, Outer Ring Road, Bellandur, Bengaluru, Karnataka - 560103", styles['Normal']),
         Paragraph("<b>Verification Status:</b>", styles['Normal']), Paragraph("<font color='green'><b>Biometrically Verified</b></font>", styles['Normal'])]
    ]

    t = Table(kyc_data, colWidths=[130, 140, 110, 140])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8FAFC')),
        ('BACKGROUND', (0,1), (1,1), colors.HexColor('#EEF2FF')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t)
    story.append(Spacer(1, 25))

    story.append(Paragraph("<font size=8 color='#64748B'>* Valid proof of Identity and Address under the Prevention of Money Laundering Act (PMLA) 2002. UIDAI verified.</font>", styles['Normal']))
    doc.build(story)
    return file_path


def generate_document_bundle(output_dir: Path, applicant_name: str, annual_income: float, scenario: str = "clean"):
    """
    Generates all 4 standard documents.
    scenario: "clean" or "discrepancy"
    Returns dict with document paths.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    is_discrepancy = (scenario.lower() == "discrepancy")

    payslip_path = output_dir / f"Payslip_{scenario}.pdf"
    generate_payslip_pdf(str(payslip_path), applicant_name, annual_income, discrepancy=is_discrepancy)

    bank_path = output_dir / f"BankStatement_{scenario}.pdf"
    generate_bank_statement_pdf(str(bank_path), applicant_name, annual_income, discrepancy=False)

    tax_path = output_dir / f"TaxReturn_{scenario}.pdf"
    generate_tax_return_pdf(str(tax_path), applicant_name, annual_income, discrepancy=is_discrepancy)

    kyc_path = output_dir / f"KYC_{scenario}.pdf"
    generate_kyc_pdf(str(kyc_path), applicant_name, discrepancy=False)

    return {
        "Payslip": payslip_path,
        "Bank Statement": bank_path,
        "Tax Return": tax_path,
        "KYC Document": kyc_path,
    }


if __name__ == "__main__":
    test_dir = Path(__file__).parent / "sample_docs"
    docs = generate_document_bundle(test_dir, "Aditi Sharma", 850000.0, "clean")
    print("Generated dummy documents successfully:", docs)
