#!/bin/bash
# Comprehensive server diagnosis for all services

echo "🔍 FULL SERVER DIAGNOSIS"
echo "======================="
echo "Checking ALL services on marcelgladbach.com"
echo ""

# 1. System Status
echo "1️⃣ SYSTEM STATUS:"
echo "Uptime: $(uptime)"
echo "Disk usage:"
df -h | grep -E "/$|/var"
echo "Memory:"
free -h
echo ""

# 2. Check all services with PM2
echo "2️⃣ PM2 PROCESSES:"
pm2 list
echo ""

# 3. Check systemd services
echo "3️⃣ SYSTEMD SERVICES:"
sudo systemctl status nginx --no-pager | head -10
echo ""

# 4. Check all nginx sites
echo "4️⃣ NGINX SITES:"
ls -la /etc/nginx/sites-enabled/
echo ""
echo "Nginx config test:"
sudo nginx -t
echo ""

# 5. Test each subdomain
echo "5️⃣ TESTING SUBDOMAINS:"
for domain in portal.marcelgladbach.com analytics.marcelgladbach.com status.marcelgladbach.com bot.marcelgladbach.com; do
    echo -n "Testing $domain: "
    if curl -sI https://$domain | grep -q "HTTP/"; then
        echo "✅ Responding"
    else
        echo "❌ Not responding"
    fi
done
echo ""

# 6. Check ports
echo "6️⃣ PORT STATUS:"
echo "Active listeners:"
sudo netstat -tlnp | grep -E ":(80|443|3000|3001|3002|4000|5000|8080|8443)\s" || sudo ss -tlnp | grep -E ":(80|443|3000|3001|3002|4000|5000|8080|8443)\s"
echo ""

# 7. Check SvelteKit portal specifically
echo "7️⃣ SVELTEKIT PORTAL CHECK:"
# Find portal directory
PORTAL_DIR=$(find /var/www -name "portal" -type d 2>/dev/null | grep -v node_modules | head -1)
if [ -n "$PORTAL_DIR" ]; then
    echo "Portal directory: $PORTAL_DIR"
    cd "$PORTAL_DIR"
    
    # Check if process is running
    if pm2 list | grep -q "portal\|sveltekit"; then
        echo "✅ Portal process found in PM2"
        pm2 describe portal 2>/dev/null || pm2 describe sveltekit 2>/dev/null || echo "Cannot get PM2 details"
    else
        echo "❌ Portal not found in PM2"
        echo "Looking for node processes:"
        ps aux | grep -E "node|vite" | grep -v grep
    fi
else
    echo "❌ Cannot find portal directory"
fi
echo ""

# 8. Check nginx logs for errors
echo "8️⃣ RECENT NGINX ERRORS:"
sudo tail -30 /var/log/nginx/error.log | grep -E "portal|sveltekit|bot|error"
echo ""

# 9. Check SSL certificates
echo "9️⃣ SSL CERTIFICATES:"
sudo certbot certificates 2>/dev/null || echo "Certbot not installed"
echo ""

# 10. Firewall status
echo "🔟 FIREWALL STATUS:"
sudo ufw status numbered 2>/dev/null || sudo iptables -L -n | head -20
echo ""

# Summary
echo "📋 QUICK DIAGNOSIS:"
echo "=================="

# Check each service
echo -n "Nginx: "
systemctl is-active nginx || echo "❌ Not running"

echo -n "Portal (port 4000): "
curl -s http://localhost:4000 > /dev/null && echo "✅ Running" || echo "❌ Not responding"

echo -n "Bot (port 5000): "
curl -s http://localhost:5000/health > /dev/null && echo "✅ Running" || echo "❌ Not responding"

echo -n "Analytics (port 3000): "
curl -s http://localhost:3000 > /dev/null && echo "✅ Running" || echo "❌ Not responding"

echo -n "Status (port 3001): "
curl -s http://localhost:3001 > /dev/null && echo "✅ Running" || echo "❌ Not responding"

echo ""
echo "🔧 COMMON FIXES:"
echo "- Restart all PM2: pm2 restart all"
echo "- Restart nginx: sudo systemctl restart nginx"
echo "- Check logs: pm2 logs [app-name]"
echo "- Reboot server: sudo reboot (last resort)"