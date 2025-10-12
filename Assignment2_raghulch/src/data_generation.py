import os, sys, csv, shutil, subprocess, textwrap
from pathlib import Path
from typing import Optional
from tqdm import tqdm

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
SDOC = DATA / "source_documents"
DOCX = SDOC / "docx"
HTML = SDOC / "html"
ASSETS = SDOC / "assets"
META = SDOC / "_meta.csv"

OUT_WORD  = DATA / "word_pdfs"
OUT_GDOCS = DATA / "google_docs_pdfs"
OUT_PY    = DATA / "python_pdfs"
for p in [OUT_WORD, OUT_GDOCS, OUT_PY]: p.mkdir(parents=True, exist_ok=True)

def which(x): return shutil.which(x)

def have_macos_word() -> bool:
    return Path("/Applications/Microsoft Word.app").exists()

def have_libreoffice() -> bool:
    return which("soffice") is not None

def chrome_candidates():
    return [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
        which("google-chrome"),
        which("chromium"),
        which("chromium-browser"),
    ]

def find_chrome() -> Optional[str]:
    for c in chrome_candidates():
        if c and Path(c).exists():
            return c
    return None

def load_meta():
    if not META.exists():
        print(f"ERR: Missing meta: {META}", file=sys.stderr); sys.exit(2)
    rows = []
    with open(META, newline="") as f:
        r = csv.DictReader(f)
        for row in r:
            rows.append({
                "id": int(row["id"]),
                "title": row["title"],
                "pages_target": max(1, int(row.get("pages_target", 1) or 1))
            })
    return rows

# ---- Python / ReportLab ----
def make_python_pdfs(limit: Optional[int]=None):
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.units import inch
    except Exception:
        print("Install reportlab: pip install reportlab", file=sys.stderr); raise

    rows = load_meta()
    if limit: rows = rows[:limit]

    for row in tqdm(rows, desc="Python PDFs"):
        doc_id = row["id"]; title = row["title"]; pages = row["pages_target"]
        out = OUT_PY / f"{doc_id:06d}_{title.replace(' ','_')}.pdf"
        if out.exists(): continue

        c = canvas.Canvas(str(out), pagesize=letter)
        W, H = letter
        c.setFont("Helvetica-Bold", 16); c.drawString(72, H-72, title)

        body = " ".join(["Synthetic content for provenance classification."] * 350)
        lines = textwrap.wrap(body, width=90)
        idx = 0
        for p in range(pages):
            c.setFont("Helvetica", 11)
            y = H-110
            # try draw an asset if exists
            chart = ASSETS / f"chart_{doc_id}.png"
            eq    = ASSETS / f"eq_{doc_id}.png"
            pick  = chart if chart.exists() else (eq if eq.exists() else None)
            if pick:
                try:
                    c.drawImage(str(pick), 72, y-200, width=4*inch, height=2.5*inch, preserveAspectRatio=True, mask='auto')
                    y -= 200
                except Exception:
                    pass
            for _ in range(30):
                if idx >= len(lines): break
                c.drawString(72, y, lines[idx]); y -= 14; idx += 1
            c.showPage()
        c.save()

# ---- Word → PDF ----
def word_to_pdf_word_mac(src: Path, dst: Path):
    script = f'''
    tell application "Microsoft Word"
        activate
        open POSIX file "{src}"
        save as active document file name (POSIX file "{dst}") file format format PDF
        close active document saving no
    end tell
    '''
    subprocess.run(["osascript", "-e", script], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def word_to_pdf_libreoffice(src: Path, out_dir: Path):
    subprocess.run(["soffice", "--headless", "--convert-to", "pdf", "--outdir", str(out_dir), str(src)],
                   check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def make_word_pdfs(limit: Optional[int]=None):
    docs = sorted(DOCX.glob("*.docx"))
    if limit: docs = docs[:limit]

    use_word = have_macos_word()
    use_lo   = have_libreoffice()
    if not use_word and not use_lo:
        print("No Word or LibreOffice found for DOCX→PDF.", file=sys.stderr); sys.exit(2)

    for docx in tqdm(docs, desc="Word PDFs"):
        out = OUT_WORD / (docx.stem + ".pdf")
        if out.exists(): continue
        try:
            if use_word: word_to_pdf_word_mac(docx, out)
            else:        word_to_pdf_libreoffice(docx, OUT_WORD)
        except subprocess.CalledProcessError as e:
            print(f"WARN: failed on {docx.name}: {e}", file=sys.stderr)

# ---- HTML → PDF via Chrome (Google Docs style) ----
def html_to_pdf_chrome(chrome_bin: str, src_html: Path, dst_pdf: Path):
    cmd = [chrome_bin, "--headless", "--disable-gpu", f"--print-to-pdf={dst_pdf}", str(src_html.resolve().as_uri())]
    subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def make_gdocs_pdfs(limit: Optional[int]=None):
    chrome = find_chrome()
    if not chrome:
        print("No Chrome/Chromium found for HTML→PDF.", file=sys.stderr); sys.exit(2)

    htmls = sorted(HTML.glob("*.html"))
    if limit: htmls = htmls[:limit]

    for html in tqdm(htmls, desc="GDocs PDFs"):
        out = OUT_GDOCS / (html.stem + ".pdf")
        if out.exists(): continue
        try:
            html_to_pdf_chrome(chrome, html, out)
        except subprocess.CalledProcessError as e:
            print(f"WARN: chrome failed {html.name}: {e}", file=sys.stderr)

def main():
    import argparse
    ap = argparse.ArgumentParser(description="Generate PDFs from three sources")
    ap.add_argument("--make-python-pdfs", action="store_true")
    ap.add_argument("--make-word-pdfs", action="store_true")
    ap.add_argument("--make-gdocs-pdfs", action="store_true")
    ap.add_argument("--max", type=int, default=None, help="limit docs (smoke test)")
    args = ap.parse_args()

    if args.make_python_pdfs: make_python_pdfs(args.max)
    if args.make_word_pdfs:   make_word_pdfs(args.max)
    if args.make_gdocs_pdfs:  make_gdocs_pdfs(args.max)

if __name__ == "__main__":
    main()
