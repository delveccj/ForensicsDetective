import sys
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
meta = pd.read_csv(ROOT/"data/source_documents/_meta.csv")
meta["pages_target"] = pd.to_numeric(meta["pages_target"], errors="coerce")

def pct(x): return 100*float(x)

has_img = meta['has_images'].astype(float).mean()
has_tbl = meta['has_tables'].astype(float).mean()

print("=== Complexity Audit ===")
print(f"Total sources: {len(meta)}")
print(f"With images/charts: {pct(has_img):.1f}%  (target ≥ 30%)")
print(f"With tables:        {pct(has_tbl):.1f}%  (target ≥ 25%)")

ok_img = has_img >= 0.30
ok_tbl = has_tbl >= 0.25

# Inclusive ranges per spec:
c_1_5   = ((meta["pages_target"]>=1)  & (meta["pages_target"]<=5)).sum()
c_6_10  = ((meta["pages_target"]>=6)  & (meta["pages_target"]<=10)).sum()
c_11_15 = ((meta["pages_target"]>=11) & (meta["pages_target"]<=15)).sum()
c_15_30 = ((meta["pages_target"]>=15) & (meta["pages_target"]<=30)).sum()  # inclusive
c_30p   = (meta["pages_target"]>=30).sum()                                  # inclusive

print(f"   1-5: {c_1_5}")
print(f"  6-10: {c_6_10}")
print(f" 11-15: {c_11_15}")
print(f" 15-30: {c_15_30}  (inclusive)")
print(f"  30+:  {c_30p}    (inclusive)")

ok_15_30 = c_15_30 >= 200
ok_30p   = c_30p   >= 50

print("\n=== Verdicts ===")
print("Images   (≥30%):", "PASS" if ok_img else "FAIL")
print("Tables   (≥25%):", "PASS" if ok_tbl else "FAIL")
print("15–30 p. (≥200):", "PASS" if ok_15_30 else "FAIL")
print("30+  p.  (≥50) :", "PASS" if ok_30p else "FAIL")

if not (ok_img and ok_tbl and ok_15_30 and ok_30p):
    sys.exit(2)
