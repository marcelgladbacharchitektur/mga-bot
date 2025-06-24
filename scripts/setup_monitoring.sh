#!/bin/bash
# Setup monitoring for MGA Telegram Bot in Uptime Kuma

# Configuration
UPTIME_KUMA_URL="https://status.marcelgladbach.com"
BOT_HEALTH_URL="https://bot.marcelgladbach.com/health"
MONITOR_NAME="Marcel Gladbach Telegram Bot"

echo "🔍 Setting up Uptime Kuma Monitoring"
echo "==================================="

# Note: Uptime Kuma API requires authentication
# You'll need to get your API token from Uptime Kuma settings

read -p "Enter your Uptime Kuma API username: " UK_USERNAME
read -s -p "Enter your Uptime Kuma API password: " UK_PASSWORD
echo ""

# Create monitor via Uptime Kuma API
# This is a template - adjust based on your Uptime Kuma version
cat > /tmp/monitor-config.json << EOF
{
  "type": "http",
  "name": "$MONITOR_NAME",
  "url": "$BOT_HEALTH_URL",
  "method": "GET",
  "interval": 60,
  "retryInterval": 60,
  "maxretries": 3,
  "accepted_statuscodes": ["200"],
  "dns_resolve_type": "A",
  "dns_resolve_server": "1.1.1.1",
  "proxyId": null,
  "notificationIDList": {},
  "tags": ["telegram", "bot", "production"],
  "mqttUsername": "",
  "mqttPassword": "",
  "mqttTopic": "",
  "mqttSuccessMessage": "",
  "databaseConnectionString": "",
  "databaseQuery": "",
  "authMethod": "",
  "authWorkstation": "",
  "authDomain": "",
  "headers": "",
  "body": "",
  "pushToken": ""
}
EOF

# Alternative: Manual setup instructions
echo ""
echo "📋 Manual Setup Instructions for Uptime Kuma:"
echo "============================================"
echo ""
echo "1. Open Uptime Kuma: $UPTIME_KUMA_URL"
echo "2. Click 'Add New Monitor'"
echo "3. Configure as follows:"
echo "   - Monitor Type: HTTP(s)"
echo "   - Friendly Name: $MONITOR_NAME"
echo "   - URL: $BOT_HEALTH_URL"
echo "   - Heartbeat Interval: 60 seconds"
echo "   - Retries: 3"
echo "   - HTTP Method: GET"
echo "   - Expected Status Codes: 200"
echo ""
echo "4. Optional Notifications:"
echo "   - Add notification channels (Email, Telegram, etc.)"
echo "   - Set up alerts for downtime"
echo ""
echo "5. Advanced Settings:"
echo "   - Certificate Expiry Notification: 14 days"
echo "   - Ignore TLS/SSL error: No (keep secure)"
echo ""

# Create a simple monitoring script for local checks
cat > /opt/mga-bot/scripts/local_monitor.sh << 'EOF'
#!/bin/bash
# Local monitoring script for MGA Bot

BOT_URL="http://localhost:5000/health"
TELEGRAM_API="https://api.telegram.org"

# Check bot health
echo -n "Bot Health: "
if curl -s "$BOT_URL" | grep -q "ok\|healthy"; then
    echo "✅ OK"
else
    echo "❌ FAILED"
    # Send alert (implement your alert mechanism)
fi

# Check Telegram API connectivity
echo -n "Telegram API: "
if curl -s -o /dev/null -w "%{http_code}" "$TELEGRAM_API" | grep -q "200\|404"; then
    echo "✅ Reachable"
else
    echo "❌ Unreachable"
fi

# Check bot process
echo -n "Bot Process: "
if systemctl is-active --quiet mga-telegram-bot; then
    echo "✅ Running"
    # Show memory usage
    PID=$(systemctl show -p MainPID mga-telegram-bot | cut -d= -f2)
    if [ "$PID" != "0" ]; then
        MEM=$(ps -p $PID -o %mem= | tr -d ' ')
        echo "   Memory Usage: ${MEM}%"
    fi
else
    echo "❌ Not Running"
fi

# Check disk space
echo -n "Disk Space: "
USAGE=$(df -h / | awk 'NR==2 {print $5}' | tr -d '%')
if [ "$USAGE" -lt 80 ]; then
    echo "✅ ${USAGE}% used"
else
    echo "⚠️  ${USAGE}% used (High!)"
fi
EOF

chmod +x /opt/mga-bot/scripts/local_monitor.sh

# Create cron job for local monitoring
echo "*/5 * * * * /opt/mga-bot/scripts/local_monitor.sh >> /var/log/mga-telegram-bot/monitor.log 2>&1" | sudo crontab -

echo ""
echo "✅ Monitoring setup complete!"
echo ""
echo "Additional monitoring endpoints to configure:"
echo "- Bot Health: $BOT_HEALTH_URL"
echo "- Nginx Status: https://bot.marcelgladbach.com/ (should return 404)"
echo ""
echo "Suggested alert rules:"
echo "1. Bot down for > 5 minutes → High priority alert"
echo "2. Response time > 5 seconds → Warning"
echo "3. SSL certificate expires in < 14 days → Warning"
echo "4. Disk usage > 80% → Warning"
echo "5. Memory usage > 80% → Warning"