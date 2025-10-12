from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
def to_map(folder):
    return {p.stem: p for p in sorted((ROOT/folder).glob("*.pdf"))}

m_word   = to_map("data/word_pdfs")
m_gdocs  = to_map("data/google_docs_pdfs")
m_py     = to_map("data/python_pdfs")
m_fourth = to_map("data/fourth_source_pdfs")

# only keep ids that exist in at least 2 sources (report all)
keys = sorted(set(m_word)|set(m_gdocs)|set(m_py)|set(m_fourth))

rows = []
for k in keys:
    rows.append(dict(
        doc_id = k,
        word   = str(m_word.get(k,"")),
        gdocs  = str(m_gdocs.get(k,"")),
        python = str(m_py.get(k,"")),
        fourth = str(m_fourth.get(k,"")),
        present = sum(bool(x) for x in [m_word.get(k), m_gdocs.get(k), m_py.get(k), m_fourth.get(k)])
    ))

df = pd.DataFrame(rows).sort_values("doc_id")
out = ROOT/"data"/"manifest_4sources.csv"
out.parent.mkdir(parents=True, exist_ok=True)
df.to_csv(out, index=False)
print(f"Wrote {out} with {len(df)} rows")
print(df.present.value_counts().rename_axis("#sources").to_frame("count"))
