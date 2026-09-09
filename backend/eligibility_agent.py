from pathlib import Path

import joblib
import pandas as pd


BASE_DIR = Path(__file__).resolve().parent

MODEL_PATH = BASE_DIR / "loan_model.pkl"
DATASET_PATH = BASE_DIR / "loan_approval_dataset.csv"


if not MODEL_PATH.exists():
    raise FileNotFoundError(
        f"Trained model not found at {MODEL_PATH}. "
        "Run 'python train_model.py' first."
    )


model = joblib.load(MODEL_PATH)


def load_dataset():
    dataset = pd.read_csv(DATASET_PATH)

    dataset.columns = dataset.columns.str.strip()

    for column in dataset.select_dtypes(
        include=["object", "str"]
    ).columns:
        dataset[column] = dataset[column].str.strip()

    return dataset


def calculate_eligibility(
    annual_income,
    loan_amount,
    validation_result,
    applicant_name=None,
    loan_id=None,
):
    if not validation_result.get("is_valid", False):
        return {
            "status": "Manual Review",
            "risk_level": "High",
            "reason": "The uploaded document could not be validated.",
            "applicant_name": applicant_name,
            "dataset_loan_id": loan_id,
            "model_prediction": "Manual Review",
            "confidence": 0,
        }

    if loan_id is None:
        return {
            "status": "Manual Review",
            "risk_level": "Medium",
            "reason": "Loan ID is missing.",
            "applicant_name": applicant_name,
            "dataset_loan_id": None,
            "model_prediction": "Manual Review",
            "confidence": 0,
        }

    dataset = load_dataset()

    matching_record = dataset[
        dataset["loan_id"] == int(loan_id)
    ]

    if matching_record.empty:
        return {
            "status": "Manual Review",
            "risk_level": "Medium",
            "reason": "No matching loan record was found.",
            "applicant_name": applicant_name,
            "dataset_loan_id": loan_id,
            "model_prediction": "Manual Review",
            "confidence": 0,
        }

    record = matching_record.iloc[0]

    model_input = pd.DataFrame(
        [
            {
                "no_of_dependents": record["no_of_dependents"],
                "education": record["education"],
                "self_employed": record["self_employed"],
                "income_annum": float(annual_income),
                "loan_amount": float(loan_amount),
                "loan_term": record["loan_term"],
                "cibil_score": record["cibil_score"],
                "residential_assets_value": record[
                    "residential_assets_value"
                ],
                "commercial_assets_value": record[
                    "commercial_assets_value"
                ],
                "luxury_assets_value": record[
                    "luxury_assets_value"
                ],
                "bank_asset_value": record["bank_asset_value"],
            }
        ]
    )

    prediction = model.predict(model_input)[0]

    probabilities = model.predict_proba(model_input)[0]
    confidence = round(
        float(max(probabilities)) * 100,
        2,
    )

    prediction_text = str(prediction).strip()

    if prediction_text.lower() == "approved":
        status = "Eligible"
        risk_level = "Low"
        reason = (
            "The trained machine-learning model predicted "
            "that the application is likely to be approved."
        )
    else:
        status = "Not Eligible"
        risk_level = "High"
        reason = (
            "The trained machine-learning model predicted "
            "that the application is likely to be rejected."
        )

    return {
        "status": status,
        "risk_level": risk_level,
        "reason": reason,
        "applicant_name": applicant_name,
        "dataset_loan_id": int(loan_id),
        "model_prediction": prediction_text,
        "confidence": confidence,
    }