import warnings
warnings.filterwarnings('ignore')
import joblib
import pandas as pd
from pathlib import Path

# ---------------------------------------------------------
# MindBridge ML inference module
# Uses the four artifacts produced by the Colab ML pipeline.
# ---------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent

MODEL_FILE = BASE_DIR / "mindbridge_random_forest.joblib"
PREPROCESSOR_FILE = BASE_DIR / "mindbridge_preprocessing_pipeline.joblib"
FEATURE_NAMES_FILE = BASE_DIR / "mindbridge_feature_names.joblib"
SHAP_EXPLAINER_FILE = BASE_DIR / "mindbridge_shap_explainer.joblib"

model = joblib.load(MODEL_FILE)
preprocessor = joblib.load(PREPROCESSOR_FILE)
feature_names = joblib.load(FEATURE_NAMES_FILE)
shap_explainer = joblib.load(SHAP_EXPLAINER_FILE)

RAW_COLUMNS = [
    "Gender",
    "Age",
    "Academic Pressure",
    "CGPA",
    "Study Satisfaction",
    "Sleep Duration",
    "Dietary Habits",
    "Degree",
    "Work/Study Hours",
    "Financial Stress",
    "Family History of Mental Illness",
]


def clean_feature_name(name):
    """Convert saved sklearn feature names into user-facing names."""
    name = str(name)

    if name.startswith("binary__"):
        name = name.replace("binary__", "")

        if name.endswith("_Male"):
            return "Gender"

        if name.endswith("_Yes"):
            return name.replace("_Yes", "")

        return name

    if name.startswith("ordinal__"):
        return name.replace("ordinal__", "")

    if name.startswith("numeric__"):
        return name.replace("numeric__", "")

    if name.startswith("nominal__Degree_"):
        return "Degree: " + name.replace("nominal__Degree_", "")

    return name


def get_risk_level(risk_probability):
    """
    Project-defined display bands.

    These bands are only for the application's Low/Moderate/High
    display. They are NOT clinical or medical thresholds.
    """
    if risk_probability < 0.33:
        return "Low"
    elif risk_probability < 0.67:
        return "Moderate"
    else:
        return "High"


def predict_wellbeing(raw_student):
    """
    Run the complete MindBridge inference pipeline.

    Parameters
    ----------
    raw_student : dict or pandas.DataFrame
        The 11 raw assessment inputs.

    Returns
    -------
    dict
        risk_score
        risk_level
        important_factors
        shap_factors
    """

    # Accept either a dictionary or a one-row DataFrame.
    if isinstance(raw_student, dict):
        raw_student = pd.DataFrame([raw_student])
    elif isinstance(raw_student, pd.DataFrame):
        raw_student = raw_student.copy()
    else:
        raise TypeError(
            "raw_student must be a dictionary or pandas DataFrame."
        )

    # Check that all 11 expected inputs are present.
    missing = [column for column in RAW_COLUMNS if column not in raw_student.columns]

    if missing:
        raise ValueError(
            f"Missing required input columns: {missing}"
        )

    # Keep only the exact ML input columns in the established order.
    raw_student = raw_student[RAW_COLUMNS]

    # Raw 11 inputs -> 38 processed features.
    processed_student = preprocessor.transform(raw_student)

    # Random Forest class-1 probability.
    risk_probability = float(
        model.predict_proba(processed_student)[0, 1]
    )

    risk_level = get_risk_level(risk_probability)

    # SHAP explanation for the same processed input.
    shap_result = shap_explainer(processed_student)
    values = shap_result.values

    # The verified SHAP artifact returns (samples, features, classes).
    if values.ndim == 3:
        shap_values = values[0, :, 1]
    else:
        shap_values = values[0]

    # Dynamic feature names length alignment
    num_features = min(len(feature_names), len(shap_values))
    
    explanation = pd.DataFrame({
        "Feature": feature_names[:num_features],
        "SHAP Value": shap_values[:num_features],
    })

    explanation["Feature"] = explanation["Feature"].apply(clean_feature_name)
    explanation["Absolute SHAP"] = explanation["SHAP Value"].abs()

    explanation = explanation.sort_values(
        "Absolute SHAP",
        ascending=False
    ).reset_index(drop=True)

    # Keep the top 10 SHAP factors for the result/LLM layer.
    shap_factors = []

    for _, row in explanation.head(10).iterrows():
        value = float(row["SHAP Value"])

        shap_factors.append({
            "feature": row["Feature"],
            "shap_value": round(value, 6),
            "direction": "increases" if value > 0 else "decreases",
        })

    return {
        "risk_score": round(risk_probability, 3),
        "risk_level": risk_level,
        "important_factors": [
            factor["feature"] for factor in shap_factors[:5]
        ],
        "shap_factors": shap_factors,
    }


if __name__ == "__main__":
    print("MindBridge ML module loaded successfully.")
    print(f"Expected raw inputs: {len(RAW_COLUMNS)}")
    print(f"Processed features: {len(feature_names)}")
