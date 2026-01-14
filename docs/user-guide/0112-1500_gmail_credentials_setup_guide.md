# Gmail API Credentials Setup Guide

**Version**: 2.0.0
**Last Updated**: 2026-01-12
**Status**: Production

Complete step-by-step guide for creating Gmail API credentials and configuring them for Gman.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Part 1: Google Cloud Console Setup](#part-1-google-cloud-console-setup)
3. [Part 2: Project Configuration](#part-2-project-configuration)
4. [Part 3: Authenticate](#part-3-authenticate)
5. [Quick Reference](#quick-reference)
6. [Troubleshooting](#troubleshooting)

---

## Prerequisites

- [ ] Google account (Gmail)
- [ ] Gman installed (`pip install -e .`)
- [ ] Python 3.10+

---

## Part 1: Google Cloud Console Setup

### Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Sign in with your Google account (same as Gmail you want to access)
3. Click project dropdown (top left, next to "Google Cloud")
4. Click **"New Project"**
   - **Project name**: `Gman` (or any name)
   - **Organization**: Leave default or select yours
5. Click **"Create"**
6. Wait for project creation notification
7. Select your new project from the project dropdown

**Checkpoint**: You should see your project name in the top-left dropdown.

---

### Step 2: Enable Gmail API

1. In your project, navigate to **APIs & Services** → **Library**
   - Direct link: https://console.cloud.google.com/apis/library
2. Search for **"Gmail API"**
3. Click the **Gmail API** result card
4. Click **"Enable"** button
5. Wait for the API to enable (few seconds)

**Checkpoint**: You should see "Gmail API" in your enabled APIs list.

---

### Step 3: Configure OAuth Consent Screen

This step is required before creating credentials.

1. Go to **APIs & Services** → **OAuth consent screen**
   - Direct link: https://console.cloud.google.com/apis/credentials/consent

2. **User Type Selection**:
   - Select **"External"** (unless you have Google Workspace with admin access)
   - Click **"Create"**

3. **App Information** (Step 1 of 4):
   - **App name**: `Gman`
   - **User support email**: Select your email from dropdown
   - **App logo**: Skip (optional)
   - **App domain**: Skip all (optional)
   - **Developer contact email**: Enter your email
   - Click **"Save and Continue"**

4. **Scopes** (Step 2 of 4):
   - Click **"Add or Remove Scopes"**
   - In the filter, search for `gmail`
   - Check the following scope(s):
     - `https://www.googleapis.com/auth/gmail.readonly` (required)
     - `https://www.googleapis.com/auth/gmail.modify` (optional, for delete operations)
   - Click **"Update"**
   - Click **"Save and Continue"**

5. **Test Users** (Step 3 of 4):
   - Click **"+ Add Users"**
   - Enter your Gmail address (the one you'll access)
   - Click **"Add"**
   - Click **"Save and Continue"**

   > **Important**: For unverified apps, only test users can authorize. Add all Gmail accounts you want to use.

6. **Summary** (Step 4 of 4):
   - Review your settings
   - Click **"Back to Dashboard"**

**Checkpoint**: OAuth consent screen status should show "Testing" with your email as a test user.

---

### Step 4: Create OAuth Credentials

1. Go to **APIs & Services** → **Credentials**
   - Direct link: https://console.cloud.google.com/apis/credentials

2. Click **"+ Create Credentials"** at the top

3. Select **"OAuth client ID"**

4. **Configure OAuth client**:
   - **Application type**: Select **"Desktop app"**
   - **Name**: `Gman Desktop` (or any descriptive name)

5. Click **"Create"**

6. **Download credentials**:
   - A dialog appears with your client ID and secret
   - Click **"Download JSON"** button
   - Save the file (it will have a long name like `client_secret_xxx.json`)

7. **Rename the downloaded file** to exactly: `credentials.json`

**Checkpoint**: You have a `credentials.json` file with this structure:
```json
{
  "installed": {
    "client_id": "xxx.apps.googleusercontent.com",
    "project_id": "your-project-id",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_secret": "xxx",
    "redirect_uris": ["http://localhost"]
  }
}
```

---

## Part 2: Project Configuration

### Step 5: Place Credentials File

**Recommended location** (secure, outside any git repository):

#### Windows (PowerShell):
```powershell
# Create config directory
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.gman"

# Move credentials (adjust source path as needed)
Move-Item -Path "$env:USERPROFILE\Downloads\credentials.json" -Destination "$env:USERPROFILE\.gman\credentials.json"

# Verify
Get-Item "$env:USERPROFILE\.gman\credentials.json"
```

#### Windows (Command Prompt):
```cmd
mkdir %USERPROFILE%\.gman
move %USERPROFILE%\Downloads\credentials.json %USERPROFILE%\.gman\credentials.json
```

#### Linux/macOS:
```bash
# Create config directory
mkdir -p ~/.gman

# Move credentials (adjust source path as needed)
mv ~/Downloads/credentials.json ~/.gman/credentials.json

# Verify
ls -la ~/.gman/credentials.json
```

**Checkpoint**: File exists at `~/.gman/credentials.json`

---

### Step 6: Create Config File (Optional)

You can either use the CLI to initialize config or create it manually.

#### Option A: Use CLI (Recommended)
```bash
gman config --init
```

#### Option B: Create Manually

**Windows (PowerShell)**:
```powershell
@"
{
  "credentials_path": "~/.gman/credentials.json",
  "output_dir": "~/.gman/backups",
  "max_emails": 1000,
  "rate_limit_per_second": 10.0,
  "log_level": "INFO"
}
"@ | Out-File -FilePath "$env:USERPROFILE\.gman\config.json" -Encoding UTF8
```

**Linux/macOS**:
```bash
cat > ~/.gman/config.json << 'EOF'
{
  "credentials_path": "~/.gman/credentials.json",
  "output_dir": "~/.gman/backups",
  "max_emails": 1000,
  "rate_limit_per_second": 10.0,
  "log_level": "INFO"
}
EOF
```

#### Verify Config
```bash
gman config --show
```

**Checkpoint**: Config file exists and `gman config --show` displays your settings.

---

## Part 3: Authenticate

### Step 7: Run Authentication

```bash
gman auth
```

**What happens**:

1. CLI displays: `Starting authentication...`

2. **Browser opens automatically** to Google OAuth consent page

3. **Select your Google account** (the one you added as test user)

4. **If you see "Google hasn't verified this app" warning**:
   - Click **"Advanced"** (small link at bottom left)
   - Click **"Go to Gman (unsafe)"**
   - This is normal for personal/unverified apps

5. **Review permissions**:
   - The page shows what access Gman is requesting
   - Click **"Continue"** to grant permissions

6. **Browser shows success**: "The authentication flow has completed. You may close this window."

7. **CLI shows success**:
   ```
   Authentication successful!
   Authenticated as: your.email@gmail.com
   Total messages: 12,345
   Total threads: 4,567
   ```

**Checkpoint**: CLI shows your email and message counts.

---

### Step 8: Verify Authentication

Run auth command again to verify stored credentials:

```bash
gman auth
```

Should immediately show success without opening browser (credentials loaded from OS keyring).

**Test with a fetch**:
```bash
gman fetch --query "is:unread" --max-emails 5
```

**Checkpoint**: Fetch completes without authentication prompts.

---

## Quick Reference

### File Locations

| Item | Windows | Linux/macOS |
|------|---------|-------------|
| Credentials | `%USERPROFILE%\.gman\credentials.json` | `~/.gman/credentials.json` |
| Config | `%USERPROFILE%\.gman\config.json` | `~/.gman/config.json` |
| Backups | `%USERPROFILE%\.gman\backups\` | `~/.gman/backups/` |
| Token storage | Windows Credential Manager | macOS Keychain / Linux Secret Service |

### OAuth Scopes Used

| Scope | Permission | Used For |
|-------|------------|----------|
| `gmail.readonly` | Read-only access | Fetching, searching, analyzing emails |
| `gmail.modify` | Read + write access | Deleting emails, modifying labels |

### Common Commands

```bash
# Authenticate (first time or refresh)
gman auth

# Force re-authentication (clear stored credentials)
gman auth --force

# Initialize configuration
gman config --init

# Show current configuration
gman config --show

# Validate configuration
gman config --validate

# Test fetch (5 unread emails)
gman fetch --query "is:unread" --max-emails 5

# Fetch with specific output
gman fetch --query "after:2025/01/01" --output-dir ./my-backup
```

---

## Troubleshooting

### Error: "Credentials file not found"

**Cause**: `credentials.json` not in expected location.

**Solution**:
1. Verify file exists: `ls ~/.gman/credentials.json`
2. Check config points to correct path: `gman config --show`
3. Re-download from Google Cloud Console if missing

---

### Error: "Access blocked: This app's request is invalid" or "redirect_uri_mismatch"

**Cause**: Credentials not configured as Desktop app.

**Solution**:
1. Go to Google Cloud Console → Credentials
2. Delete existing OAuth client
3. Create new OAuth client ID with type **"Desktop app"**
4. Download new `credentials.json`

---

### Error: "Access blocked: Gman has not completed the Google verification process"

**Cause**: Your email not added as test user.

**Solution**:
1. Go to Google Cloud Console → OAuth consent screen
2. Click **"Edit App"**
3. Go to **"Test users"** section
4. Add your Gmail address
5. Save and retry authentication

---

### Error: "Token has been expired or revoked"

**Cause**: Stored credentials expired or manually revoked.

**Solution**:
```bash
gman auth --force
```
This clears stored credentials and initiates fresh OAuth flow.

---

### Error: "Insufficient Permission" or "Request had insufficient authentication scopes"

**Cause**: Required scope not granted during authorization.

**Solution**:
1. Go to Google Cloud Console → OAuth consent screen
2. Edit scopes to include required scope (e.g., `gmail.modify` for delete)
3. Force re-authentication:
   ```bash
   gman auth --force
   ```
4. Accept the new permissions in browser

---

### Browser doesn't open automatically

**Cause**: System doesn't support automatic browser launch.

**Solution**:
1. Copy the URL displayed in terminal
2. Manually paste into browser
3. Complete authorization
4. Return to terminal (should auto-detect completion)

---

### Credentials stored in wrong keyring account

**Cause**: Multiple user accounts or keyring issues.

**Solution**:
1. Clear keyring entry manually:
   - **Windows**: Credential Manager → Windows Credentials → Find `gman` → Remove
   - **macOS**: Keychain Access → Find `gman` → Delete
   - **Linux**: `secret-tool clear service gman`
2. Re-authenticate: `gman auth`

---

## See Also

- [Configuration Reference](configuration.md) - Full config options
- [CLI Reference](cli-reference.md) - All CLI commands
- [README](../../README.md) - Project overview

---

**Setup complete!** You're ready to use Gman.
