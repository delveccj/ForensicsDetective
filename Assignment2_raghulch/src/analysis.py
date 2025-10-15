import argparse
import json
import time
from collections import Counter, defaultdict
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import SGDClassifier
from sklearn.model_selection import StratifiedKFold
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from scipy import stats
from statsmodels.stats.contingency_tables import mcnemar

from classification import tune_mlp, tune_rf
from utils import (
    RANDOM_STATE,
    compute_metrics,
    load_dataset,
    save_confusion,
)

ASSIGN_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ASSIGN_DIR / "data"
RESULTS_DIR = ASSIGN_DIR / "results"
CONF_DIR = RESULTS_DIR / "confusion_matrices"
MODELS_DIR = RESULTS_DIR / "models"
LOGS_DIR = RESULTS_DIR / "logs"
RESULTS_CSV = RESULTS_DIR / "performance_metrics.csv"
STATS_JSON = RESULTS_DIR / "statistical_results.json"


def ensure_dirs():
    for d in [RESULTS_DIR, CONF_DIR, MODELS_DIR, LOGS_DIR]:
        d.mkdir(parents=True, exist_ok=True)


def make_svm():
    return SVC(kernel="rbf", C=1.0, gamma="scale", random_state=RANDOM_STATE)


def make_sgd():
    return SGDClassifier(loss="hinge", alpha=0.01, max_iter=1000, tol=1e-3, random_state=RANDOM_STATE)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--include-fifth",
        action="store_true",
        help="Include fifth_source_pdfs_png as a 5th class (bonus).",
    )
    args = ap.parse_args()

    ensure_dirs()

    # --- Load & scale ---
    X, y, class_names = load_dataset(DATA_DIR, include_fifth=args.include_fifth, target_size=(200, 200))
    scaler = StandardScaler()
    X = scaler.fit_transform(X)

    # --- Make robust to thin/empty classes after skipping corrupt PNGs ---
    orig_counts = Counter(y.tolist())
    print("[INFO] Class counts (original):", dict(orig_counts))

    # keep labels that have at least 2 samples
    valid_labels = sorted([lab for lab, n in orig_counts.items() if n >= 2])
    if len(valid_labels) < 2:
        raise RuntimeError(
            f"Not enough valid classes to train (need >=2). Counts: {dict(orig_counts)}. "
            "One or more folders may be nearly empty/corrupt."
        )

    # filter X/y and remap labels to 0..C-1
    keep_mask = np.isin(y, valid_labels)
    X = X[keep_mask]
    y = y[keep_mask]
    label_remap = {old: new for new, old in enumerate(valid_labels)}
    y = np.vectorize(label_remap.get)(y)
    class_names = [class_names[old] for old in valid_labels]

    # choose k so every class can appear in each fold
    per_class = Counter(y.tolist())
    min_per_class = min(per_class.values())
    k_folds = min(5, min_per_class)
    if k_folds < 2:
        raise RuntimeError(f"Cannot form >=2 folds; smallest class has {min_per_class} samples.")
    print(f"[INFO] Using StratifiedKFold with k={k_folds}. Kept classes & counts:", dict(per_class))

    # --- Task 4: tune & save two new classifiers (RF, MLP) ---
    print(">>> Tuning RandomForest")
    rf_best, rf_params = tune_rf(X, y, cv_splits=3, n_iter=30)
    print(">>> Tuning MLP")
    mlp_best, mlp_params = tune_mlp(X, y, cv_splits=3, n_iter=30)
    joblib.dump(rf_best, MODELS_DIR / "rf_best.pkl")
    joblib.dump(mlp_best, MODELS_DIR / "mlp_best.pkl")
    (RESULTS_DIR / "best_params_summary.json").write_text(json.dumps({"rf": rf_params, "mlp": mlp_params}, indent=2))

    # --- Task 5: train/evaluate all 4 models with SAME folds ---
    models = {"svm_rbf": make_svm(), "sgd_hinge": make_sgd(), "rf": rf_best, "mlp": mlp_best}

    def append_row(row):
        df = pd.DataFrame([row])
        header = not RESULTS_CSV.exists()
        df.to_csv(RESULTS_CSV, mode="a", index=False, header=header)

    skf = StratifiedKFold(n_splits=k_folds, shuffle=True, random_state=RANDOM_STATE)
    fold_acc = defaultdict(list)
    last_fold = {}

    for k, (tr, te) in enumerate(skf.split(X, y), start=1):
        Xtr, Xte = X[tr], X[te]
        ytr, yte = y[tr], y[te]
        for name, model in models.items():
            t0 = time.perf_counter()
            model.fit(Xtr, ytr)
            t1 = time.perf_counter()
            t2 = time.perf_counter()
            yhat = model.predict(Xte)
            t3 = time.perf_counter()
            m = compute_metrics(yte, yhat)
            append_row(
                dict(
                    model=name,
                    fold=k,
                    **m,
                    train_time_sec=t1 - t0,
                    predict_time_sec=t3 - t2,
                    n_test=len(yte),
                )
            )
            save_confusion(yte, yhat, class_names, f"{name} (fold {k})", CONF_DIR / f"{name}_fold{k}.png")
            fold_acc[name].append(m["accuracy"])
            if k == skf.get_n_splits():
                last_fold[name] = (yte.copy(), yhat.copy())

    # summary rows
    for name, accs in fold_acc.items():
        append_row(
            dict(
                model=name,
                fold="mean±std",
                accuracy=f"{np.mean(accs):.4f}±{np.std(accs):.4f}",
                precision_weighted="",
                recall_weighted="",
                f1_weighted="",
                train_time_sec="",
                predict_time_sec="",
                n_test="",
            )
        )

    # stats: paired t-tests + McNemar (last fold)
    stats_rows = []
    names = list(fold_acc.keys())
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = names[i], names[j]
            t, p = stats.ttest_rel(fold_acc[a], fold_acc[b])
            stats_rows.append({"test": "paired_t", "model_a": a, "model_b": b, "t_stat": float(t), "p_value": float(p)})

    def mcnemar_row(a, b):
        yt_a, yp_a = last_fold[a]
        yt_b, yp_b = last_fold[b]
        assert np.array_equal(yt_a, yt_b)
        a_ok = yp_a == yt_a
        b_ok = yp_b == yt_b
        n01 = int(np.sum((~a_ok) & b_ok))
        n10 = int(np.sum(a_ok & (~b_ok)))
        res = mcnemar([[0, n01], [n10, 0]], exact=True)
        return {
            "test": "mcnemar_last_fold",
            "model_a": a,
            "model_b": b,
            "statistic": float(res.statistic),
            "p_value": float(res.pvalue),
            "n01": n01,
            "n10": n10,
        }

    for a, b in [("svm_rbf", "rf"), ("svm_rbf", "mlp"), ("rf", "mlp")]:
        if a in last_fold and b in last_fold:
            stats_rows.append(mcnemar_row(a, b))

    STATS_JSON.write_text(json.dumps(stats_rows, indent=2))

    print("\nArtifacts:")
    print(f" - metrics CSV: {RESULTS_CSV}")
    print(f" - confusion matrices: {CONF_DIR}/*.png")
    print(f" - models: {MODELS_DIR/'rf_best.pkl'}, {MODELS_DIR/'mlp_best.pkl'}")
    print(f" - stats JSON: {STATS_JSON}")
    print("BONUS 5-class" if args.include_fifth else "Core 4-class")


if __name__ == "__main__":
    main()

