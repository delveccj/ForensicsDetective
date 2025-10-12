# SETUP

 ## First ForensicsDetective Task: Configure the Archive


 ## 1. System Data

**System of Operation:** macOS 
**Version of Python:** 3.13 (in virtual environment `.venv`) 
**Version of GIT:** (check with `git --version`)
**Homebrew was used to install Poppler as the PDF engine. 
** Package Manager:** pip 
**Virtual Environment:** `.venv` 
**IDE/Terminal Used:** macOS Terminal

 ## 2. The repository setup procedure

 ### First Step: Fork - Original Source:  [ForensicsDetective: https://github.com/delveccj] Forked to my GitHub workspace: [https://github.com/raghuldav/ForensicsDetective] (https://github.com/delveccj/ForensicsDetective) (ForensicsDetective: https://github.com/raghuldav)

 ### Clone 
```bash 
git clone git@github.com:raghuldav/ForensicsDetective.git 
cd ForensicsDetective

### Step 2)  Detective Forensics

 ### Create and Activate the Virtual Environment in Step Three 
```bash 
Python3 -m venv.venv source.venv/bin/activate

 Installing dependencies is the fourth step. 
```bash 
pip install --upgrade 
pip install numpy pandas scikit-learn pillow pdf2image reportlab scikit-image matplotlib tqdm python-docx pypdf2
brew install poppler

 ### Step 5: Examine the Framework
 To see if any folders or scripts are required:
 "convert|classif|train|pdf|image" || true ```bash ls -R | egrep -i

 Key files and folders found:

 convert.py

 Python's train_baseline_classifiers

 binary_image.py from pdf

 Directories: google_docs_pdfs/, word_pdfs/ Python_pdfs/

 Directories of output: *_pdfs_png/

 ## 3. Verification of Conversion (PDF → PNG)
Confirmed convert pipeline using convert.py on all three data sets
```bash
mkdir -p logsided

# Convert Word PDFs → PNGs
```bash
python convert.py --in_dir word_pdfs --out_dir word_pdfs_png --limit 3 2>&1 | tee logs/conversion_word.txt || "\\"
python convert.py word_pdfs word_pdfs_png 2>&1 | tee logs/conversion_word.txt

# Convert Google Docs PDFs → PNGs
```bash
python convert.py --in_dir google_docs_pdfs --out_dir google_docs_pdfs_png --limit 3 2>&1 | tee logs/conversion_gdocs.txt || \
python convert.py google_docs_pdfs google_docs_pdfs_png 2>&1 | tee logs/conversion_gdocs.txt

# Convert Python PDFs → PNGs
```bash
python convert.py --in_dir python_pdfs --out_dir python_pdfs_png --limit 3 2>&1 | tee logs/conversion_python.txt || \
python convert.py python_pdfs python_pdfs_png 2>&1 | tee logs/conversion_python.txt

### Result:
PNG images were successfully created under:

word_pdfs_png/
google_docs_pdfs_png/

python_pdfs_png/

## 4. Classification Verification
Trained and validated baseline classifiers with train_baseline_classifiers.py.
```bash
python train_baseline_classifiers.py \
  --data_dirs word_pdfs_png google_docs_pdfs_png python_pdfs_png \
  --out results_baseline 2>&1 | tee logs/classification_baseline.txt || \
python train_baseline_classifiers.py word_pdfs_png google_docs_pdfs_png python_pdfs_png \
  2>&1 | tee logs/classification_baseline.txt

### Result:
Baseline classifier ran successfully, showing confusion matrix and accuracy figures in terminal output and logs.

## 5. Verifying Logs and Output
```bash
logs/conversion_word.txt
logs/conversion_gdocs.txt
logs/conversion_python.txt
logs/classification_baseline.txt

### Output directories confirmed:
word_pdfs_png/
google_docs_pdfs_png/
python_pdfs_png/

All scripts completed successfully with no errors.


## 6. Summary of Validation Commands
```bash
# Start environment
source .venv/bin/activate

# Script help text
python convert.py -h
python train_baseline_classifiers.py -h

# Run conversions
python convert.py word_pdfs word_pdfs_png
python convert.py google_docs_pdfs google_docs_pdfs_png
python convert.py python_pdfs python_pdfs_png



# Run classification
python train_baseline_classifiers.py word_pdfs_png google_docs_pdfs_png python_pdfs_png



