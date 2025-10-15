import os, subprocess, shutil
from pathlib import Path

try:
    import fitz  # PyMuPDF fallback (only used if pdftoppm not found)
except Exception:
    fitz = None

def find_root():
    env = os.getenv("ASSIGN_ROOT")
    if env and (Path(env)/"data").exists():
        return Path(env)
    here = Path(__file__).resolve()
    for anc in [here.parent, *here.parents]:
        if (anc/"data").exists():
            return anc
    return here.parent

ROOT = find_root()
PDF_DIRS = [
    ROOT/"data/word_pdfs",
    ROOT/"data/google_docs_pdfs",
    ROOT/"data/python_pdfs",
    ROOT/"data/fourth_source_pdfs",
    ROOT/"data/fifth_source_pdfs",
]

def render_with_poppler(pdf_path: Path, out_png: Path):
    out_png.parent.mkdir(parents=True, exist_ok=True)
    stem = out_png.with_suffix("")  
    cmd = ["pdftoppm", "-png", "-singlefile", str(pdf_path), str(stem)]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(res.stderr)

def render_with_pymupdf(pdf_path: Path, out_png: Path, dpi=200):
    if fitz is None:
        raise RuntimeError("PyMuPDF not installed and pdftoppm not found.")
    out_png.parent.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(pdf_path)
    if doc.page_count == 0:
        return
    page = doc.load_page(0)
    mat = fitz.Matrix(dpi/72, dpi/72)
    pix = page.get_pixmap(matrix=mat, alpha=False)
    pix.save(str(out_png))

def convert_folder(pdf_dir: Path):
    if not pdf_dir.exists():
        print(f"[SKIP] {pdf_dir}")
        return
    out_dir = pdf_dir.with_name(pdf_dir.name + "_png")
    out_dir.mkdir(parents=True, exist_ok=True)
    pdfs = sorted(pdf_dir.glob("*.pdf"))
    use_poppler = shutil.which("pdftoppm") is not None
    print(f"[{pdf_dir}] {len(pdfs)} PDFs -> {out_dir}  (poppler={use_poppler})")
    for pdf in pdfs:
        out_png = out_dir / f"{pdf.stem}.png"
        if out_png.exists():
            continue
        try:
            if use_poppler:
                render_with_poppler(pdf, out_png)
            else:
                render_with_pymupdf(pdf, out_png, dpi=200)
        except Exception as e:
            print("  ERROR:", pdf.name, e)

def main():
    print("[ROOT]", ROOT)
    for d in PDF_DIRS:
        convert_folder(d)

if __name__ == "__main__":
    # Guarded execution: creating the file won't trigger conversion.
    main()
