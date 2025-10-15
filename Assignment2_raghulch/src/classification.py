from pathlib import Path
import json
from typing import Dict, Any, Tuple

import joblib
from scipy.stats import randint, loguniform
from sklearn.model_selection import StratifiedKFold, RandomizedSearchCV
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.neural_network import MLPClassifier

RANDOM_STATE = 42
RESULTS_DIR = Path(__file__).resolve().parents[1] / "results"
MODELS_DIR = RESULTS_DIR / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)


def build_rf() -> Pipeline:
    # Ensemble category
    return Pipeline([("rf", RandomForestClassifier(random_state=RANDOM_STATE, n_jobs=-1))])


def tune_rf(X, y, cv_splits=3, n_iter=30) -> Tuple[Pipeline, Dict[str, Any]]:
    """Randomized tuning over RF hyperparameters."""
    param_dist = {
        "rf__n_estimators": randint(300, 900),
        "rf__max_depth": randint(6, 40),
        "rf__min_samples_split": randint(2, 20),
        "rf__min_samples_leaf": randint(1, 10),
        "rf__max_features": ["sqrt", "log2", None],
        "rf__bootstrap": [True, False],
    }
    cv = StratifiedKFold(n_splits=cv_splits, shuffle=True, random_state=RANDOM_STATE)
    search = RandomizedSearchCV(
        build_rf(),
        param_distributions=param_dist,
        n_iter=n_iter,
        scoring="accuracy",
        n_jobs=-1,
        cv=cv,
        random_state=RANDOM_STATE,
        verbose=1,
    )
    search.fit(X, y)
    joblib.dump(search.best_estimator_, MODELS_DIR / "rf_best.pkl")
    (RESULTS_DIR / "best_params_rf.json").write_text(json.dumps(search.best_params_, indent=2))
    return search.best_estimator_, search.best_params_


def build_mlp() -> Pipeline:
    # Neural Net category (requires scaling)
    return Pipeline(
        [("scaler", StandardScaler()), ("mlp", MLPClassifier(random_state=RANDOM_STATE, max_iter=400))]
    )


def tune_mlp(X, y, cv_splits=3, n_iter=30) -> Tuple[Pipeline, Dict[str, Any]]:
    """Randomized tuning over MLP architecture & regularization."""
    param_dist = {
        "mlp__hidden_layer_sizes": [(256,), (512,), (256, 128), (512, 256)],
        "mlp__alpha": loguniform(1e-6, 1e-2),
        "mlp__learning_rate_init": loguniform(1e-4, 5e-3),
        "mlp__activation": ["relu", "tanh"],
        "mlp__batch_size": [128, 256],
        "mlp__solver": ["adam", "sgd"],
        "mlp__beta_1": [0.8, 0.9, 0.99],
        "mlp__beta_2": [0.999, 0.98],
    }
    cv = StratifiedKFold(n_splits=cv_splits, shuffle=True, random_state=RANDOM_STATE)
    search = RandomizedSearchCV(
        build_mlp(),
        param_distributions=param_dist,
        n_iter=n_iter,
        scoring="accuracy",
        n_jobs=-1,
        cv=cv,
        random_state=RANDOM_STATE,
        verbose=1,
    )
    search.fit(X, y)
    joblib.dump(search.best_estimator_, MODELS_DIR / "mlp_best.pkl")
    (RESULTS_DIR / "best_params_mlp.json").write_text(json.dumps(search.best_params_, indent=2))
    return search.best_estimator_, search.best_params_


# Optional standalone runner (Task 4 only). Safe to leave; analysis.py is still main entrypoint.
if __name__ == "__main__":
    from sklearn.preprocessing import StandardScaler
    from utils import load_dataset

    ASSIGN_DIR = Path(__file__).resolve().parents[1]
    DATA_DIR = ASSIGN_DIR / "data"

    X, y, _ = load_dataset(DATA_DIR, include_fifth=False, target_size=(200, 200))
    X = StandardScaler().fit_transform(X)
    rf_best, rf_params = tune_rf(X, y, cv_splits=3, n_iter=30)
    mlp_best, mlp_params = tune_mlp(X, y, cv_splits=3, n_iter=30)
    (RESULTS_DIR / "best_params_summary.json").write_text(
        json.dumps({"rf": rf_params, "mlp": mlp_params}, indent=2)
    )
    print("Saved:", MODELS_DIR / "rf_best.pkl", MODELS_DIR / "mlp_best.pkl")
