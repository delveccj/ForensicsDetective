#!/usr/bin/env python3
"""
Master Dataset Expansion Pipeline

Orchestrates the complete process of scaling PDF datasets to 5,000+
samples per type. Handles parallel generation, conversion to binary
images, and validation of the expanded dataset.
"""

import os
import time
import subprocess
import shutil
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import sys

class DatasetExpansionPipeline:
    def __init__(self, base_dir='ForensicsDetective'):
        self.base_dir = base_dir
        self.scaled_dir = os.path.join(base_dir, 'scaled_pdfs')
        self.images_dir = os.path.join(base_dir, 'scaled_images')

        # Create directories
        self.pdf_dirs = {
            'word': os.path.join(self.scaled_dir, 'word_pdfs'),
            'google': os.path.join(self.scaled_dir, 'google_docs_pdfs'),
            'python': os.path.join(self.scaled_dir, 'python_pdfs'),
            'fpdf': os.path.join(self.scaled_dir, 'fpdf_pdfs')
        }

        self.image_dirs = {
            'word': os.path.join(self.images_dir, 'word_pdfs_png'),
            'google': os.path.join(self.images_dir, 'google_docs_pdfs_png'),
            'python': os.path.join(self.images_dir, 'python_pdfs_png'),
            'fpdf': os.path.join(self.images_dir, 'fpdf_pdfs_png')
        }

        for dir_path in self.pdf_dirs.values():
            os.makedirs(dir_path, exist_ok=True)
        for dir_path in self.image_dirs.values():
            os.makedirs(dir_path, exist_ok=True)

        # Thread safety
        self.lock = threading.Lock()

    def count_current_pdfs(self):
        """Count current PDFs in each category."""
        counts = {}
        for category, pdf_dir in self.pdf_dirs.items():
            if os.path.exists(pdf_dir):
                # For word category, count both .pdf and .docx files
                if category == 'word':
                    pdf_files = [f for f in os.listdir(pdf_dir) if f.endswith(('.pdf', '.docx'))]
                else:
                    pdf_files = [f for f in os.listdir(pdf_dir) if f.endswith('.pdf')]
                counts[category] = len(pdf_files)
            else:
                counts[category] = 0
        return counts

    def run_scaled_generation(self, target_samples=5000):
        """Run the scalable PDF generation script."""
        print("Step 1: Running scalable PDF generation...")
        print(f"Target samples per type: {target_samples}")

        try:
            # Use virtual environment python
            python_exe = os.path.join(os.path.dirname(sys.executable), 'python.exe')
            cmd = [
                python_exe, 'src/generate_scaled_dataset.py'
            ]
            result = subprocess.run(cmd, cwd=self.base_dir, capture_output=True, text=True)

            if result.returncode == 0:
                print("✓ Scalable generation completed successfully")
                print(result.stdout.split('\n')[-10:])  # Show last 10 lines
                return True
            else:
                print("✗ Scalable generation failed")
                print("Error:", result.stderr)
                return False

        except Exception as e:
            print(f"Error running scalable generation: {e}")
            return False

    def run_batch_word_generation(self, target_samples=5000):
        """Run the batch Word PDF generation script."""
        print("\nStep 2: Running batch Word PDF generation...")

        try:
            # Use virtual environment python
            python_exe = os.path.join(os.path.dirname(sys.executable), 'python.exe')
            cmd = [
                python_exe, 'src/generate_batch_pdfs.py'
            ]
            result = subprocess.run(cmd, cwd=self.base_dir, capture_output=True, text=True)

            if result.returncode == 0:
                print("✓ Batch Word generation completed successfully")
                return True
            else:
                print("✗ Batch Word generation failed")
                print("Error:", result.stderr)
                return False

        except Exception as e:
            print(f"Error running batch Word generation: {e}")
            return False

    def convert_pdfs_to_images_batch(self, max_workers=4):
        """Convert all PDFs to binary images in parallel."""
        print("\nStep 3: Converting PDFs to binary images...")

        from pdf_to_binary_image import pdf_to_binary_image

        total_conversions = 0
        successful_conversions = 0

        for category in ['word', 'google', 'python', 'fpdf']:
            pdf_dir = self.pdf_dirs[category]
            image_dir = self.image_dirs[category]

            if not os.path.exists(pdf_dir):
                print(f"PDF directory {pdf_dir} not found, skipping {category}")
                continue

            # Only process PDF files for image conversion
            pdf_files = [f for f in os.listdir(pdf_dir) if f.endswith('.pdf')]
            print(f"Converting {len(pdf_files)} {category} PDFs to images...")

            # Process in parallel
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = []
                for pdf_file in pdf_files:
                    pdf_path = os.path.join(pdf_dir, pdf_file)
                    image_path = os.path.join(image_dir, pdf_file.replace('.pdf', '.png'))
                    futures.append(executor.submit(self._convert_single_pdf, pdf_path, image_path))

                for future in as_completed(futures):
                    total_conversions += 1
                    try:
                        if future.result():
                            successful_conversions += 1
                    except Exception as e:
                        print(f"Conversion error: {e}")

        print(f"Converted {successful_conversions}/{total_conversions} PDFs to images")
        return successful_conversions == total_conversions

    def _convert_single_pdf(self, pdf_path, image_path):
        """Convert a single PDF to binary image."""
        try:
            from pdf_to_binary_image import pdf_to_binary_image
            pdf_to_binary_image(pdf_path, image_path)
            return True
        except Exception as e:
            print(f"Failed to convert {pdf_path}: {e}")
            return False

    def validate_expanded_dataset(self):
        """Validate the expanded dataset quality."""
        print("\nStep 4: Validating expanded dataset...")

        validation_results = {}

        for category in ['word', 'google', 'python', 'fpdf']:
            # For word category, count both .pdf and .docx files
            if category == 'word':
                pdf_count = len([f for f in os.listdir(self.pdf_dirs[category]) if f.endswith(('.pdf', '.docx'))])
            else:
                pdf_count = len([f for f in os.listdir(self.pdf_dirs[category]) if f.endswith('.pdf')])
            image_count = len([f for f in os.listdir(self.image_dirs[category]) if f.endswith('.png')])

            validation_results[category] = {
                'pdfs': pdf_count,
                'images': image_count,
                'matched': pdf_count == image_count
            }

            print(f"{category}: {pdf_count} PDFs, {image_count} images {'✓' if pdf_count == image_count else '✗'}")

        # Check if we have sufficient samples
        total_samples = sum(r['pdfs'] for r in validation_results.values())
        min_samples_per_type = min(r['pdfs'] for r in validation_results.values())

        print(f"\nTotal samples: {total_samples}")
        print(f"Minimum per type: {min_samples_per_type}")

        if min_samples_per_type >= 5000:
            print("✓ Dataset expansion target achieved (5000+ per type)")
            return True
        elif min_samples_per_type >= 1000:
            print("⚠ Partial expansion achieved (1000+ per type)")
            return True
        else:
            print("✗ Insufficient samples generated")
            return False

    def run_training_validation(self):
        """Run training on expanded dataset to validate performance."""
        print("\nStep 5: Running training validation on expanded dataset...")

        try:
            # Copy scaled images to main directories for training
            for category in ['word', 'google', 'python', 'fpdf']:
                src_dir = self.image_dirs[category]
                dst_dir = os.path.join(self.base_dir, f'{category}_pdfs_png')

                if os.path.exists(src_dir):
                    # Clear destination directory
                    if os.path.exists(dst_dir):
                        shutil.rmtree(dst_dir)
                    shutil.copytree(src_dir, dst_dir)
                    print(f"Copied {category} images to {dst_dir}")

            # Run 4-class training
            python_exe = os.path.join(os.path.dirname(sys.executable), 'python.exe')
            cmd = [python_exe, 'src/train_4class_classifiers.py']
            result = subprocess.run(cmd, cwd=self.base_dir, capture_output=True, text=True)

            if result.returncode == 0:
                print("✓ Training validation completed successfully")
                # Extract accuracy from output
                lines = result.stdout.split('\n')
                for line in lines:
                    if 'Accuracy:' in line:
                        print(f"Training result: {line.strip()}")
                return True
            else:
                print("✗ Training validation failed")
                print("Error:", result.stderr)
                return False

        except Exception as e:
            print(f"Error in training validation: {e}")
            return False

    def generate_expansion_report(self, start_time, results):
        """Generate a comprehensive expansion report."""
        total_time = time.time() - start_time

        report = f"""
DATASET EXPANSION REPORT
{'='*50}

Expansion Duration: {total_time:.2f} seconds ({total_time/60:.1f} minutes)

CURRENT DATASET STATUS:
{'='*30}
"""

        final_counts = self.count_current_pdfs()
        for category, count in final_counts.items():
            report += f"{category.capitalize()}: {count} PDFs\n"

        report += f"\nTotal: {sum(final_counts.values())} PDFs\n\n"

        report += f"""
EXPANSION RESULTS:
{'='*20}
"""

        if results.get('scaled_generation', False):
            report += "[SUCCESS] Scalable PDF generation: SUCCESS\n"
        else:
            report += "[FAILED] Scalable PDF generation: FAILED\n"

        if results.get('batch_word_generation', False):
            report += "[SUCCESS] Batch Word PDF generation: SUCCESS\n"
        else:
            report += "[FAILED] Batch Word PDF generation: FAILED\n"

        if results.get('image_conversion', False):
            report += "[SUCCESS] PDF to image conversion: SUCCESS\n"
        else:
            report += "[FAILED] PDF to image conversion: FAILED\n"

        if results.get('validation', False):
            report += "[SUCCESS] Dataset validation: SUCCESS\n"
        else:
            report += "[FAILED] Dataset validation: FAILED\n"

        if results.get('training', False):
            report += "[SUCCESS] Training validation: SUCCESS\n"
        else:
            report += "[FAILED] Training validation: FAILED\n"

        # Performance metrics
        min_samples = min(final_counts.values())
        if min_samples >= 5000:
            report += "\n[SUCCESS] TARGET ACHIEVED: 5000+ samples per PDF type!\n"
        elif min_samples >= 1000:
            report += f"\n[WARNING] PARTIAL SUCCESS: {min_samples} samples per type (target: 5000+)\n"
        else:
            report += f"\n[FAILED] INSUFFICIENT: Only {min_samples} samples per type\n"

        report += f"""
NEXT STEPS:
{'='*12}
1. Review generated PDFs for quality
2. Fine-tune classifiers if needed
3. Generate additional samples if target not met
4. Run final_analysis.py for comprehensive evaluation
5. Prepare submission with expanded dataset

RECOMMENDATIONS:
{'='*16}
- Ensure balanced representation across all PDF types
- Validate PDF quality and readability
- Test classifier performance on unseen data
- Document any data augmentation techniques used
"""

        # Save report
        report_path = os.path.join(self.base_dir, 'DATASET_EXPANSION_REPORT.md')
        with open(report_path, 'w') as f:
            f.write(report)

        print(f"\nReport saved to: {report_path}")
        print("\n" + "="*60)
        print(report)
        print("="*60)

    def run_full_expansion_pipeline(self, target_samples_per_type=5000):
        """Run the complete dataset expansion pipeline."""
        print("STARTING DATASET EXPANSION PIPELINE")
        print("=" * 60)
        print(f"Target: {target_samples_per_type} samples per PDF type")
        print(f"Total target: {target_samples_per_type * 4} PDFs")
        print("=" * 60)

        start_time = time.time()
        results = {}

        # Show current status
        current_counts = self.count_current_pdfs()
        print("Current PDF counts:")
        for category, count in current_counts.items():
            print(f"  {category}: {count}")
        print(f"  Total: {sum(current_counts.values())}")
        print()

        # Step 1: Scalable generation (FPDF and Python PDFs)
        results['scaled_generation'] = self.run_scaled_generation(target_samples_per_type)

        # Step 2: Batch Word generation
        results['batch_word_generation'] = self.run_batch_word_generation(target_samples_per_type)

        # Step 3: Convert all PDFs to images
        results['image_conversion'] = self.convert_pdfs_to_images_batch()

        # Step 4: Validate dataset
        results['validation'] = self.validate_expanded_dataset()

        # Step 5: Training validation
        results['training'] = self.run_training_validation()

        # Generate final report
        self.generate_expansion_report(start_time, results)

        return results

def main():
    """Main execution for dataset expansion pipeline."""
    print("ForensicsDetective Dataset Expansion Pipeline")
    print("=" * 50)

    # Check if we're in the right directory
    current_dir = os.getcwd()
    if os.path.basename(current_dir) == 'ForensicsDetective':
        # We're already in ForensicsDetective, use current directory
        base_dir = '.'
    elif os.path.exists('ForensicsDetective'):
        # We're in parent directory
        base_dir = 'ForensicsDetective'
    else:
        print("Error: Please run this script from the ForensicsDetective directory or its parent")
        print("Current directory:", current_dir)
        return

    # Initialize pipeline
    pipeline = DatasetExpansionPipeline(base_dir)

    # For demonstration, use smaller target
    # In production, use target_samples_per_type=5000
    results = pipeline.run_full_expansion_pipeline(target_samples_per_type=10000)  # Increased to 10,000 per type

    # Summary
    successful_steps = sum(1 for r in results.values() if r)
    total_steps = len(results)

    print(f"\nPipeline completed: {successful_steps}/{total_steps} steps successful")

    if successful_steps == total_steps:
        print("🎉 Dataset expansion pipeline completed successfully!")
    else:
        print("⚠ Pipeline completed with some failures. Check the report for details.")

if __name__ == "__main__":
    main()