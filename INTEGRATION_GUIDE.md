# Marcel Gladbach Telegram Bot - Server Integration Guide

## Overview
This guide provides a step-by-step approach to safely integrate the MGA Telegram Bot into your existing server infrastructure without disrupting current services.

## Pre-Deployment Checklist

### 1. Run Server Analysis
First, understand your current server state:
```bash
ssh root@157.90.232.184
cd /tmp
# Copy and run the server_analysis.sh script
./server_analysis.sh > server_analysis_$(date +%Y%m%d).log
```

### 2. Verify Prerequisites
- [ ] Port 5000 is available
- [ ] Subdomain `bot.marcelgladbach.com` is not in use
- [ ] DNS A record for `bot.marcelgladbach.com` → `157.90.232.184`
- [ ] At least 1GB free disk space
- [ ] Python 3.8+ installed
- [ ] Git installed

### 3. Prepare Credentials
Create `.env` file with:
```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
GOOGLE_SERVICE_ACCOUNT_JSON=/opt/mga-bot/service-account-key.json
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_supabase_anon_key
SHARED_DRIVE_ID=your_shared_drive_id
```

## Deployment Process

### Phase 1: Setup
```bash
# 1. Transfer deployment scripts to server
scp scripts/safe_server_deploy.sh root@157.90.232.184:/tmp/
scp scripts/rollback_deployment.sh root@157.90.232.184:/tmp/
scp scripts/server_analysis.sh root@157.90.232.184:/tmp/

# 2. SSH to server
ssh root@157.90.232.184

# 3. Run analysis first
/tmp/server_analysis.sh

# 4. Review output and ensure no conflicts
```

### Phase 2: Deploy
```bash
# 1. Make scripts executable
chmod +x /tmp/*.sh

# 2. Run deployment
/tmp/safe_server_deploy.sh

# 3. Monitor deployment progress
# The script will pause at critical points
```

### Phase 3: Configure Webhook
```bash
# After successful deployment
export TOKEN="your_telegram_bot_token"
curl -F "url=https://bot.marcelgladbach.com/webhook" \
     https://api.telegram.org/bot$TOKEN/setWebhook
```

### Phase 4: Setup Monitoring
```bash
# 1. Run monitoring setup
/opt/mga-bot/scripts/setup_monitoring.sh

# 2. Add to Uptime Kuma manually:
# - URL: https://bot.marcelgladbach.com/health
# - Check interval: 60 seconds
# - Alert on 3 consecutive failures
```

## Integration Points

### 1. Nginx Structure
Your nginx will have this structure:
```
/etc/nginx/
├── sites-available/
│   ├── default
│   ├── umami.conf
│   ├── uptime-kuma.conf
│   ├── portal.conf
│   └── telegram-bot.conf  # New
└── sites-enabled/
    └── ... (symlinks to above)
```

### 2. Service Architecture
```
systemctl status mga-telegram-bot  # Your bot
systemctl status umami            # Analytics
systemctl status uptime-kuma      # Monitoring
systemctl status portal           # SvelteKit app
```

### 3. Port Mapping
| Service | Internal Port | External URL |
|---------|---------------|--------------------------------------|
| Umami Analytics | 3000 | https://analytics.marcelgladbach.com |
| Uptime Kuma | 3001 | https://status.marcelgladbach.com |
| SvelteKit Portal | 4000 | https://portal.marcelgladbach.com |
| Telegram Bot | 5000 | https://bot.marcelgladbach.com |

## Troubleshooting

### Bot Not Responding
```bash
# Check service status
sudo systemctl status mga-telegram-bot

# View logs
sudo journalctl -u mga-telegram-bot -f

# Check port
sudo ss -tlnp | grep 5000

# Test health endpoint
curl http://localhost:5000/health
```

### Nginx Issues
```bash
# Test configuration
sudo nginx -t

# Check error logs
sudo tail -f /var/log/nginx/error.log

# Reload safely
sudo systemctl reload nginx
```

### Webhook Problems
```bash
# Check webhook status
curl https://api.telegram.org/bot$TOKEN/getWebhookInfo

# View webhook logs
sudo tail -f /var/log/nginx/bot.marcelgladbach.com.access.log
```

## Maintenance

### Daily Checks
- Monitor bot health in Uptime Kuma
- Check disk space: `df -h`
- Review logs for errors

### Weekly Tasks
- Check SSL certificate expiry
- Review resource usage
- Update bot if needed

### Updates
```bash
cd /opt/mga-bot
sudo -u mga-bot git pull
sudo -u mga-bot /opt/mga-bot/venv/bin/pip install -r requirements.txt
sudo systemctl restart mga-telegram-bot
```

## Emergency Procedures

### Quick Stop
```bash
sudo systemctl stop mga-telegram-bot
```

### Full Rollback
```bash
/opt/mga-bot/scripts/rollback_deployment.sh
```

### Service Recovery
If other services are affected:
```bash
# Restart all services
sudo systemctl restart nginx
sudo systemctl restart umami
sudo systemctl restart uptime-kuma
sudo systemctl restart portal
```

## Security Notes

1. The bot runs as a dedicated user `mga-bot`
2. Telegram webhook only accepts IPs from Telegram's range
3. SSL/TLS is mandatory for webhooks
4. The bot has restricted file system access
5. Logs are rotated automatically

## Support Contacts

- Server Admin: [Your contact]
- Hetzner Support: https://console.hetzner.cloud/
- Telegram Bot API: https://core.telegram.org/bots/api

---

Remember: Always test in off-peak hours and have the rollback script ready!