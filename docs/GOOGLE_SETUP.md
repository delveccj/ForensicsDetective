# Google Drive API Setup Guide

Follow these steps to set up Google Drive API access for the PDF conversion script.

## Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click "Select a project" → "New Project"
3. Name your project (e.g., "forensics-detective-pdf-converter")
4. Click "Create"

## Step 2: Enable Google Drive API

1. In your project dashboard, go to "APIs & Services" → "Library"
2. Search for "Google Drive API"
3. Click on it and press "Enable"

## Step 3: Create Service Account

1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "Service Account"
3. Enter service account details:
   - **Name**: `pdf-converter-service`
   - **Description**: `Service account for converting Word docs to PDFs via Google Docs`
4. Click "Create and Continue"
5. Skip the optional steps (click "Done")

## Step 4: Generate Credentials JSON

1. Find your newly created service account in the credentials list
2. Click on the service account email
3. Go to the "Keys" tab
4. Click "Add Key" → "Create new key"
5. Select "JSON" format
6. Click "Create"
7. A JSON file will download automatically

## Step 5: Set Up Credentials File

1. Rename the downloaded JSON file to `google_credentials.json`
2. Move it to your project directory: `/Users/jmdv/ResearchAndDevelopment/ForensicsDetective/`
3. **IMPORTANT**: Add this file to your `.gitignore` to keep credentials private

## Step 6: Test the Setup

Run this command to test a small batch:

```bash
python google_docs_converter.py
```

## Troubleshooting

### Common Issues:

1. **"Credentials file not found"**
   - Make sure `google_credentials.json` is in the project root
   - Check the file name is exactly `google_credentials.json`

2. **"API not enabled"**
   - Ensure Google Drive API is enabled in your project
   - Wait a few minutes after enabling APIs

3. **"Access denied"**
   - Service account permissions are automatically sufficient for this use case
   - The script creates its own temporary folder in Google Drive

4. **"Quota exceeded"**
   - Google Drive API has daily limits
   - The script includes delays to respect rate limits
   - If needed, you can run the script in smaller batches

## Security Notes

- The service account only has access to files it creates
- All temporary Google Docs are automatically deleted after PDF export
- Your credentials file should never be shared or committed to version control
- Consider setting up API quotas/limits in Google Cloud Console for safety

## Script Features

- **Batch processing**: Handles all 398 files automatically
- **Resume capability**: Skips files that already exist as PDFs
- **Progress tracking**: Shows detailed progress and error reporting
- **Cleanup**: Automatically deletes temporary Google Docs
- **Rate limiting**: Includes delays to respect API limits

Once you've completed the setup, you're ready to convert all 398 Word documents to Google Docs PDFs!