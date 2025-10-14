# OAuth Setup Guide for Personal Google Drive

This guide shows how to set up OAuth to use YOUR personal Google Drive (much more reliable than service accounts!)

## Step 1: Go to Google Cloud Console

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select your existing project (or create a new one)
3. Make sure Google Drive API is enabled (you may have done this already)

## Step 2: Create OAuth 2.0 Credentials (NOT Service Account!)

1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → **"OAuth client ID"** (not service account!)
3. If prompted, configure the OAuth consent screen:
   - **User type**: External (for personal Gmail accounts)
   - **Application name**: "PDF Converter" (keep it simple!)
   - **Publishing status**: **TESTING** (very important!)
   - **Test users**: Add your email address
   - **Scopes**: No need to add any (we'll handle this in code)

4. For OAuth client ID:
   - **Application type**: "Desktop application"
   - **Name**: "PDF Converter Desktop App"
   - Click "Create"

## Step 3: Download OAuth Credentials

1. After creating, you'll see a download button
2. Click "Download JSON"
3. **Rename the file to**: `oauth_credentials.json`
4. **Move it to your project directory**: `/Users/jmdv/ResearchAndDevelopment/ForensicsDetective/`

## Step 4: Install Additional OAuth Package

```bash
pip install google-auth-oauthlib
```

## Step 5: Run the OAuth Script

```bash
python google_docs_converter_oauth.py
```

## What Will Happen:

1. **First run**: A browser window opens asking you to log into your Google account
2. **You authorize**: Grant permission for the app to access your Google Drive
3. **Credentials saved**: Future runs won't need browser login
4. **Conversion starts**: Uses YOUR personal 15GB Google Drive space

## Key Differences from Service Account:

| Service Account | OAuth (Personal) |
|----------------|------------------|
| ❌ Mysterious 0GB quota | ✅ Your full 15GB Drive space |
| ❌ Isolated storage space | ✅ Uses your familiar Google Drive |
| ❌ No web interface access | ✅ You can see files in drive.google.com |
| ❌ Complex permissions | ✅ Simple "yes/no" authorization |

## Security Notes:

- **OAuth is SAFER**: You control what the app can access
- **Revokable**: You can revoke access anytime in your Google Account settings
- **Transparent**: You can see exactly what files are created/deleted
- **No shared credentials**: Your personal login, your control

## Troubleshooting:

1. **"OAuth credentials not found"**: Make sure file is named exactly `oauth_credentials.json`
2. **Browser doesn't open**: The script will show a URL you can copy/paste
3. **Permission denied**: Make sure you're logged into the correct Google account
4. **Quota exceeded**: Check your personal Google Drive storage (drive.google.com)

## File Locations:

After setup, you'll have:
- `oauth_credentials.json` (OAuth credentials - keep private!)
- `token.pickle` (Saved login session - created automatically)

Ready to convert 398 PDFs with your personal Google Drive! 🚀