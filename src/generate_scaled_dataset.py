#!/usr/bin/env python3
"""
Scalable PDF Generation Pipeline for Dataset Expansion

Generates thousands of PDFs per source type by creating variations
from existing source documents. Supports batch processing and
parallel generation for efficient scaling to 5,000+ samples.
"""

import os
import random
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from fpdf import FPDF
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from docx import Document
import threading

class ScalablePDFGenerator:
    def __init__(self, source_docs_dir='wikipedia_docs_expanded', output_base_dir='scaled_pdfs'):
        self.source_docs_dir = source_docs_dir
        self.output_base_dir = output_base_dir
        self.source_files = self._get_source_files()

        # Create output directories
        self.pdf_dirs = {
            'word': os.path.join(output_base_dir, 'word_pdfs'),
            'google': os.path.join(output_base_dir, 'google_docs_pdfs'),
            'python': os.path.join(output_base_dir, 'python_pdfs'),
            'fpdf': os.path.join(output_base_dir, 'fpdf_pdfs')
        }

        for dir_path in self.pdf_dirs.values():
            os.makedirs(dir_path, exist_ok=True)

        # Thread safety
        self.lock = threading.Lock()

    def _get_source_files(self):
        """Get list of source Word documents."""
        if not os.path.exists(self.source_docs_dir):
            print(f"Source directory {self.source_docs_dir} not found")
            return []

        files = [f for f in os.listdir(self.source_docs_dir) if f.endswith('.docx')]
        print(f"Found {len(files)} source documents")
        return files

    def _extract_text_from_docx(self, docx_path):
        """Extract text content from Word document."""
        try:
            doc = Document(docx_path)
            text_content = []

            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text_content.append(paragraph.text.strip())

            return text_content
        except Exception as e:
            print(f"Error reading {docx_path}: {e}")
            return None

    def _clean_text_for_fpdf(self, text):
        """Clean text for FPDF compatibility."""
        replacements = {
            '\u2013': '-', '\u2014': '-', '\u2018': "'", '\u2019': "'",
            '\u201c': '"', '\u201d': '"', '\u2026': '...', '\u00e9': 'e',
            '\u00e8': 'e', '\u00ea': 'e', '\u00eb': 'e', '\u00e0': 'a',
            '\u00e2': 'a', '\u00e4': 'a', '\u00f6': 'o', '\u00fc': 'u',
            '\u00df': 'ss', '\u010c': 'C', '\u0259': 'e', '\u20ae': 'R'
        }

        cleaned = text
        for unicode_char, ascii_char in replacements.items():
            cleaned = cleaned.replace(unicode_char, ascii_char)

        # Remove remaining non-latin-1 characters
        cleaned = ''.join(c for c in cleaned if ord(c) < 256)
        return cleaned

    def generate_fpdf_variations(self, text_content, base_filename, variations=10):
        """Generate multiple FPDF variations from same content."""
        generated_files = []

        for i in range(variations):
            try:
                # Create variation parameters
                font_size = random.choice([10, 11, 12, 14])
                margin = random.choice([10, 15, 20])
                line_spacing = random.choice([3, 4, 5])

                pdf = FPDF()
                pdf.add_page()
                pdf.set_font('Arial', 'B', 14)
                pdf.cell(0, 10, f"{base_filename.replace('_', ' ')} - Version {i+1}", ln=True, align='C')
                pdf.ln(10)

                pdf.set_font('Arial', size=font_size)
                pdf.set_margins(margin, margin, margin)

                for paragraph in text_content:
                    if paragraph.strip():
                        clean_text = self._clean_text_for_fpdf(paragraph)
                        words = clean_text.split()
                        line = ""

                        for word in words:
                            if pdf.get_string_width(line + word) < (210 - 2*margin - 20):  # Page width minus margins
                                line += word + " "
                            else:
                                pdf.multi_cell(0, line_spacing, line)
                                line = word + " "

                        if line:
                            pdf.multi_cell(0, line_spacing, line)
                        pdf.ln(line_spacing)

                # Save PDF
                output_filename = f"{base_filename}_fpdf_v{i+1}.pdf"
                output_path = os.path.join(self.pdf_dirs['fpdf'], output_filename)
                pdf.output(output_path)

                generated_files.append(output_path)

            except Exception as e:
                print(f"Error generating FPDF variation {i+1} for {base_filename}: {e}")

        return generated_files

    def generate_python_variations(self, text_content, base_filename, variations=10):
        """Generate multiple ReportLab variations from same content."""
        generated_files = []

        for i in range(variations):
            try:
                # Create variation parameters
                page_size = random.choice([letter, A4])
                font_size = random.choice([10, 11, 12, 14])
                margin = random.choice([36, 50, 72])  # points

                output_filename = f"{base_filename}_python_v{i+1}.pdf"
                output_path = os.path.join(self.pdf_dirs['python'], output_filename)

                # Create PDF document
                doc = SimpleDocTemplate(output_path, pagesize=page_size,
                                      leftMargin=margin, rightMargin=margin,
                                      topMargin=margin, bottomMargin=margin)

                styles = getSampleStyleSheet()
                style = styles['Normal']
                style.fontSize = font_size
                style.leading = font_size * 1.2

                # Build content
                story = []

                # Add title
                title_style = styles['Heading1']
                title_style.fontSize = 16
                story.append(Paragraph(f"{base_filename.replace('_', ' ')} - Version {i+1}", title_style))
                story.append(Spacer(1, 12))

                # Add content paragraphs
                for paragraph_text in text_content:
                    if paragraph_text.strip():
                        story.append(Paragraph(paragraph_text, style))
                        story.append(Spacer(1, 6))

                # Generate PDF
                doc.build(story)
                generated_files.append(output_path)

            except Exception as e:
                print(f"Error generating Python variation {i+1} for {base_filename}: {e}")

        return generated_files

    def process_single_document(self, docx_filename, variations_per_type=10):
        """Process a single source document to generate PDFs of all types."""
        docx_path = os.path.join(self.source_docs_dir, docx_filename)
        base_filename = docx_filename.replace('.docx', '')

        # Extract text content
        text_content = self._extract_text_from_docx(docx_path)
        if text_content is None:
            return {'filename': docx_filename, 'status': 'failed', 'error': 'Could not extract text'}

        generated_files = {
            'fpdf': [],
            'python': []
        }

        # Generate FPDF variations
        fpdf_files = self.generate_fpdf_variations(text_content, base_filename, variations_per_type)
        generated_files['fpdf'] = fpdf_files

        # Generate Python/ReportLab variations
        python_files = self.generate_python_variations(text_content, base_filename, variations_per_type)
        generated_files['python'] = python_files

        # For Word and Google Docs, we would need to create variations by modifying the source documents
        # For now, we'll note that these would need to be generated separately

        return {
            'filename': docx_filename,
            'status': 'success',
            'fpdf_count': len(fpdf_files),
            'python_count': len(python_files),
            'total_generated': len(fpdf_files) + len(python_files)
        }

    def generate_scaled_dataset(self, target_samples_per_type=500, max_workers=4):
        """Generate scaled dataset with target number of samples per type."""
        print("Starting scalable PDF generation...")
        print(f"Target samples per type: {target_samples_per_type}")
        print(f"Available source documents: {len(self.source_files)}")
        print(f"Output directories: {self.pdf_dirs}")
        print("=" * 60)

        if not self.source_files:
            print("No source documents found!")
            return

        # Calculate how many variations needed per document
        variations_needed = min(100, max(50, target_samples_per_type // len(self.source_files)))  # Generate at least 50 variations per document
        print(f"Generating {variations_needed} variations per source document")

        total_expected = len(self.source_files) * variations_needed * 2  # FPDF and Python
        print(f"Expected total PDFs: {total_expected}")
        print()

        start_time = time.time()
        results = []

        # Process documents (for demo, limit to first 10 documents)
        demo_limit = len(self.source_files)  # Process all documents for full dataset
        documents_to_process = self.source_files[:demo_limit]

        print(f"Processing {len(documents_to_process)} documents...")

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_doc = {
                executor.submit(self.process_single_document, docx_file, variations_needed):
                docx_file for docx_file in documents_to_process
            }

            # Process completed tasks
            for future in as_completed(future_to_doc):
                docx_file = future_to_doc[future]
                try:
                    result = future.result()
                    results.append(result)

                    with self.lock:
                        status = "SUCCESS" if result['status'] == 'success' else "FAILED"
                        if result['status'] == 'success':
                            print(f"[{len(results):2d}/{len(documents_to_process)}] {status}: {docx_file} -> "
                                  f"{result['fpdf_count']} FPDF + {result['python_count']} Python PDFs")
                        else:
                            print(f"[{len(results):2d}/{len(documents_to_process)}] {status}: {docx_file} - {result.get('error', 'Unknown error')}")

                except Exception as e:
                    print(f"Exception processing {docx_file}: {e}")

        # Summary
        total_time = time.time() - start_time
        successful = sum(1 for r in results if r['status'] == 'success')
        total_fpdf = sum(r.get('fpdf_count', 0) for r in results)
        total_python = sum(r.get('python_count', 0) for r in results)

        print("\n" + "=" * 60)
        print("SCALABLE PDF GENERATION COMPLETE")
        print("=" * 60)
        print(f"Documents processed: {len(results)}")
        print(f"Successful: {successful}")
        print(f"Failed: {len(results) - successful}")
        print(f"Total FPDF PDFs generated: {total_fpdf}")
        print(f"Total Python PDFs generated: {total_python}")
        print(".2f")
        print(".2f")

        return results

def main():
    """Main execution for scalable PDF generation."""
    print("Scalable PDF Generation for Dataset Expansion")
    print("=" * 50)

    # Check dependencies
    try:
        from fpdf import FPDF
        print("[OK] FPDF available")
    except ImportError:
        print("[ERROR] FPDF not installed. Run: pip install fpdf")
        return

    try:
        from reportlab.pdfgen import canvas
        print("[OK] ReportLab available")
    except ImportError:
        print("[ERROR] ReportLab not installed. Run: pip install reportlab")
        return

    try:
        import docx
        print("[OK] python-docx available")
    except ImportError:
        print("[ERROR] python-docx not installed. Run: pip install python-docx")
        return

    print()

    # Generate scaled dataset
    generator = ScalablePDFGenerator()

    # For demonstration, generate smaller dataset
    # In production, use target_samples_per_type=5000
    results = generator.generate_scaled_dataset(target_samples_per_type=1000)

    print("\nNext steps:")
    print("1. Scale up to full dataset (5000+ samples per type)")
    print("2. Implement Word and Google Docs variation generation")
    print("3. Convert all PDFs to binary images")
    print("4. Train classifiers on expanded dataset")

if __name__ == "__main__":
    main()