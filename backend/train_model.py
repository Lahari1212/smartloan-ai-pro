import joblib
import pandas as pd
from pathlib import Path

from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.ensemble import RandomForestClassifier


BASE_DIR = Path(__file__).resolve().parent
DATASET_PATH = BASE_DIR / "loan_approval_dataset.csv"
MODEL_PATH = BASE_DIR / "loan_model.pkl"


def train_model_pipeline():
    print("Step 1: Reading dataset...", flush=True)
    if not DATASET_PATH.exists():
        raise FileNotFoundError(f"Dataset not found at {DATASET_PATH}")

    df = pd.read_csv(DATASET_PATH)
    df.columns = df.columns.str.strip()
    for col in df.columns:
        if df[col].dtype == object or str(df[col].dtype) == "string":
            df[col] = df[col].astype(str).str.strip()

    features = [
        "no_of_dependents",
        "education",
        "self_employed",
        "income_annum",
        "loan_amount",
        "loan_term",
        "cibil_score",
        "residential_assets_value",
        "commercial_assets_value",
        "luxury_assets_value",
        "bank_asset_value",
    ]
    target = "loan_status"

    X = df[features]
    y = df[target]

    print("Step 2: Building preprocessing pipelines...", flush=True)
    numerical_features = [
        "no_of_dependents",
        "income_annum",
        "loan_amount",
        "loan_term",
        "cibil_score",
        "residential_assets_value",
        "commercial_assets_value",
        "luxury_assets_value",
        "bank_asset_value",
    ]
    categorical_features = ["education", "self_employed"]

    numerical_pipeline = Pipeline(steps=[("imputer", SimpleImputer(strategy="median"))])
    categorical_pipeline = Pipeline(steps=[
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("encoder", OneHotEncoder(handle_unknown="ignore")),
    ])

    preprocessor = ColumnTransformer(transformers=[
        ("numerical", numerical_pipeline, numerical_features),
        ("categorical", categorical_pipeline, categorical_features),
    ])

    print("Step 3: Instantiating RandomForestClassifier...", flush=True)
    model = RandomForestClassifier(n_estimators=100, random_state=42, class_weight="balanced", n_jobs=1)
    pipeline = Pipeline(steps=[("preprocessor", preprocessor), ("model", model)])

    print("Step 4: Splitting and fitting...", flush=True)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    pipeline.fit(X_train, y_train)

    preds = pipeline.predict(X_test)
    acc = accuracy_score(y_test, preds)
    print(f"Step 5: Model trained successfully! Test Accuracy: {acc:.2%}", flush=True)

    joblib.dump(pipeline, MODEL_PATH)
    print(f"Model saved to {MODEL_PATH}", flush=True)
    return pipeline


if __name__ == "__main__":
    train_model_pipeline()