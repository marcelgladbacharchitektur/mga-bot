# Deployment Guide - MGA Bot

## Overview

This guide documents the CI/CD deployment process for the MGA Bot to Hetzner server using GitHub Actions with rsync-based deployment.

## Required GitHub Secrets

Before deployment can work, configure these secrets in your GitHub repository:

1. **SSH_PRIVATE_KEY**: RSA private key for authentication
   - Format: Complete RSA private key including headers
   - Example: `-----BEGIN OPENSSH PRIVATE KEY-----...`

2. **SSH_USER**: SSH username for server access
   - Default: `root`

3. **SSH_HOST**: Server IP address or hostname
   - Example: `157.90.232.184`

4. **TARGET_DIR**: Deployment directory on server
   - Example: `/var/www/mga-portal`

5. **Application Secrets**:
   - TELEGRAM_BOT_TOKEN
   - GROQ_API_KEY
   - GOOGLE_SERVICE_ACCOUNT_JSON
   - GOOGLE_DRIVE_ROOT_FOLDER_ID
   - SUPABASE_URL
   - SUPABASE_ANON_KEY

## Deployment Process

The deployment follows these steps:

1. **Test Phase**:
   - Runs pytest tests with mocked external services
   - Validates code quality and functionality

2. **SSH Setup**:
   - Authenticates using RSA key via webfactory/ssh-agent
   - Adds server to known_hosts

3. **Environment Configuration**:
   - Creates .env file with all secrets
   - File is synced with the application code

4. **Rsync Deployment**:
   - Syncs only necessary files (Python, requirements, tests, .env)
   - Excludes development files and caches
   - Uses --delete for clean deployments

5. **Post-Deployment**:
   - Installs/updates Python dependencies
   - Restarts PM2 process with updated environment
   - Saves PM2 configuration

## Server Setup

Ensure the server has:
- Python 3.10+
- pip3
- PM2 (for process management)
- SSH access with the provided key

## Testing Deployment

1. Make a change to any Python file
2. Commit and push to main branch
3. Monitor GitHub Actions for deployment progress
4. Check server logs: `pm2 logs telegram-google`

## Troubleshooting

### SSH Authentication Fails
- Verify SSH_PRIVATE_KEY is correctly formatted
- Ensure server has corresponding public key in authorized_keys
- Check SSH_USER and SSH_HOST values

### Rsync Errors
- Verify TARGET_DIR exists on server
- Check file permissions
- Ensure rsync is installed on server

### PM2 Issues
- Run `pm2 list` to check process status
- Check logs: `pm2 logs telegram-google`
- Restart manually: `pm2 restart telegram-google`