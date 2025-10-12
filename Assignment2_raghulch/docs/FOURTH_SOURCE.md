 # 4th PDF Source - "Print to PDF" in browser `wkhtmltopdf`.


**Option (from the assignment's "Recommended Options")::**
The browser-based PDF generation: Chrome/Firefox "Print to PDF" option. (Recommended - Strong, reliable results).
**Conversion Technology:** `wkhtmltopdf` (headless, open-source HTML to PDF document converter utilizing a Webkit engine).

We use the **same HTML inputs** as the other sources to achieve **content parity**, and we set all the converter flags to achieve **reproducibility** (page size, DPI, margins, media type, JS disabled).


## Why this source?  


- **content control**: we are using the exact same inputs, as in `data/source_documents/html/*.html`.
- **Parameter control:** Fixed flags (A4, DPI=150, margins, print CSS, JS off).
- **Scale:** Quick and stable for **6k+ PDFs** at once (we generated **6,250**).
- **Reproducible:** Deterministic command; same flags across runs and machines.

## Reproducible flags
wkhtmltopdf --page-size A4 --dpi 150 --print-media-type --disable-javascript
--image-dpi 150 --margin-top 10mm --margin-right 10mm
--margin-bottom 10mm --margin-left 10mm <input.html> <output.pdf>

## How to run
python src/fourth_source.py --max 10 # smoke test
python src/fourth_source.py # full run (>=5k)
python src/check_counts.py # verify counts
python src/build_manifest.py # build 4-source manifest
python src/check_task3.py # asserts >= 5k in fourth_source_pdfs

## Summary
- Option: Browser-based PDF Generation
- Inputs: identical HTML as other sources
- Params: A4, DPI 150, margins 10mm, print CSS, JS off
- Scale: 6,250 PDFs (≥5,000)
- Artifacts: data/fourth_source_pdfs/, data/manifest_4sources.csv
- Reproducible: fixed flags, headless

