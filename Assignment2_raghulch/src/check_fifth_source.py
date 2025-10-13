import argparse, random, statistics, sys
from pathlib import Path

try:
    from PyPDF2 import PdfReader
except Exception:
    PdfReader = None  # If missing, we silently skip the readability block

ROOT        = Path(__file__).resolve().parents[1]
HTML_DIR    = ROOT/"data/source_documents/html"
FIFTH_DIR   = ROOT/"data/fifth_source_pdfs"

def list_stems(dirpath: Path, suffix: str):
    return sorted([p.stem for p in dirpath.glob(f"*{suffix}")])

def human(n):
    for unit in ["B","KB","MB","GB"]:
        if n < 1024: return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"

def main(sample:int=50, require_min:int=5000):
    if not FIFTH_DIR.exists():
        print(f"ERROR: missing folder: {FIFTH_DIR}", file=sys.stderr)
        sys.exit(2)

    html_stems  = set(list_stems(HTML_DIR, ".html"))
    pdf_paths   = sorted(FIFTH_DIR.glob("*.pdf"))
    pdf_stems   = set([p.stem for p in pdf_paths])

    # Scale
    total_pdfs = len(pdf_paths)
    ok_scale   = total_pdfs >= require_min

    # Content control
    missing_from_fifth = sorted(list(html_stems - pdf_stems))[:10]
    extra_in_fifth     = sorted(list(pdf_stems - html_stems))[:10]
    cov = (len(pdf_stems & html_stems) / max(1, len(html_stems))) * 100

    # File size stats
    sizes = [p.stat().st_size for p in pdf_paths]
    sizes_nonzero = sum(1 for s in sizes if s > 0)
    size_min = min(sizes) if sizes else 0
    size_max = max(sizes) if sizes else 0
    size_med = statistics.median(sizes) if sizes else 0
    ok_sizes = sizes_nonzero == total_pdfs and size_min > 0

    # Readability/page checks (sample) — only if PyPDF2 present
    readable_ok = True
    readable_msg = None
    if PdfReader is not None and total_pdfs:
        pages_checked = 0
        page_counts   = []
        sample_paths  = random.sample(pdf_paths, min(sample, total_pdfs))
        for p in sample_paths:
            try:
                r = PdfReader(str(p))
                page_counts.append(len(r.pages))
                pages_checked += 1
            except Exception as e:
                readable_ok = False
                readable_msg = f"Failed to open {p.name}: {e}"
                break
        if readable_msg is None:
            readable_msg = (
                f"Opened {pages_checked} PDFs; pages (min/mean/max): "
                f"{min(page_counts)}/{(sum(page_counts)/len(page_counts)):.2f}/{max(page_counts)}"
            )

    # Report
    print("Fifth Source Audit (Chrome headless)")
    print(f"HTML dir:  {HTML_DIR}")
    print(f"PDF dir:   {FIFTH_DIR}")

    print("\n Scale ")
    print(f"Total PDFs: {total_pdfs}  (require ≥ {require_min})  => {'PASS' if ok_scale else 'FAIL'}")

    print("\n Content Control (same inputs)")
    print(f"Coverage vs HTML sources: {cov:.2f}%")
    if missing_from_fifth:
        print(f"Examples missing in 5th source (first 10): {missing_from_fifth}")
    if extra_in_fifth:
        print(f"Examples extra in 5th source (first 10): {extra_in_fifth}")
    ok_coverage = cov > 95.0
    print(f"Coverage ≥95% => {'PASS' if ok_coverage else 'WARN/FAIL'}")

    print("\n File Sizes")
    if total_pdfs:
        print(f"Non-zero files: {sizes_nonzero}/{total_pdfs}")
        print(f"Size min/median/max: {human(size_min)}, {human(size_med)}, {human(size_max)}")
    print(f"All files non-zero => {'PASS' if ok_sizes else 'FAIL'}")

    if PdfReader is not None:
        print("\n Feasibility / Readability (sample)")
        print(readable_msg)
        print(f"Readability (sample) => {'PASS' if readable_ok else 'FAIL'}")

    # Exit code: fail if core requirements not met
    if not (ok_scale and ok_sizes and ok_coverage and (PdfReader is None or readable_ok)):
        sys.exit(2)

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", type=int, default=50, help="sample size for page-open checks")
    ap.add_argument("--require-min", type=int, default=5000, help="minimum PDFs required")
    args = ap.parse_args()
    main(sample=args.sample, require_min=args.require_min)
