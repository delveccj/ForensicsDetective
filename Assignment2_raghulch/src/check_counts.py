from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
def count(p): return len(list(p.glob("*.pdf")))
print("PDF Counts")
print("  word_pdfs:          ", count(ROOT/"data/word_pdfs"))
print("  google_docs_pdfs:   ", count(ROOT/"data/google_docs_pdfs"))
print("  python_pdfs:        ", count(ROOT/"data/python_pdfs"))
print("  fourth_source_pdfs: ", count(ROOT/"data/fourth_source_pdfs"))
