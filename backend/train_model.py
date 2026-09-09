import joblib
import pandas as pd

from pathlib import Path

from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.ensemble import RandomForestClassifier


BASE_DIR = Path(__file__).parent

DATASET_PATH = BASE_DIR / "loan_approval_dataset.csv"
MODEL_PATH = BASE_DIR / "loan_model.pkl"


# 1. Load dataset
df = pd.read_csv(DATASET_PATH)

# 2. Remove unwanted spaces from column names and text values
df.columns = df.columns.str.strip()

for column in df.select_dtypes(include=["object"]).columns:
    df[column] = df[column].str.strip()


# 3. Select useful features
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


# 4. Separate numerical and categorical columns
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

categorical_features = [
    "education",
    "self_employed",
]


# 5. Preprocess numerical and categorical data
numerical_pipeline = Pipeline(
    steps=[
        ("imputer", SimpleImputer(strategy="median")),
    ]
)

categorical_pipeline = Pipeline(
    steps=[
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("encoder", OneHotEncoder(handle_unknown="ignore")),
    ]
)

preprocessor = ColumnTransformer(
    transformers=[
        ("numerical", numerical_pipeline, numerical_features),
        ("categorical", categorical_pipeline, categorical_features),
    ]
)


# 6. Create the machine-learning model
model = RandomForestClassifier(
    n_estimators=200,
    random_state=42,
    class_weight="balanced",
)


# 7. Combine preprocessing and model
model_pipeline = Pipeline(
    steps=[
        ("preprocessor", preprocessor),
        ("model", model),
    ]
)


# 8. Split the dataset
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42,
    stratify=y,
)


# 9. Train the model
print("Training the loan approval model...")

model_pipeline.fit(X_train, y_train)


# 10. Test the model
predictions = model_pipeline.predict(X_test)

accuracy = accuracy_score(y_test, predictions)

print(f"Model accuracy: {accuracy:.2%}")
print("\nClassification report:")
print(classification_report(y_test, predictions))


# 11. Save the trained model
joblib.dump(model_pipeline, MODEL_PATH)

print(f"\nModel saved successfully at: {MODEL_PATH}")