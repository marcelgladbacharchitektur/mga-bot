# GitHub Secrets Setup Guide

This guide explains how to configure the required GitHub secrets for the deployment workflow.

## Required Secrets

Navigate to your repository's Settings → Secrets and variables → Actions, then add the following secrets:

### 1. SSH Authentication
- **SSH_PRIVATE_KEY**: Your SSH private key for accessing the deployment server
  ```
  -----BEGIN OPENSSH PRIVATE KEY-----
  [Your private key content]
  -----END OPENSSH PRIVATE KEY-----
  ```
- **SSH_HOST**: The hostname or IP address of your deployment server
- **SSH_USER**: The username for SSH connection
- **TARGET_DIR**: The target directory path on the server (e.g., `/home/user/telegram-bot`)

### 2. Telegram Configuration
- **TELEGRAM_BOT_TOKEN**: Your Telegram Bot API token from @BotFather

### 3. API Keys
- **GROQ_API_KEY**: Your Groq API key for AI functionality
- **GOOGLE_SERVICE_ACCOUNT_JSON**: The complete JSON content of your Google service account credentials
- **GOOGLE_DRIVE_ROOT_FOLDER_ID**: The ID of your Google Drive root folder

### 4. Supabase Configuration
- **SUPABASE_URL**: Your Supabase project URL
- **SUPABASE_ANON_KEY**: Your Supabase anonymous key

## Setting Up Secrets

1. Go to your repository on GitHub
2. Click on "Settings" tab
3. In the left sidebar, click "Secrets and variables" → "Actions"
4. Click "New repository secret"
5. Enter the secret name exactly as shown above
6. Paste the secret value
7. Click "Add secret"

## Important Notes

- Make sure there are no extra spaces or newlines in your secrets
- For multi-line secrets like SSH_PRIVATE_KEY and GOOGLE_SERVICE_ACCOUNT_JSON, paste them exactly as they are
- The workflow will validate that all required secrets are present before deployment
- Never commit these secrets to your repository

## Testing Your Configuration

### 1. Test on GitHub (Recommended)
After setting up your secrets, you can test them using the test workflow:

1. Go to your repository's "Actions" tab
2. Select "Test Secrets Configuration" from the left sidebar
3. Click "Run workflow" → "Run workflow"
4. Check the output to see which secrets are configured correctly

### 2. Test Locally
You can also test your configuration locally:

```bash
# Run the local test script
python3 test_secrets_locally.py
```

To set environment variables locally for testing:
```bash
export TELEGRAM_BOT_TOKEN="your_token_here"
export GROQ_API_KEY="your_api_key_here"
# ... set other variables
```

## Troubleshooting

- If you see "Context access might be invalid" warnings in your IDE, this is normal when the secrets aren't available locally. The workflow will work correctly on GitHub Actions as long as the secrets are properly configured in your repository settings.
- Make sure your SSH_PRIVATE_KEY includes the full key with header and footer lines
- For GOOGLE_SERVICE_ACCOUNT_JSON, paste the entire JSON content as a single-line or multi-line string
- If deployment fails, check the GitHub Actions logs for specific error messages