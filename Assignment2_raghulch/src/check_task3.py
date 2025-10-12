from pathlib import Path
def count(p): return len(list(Path(p).glob("*.pdf")))
ROOT = Path(__file__).resolve().parents[1]
word   = count(ROOT/"data/word_pdfs")
gdocs  = count(ROOT/"data/google_docs_pdfs")
python = count(ROOT/"data/python_pdfs")
fourth = count(ROOT/"data/fourth_source_pdfs")
print("Counts:", dict(word=word, gdocs=gdocs, python=python, fourth=fourth))
assert fourth >= 5000, "Fourth source must be ≥ 5,000 PDFs"
print("Task 3 scale requirement: PASS")
