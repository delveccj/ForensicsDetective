# src/utils.py
from __future__ import annotations
import os, itertools
from pathlib import Path
from typing import Tuple, List
import numpy as np

from PIL import Image, ImageFile
ImageFile.LOAD_TRUNCATED_IMAGES = True  # tolerate slightly truncated PNGs

from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import (
    confusion_matrix,
    accuracy_score,
    precision_recall_fscore_support,
)

# Global config (imported by analysis.py)

RANDOM_STATE = int(os.getenv("RANDOM_STATE", "42"))
CV_FOLDS     = int(os.getenv("CV_FOLDS", "5"))
TEST_SIZE    = float(os.getenv("TEST_SIZE", "0.2"))

def get_splitter() -> StratifiedKFold:
    """Deterministic StratifiedKFold used by ALL models to keep splits identical."""
    return StratifiedKFold(n_splits=CV_FOLDS, shuffle=True, random_state=RANDOM_STATE)

# Image dataset loading
def load_png_dir(
    dirpath: Path,
    label: int,
    target_size: Tuple[int, int] = (200, 200),
) -> Tuple[list, list]:
    """
    Load grayscale, resized PNGs from a directory into flat numpy vectors.
    Corrupt/empty images are skipped safely.

    Env:
      MIN_BYTES (int, default=0): minimum file size to accept. Set 0 to disable size filtering.
    """
    X, y = [], []
    if not dirpath.exists():
        print(f"[WARN] missing folder: {dirpath}")
        return X, y

    files = sorted(f for f in os.listdir(dirpath) if f.lower().endswith(".png"))
    if not files:
        print(f"[WARN] {dirpath.name}: no PNGs found")
        return X, y

    # Size gate: configurable, defaults to 0 (no size-based skipping)
    try:
        min_bytes = int(os.getenv("MIN_BYTES", "0"))
    except Exception:
        min_bytes = 0

    skipped = 0
    for fname in files:
        p = dirpath / fname
        try:
            if p.stat().st_size <= min_bytes:
                skipped += 1
                continue
        except Exception:
            skipped += 1
            continue

        try:
            with Image.open(p) as img:
                img = img.convert("L").resize(target_size, Image.LANCZOS)
                arr = (np.asarray(img, dtype=np.float32) / 255.0).ravel()
                X.append(arr)
                y.append(label)
        except Exception:
            # Any PIL/IO error → skip
            skipped += 1
            continue

    if skipped:
        print(f"[WARN] {dirpath.name}: skipped {skipped} corrupt/tiny images")
    return X, y


def load_dataset(
    data_dir: Path,
    include_fifth: bool = False,
    target_size: Tuple[int, int] = (200, 200),
) -> Tuple[np.ndarray, np.ndarray, List[str]]:
    """
    Build the dataset from expected *_pdfs_png folders (under `data_dir`).
    """
    mapping = [
        ("word_pdfs_png", 0, "Word"),
        ("google_docs_pdfs_png", 1, "GoogleDocs"),
        ("python_pdfs_png", 2, "Python"),
        ("fourth_source_pdfs_png", 3, "Fourth"),
    ]
    if include_fifth:
        mapping.append(("fifth_source_pdfs_png", 4, "Fifth"))

    X_all, y_all, class_names = [], [], []
    for folder, lab, cname in mapping:
        Xi, yi = load_png_dir(Path(data_dir) / folder, lab, target_size)
        if yi:
            X_all += Xi
            y_all += yi
            class_names.append(cname)
        else:
            print(f"[WARN] no valid images kept in {folder}")

    if X_all:
        X = np.stack(X_all, axis=0).astype(np.float32)
        y = np.asarray(y_all, dtype=np.int64)
    else:
        raise RuntimeError("No valid images found in any class. Check paths, LFS checkout, and MIN_BYTES.")

    # Sanity: need >= 2 classes with samples
    from collections import Counter
    counts = Counter(y.tolist())
    print("[INFO] Class counts (kept):", dict(sorted(counts.items())))
    if sum(c > 0 for c in counts.values()) < 2:
        raise RuntimeError(f"Not enough valid classes to train (need >=2). Counts: {dict(counts)}")

    return X, y, class_names

# Metrics & confusion matrix

def compute_metrics(y_true: np.ndarray, y_pred: np.ndarray, average: str = "weighted") -> dict:
    """
    Weighted precision/recall/F1 + accuracy, safe with missing labels (zero_division=0).
    """
    acc = float(accuracy_score(y_true, y_pred))
    prec, rec, f1, _ = precision_recall_fscore_support(
        y_true, y_pred, average=average, zero_division=0
    )
    return {
        "accuracy": acc,
        "precision_weighted": float(prec),
        "recall_weighted": float(rec),
        "f1_weighted": float(f1),
    }

def save_confusion(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    classes: List[str],
    title: str,
    out_path: Path,
) -> None:
    """Save a labeled confusion matrix PNG."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    cm = confusion_matrix(y_true, y_pred, labels=list(range(len(classes))))
    fig = plt.figure(figsize=(6, 5))
    plt.imshow(cm, interpolation="nearest")
    plt.title(title)
    plt.colorbar()
    ticks = np.arange(len(classes))
    plt.xticks(ticks, classes, rotation=45, ha="right")
    plt.yticks(ticks, classes)

    thr = cm.max() / 2 if cm.size and cm.max() > 0 else 0.5
    for i, j in itertools.product(range(cm.shape[0]), range(cm.shape[1])):
        plt.text(
            j, i, format(cm[i, j], "d"),
            ha="center", va="center",
            color="white" if cm[i, j] > thr else "black",
        )
    plt.ylabel("True")
    plt.xlabel("Predicted")
    plt.tight_layout()
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)

# alias some projects expect
save_confusion_matrix = save_confusion
