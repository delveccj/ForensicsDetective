import argparse, subprocess
from pathlib import Path
from tqdm import tqdm

ROOT = Path(__file__).resolve().parents[1]
HTML_DIR = ROOT / "data/source_documents/html"
OUT_DIR  = ROOT / "data/fourth_source_pdfs"
OUT_DIR.mkdir(parents=True, exist_ok=True)

WKHTML_ARGS = [
  "--page-size", "A4",
  "--dpi", "150",
  "--print-media-type",
  "--disable-javascript",
  "--image-dpi", "150",
  "--margin-top", "10mm",
  "--margin-right", "10mm",
  "--margin-bottom", "10mm",
  "--margin-left", "10mm",
]

def convert_one(html_path: Path, pdf_path: Path, extra=None):
    args = ["wkhtmltopdf"] + (extra or []) + WKHTML_ARGS + [str(html_path), str(pdf_path)]
    proc = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"wkhtmltopdf failed on {html_path.name}:\n{proc.stderr}")

def main(max_n: int = 0, overwrite: bool = False):
    htmls = sorted(HTML_DIR.glob("*.html"))
    if max_n and max_n > 0:
        htmls = htmls[:max_n]
    pbar = tqdm(htmls, desc="Fourth PDFs", unit="file")
    done = 0
    for h in pbar:
        out = OUT_DIR / (h.stem + ".pdf")
        if out.exists() and not overwrite:
            continue
        try:
            convert_one(h, out)
            done += 1
        except Exception as e:
            pbar.write(f"WARN: {e}")
    print(f"Generated {done} PDFs in {OUT_DIR}")

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--max", type=int, default=0)
    ap.add_argument("--overwrite", action="store_true")
    args = ap.parse_args()
    main(max_n=args.max, overwrite=args.overwrite)
