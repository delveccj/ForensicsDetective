import argparse, os, shutil, subprocess
from pathlib import Path
from tqdm import tqdm

ROOT       = Path(__file__).resolve().parents[1]
HTML_DIR   = ROOT / "data/source_documents/html"
OUTPUT_DIR = ROOT / "data/fifth_source_pdfs"

# candidates if CHROME_BIN not provided
CANDIDATES = ["google-chrome", "google-chrome-stable", "chromium-browser", "chromium"]

def find_chrome(explicit_bin: str | None):
    if explicit_bin:
        return explicit_bin
    env = os.environ.get("CHROME_BIN")
    if env:
        return env
    for c in CANDIDATES:
        p = shutil.which(c)
        if p:
            return p
    return None

def main(max_n: int = 0, html_dir: str | None = None, out_dir: str | None = None, chrome_bin: str | None = None):
    html_root = Path(html_dir) if html_dir else HTML_DIR
    out_root  = Path(out_dir)  if out_dir  else OUTPUT_DIR
    out_root.mkdir(parents=True, exist_ok=True)

    html_files = sorted(html_root.glob("*.html"))
    if max_n and max_n > 0:
        html_files = html_files[:max_n]

    CHROME = find_chrome(chrome_bin)
    print(f"[DEBUG] HTML_DIR={html_root} (found {len(html_files)} html)")
    print(f"[DEBUG] OUT_DIR={out_root}")
    print(f"[DEBUG] CHROME_BIN={CHROME}")

    if not CHROME:
        raise SystemExit("No Chrome/Chromium found. Install chrome or set CHROME_BIN.")

    # Generate
    for h in tqdm(html_files, desc="Chrome PDF Export", unit="file"):
        out_pdf = out_root / f"{h.stem}.pdf"
        # chrome needs file:// absolute path
        src_url = "file://" + str(h.resolve())
        cmd = [
            CHROME,
            "--headless", "--disable-gpu", "--no-sandbox",
            "--print-to-pdf=" + str(out_pdf.resolve()),
            "--disable-dev-shm-usage",
            "--virtual-time-budget=10000",
            src_url,
        ]
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if proc.returncode != 0:
            print(f"[WARN] failed on {h.name}: {proc.stderr.strip()}")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--max", type=int, default=0)
    p.add_argument("--html-dir", type=str, default=None)
    p.add_argument("--out-dir",  type=str, default=None)
    p.add_argument("--chrome-bin", type=str, default=None)
    args = p.parse_args()
    main(args.max, args.html_dir, args.out_dir, args.chrome_bin)
