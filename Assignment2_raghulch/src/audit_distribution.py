import sys
from pathlib import Path
import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
META = ROOT/"data/source_documents/_meta.csv"

df = pd.read_csv(META)
df["pages_target"] = pd.to_numeric(df["pages_target"], errors="coerce").fillna(1).astype(int)

mean = df["pages_target"].mean()
std  = df["pages_target"].std(ddof=0)

c_1_5   = ((df["pages_target"]>=1 ) & (df["pages_target"]<=5 )).sum()
c_6_10  = ((df["pages_target"]>=6 ) & (df["pages_target"]<=10)).sum()
c_11_15 = ((df["pages_target"]>=11) & (df["pages_target"]<=15)).sum()
c_15_30 = ((df["pages_target"]>=15) & (df["pages_target"]<=30)).sum()
c_30p   =  (df["pages_target"]>=30).sum()

print("Page Length Stats")
print(f"Total docs: {len(df)}")
print(f"Mean pages: {mean:.3f}   (target ≈ 3)")
print(f"Std  pages: {std:.3f}    (target ≈ 1.5)")
print("\nBuckets:")
print(f"  1–5  : {c_1_5}")
print(f"  6–10 : {c_6_10}")
print(f" 11–15 : {c_11_15}")
print(f" 15–30 : {c_15_30} (need ≥ 200)")
print(f"  30+  : {c_30p}   (need ≥ 50)")

ok_t15_30 = c_15_30 >= 200
ok_t30p   = c_30p   >= 50

print("\n Verdicts (5.2.3)")
print("Tail 15–30 ≥200:", "PASS" if ok_t15_30 else "FAIL")
print("Tail 30+   ≥50 :", "PASS" if ok_t30p   else "FAIL")

if not (ok_t15_30 and ok_t30p):
    sys.exit(2)
