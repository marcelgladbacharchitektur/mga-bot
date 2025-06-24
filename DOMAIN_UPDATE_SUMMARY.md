# Domain Update Summary - Marcel Gladbach Infrastructure

## Overview
All configuration files and scripts have been updated to reflect the correct domain mappings and service architecture.

## Correct Domain Mapping

| Service | Subdomain | Purpose |
|---------|-----------|---------|
| Umami Analytics | analytics.marcelgladbach.com | Web analytics platform |
| Uptime Kuma | status.marcelgladbach.com | Service monitoring (NOT "Kumo") |
| SvelteKit Portal | portal.marcelgladbach.com | Main web portal |
| Telegram Bot | bot.marcelgladbach.com | Telegram bot webhook endpoint |

## Files Updated

### 1. Architecture Documentation
- `/ARCHITECTURAL_DEPLOYMENT_PLAN.md` - Updated all domain references and removed Kumo references
- `/INTEGRATION_GUIDE.md` - Updated domain mappings and service lists

### 2. Deployment Scripts
- `/scripts/safe_server_deploy.sh` - Updated domains, SSL paths, and service checks
- `/scripts/server_analysis.sh` - Updated to check for correct services
- `/scripts/setup_monitoring.sh` - Updated monitoring URLs
- `/scripts/deploy_nginx_fix.sh` - Updated organization name in SSL cert
- `/scripts/rollback_deployment.sh` - Removed Kumo from service checks
- `/deploy.sh` - No changes needed (doesn't contain domain references)

### 3. New Files Created
- `/nginx/bot-marcelgladbach.conf` - Nginx configuration template for bot.marcelgladbach.com
- `/scripts/check_existing_nginx.sh` - Script to check existing nginx configurations
- `/DOMAIN_UPDATE_SUMMARY.md` - This summary document

## Important Notes

### SSL Certificates
The configurations assume Let's Encrypt certificates at:
- `/etc/letsencrypt/live/marcelgladbach.com/fullchain.pem`
- `/etc/letsencrypt/live/marcelgladbach.com/privkey.pem`

If using a wildcard certificate, ensure it covers `*.marcelgladbach.com`.

### Nginx Configuration Safety
Before deploying:
1. Run `/scripts/check_existing_nginx.sh` on the server to check for existing configurations
2. Backup all existing nginx configs: `sudo cp -r /etc/nginx /etc/nginx.backup.$(date +%Y%m%d)`
3. Test any new configurations: `sudo nginx -t`
4. Reload (don't restart) nginx: `sudo systemctl reload nginx`

### DNS Requirements
Ensure these A records point to 157.90.232.184:
- analytics.marcelgladbach.com
- status.marcelgladbach.com
- portal.marcelgladbach.com
- bot.marcelgladbach.com

### Service Names Clarification
- **Uptime Kuma** (NOT "Kumo") - Service monitoring dashboard
- **No file manager service** - Kumo was incorrectly listed and has been removed

## Deployment Checklist

Before deploying the bot:

1. [ ] Verify DNS records are configured
2. [ ] Run `check_existing_nginx.sh` to check for conflicts
3. [ ] Ensure SSL certificates exist or create them with certbot
4. [ ] Backup existing configurations
5. [ ] Run `server_analysis.sh` to understand current state
6. [ ] Deploy using `safe_server_deploy.sh`
7. [ ] Monitor deployment with Uptime Kuma at status.marcelgladbach.com

## Rollback Plan

If issues occur:
1. Run `/scripts/rollback_deployment.sh`
2. This will safely remove the bot without affecting other services
3. Logs are archived before removal

## Contact for Questions

For any questions about this infrastructure update, refer to the updated documentation or check the existing services at their respective subdomains.