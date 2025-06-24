#!/bin/bash
# Setup SSL and start bot with proper HTTPS configuration

set -euo pipefail

echo "🔐 Setting up SSL for Telegram Bot"
echo "=================================="

# Create certificates directory
mkdir -p certs
cd certs

# Generate self-signed SSL certificate
if [ ! -f server.crt ]; then
    echo "📝 Generating SSL certificate..."
    openssl req -newkey rsa:2048 -sha256 -nodes -keyout server.key -x509 -days 365 -out server.crt \
        -subj "/C=AT/ST=Tirol/L=Innsbruck/O=MGA/CN=$SSH_HOST"
    echo "✅ SSL certificate created"
else
    echo "✅ SSL certificate already exists"
fi

cd ..

# Install gunicorn if not present
if ! pip3 list | grep -q gunicorn; then
    echo "📦 Installing gunicorn..."
    pip3 install --user gunicorn
fi

# Create startup script with SSL support
cat > start_bot_ssl.py << 'EOF'
#!/usr/bin/env python3
"""SSL-enabled startup script for the Telegram bot"""
import os
import ssl
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

# Import the Flask app
from src.telegram_agent_google import app

# Import initialization function if it exists
try:
    from src.telegram_agent_google import init_services
    init_services()
except ImportError:
    pass

if __name__ == '__main__':
    # Create SSL context
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain('certs/server.crt', 'certs/server.key')
    
    # Run with SSL
    app.run(host='0.0.0.0', port=8443, debug=False, ssl_context=context)
EOF

chmod +x start_bot_ssl.py

# Stop any existing PM2 process
echo "🔄 Restarting PM2 process..."
pm2 delete telegram-google || true

# Start with gunicorn and SSL
pm2 start ecosystem.config.js \
    --name telegram-google \
    --interpreter python3 \
    -- --certfile=certs/server.crt --keyfile=certs/server.key --bind 0.0.0.0:8443 src.telegram_agent_google:app

# Alternative: Use the SSL wrapper script
# pm2 start start_bot_ssl.py --name telegram-google --interpreter python3

pm2 save
pm2 startup || true

echo "✅ Bot started with SSL support!"
echo ""
echo "📊 Current status:"
pm2 list
echo ""
echo "📝 Recent logs:"
pm2 logs telegram-google --lines 20 --nostream