# src/utils.py
from __future__ import annotations
import os, itertools
from pathlib import Path
from typing import Tuple, List
import numpy as np

from PIL import Image, ImageFile
ImageFile.LOAD_TRUNCATED_IMAGES = True  # tolerate slightly truncated PNGs

# Try to import PyMuPDF for PDF fallback
try:
    import fitz  # PyMuPDF
    _HAVE_FITZ = True
except Exception:
    fitz = None
    _HAVE_FITZ = False

from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import (
    confusion_matrix,
    accuracy_score,
    precision_recall_fscore_support,
)

# -------- global config (used by analysis.py) --------
RANDOM_STATE = int(os.getenv("RANDOM_STATE", "42"))
CV_FOLDS     = int(os.getenv("CV_FOLDS", "5"))
TEST_SIZE    = float(os.getenv("TEST_SIZE", "0.2"))

def get_splitter() -> StratifiedKFold:
    return StratifiedKFold(n_splits=CV_FOLDS, shuffle=True, random_state=RANDOM_STATE)

# -------- helpers --------
def _to_gray_resized_array(im: Image.Image, target_size: Tuple[int,int]) -> np.ndarray:
    if im.mode != "L":
        im = im.convert("L")
    im = im.resize(target_size, Image.LANCZOS)
    arr = (np.asarray(im, dtype=np.float32) / 255.0).ravel()
    return arr

def _render_pdf_page0_to_array(pdf_path: Path, target_size: Tuple[int,int], dpi: int = 150) -> np.ndarray | None:
    """Render first page of a PDF to a grayscale, resized vector. Returns None on failure."""
    if not _HAVE_FITZ:
        return None
    try:
        doc = fitz.open(pdf_path)
        if doc.page_count == 0:
            return None
        page = doc.load_page(0)
        zoom = dpi / 72.0
        pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
        # Convert raw bytes -> PIL -> resize/gray -> vector
        im = Image.frombytes("RGB" if pix.n>=3 else "L", (pix.width, pix.height), pix.samples)
        return _to_gray_resized_array(im, target_size)
    except Exception:
        return None

# -------- loaders --------
def load_png_dir(dirpath: Path, label: int, target_size: Tuple[int,int]=(200,200)) -> Tuple[list, list]:
    """
    Load grayscale, resized PNGs from dirpath into 1D numpy vectors.
    Skips unreadable files. MIN_BYTES=0 by default (accept all non-empty files).
    """
    X, y = [], []
    if not dirpath.exists():
        print(f"[WARN] missing folder: {dirpath}")
        return X, y

    files = sorted(f for f in os.listdir(dirpath) if f.lower().endswith(".png"))
    if not files:
        print(f"[WARN] {dirpath.name}: no PNGs found")
        return X, y

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
                arr = _to_gray_resized_array(img, target_size)
                X.append(arr); y.append(label)
        except Exception:
            skipped += 1

    if skipped:
        print(f"[WARN] {dirpath.name}: skipped {skipped} corrupt/tiny images")
    return X, y

def load_pdf_dir(dirpath: Path, label: int, target_size: Tuple[int,int]=(200,200)) -> Tuple[list, list]:
    """
    Fallback loader: render PDF page 1 (page 0) to arrays using PyMuPDF (fitz).
    """
    X, y = [], []
    if not dirpath.exists():
        print(f"[WARN] missing folder: {dirpath}")
        return X, y
    if not _HAVE_FITZ:
        print(f"[WARN] PyMuPDF not available; cannot render PDFs in {dirpath.name}")
        return X, y

    files = sorted(f for f in os.listdir(dirpath) if f.lower().endswith(".pdf"))
    if not files:
        print(f"[WARN] {dirpath.name}: no PDFs found (for fallback)")
        return X, y

    kept = 0; bad = 0
    for fname in files:
        p = dirpath / fname
        arr = _render_pdf_page0_to_array(p, target_size, dpi=150)
        if arr is None:
            bad += 1
            continue
        X.append(arr); y.append(label); kept += 1

    print(f"[INFO] (PDF fallback) {dirpath.name}: kept {kept}, failed {bad}")
    return X, y

def load_dataset(data_dir: Path, include_fifth: bool=False, target_size: Tuple[int,int]=(200,200)) -> Tuple[np.ndarray, np.ndarray, List[str]]:
    """
    Build dataset. Preferred: *_pdfs_png dirs.
    If a class has 0 valid PNGs, try *_pdfs via PDF fallback (in-memory render).
    """
    mapping = [
        ("word_pdfs_png",            "word_pdfs",            0, "Word"),
        ("google_docs_pdfs_png",     "google_docs_pdfs",     1, "GoogleDocs"),
        ("python_pdfs_png",          "python_pdfs",          2, "Python"),
        ("fourth_source_pdfs_png",   "fourth_source_pdfs",   3, "Fourth"),
    ]
    if include_fifth:
        mapping.append(("fifth_source_pdfs_png", "fifth_source_pdfs", 4, "Fifth"))

    X_all, y_all, class_names = [], [], []
    for png_dir_name, pdf_dir_name, lab, cname in mapping:
        png_dir = Path(data_dir)/png_dir_name
        pdf_dir = Path(data_dir)/pdf_dir_name

        Xi, yi = load_png_dir(png_dir, lab, target_size)
        if not yi:
            print(f"[INFO] {png_dir_name}: 0 valid PNGs -> trying PDF fallback from {pdf_dir_name}")
            Xi, yi = load_pdf_dir(pdf_dir, lab, target_size)

        if yi:
            X_all += Xi; y_all += yi; class_names.append(cname)
        else:
            print(f"[WARN] no valid samples for class '{cname}' (png and pdf both failed)")

    if not X_all:
        raise RuntimeError("No valid images found in any class. Check paths, LFS checkout, MIN_BYTES, and PyMuPDF.")

    X = np.stack(X_all, axis=0).astype(np.float32)
    y = np.asarray(y_all, dtype=np.int64)

    from collections import Counter
    counts = Counter(y.tolist())
    print("[INFO] Class counts (kept):", dict(sorted(counts.items())))
    if sum(c > 0 for c in counts.values()) < 2:
        raise RuntimeError(f"Not enough valid classes to train (need >=2). Counts: {dict(counts)}")

    return X, y, class_names

# -------- metrics & confusion matrix --------
def compute_metrics(y_true: np.ndarray, y_pred: np.ndarray, average: str = "weighted") -> dict:
    acc = float(accuracy_score(y_true, y_pred))
    prec, rec, f1, _ = precision_recall_fscore_support(y_true, y_pred, average=average, zero_division=0)
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
