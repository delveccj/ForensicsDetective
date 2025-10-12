# ForensicsDetective — Scaled PDF Forensics

This repository contains a full pipeline to generate large document corpora (10k+ per source), export PDFs from 4 sources, convert PDFs to images, train multiple classifiers (SVM, SGD, RandomForest, MLP) for **4-class** PDF provenance, and analyze results.

## Quickstart
```bash
# 0) env
pip install -r requirements.txt

# 1) Generate sources (DOCX/HTML with images/tables/equations + metadata)
python src/data_generation.py --make-sources --n 6000

# 2) Make PDFs for each source (scale N as needed)
python src/data_generation.py --make-python-pdfs
python src/data_generation.py --make-word-pdfs
python src/data_generation.py --make-gdocs-pdfs
python src/data_generation.py --make-fourth-pdfs  # headless Chrome "Print to PDF"

# 3) Convert PDFs -> grayscale images
python src/image_conversion.py --data-root data --dpi 150

# 4) Train 4-class classifiers
python src/classification.py --data-root data --out results

# 5) Analyze and export figures + stats
python src/analysis.py --metrics results/performance_metrics.csv --out results
python results/statistical_analysis.py --metrics results/performance_metrics.csv

