import os
import itertools
from pathlib import Path
from typing import List, Tuple

import numpy as np
from PIL import Image, ImageFile
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import (
    confusion_matrix,
    accuracy_score,
    precision_recall_fscore_support,
)

# Globals / CV config
RANDOM_STATE = 42
K_FOLDS = 5

# Let PIL attempt to load truncated PNGs; we still protect with try/except.
ImageFile.LOAD_TRUNCATED_IMAGES = True

# Cross-validation splitter
def get_splitter() -> StratifiedKFold:
    """Deterministic StratifiedKFold used by ALL models to keep splits identical."""
    return StratifiedKFold(n_splits=K_FOLDS, shuffle=True, random_state=RANDOM_STATE)

# Image dataset loaders
def load_png_dir(
    dirpath: Path, label: int, target_size: Tuple[int, int] = (200, 200)
) -> Tuple[list, list]:
    """
    Load grayscale, resized PNGs from a directory into flat numpy vectors.
    Corrupt/empty images are skipped safely.

    Args:
        dirpath: directory containing .png files
        label: integer class id to assign to all files in this folder
        target_size: (width, height) to resize each image

    Returns:
        X: list[np.ndarray] each of shape (W*H,)
        y: list[int]
    """
    X, y = [], []
    if not dirpath.exists():
        return X, y

    files = sorted(f for f in os.listdir(dirpath) if f.lower().endswith(".png"))
    skipped = 0

    for fname in files:
        p = dirpath / fname

        # Skip obviously broken files (empty / tiny).
        try:
            if p.stat().st_size < 1024:  # <1KB → likely truncated/empty
                skipped += 1
                continue
        except Exception:
            skipped += 1
            continue

        try:
            # Open → convert to grayscale → resize → flatten
            with Image.open(p) as img:
                img = img.convert("L")
                img = img.resize(target_size, Image.LANCZOS)
                X.append(np.asarray(img, dtype=np.float32).ravel())
                y.append(label)
        except Exception:
            # any PIL/IO error → skip
            skipped += 1
            continue

    if skipped:
        print(f"[WARN] {dirpath.name}: skipped {skipped} corrupt/tiny images")
    return X, y


def load_dataset(
    data_dir: Path, include_fifth: bool = False, target_size: Tuple[int, int] = (200, 200)
) -> Tuple[np.ndarray, np.ndarray, List[str]]:
    """
    Build the full dataset from the expected *_pdfs_png folders.

    Folders (4-class core):
      - word_pdfs_png
      - google_docs_pdfs_png
      - python_pdfs_png
      - fourth_source_pdfs_png
    Optional 5th:
      - fifth_source_pdfs_png

    Returns:
        X: np.ndarray [N, W*H] float32
        y: np.ndarray [N] int64
        class_names: list[str] in folder order
    """
    mapping = [
        ("word_pdfs_png", 0),
        ("google_docs_pdfs_png", 1),
        ("python_pdfs_png", 2),
        ("fourth_source_pdfs_png", 3),
    ]
    if include_fifth:
        mapping.append(("fifth_source_pdfs_png", 4))

    X_all, y_all = [], []
    for folder, lab in mapping:
        Xi, yi = load_png_dir(data_dir / folder, lab, target_size)
        X_all += Xi
        y_all += yi

    if X_all:
        X = np.stack(X_all, axis=0).astype(np.float32)
    else:
        X = np.empty((0, target_size[0] * target_size[1]), dtype=np.float32)
    y = np.asarray(y_all, dtype=np.int64) if y_all else np.empty((0,), dtype=np.int64)
    class_names = [name.replace("_pdfs_png", "") for name, _ in mapping]
    return X, y, class_names

# Metrics & visualization

def compute_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    """Weighted precision/recall/F1 + accuracy (handles missing labels gracefully)."""
    acc = accuracy_score(y_true, y_pred)
    prec, rec, f1, _ = precision_recall_fscore_support(
        y_true, y_pred, average="weighted", zero_division=0
    )
    return dict(
        accuracy=acc,
        precision_weighted=prec,
        recall_weighted=rec,
        f1_weighted=f1,
    )


def save_confusion(
    y_true: np.ndarray, y_pred: np.ndarray, classes: List[str], title: str, out_path: Path
) -> None:
    """Save a labeled confusion matrix PNG."""
    import matplotlib.pyplot as plt  # local import to avoid matplotlib import at module load

    cm = confusion_matrix(y_true, y_pred)
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
            j,
            i,
            format(cm[i, j], "d"),
            ha="center",
            va="center",
            color="white" if cm[i, j] > thr else "black",
        )
    plt.ylabel("True")
    plt.xlabel("Predicted")
    plt.tight_layout()
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)

