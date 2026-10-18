import pandas as pd
import numpy as np
import joblib
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder, OrdinalEncoder
from sklearn.pipeline import Pipeline
import shap

# 1. Dummy dataset generation matching the 11 features
np.random.seed(42)
n_samples = 200

data = {
    'Gender': np.random.choice(['Male', 'Female'], n_samples),
    'Age': np.random.randint(18, 30, n_samples),
    'Academic Pressure': np.random.randint(1, 6, n_samples),
    'CGPA': np.round(np.random.uniform(5.0, 10.0, n_samples), 2),
    'Study Satisfaction': np.random.randint(1, 6, n_samples),
    'Sleep Duration': np.random.choice(['Less than 5 hours', '5-6 hours', '7-8 hours', 'More than 8 hours'], n_samples),
    'Dietary Habits': np.random.choice(['Healthy', 'Moderate', 'Unhealthy'], n_samples),
    'Degree': np.random.choice(['B.Tech', 'BCA', 'B.Sc', 'B.Com'], n_samples),
    'Work/Study Hours': np.random.randint(2, 12, n_samples),
    'Financial Stress': np.random.randint(1, 6, n_samples),
    'Family History of Mental Illness': np.random.choice(['Yes', 'No'], n_samples),
    'Depression': np.random.choice([0, 1], n_samples)
}

df = pd.DataFrame(data)
X = df.drop(columns=['Depression'])
y = df['Depression']

# Preprocessing pipeline setup
num_cols = ['Age', 'Academic Pressure', 'CGPA', 'Study Satisfaction', 'Work/Study Hours', 'Financial Stress']
cat_cols = ['Gender', 'Degree', 'Family History of Mental Illness']
ord_cols = ['Sleep Duration', 'Dietary Habits']

sleep_order = ['Less than 5 hours', '5-6 hours', '7-8 hours', 'More than 8 hours']
diet_order = ['Unhealthy', 'Moderate', 'Healthy']

preprocessor = ColumnTransformer(
    transformers=[
        ('num', StandardScaler(), num_cols),
        ('cat', OneHotEncoder(handle_unknown='ignore', sparse_output=False), cat_cols),
        ('ord', OrdinalEncoder(categories=[sleep_order, diet_order], handle_unknown='use_encoded_value', unknown_value=-1), ord_cols)
    ]
)

X_trans = preprocessor.fit_transform(X)

# Model training
model = RandomForestClassifier(n_estimators=50, random_state=42)
model.fit(X_trans, y)

# Save preprocessor and model
joblib.dump(preprocessor, 'mindbridge_preprocessing_pipeline.joblib')
joblib.dump(model, 'mindbridge_random_forest.joblib')
joblib.dump(X.columns.tolist(), 'mindbridge_feature_names.joblib')

# SHAP explainer setup
explainer = shap.TreeExplainer(model)
joblib.dump(explainer, 'mindbridge_shap_explainer.joblib')

print("Successfully regenerated all joblib files for Python 3.14 / latest scikit-learn!")