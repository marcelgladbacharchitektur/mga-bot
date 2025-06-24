#!/bin/bash
# Script to check existing nginx configurations for marcelgladbach.com subdomains

echo "🔍 Checking existing nginx configurations for marcelgladbach.com"
echo "============================================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo "📂 Checking /etc/nginx/sites-available/:"
echo "---------------------------------------"
for conf in /etc/nginx/sites-available/*; do
    if [ -f "$conf" ]; then
        echo -e "\n${YELLOW}File: $(basename $conf)${NC}"
        # Check for marcelgladbach.com domains
        if grep -q "marcelgladbach.com" "$conf" 2>/dev/null; then
            echo -e "${GREEN}Found marcelgladbach.com configuration:${NC}"
            grep -n "server_name.*marcelgladbach.com" "$conf" | sed 's/^/  /'
            grep -n "proxy_pass" "$conf" 2>/dev/null | sed 's/^/  /'
        fi
    fi
done

echo -e "\n📂 Checking /etc/nginx/sites-enabled/:"
echo "-------------------------------------"
ls -la /etc/nginx/sites-enabled/ | grep -v "total\|^d" | awk '{print "  " $9 " -> " $11}'

echo -e "\n🌐 Checking for specific subdomains:"
echo "----------------------------------"
for subdomain in analytics status portal bot; do
    echo -n "  $subdomain.marcelgladbach.com: "
    if grep -r "$subdomain.marcelgladbach.com" /etc/nginx/sites-enabled/ &>/dev/null; then
        echo -e "${RED}Already configured${NC}"
        grep -l "$subdomain.marcelgladbach.com" /etc/nginx/sites-enabled/* | sed 's/^/    Found in: /'
    else
        echo -e "${GREEN}Available${NC}"
    fi
done

echo -e "\n🔒 SSL Certificate Check:"
echo "-----------------------"
if [ -d "/etc/letsencrypt/live/marcelgladbach.com" ]; then
    echo -e "${GREEN}✅ Let's Encrypt certificate found for marcelgladbach.com${NC}"
    sudo ls -la /etc/letsencrypt/live/marcelgladbach.com/ | grep -E "cert|chain|privkey" | sed 's/^/  /'
else
    echo -e "${YELLOW}⚠️  No Let's Encrypt certificate found for marcelgladbach.com${NC}"
    echo "  Available certificates:"
    sudo ls /etc/letsencrypt/live/ 2>/dev/null | sed 's/^/    /' || echo "    None found"
fi

echo -e "\n⚠️  IMPORTANT NOTES:"
echo "==================="
echo "1. Before deploying the bot, ensure DNS records are set up:"
echo "   - analytics.marcelgladbach.com → 157.90.232.184"
echo "   - status.marcelgladbach.com → 157.90.232.184"
echo "   - portal.marcelgladbach.com → 157.90.232.184"
echo "   - bot.marcelgladbach.com → 157.90.232.184"
echo ""
echo "2. If SSL certificates don't exist, run:"
echo "   sudo certbot certonly --nginx -d marcelgladbach.com -d *.marcelgladbach.com"
echo ""
echo "3. Always backup existing configurations before making changes!"