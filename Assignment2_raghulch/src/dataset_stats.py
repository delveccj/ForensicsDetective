from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
meta = pd.read_csv(ROOT/"data/source_documents/_meta.csv")
meta["pages_target"] = pd.to_numeric(meta["pages_target"], errors="coerce").fillna(1).astype(int)

print("Complexity")
for col in ["has_images","has_tables","has_equations"]:
    if col in meta.columns:
        print(f"{col}:", f"{100*pd.to_numeric(meta[col], errors='coerce').fillna(0).mean():.1f}%")

print("\nPage Length")
print("Mean:", meta["pages_target"].mean(), "Std:", meta["pages_target"].std(ddof=0))
print(meta["pages_target"].describe())

def count(p): return len(list((ROOT/p).glob("*.pdf")))
print("\nPDF Counts")
print("word_pdfs:",      count("data/word_pdfs"))
print("google_docs_pdfs:",count("data/google_docs_pdfs"))
print("python_pdfs:",    count("data/python_pdfs"))
