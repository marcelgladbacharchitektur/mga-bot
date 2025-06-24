#!/bin/bash
# Server Analysis Script - Non-intrusive discovery of existing services
# Run this BEFORE deploying to understand the current server state

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
echo -e "${BLUE}    Marcel Gladbach Server Infrastructure Analysis${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
echo "Server IP: 157.90.232.184"
echo "Analysis Date: $(date)"
echo ""

# Function to print section headers
print_section() {
    echo -e "\n${YELLOW}▶ $1${NC}"
    echo "$(printf '─%.0s' {1..50})"
}

# 1. System Information
print_section "System Information"
echo "Hostname: $(hostname)"
echo "OS: $(lsb_release -d 2>/dev/null | cut -f2 || cat /etc/os-release | grep PRETTY_NAME | cut -d'"' -f2)"
echo "Kernel: $(uname -r)"
echo "Uptime: $(uptime -p)"

# 2. Resource Usage
print_section "Resource Usage"
echo "CPU Cores: $(nproc)"
echo "Load Average: $(uptime | awk -F'load average:' '{print $2}')"
echo ""
echo "Memory Usage:"
free -h | grep -E "^(Mem|Swap)" | awk '{printf "  %-6s Total: %6s Used: %6s Free: %6s\n", $1, $2, $3, $4}'
echo ""
echo "Disk Usage:"
df -h | grep -E "^/dev|Filesystem" | awk '{printf "  %-20s %6s %6s %6s %5s %s\n", $1, $2, $3, $4, $5, $6}'

# 3. Network Ports Analysis
print_section "Active Network Ports"
echo -e "${BLUE}Web Services (80/443):${NC}"
sudo ss -tlnp | grep -E ':80\s|:443\s' | awk '{print "  " $0}' || echo "  No services on standard web ports"

echo -e "\n${BLUE}Application Ports (3000-5000):${NC}"
sudo ss -tlnp | grep -E ':(3[0-9]{3}|4[0-9]{3}|5000)\s' | awk '{print "  Port " $4 " - " $6}' | sort -u

echo -e "\n${BLUE}Other Notable Ports:${NC}"
sudo ss -tlnp | grep -vE ':(22|80|443|3[0-9]{3}|4[0-9]{3}|5000)\s' | grep LISTEN | head -10 | awk '{print "  " $4 " - " $6}'

# 4. Nginx Analysis
print_section "Nginx Configuration"
if command -v nginx &> /dev/null; then
    echo "Nginx Version: $(nginx -v 2>&1 | cut -d' ' -f3)"
    echo ""
    echo "Active Sites:"
    for site in /etc/nginx/sites-enabled/*; do
        if [ -f "$site" ]; then
            echo -e "\n  ${GREEN}$(basename $site)${NC}"
            # Extract server_name and proxy_pass
            grep -E "server_name|proxy_pass|listen" "$site" 2>/dev/null | grep -v "#" | sed 's/^/    /' | head -10
        fi
    done
    
    echo -e "\n${BLUE}SSL Certificates:${NC}"
    sudo grep -r "ssl_certificate" /etc/nginx/sites-enabled/ 2>/dev/null | grep -v "#" | awk -F: '{print "  " $2}' | sort -u | head -10
else
    echo "Nginx not installed"
fi

# 5. Process Analysis
print_section "Running Services (Potential MGA Services)"
echo -e "${BLUE}Systemd Services:${NC}"
systemctl list-units --type=service --state=running | grep -E "mga|portal|umami|uptime|bot|node|pm2" | awk '{print "  " $1 " - " $5}'

echo -e "\n${BLUE}Process Overview:${NC}"
ps aux | grep -E "node|python|java|ruby" | grep -v grep | awk '{print "  " $11 " (PID: " $2 ", User: " $1 ")"}' | sort -u | head -15

# 6. Docker/Container Check
print_section "Container Environment"
if command -v docker &> /dev/null; then
    echo "Docker installed: Yes"
    if sudo docker ps &>/dev/null; then
        echo "Running Containers:"
        sudo docker ps --format "table {{.Names}}\t{{.Ports}}\t{{.Status}}" | sed 's/^/  /'
    else
        echo "Docker not accessible or no containers running"
    fi
else
    echo "Docker not installed"
fi

# 7. PM2 Check
print_section "PM2 Process Manager"
if command -v pm2 &> /dev/null; then
    echo "PM2 installed: Yes"
    pm2 list 2>/dev/null | sed 's/^/  /' || echo "  PM2 not accessible"
else
    echo "PM2 not installed"
fi

# 8. SSL/TLS Analysis
print_section "SSL/TLS Certificates"
echo "Let's Encrypt Certificates:"
if [ -d "/etc/letsencrypt/live" ]; then
    sudo ls -la /etc/letsencrypt/live/ | grep -v "total\|README" | awk '{print "  " $9}' | grep -v "^  $"
else
    echo "  No Let's Encrypt certificates found"
fi

# 9. Firewall Status
print_section "Firewall Configuration"
if command -v ufw &> /dev/null; then
    sudo ufw status numbered | head -20 | sed 's/^/  /'
elif command -v iptables &> /dev/null; then
    echo "iptables rules (first 10):"
    sudo iptables -L -n | head -10 | sed 's/^/  /'
else
    echo "No standard firewall detected"
fi

# 10. Cron Jobs
print_section "Scheduled Tasks (Cron)"
echo "Root crontab:"
sudo crontab -l 2>/dev/null | grep -v "^#" | head -5 | sed 's/^/  /' || echo "  No cron jobs"

# 11. Recent Logs Check
print_section "Recent System Activity"
echo "Last 5 nginx access entries:"
sudo tail -5 /var/log/nginx/access.log 2>/dev/null | awk '{print "  " $1 " - " $7}' || echo "  No recent access logs"

echo -e "\n${BLUE}Last system restarts:${NC}"
last reboot | head -3 | sed 's/^/  /'

# Summary and Recommendations
print_section "Analysis Summary"
echo -e "${GREEN}Discovered Services:${NC}"
echo "  • Nginx web server: $(systemctl is-active nginx 2>/dev/null || echo "inactive")"
echo "  • Potential Node.js apps on ports: $(sudo ss -tlnp | grep -E ':(3[0-9]{3}|4[0-9]{3})\s' | grep -oE ':[0-9]+' | cut -d: -f2 | tr '\n' ' ')"

echo -e "\n${YELLOW}Recommended Bot Configuration:${NC}"
echo "  • Bot Port: 5000 (appears to be free)"
echo "  • Nginx Site: bot.marcelgladbach.com"
echo "  • SSL: Use existing Let's Encrypt setup"
echo "  • Process Manager: systemd (recommended)"

echo -e "\n${RED}Potential Conflicts to Address:${NC}"
# Check for port 5000
if sudo ss -tlnp | grep -q ':5000\s'; then
    echo "  ⚠️  Port 5000 is already in use!"
else
    echo "  ✅ Port 5000 is available"
fi

# Check for bot subdomain
if grep -r "bot.marcelgladbach" /etc/nginx/sites-enabled/ &>/dev/null; then
    echo "  ⚠️  bot.marcelgladbach subdomain already configured in nginx"
else
    echo "  ✅ bot.marcelgladbach subdomain available"
fi

echo -e "\n${BLUE}═══════════════════════════════════════════════${NC}"
echo "Analysis complete. Save this output before deployment!"
echo -e "${BLUE}═══════════════════════════════════════════════${NC}"