#!/usr/bin/env python3
import os

dirs = ['word_pdfs', 'google_docs_pdfs', 'python_pdfs', 'fpdf_pdfs']
for d in dirs:
    if os.path.exists(d):
        pdfs = [f for f in os.listdir(d) if f.endswith('.pdf')]
        print(f'{d}: {len(pdfs)} PDFs')
    else:
        print(f'{d}: directory not found')