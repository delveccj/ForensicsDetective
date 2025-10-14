#!/usr/bin/env python3
"""
Batch PDF Generator from Word Documents

Converts Word documents to PDFs using Microsoft Word automation
for the forensics research dataset expansion.
"""

import os
import comtypes.client
import time

def convert_docx_to_pdf_batch(input_dir='wikipedia_docs_expanded', output_dir='word_pdfs_expanded'):
    """
    Batch convert Word documents to PDFs using Microsoft Word.
    
    Args:
        input_dir (str): Directory containing .docx files
        output_dir (str): Directory to save PDFs
    """
    # Create output directory
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Get list of Word documents
    docx_files = [f for f in os.listdir(input_dir) if f.endswith('.docx')]
    
    if not docx_files:
        print(f"No .docx files found in {input_dir}")
        return 0, 0
    
    print(f"Converting {len(docx_files)} Word documents to PDFs...")
    print(f"Input: {input_dir}")
    print(f"Output: {output_dir}")
    print("=" * 60)
    
    # Initialize Word application
    try:
        word = comtypes.client.CreateObject('Word.Application')
        word.Visible = False  # Run in background
    except Exception as e:
        print(f"Error initializing Word: {e}")
        print("Make sure Microsoft Word is installed")
        return 0, 0
    
    successful = 0
    failed = 0
    
    try:
        for i, docx_file in enumerate(docx_files, 1):
            try:
                # Full paths
                input_path = os.path.join(input_dir, docx_file)
                pdf_filename = docx_file.replace('.docx', '.pdf')
                output_path = os.path.join(output_dir, pdf_filename)
                
                # Skip if PDF already exists
                if os.path.exists(output_path):
                    print(f"[{i:3d}/{len(docx_files)}] SKIPPED {docx_file} (PDF exists)")
                    successful += 1
                    continue
                
                # Open document
                doc = word.Documents.Open(input_path)
                
                # Save as PDF (format 17 = PDF)
                doc.SaveAs(output_path, FileFormat=17)
                
                # Close document
                doc.Close()
                
                print(f"[{i:3d}/{len(docx_files)}] {docx_file} -> {pdf_filename}")
                successful += 1
                
            except Exception as e:
                print(f"[{i:3d}/{len(docx_files)}] FAILED {docx_file}: {str(e)}")
                failed += 1
            
            # Small delay to prevent overwhelming Word
            time.sleep(0.1)
    
    finally:
        # Close Word application
        word.Quit()
    
    print(f"\nWord to PDF conversion complete!")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    
    return successful, failed

def main():
    """Main execution."""
    print("Batch Word to PDF Converter")
    print("=" * 40)
    
    # Check if comtypes is available
    try:
        import comtypes
        print("comtypes available for Word automation")
    except ImportError:
        print("Error: comtypes not installed. Run: pip install comtypes")
        return
    
    print()
    
    # Convert documents
    successful, failed = convert_docx_to_pdf_batch()
    
    if successful > 0:
        print(f"\nNext step: Convert PDFs to binary images")
        print("Run: python pdf_to_binary_image.py --word-pdfs")

if __name__ == "__main__":
    main()