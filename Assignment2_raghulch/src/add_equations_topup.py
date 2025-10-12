from pathlib import Path
import random, csv
import matplotlib.pyplot as plt
from docx import Document
from docx.shared import Inches

ROOT = Path(__file__).resolve().parents[1]
DOCX = ROOT/"data/source_documents/docx"
ASSETS = ROOT/"data/source_documents/assets"
META  = ROOT/"data/source_documents/_meta.csv"
ASSETS.mkdir(parents=True, exist_ok=True)

def make_eq_png(out_path, eq):
    # render LaTeX-like equation with mathtext
    plt.figure()
    try:
        plt.text(0.05, 0.5, eq, fontsize=24)
    except Exception as e:
        # Fallback: write the string literally if mathtext fails
        plt.text(0.05, 0.5, eq.replace("$",""), fontsize=24)
    plt.axis('off')
    plt.savefig(out_path, bbox_inches="tight")
    plt.close()

# IMPORTANT: single backslashes (use raw strings)
eqs = [
    r"$E=mc^2$",
    r"$\int_a^b f(x)\,dx$",
    r"$\nabla\cdot \vec{E}=\rho/\epsilon_0$",
    r"$P(A|B)=\frac{P(A\cap B)}{P(B)}$",
    r"$a^2+b^2=c^2$",
    r"$\sum_{i=1}^{n} i = \frac{n(n+1)}{2}$",
]

docs = sorted(DOCX.glob("*.docx"))
pick = set(random.sample(range(len(docs)), max(1, int(0.25*len(docs)))))

for i,docx in enumerate(docs):
    if i not in pick: continue
    d = Document(docx)
    img = ASSETS/f"eq_extra_{i}.png"
    make_eq_png(img, random.choice(eqs))
    d.add_picture(str(img), width=Inches(3))
    d.save(docx)

# Update meta with has_equations
rows = []
with open(META, newline="") as f:
    r = csv.DictReader(f); rows = list(r); fields = r.fieldnames
if "has_equations" not in fields:
    fields = fields + ["has_equations"]
for i,row in enumerate(rows):
    row["has_equations"] = "1" if i in pick else row.get("has_equations","0")
with open(META, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(rows)
print(f"Injected equations into ~{int(100*len(pick)/max(1,len(docs)))}% docs and updated meta.")
