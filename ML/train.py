from pathlib import Path

import joblib
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, roc_auc_score
from sklearn.model_selection import GroupShuffleSplit
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

FOLDER = Path(__file__).parent
FEATURES = ["acute_load", "chronic_load", "acwr", "sleep_avg", "fatigue_avg", "stress_avg"]

df = pd.read_csv(FOLDER / "synthetic_data.csv")
X = df[FEATURES]
y = df["injury_next_7d"]

# On sépare par athlète (pas par ligne) pour ne pas tricher
splitter = GroupShuffleSplit(n_splits=1, test_size=0.25, random_state=42)
train_idx, test_idx = next(splitter.split(X, y, groups=df["athlete_id"]))
X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]

model = make_pipeline(
    StandardScaler(),
    LogisticRegression(class_weight="balanced", max_iter=1000),
)
model.fit(X_train, y_train)

proba = model.predict_proba(X_test)[:, 1]
pred = (proba >= 0.5).astype(int)

print("AUC :", round(roc_auc_score(y_test, proba), 3))
print(classification_report(y_test, pred, digits=3))

joblib.dump(
    {"model": model, "features": FEATURES, "version": "v1"},
    FOLDER / "model.pkl",
)
print("Modèle sauvegardé : ml/model.pkl")