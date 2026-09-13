"""
SmartLoan AI — Official Loan Underwriting & Decision PDF Report Generator
Generates a structured, publication-ready PDF summary for loan officer reviews and audits.
"""
from io import BytesIO
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable


def generate_underwriting_pdf(
    application: dict,
    documents: list,
    validation_report: dict = None,
    ml_result: dict = None,
    audit_log: list = None,
) -> BytesIO:
    """
    Generates a PDF bytes buffer containing the full underwriting dossier.
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40,
    )

    styles = getSampleStyleSheet()

    # Custom styles
    primary_color = colors.HexColor("#1E3A8A")
    secondary_color = colors.HexColor("#2563EB")
    dark_text = colors.HexColor("#0F172A")
    muted_text = colors.HexColor("#64748B")

    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=primary_color,
        spaceAfter=4,
    )

    subtitle_style = ParagraphStyle(
        "DocSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        textColor=muted_text,
        spaceAfter=15,
    )

    section_heading = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=16,
        textColor=primary_color,
        spaceBefore=12,
        spaceAfter=6,
    )

    body_style = ParagraphStyle(
        "BodyTextCustom",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=dark_text,
    )

    bold_body = ParagraphStyle(
        "BoldBody",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=13,
        textColor=dark_text,
    )

    story = []

    # 1. Header Banner
    story.append(Paragraph("SMARTLOAN AI • LOAN UNDERWRITING DOSSIER", subtitle_style))
    story.append(Paragraph("Official Loan Assessment & Decision Report", title_style))
    story.append(Paragraph(f"Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')} UTC", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=primary_color, spaceAfter=15))

    # 2. Key Status Box
    status = application.get("status", "Pending")
    decision_color = (
        colors.HexColor("#166534") if "approved" in status.lower()
        else colors.HexColor("#991B1B") if "rejected" in status.lower()
        else colors.HexColor("#92400E")
    )
    status_bg = (
        colors.HexColor("#DCFCE7") if "approved" in status.lower()
        else colors.HexColor("#FEE2E2") if "rejected" in status.lower()
        else colors.HexColor("#FEF3C7")
    )

    status_data = [
        [
            Paragraph("<b>Application ID:</b>", body_style),
            Paragraph(str(application.get("application_id", "—")), bold_body),
            Paragraph("<b>Final Status:</b>", body_style),
            Paragraph(f"<font color='{decision_color.hexval()}'><b>{status.upper()}</b></font>", bold_body),
        ],
        [
            Paragraph("<b>Applicant Name:</b>", body_style),
            Paragraph(str(application.get("applicant_name", "—")), bold_body),
            Paragraph("<b>Reviewer:</b>", body_style),
            Paragraph(str(application.get("reviewed_by") or "Automated AI Pipeline"), body_style),
        ],
    ]
    status_table = Table(status_data, colWidths=[100, 160, 90, 180])
    status_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#E2E8F0")),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(status_table)
    story.append(Spacer(1, 10))

    # 3. Application Financial Details
    story.append(Paragraph("1. Financial & Credit Profile", section_heading))
    loan_amount = float(application.get("loan_amount") or 0)
    income = float(application.get("annual_income") or 0)
    lti = (loan_amount / income * 100) if income > 0 else 0

    fin_data = [
        [
            Paragraph("<b>Requested Loan:</b>", body_style),
            Paragraph(f"₹{loan_amount:,.2f}", bold_body),
            Paragraph("<b>Annual Income:</b>", body_style),
            Paragraph(f"₹{income:,.2f}", bold_body),
        ],
        [
            Paragraph("<b>Loan Term:</b>", body_style),
            Paragraph(f"{application.get('loan_term', 10)} Years", body_style),
            Paragraph("<b>CIBIL Score:</b>", body_style),
            Paragraph(str(application.get("cibil_score", 750)), bold_body),
        ],
        [
            Paragraph("<b>Loan-to-Income:</b>", body_style),
            Paragraph(f"{lti:.1f}%", bold_body),
            Paragraph("<b>Employment / Edu:</b>", body_style),
            Paragraph(f"{application.get('self_employed', 'No')} Self-Employed / {application.get('education', 'Graduate')}", body_style),
        ],
        [
            Paragraph("<b>Residential Assets:</b>", body_style),
            Paragraph(f"₹{float(application.get('residential_assets_value') or 0):,.2f}", body_style),
            Paragraph("<b>Bank Asset Value:</b>", body_style),
            Paragraph(f"₹{float(application.get('bank_asset_value') or 0):,.2f}", body_style),
        ],
    ]
    fin_table = Table(fin_data, colWidths=[110, 150, 110, 160])
    fin_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ('PADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(fin_table)
    story.append(Spacer(1, 10))

    # 4. Verified Document Repository
    story.append(Paragraph(f"2. Verified Document Repository ({len(documents)} items)", section_heading))
    doc_rows = [[
        Paragraph("<b>Document Type</b>", bold_body),
        Paragraph("<b>Filename</b>", bold_body),
        Paragraph("<b>Class Conf.</b>", bold_body),
        Paragraph("<b>Extraction Conf.</b>", bold_body),
    ]]
    for d in documents:
        doc_rows.append([
            Paragraph(d.get("document_type", "Unknown"), body_style),
            Paragraph(d.get("original_filename", "—")[:30], body_style),
            Paragraph(f"{d.get('classification_confidence', 0):.1f}%", body_style),
            Paragraph(f"{d.get('confidence_score', 0):.1f}%", body_style),
        ])

    doc_table = Table(doc_rows, colWidths=[130, 220, 90, 90])
    doc_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#F1F5F9")),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ('PADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(doc_table)
    story.append(Spacer(1, 10))

    # 5. ML Model Risk Assessment & Cross-Validation
    story.append(Paragraph("3. AI Underwriting & Anomaly Analysis", section_heading))
    ml = ml_result or {}
    val = validation_report or {}
    inconsistencies = val.get("inconsistencies", [])

    ml_data = [
        [
            Paragraph("<b>ML Model Recommendation:</b>", body_style),
            Paragraph(str(ml.get("model_prediction") or ml.get("status") or "Evaluated"), bold_body),
            Paragraph("<b>Model Confidence:</b>", body_style),
            Paragraph(f"{ml.get('confidence', 0):.1f}%", bold_body),
        ],
        [
            Paragraph("<b>Calculated Risk Level:</b>", body_style),
            Paragraph(str(ml.get("risk_level", "Medium")), bold_body),
            Paragraph("<b>Anomalies Detected:</b>", body_style),
            Paragraph(f"{len(inconsistencies)} Flag(s)", bold_body),
        ],
    ]
    ml_table = Table(ml_data, colWidths=[150, 120, 130, 130])
    ml_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ('PADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(ml_table)

    if inconsistencies:
        story.append(Spacer(1, 6))
        for idx, inc in enumerate(inconsistencies[:4], 1):
            sev = inc.get("severity", "MEDIUM")
            msg = inc.get("message", "Anomaly detected")
            story.append(Paragraph(
                f"• <font color='#991B1B'><b>[{sev}]</b></font> {msg}",
                body_style
            ))

    # 6. Officer Decision & Review Notes
    story.append(Spacer(1, 10))
    story.append(Paragraph("4. Human Loan Officer Review & Binding Decision", section_heading))
    notes = application.get("review_notes") or "Standard automated assessment — no special officer remarks recorded."
    decision_rows = [
        [
            Paragraph("<b>Final Decision:</b>", bold_style if 'bold_style' in locals() else bold_body),
            Paragraph(f"<font color='{decision_color.hexval()}'><b>{status}</b></font>", bold_body),
        ],
        [
            Paragraph("<b>Reviewed By:</b>", body_style),
            Paragraph(str(application.get("reviewed_by") or "Officer Assigned"), body_style),
        ],
        [
            Paragraph("<b>Decision Timestamp:</b>", body_style),
            Paragraph(str(application.get("reviewed_at") or datetime.now().strftime("%Y-%m-%d %H:%M")), body_style),
        ],
        [
            Paragraph("<b>Reviewer Notes:</b>", body_style),
            Paragraph(notes, body_style),
        ],
    ]
    dec_table = Table(decision_rows, colWidths=[120, 410])
    dec_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#CBD5E1")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(dec_table)

    # 7. Regulatory Disclaimer & Signoff
    story.append(Spacer(1, 15))
    story.append(HRFlowable(width="100%", thickness=0.5, color=muted_text, spaceAfter=8))
    disclaimer = (
        "<b>COMPLIANCE NOTICE:</b> SmartLoan AI provides assistive extraction, cross-document verification, "
        "and ML underwriting indicators. The final loan determination is executed by an authorized human loan officer in "
        "accordance with applicable lending and credit regulations."
    )
    story.append(Paragraph(disclaimer, ParagraphStyle("Discl", parent=styles["Normal"], fontSize=7.5, leading=10, textColor=muted_text)))

    doc.build(story)
    buffer.seek(0)
    return buffer
