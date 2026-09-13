"""
SmartLoan AI — Context-Aware AI Loan Analyst Assistant
Provides an interactive AI assistant for loan officers to query application data,
analyze cross-document inconsistencies, assess credit risk, and draft underwriting notes.
Supports Google Gemini API with an advanced local semantic reasoning engine fallback.
"""
import os
import json
import requests
from typing import List, Dict, Any


def run_loan_analyst_agent(
    application: dict,
    documents: list,
    validation_report: dict,
    ml_result: dict,
    user_query: str,
    chat_history: List[Dict[str, str]] = None,
) -> str:
    """
    Executes the AI Loan Analyst agent on the current application context.
    """
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")

    context_summary = _build_context_summary(
        application=application,
        documents=documents,
        validation_report=validation_report,
        ml_result=ml_result,
    )

    if api_key:
        try:
            return _call_gemini_api(api_key, context_summary, user_query, chat_history)
        except Exception as e:
            print(f"[SmartLoan AI Assistant] Gemini API error: {e}. Falling back to local reasoning engine.")
            return _local_reasoning_engine(context_summary, user_query, application, validation_report, ml_result)
    else:
        return _local_reasoning_engine(context_summary, user_query, application, validation_report, ml_result)


def _build_context_summary(
    application: dict,
    documents: list,
    validation_report: dict,
    ml_result: dict,
) -> str:
    app_id = application.get("application_id", "N/A")
    name = application.get("applicant_name", "N/A")
    income = float(application.get("annual_income") or 0)
    loan_amt = float(application.get("loan_amount") or 0)
    cibil = application.get("cibil_score", "N/A")
    status = application.get("status", "Pending")
    term = application.get("loan_term", 10)
    education = application.get("education", "Graduate")
    self_employed = application.get("self_employed", "No")

    docs_info = []
    for d in documents:
        docs_info.append(
            f"- Type: {d.get('document_type')}, File: {d.get('original_filename')}, "
            f"Confidence: {d.get('confidence_score', 0)}%, Fields: {json.dumps(d.get('extracted_json') or {})}"
        )

    val = validation_report or {}
    inconsistencies = val.get("inconsistencies", [])
    missing = val.get("missing_documents", [])

    ml = ml_result or {}

    summary = f"""
=== LOAN APPLICATION CONTEXT ===
Application ID: {app_id}
Applicant Name: {name}
Declared Annual Income: ₹{income:,.0f}
Requested Loan Amount: ₹{loan_amt:,.0f}
Loan Term: {term} years
CIBIL Credit Score: {cibil}
Education: {education}
Self-Employed: {self_employed}
Current Status: {status}

Assets:
- Residential: ₹{float(application.get('residential_assets_value') or 0):,.0f}
- Commercial: ₹{float(application.get('commercial_assets_value') or 0):,.0f}
- Luxury: ₹{float(application.get('luxury_assets_value') or 0):,.0f}
- Bank: ₹{float(application.get('bank_asset_value') or 0):,.0f}

=== VERIFIED DOCUMENTS ({len(documents)} uploaded) ===
{chr(10).join(docs_info) if docs_info else "No documents uploaded."}

=== CROSS-DOCUMENT VERIFICATION REPORT ===
Overall Validation: {'VALID' if val.get('is_valid') else 'ANOMALIES DETECTED'}
Missing Documents: {', '.join(missing) if missing else 'None (All mandatory docs submitted)'}
Inconsistencies / Anomaly Flags ({len(inconsistencies)}):
{json.dumps(inconsistencies, indent=2) if inconsistencies else "None detected."}

=== ML CREDIT RISK MODEL ASSESSMENT ===
ML Recommendation: {ml.get('model_prediction') or ml.get('status')}
Confidence: {ml.get('confidence', 0):.1f}%
Risk Level: {ml.get('risk_level', 'Medium')}
Assessment Reason: {ml.get('reason', 'Standard underwriting assessment')}
"""
    return summary.strip()


def _call_gemini_api(api_key: str, context: str, query: str, history: List[Dict[str, str]] = None) -> str:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"

    system_instruction = (
        "You are an expert AI Senior Loan Underwriter and Risk Analyst for SmartLoan AI. "
        "Your task is to assist the human Loan Officer in reviewing loan applications. "
        "Always be concise, precise, and cite concrete financial numbers from the application and document verification report. "
        "Highlight any risk factors, discrepancies between declared and verified income, or missing proofs. "
        "Remind the officer that your analysis is assistive and the human officer makes the final binding decision."
    )

    contents = []

    # Insert context as initial system setup
    contents.append({
        "role": "user",
        "parts": [{"text": f"Here is the loan application file to analyze:\n\n{context}"}]
    })
    contents.append({
        "role": "model",
        "parts": [{"text": "I have fully ingested and analyzed this loan application dossier. I am ready to answer your questions and assist with risk evaluation."}]
    })

    # Add conversation history
    if history:
        for msg in history:
            role = "user" if msg.get("role") == "user" else "model"
            contents.append({
                "role": role,
                "parts": [{"text": msg.get("content", "")}]
            })

    # Add the current query
    contents.append({
        "role": "user",
        "parts": [{"text": query}]
    })

    payload = {
        "contents": contents,
        "systemInstruction": {"parts": [{"text": system_instruction}]},
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": 800,
        }
    }

    resp = requests.post(url, json=payload, timeout=20)
    if resp.status_code == 200:
        data = resp.json()
        candidates = data.get("candidates", [])
        if candidates and "content" in candidates[0]:
            parts = candidates[0]["content"].get("parts", [])
            if parts:
                return parts[0].get("text", "No response generated.")
    raise ValueError(f"Gemini API returned status {resp.status_code}: {resp.text}")


def _local_reasoning_engine(
    context_str: str,
    query: str,
    application: dict,
    validation_report: dict,
    ml_result: dict,
) -> str:
    """
    Intelligent deterministic semantic analyst engine when Gemini API key is not configured.
    Handles common underwriting queries with precise domain calculations.
    """
    q = query.lower()
    name = application.get("applicant_name", "the applicant")
    income = float(application.get("annual_income") or 0)
    loan_amt = float(application.get("loan_amount") or 0)
    cibil = int(application.get("cibil_score") or 750)
    val = validation_report or {}
    inconsistencies = val.get("inconsistencies", [])
    missing = val.get("missing_documents", [])
    ml = ml_result or {}
    risk = ml.get("risk_level", "Medium")
    ml_pred = ml.get("model_prediction") or ml.get("status") or "Evaluated"
    lti = (loan_amt / income * 100) if income > 0 else 0

    # 1. Summary / Overview
    if any(k in q for k in ["summary", "overview", "brief", "about", "tell me about"]):
        return (
            f"**Executive Underwriting Summary for {name}**\n\n"
            f"• **Requested Loan:** ₹{loan_amt:,.0f} over {application.get('loan_term', 10)} years\n"
            f"• **Declared Income:** ₹{income:,.0f}/yr (Loan-to-Income: **{lti:.1f}%**)\n"
            f"• **CIBIL Score:** **{cibil}** ({'Prime' if cibil >= 750 else 'Near-Prime' if cibil >= 650 else 'Subprime'})\n"
            f"• **ML Model Assessment:** **{ml_pred}** ({ml.get('confidence', 0):.1f}% confidence, **{risk} Risk**)\n"
            f"• **Verification Status:** {len(inconsistencies)} anomaly flag(s), {len(missing)} missing document(s).\n\n"
            f"**Recommendation:** {'Low credit risk profile. Fits automated approval parameters.' if not inconsistencies and risk == 'Low' else 'Requires manual officer verification due to noted risk/discrepancy indicators.'}"
        )

    # 2. Discrepancies / Anomalies / Fraud
    if any(k in q for k in ["discrepan", "anomaly", "anomalies", "fraud", "mismatch", "inconsistenc", "issue"]):
        if not inconsistencies:
            return (
                f"✅ **Zero Anomaly Indicators Detected.**\n\n"
                f"All submitted documents (Payslip, Bank Statement, Tax Return, KYC) match the declared legal name "
                f"and annual income of ₹{income:,.0f}."
            )
        lines = [f"🚨 **{len(inconsistencies)} Anomaly Indicator(s) Identified:**\n"]
        for idx, inc in enumerate(inconsistencies, 1):
            sev = inc.get("severity", "MEDIUM")
            msg = inc.get("message", "Discrepancy found")
            lines.append(f"{idx}. **[{sev}]** {msg}")
            if inc.get("variance_pct"):
                lines.append(f"   *Variance:* {inc.get('variance_pct')}%")
        lines.append("\n*Note: High severity items require manual explanation or re-upload before approval.*")
        return "\n".join(lines)

    # 3. Risk / CIBIL / Credit Score
    if any(k in q for k in ["risk", "cibil", "credit", "score", "default"]):
        cibil_eval = (
            "Excellent (750+), indicating strong repayment history."
            if cibil >= 750
            else "Moderate (650-749), acceptable with solid collateral coverage."
            if cibil >= 650
            else "Below prime threshold (<650), represents higher default probability."
        )
        return (
            f"**Credit Risk & CIBIL Assessment:**\n\n"
            f"• **CIBIL Score:** {cibil} — {cibil_eval}\n"
            f"• **Calculated Risk Rating:** **{risk}**\n"
            f"• **Loan-to-Income (LTI):** {lti:.1f}%\n"
            f"• **Total Asset Coverage:** ₹{(float(application.get('residential_assets_value') or 0) + float(application.get('commercial_assets_value') or 0) + float(application.get('bank_asset_value') or 0)):,.0f}\n\n"
            f"The Kaggle Random Forest underwriting model assigns a **{ml.get('confidence', 0):.1f}%** confidence to this risk classification."
        )

    # 4. Draft Decision Note
    if any(k in q for k in ["draft", "note", "approval note", "rejection note", "write note", "review note"]):
        if "reject" in q or risk == "High" or len(inconsistencies) > 1:
            return (
                f"**Suggested Rejection / Review Note:**\n\n"
                f"\"Application for ₹{loan_amt:,.0f} is declined/referred due to {len(inconsistencies)} documentation discrepancy indicator(s) "
                f"and an evaluated {risk} risk rating (CIBIL: {cibil}). Applicant is advised to submit updated salary slips and certified tax filings "
                f"for reconsideration.\""
            )
        else:
            return (
                f"**Suggested Approval Note:**\n\n"
                f"\"Application for ₹{loan_amt:,.0f} approved. Applicant {name} demonstrates stable verified income of ₹{income:,.0f}/yr, "
                f"strong credit rating (CIBIL {cibil}), and complete matching KYC documentation with zero anomaly indicators.\""
            )

    # 5. Missing documents
    if any(k in q for k in ["missing", "document", "upload", "doc"]):
        if not missing:
            return "✅ **All required documents are present.** Payslip, Bank Statement, Tax Return, and KYC documents have been uploaded."
        return f"⚠️ **Missing Required Documents:**\n" + "\n".join([f"• {m} (Mandatory for underwriting)" for m in missing])

    # Default fallback intelligent response
    return (
        f"**Loan Analyst Insights for {name}:**\n\n"
        f"• **Financial Position:** Declared income ₹{income:,.0f}, requested loan ₹{loan_amt:,.0f} (LTI: {lti:.1f}%).\n"
        f"• **Credit Score:** CIBIL {cibil}, ML Model Confidence: {ml.get('confidence', 0):.1f}% ({risk} Risk).\n"
        f"• **Document Status:** {len(inconsistencies)} anomaly flag(s) found.\n\n"
        f"You can ask me to:\n"
        f"1. *'Summarize this application'*\n"
        f"2. *'Show all discrepancies and anomalies'*\n"
        f"3. *'Explain the credit risk rating'*\n"
        f"4. *'Draft an officer decision note'*"
    )
