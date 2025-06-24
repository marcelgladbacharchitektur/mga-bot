# Fix SSH Key Format for GitHub Actions

The error "error in libcrypto" occurs when your SSH private key is in the newer OpenSSH format, which is not compatible with some SSH agents.

## Solution: Convert Your SSH Key to PEM Format

### 1. Check your current key format
```bash
head -n 1 github_deploy_rsa
```

If it shows `-----BEGIN OPENSSH PRIVATE KEY-----`, you need to convert it.

### 2. Convert to PEM format
```bash
# Make a backup first
cp github_deploy_rsa github_deploy_rsa.backup

# Convert to PEM format
ssh-keygen -p -f github_deploy_rsa -m PEM -N ""
```

### 3. Verify the conversion
```bash
head -n 1 github_deploy_rsa
```

It should now show `-----BEGIN RSA PRIVATE KEY-----`

### 4. Update the GitHub secret
1. Copy the entire content of the converted key:
   ```bash
   cat github_deploy_rsa
   ```

2. Go to your GitHub repository:
   - Settings → Secrets and variables → Actions
   - Click on `SSH_PRIVATE_KEY`
   - Click "Update secret"
   - Paste the new PEM format key
   - Save

### Alternative: Generate a new SSH key pair in PEM format
```bash
# Generate new key in PEM format
ssh-keygen -t rsa -b 4096 -m PEM -f github_deploy_rsa_new -N ""

# Display public key to add to server
cat github_deploy_rsa_new.pub
```

## Important Notes
- Always use PEM format for GitHub Actions compatibility
- The key must include the header `-----BEGIN RSA PRIVATE KEY-----`
- Don't commit private keys to your repository
- After updating the secret, delete local copies of private keys