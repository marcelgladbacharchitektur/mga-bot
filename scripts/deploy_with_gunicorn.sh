#!/bin/bash
# Alternative deployment using Gunicorn with SSL

echo "🚀 Deploying MGA Bot with Gunicorn SSL"
echo "====================================="

# Install Gunicorn
pip3 install gunicorn

# Create Gunicorn configuration
cat > /var/www/mga-portal/gunicorn_config.py << 'EOF'
import multiprocessing

bind = "0.0.0.0:8443"
workers = 2
worker_class = "sync"
worker_connections = 1000
timeout = 300
keepalive = 2

# SSL Configuration
keyfile = "/etc/ssl/telegram-bot.key"
certfile = "/etc/ssl/telegram-bot.crt"

# Logging
accesslog = "/var/log/gunicorn/access.log"
errorlog = "/var/log/gunicorn/error.log"
loglevel = "info"

# Process naming
proc_name = 'mga-telegram-bot'

# Server mechanics
daemon = False
pidfile = "/var/run/gunicorn.pid"
user = "www-data"
group = "www-data"
tmp_upload_dir = None

# Server hooks
def pre_fork(server, worker):
    server.log.info("Worker spawned (pid: %s)", worker.pid)

def pre_exec(server):
    server.log.info("Forked child, re-executing.")

def when_ready(server):
    server.log.info("Server is ready. Spawning workers")
EOF

# Create SSL certificates
sudo mkdir -p /etc/ssl
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/ssl/telegram-bot.key \
    -out /etc/ssl/telegram-bot.crt \
    -subj "/C=AT/ST=Tirol/L=Innsbruck/O=MGA/CN=telegram-bot"

# Create log directory
sudo mkdir -p /var/log/gunicorn
sudo chown www-data:www-data /var/log/gunicorn

# Create systemd service
cat > /etc/systemd/system/mga-bot-gunicorn.service << 'EOF'
[Unit]
Description=MGA Telegram Bot with Gunicorn
After=network.target

[Service]
Type=notify
User=www-data
Group=www-data
RuntimeDirectory=gunicorn
WorkingDirectory=/var/www/mga-portal
Environment="PATH=/usr/local/bin:/usr/bin:/bin"
EnvironmentFile=/var/www/mga-portal/.env
ExecStart=/usr/local/bin/gunicorn \
          --config /var/www/mga-portal/gunicorn_config.py \
          src.telegram_agent_google:app
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable mga-bot-gunicorn
sudo systemctl start mga-bot-gunicorn

# Check status
sudo systemctl status mga-bot-gunicorn

echo "✅ Bot deployed with Gunicorn SSL!"