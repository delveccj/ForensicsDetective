
**Why this source:** Deterministic, scriptable, and uses the exact same HTML inputs used by the other methods, ensuring content parity.

**Command/flags used (fixed for reproducibility):**
wkhtmltopdf
--page-size A4
--dpi 150
--print-media-type
--disable-javascript
--image-dpi 150
--margin-top 10mm
--margin-right 10mm
--margin-bottom 10mm
--margin-left 10mm
<input.html> <output.pdf>

**How to run:**

python src/fourth_source.py --max 50 # quick test
python src/fourth_source.py # full dataset
python src/check_counts.py # verify counts (>= 5,000)


**Scale achieved:** 6,250 PDFs in `data/fourth_source_pdfs/`.

**Notes:**
- Uses the same HTML sources under `data/source_documents/html/`
- JS disabled to avoid runtime variance
- A4 size + margins + DPI fixed
