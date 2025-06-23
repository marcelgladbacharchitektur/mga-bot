# MGA Portal - Complete Infrastructure Documentation

## Server Infrastructure

### Hetzner Cloud Server
- **Provider**: Hetzner Cloud
- **Server Type**: (likely CX21 or similar)
- **Location**: Germany (Nuremberg/Falkenstein)
- **Public IP**: 157.90.232.184
- **SSH Access**:
  - Host: 157.90.232.184
  - Port: 22
  - User: root
  - Authentication: SSH Key (siehe unten)
- **OS**: Ubuntu (check with `lsb_release -a`)

### SSH Connection
```bash
# Save the private key to a file (e.g., ~/.ssh/mga-hetzner)
chmod 600 ~/.ssh/mga-hetzner

# Connect to server
ssh -i ~/.ssh/mga-hetzner root@157.90.232.184
```

### SSH Private Key
```
-----BEGIN OPENSSH PRIVATE KEY-----
b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAAAMwAAAAtzc2gtZW
QyNTUxOQAAACCJrn1h7i5VTY0BcRoe44csC/OQ76EZzsvz1Syo1TsD6gAAAJjwQaa/8EGm
vwAAAAtzc2gtZWQyNTUxOQAAACCJrn1h7i5VTY0BcRoe44csC/OQ76EZzsvz1Syo1TsD6g
AAAEC9e3aVmBycKMDoC7neCoQMldF4wGMNLh+vE5UZQyw3uYmufWHuLlVNjQFxGh7jhywL
85DvoRnOy/PVLKjVOwPqAAAADmdpdGh1Yi1hY3Rpb25zAQIDBAUGBw==
-----END OPENSSH PRIVATE KEY-----
```

## Services & URLs

### MGA Portal
- **URL**: https://portal.marcelgladbach.at
- **Admin Login**: admin@marcelgladbach.at / MGA-Portal2024!

### Nextcloud
- **URL**: https://cloud.marcelgladbach.at
- **Admin**: admin / tazqoP-2rapsa-vyhsyr

### Analytics (Umami)
- **URL**: https://analytics.marcelgladbach.at
- **Login**: (check in Umami settings)

### Status Monitoring (Uptime Kuma)
- **URL**: https://status.marcelgladbach.at
- **Login**: (check in Uptime Kuma settings)

## Database

### Supabase (PostgreSQL)
- **Project URL**: (check .env file)
- **Connection Details**: 
  - See DATABASE_URL in .env
  - See DATABASE_URL_POOLED in .env
  - See DATABASE_URL_DIRECT in .env

## Environment Variables (.env)

### Authentication
- **NEXTAUTH_URL**: http://localhost:3000 (production: https://portal.marcelgladbach.at)
- **NEXTAUTH_SECRET**: (check .env file)

### Supabase
- **NEXT_PUBLIC_SUPABASE_URL**: (check .env file)
- **NEXT_PUBLIC_SUPABASE_ANON_KEY**: (check .env file)

### Nextcloud Integration
- **NEXTCLOUD_URL**: https://cloud.marcelgladbach.at
- **NEXTCLOUD_USER**: (check .env file)
- **NEXTCLOUD_APP_PASSWORD**: (needs to be generated in Nextcloud)

### Google OAuth (if configured)
- **GOOGLE_CLIENT_ID**: (check .env file)
- **GOOGLE_CLIENT_SECRET**: (check .env file)

### Email Service (if configured)
- **EMAIL_SERVER**: (check .env file)
- **EMAIL_FROM**: (check .env file)

## Service Architecture & Ports

### Port Mapping Overview
```
Public Internet
    ↓
Caddy Reverse Proxy (ports 80, 443)
    ├── portal.marcelgladbach.at → localhost:3000 (MGA Portal)
    ├── cloud.marcelgladbach.at → localhost:8080 (Nextcloud)
    ├── analytics.marcelgladbach.at → localhost:3001 (Umami)
    └── status.marcelgladbach.at → localhost:3003 (Uptime Kuma)
```

### Running Services

#### 1. MGA Portal (Next.js App)
- **Port**: 3000 (local only)
- **Process Manager**: PM2
- **Location**: /var/www/mga-portal
- **Start Command**: `npm run start`
- **PM2 Name**: mga-portal
- **Logs**: `pm2 logs mga-portal`
- **Restart**: `pm2 restart mga-portal`
- **Environment**: Production

#### 2. Nextcloud (Docker Container)
- **Container Name**: nextcloud-admin
- **Port**: 8080 (host) → 80 (container)
- **Image**: nextcloud:latest
- **Data Volume**: Docker volume (persistent)
- **Access Container**: `docker exec -it nextcloud-admin bash`
- **Run as www-data**: `docker exec -u www-data nextcloud-admin php occ [command]`
- **Logs**: `docker logs nextcloud-admin`
- **Restart**: `docker restart nextcloud-admin`

#### 3. Umami Analytics
- **Port**: 3001 (local only)
- **Type**: Node.js application
- **Database**: PostgreSQL (separate container or service)
- **Purpose**: Website analytics
- **Data**: Persistent database storage

#### 4. Uptime Kuma (Status Monitoring)
- **Port**: 3003 (local only)
- **Type**: Docker container or PM2 process
- **Purpose**: Service uptime monitoring
- **Data**: SQLite database (persistent volume)

### Database Services

#### PostgreSQL (if running locally)
- **Port**: 5432 (standard)
- **Used by**: Umami, possibly others
- **Access**: `psql -U postgres`

#### Supabase (External)
- **Type**: Managed PostgreSQL
- **Used by**: MGA Portal
- **Access**: Via connection string in .env

### Process Management

#### PM2 Commands
```bash
# List all processes
pm2 list

# View specific process
pm2 show mga-portal

# View logs
pm2 logs
pm2 logs mga-portal --lines 100

# Restart services
pm2 restart all
pm2 restart mga-portal

# Save PM2 process list
pm2 save

# Resurrect saved processes after reboot
pm2 resurrect
```

#### Docker Commands
```bash
# List running containers
docker ps

# List all containers
docker ps -a

# View container logs
docker logs nextcloud-admin
docker logs -f nextcloud-admin  # Follow logs

# Container stats
docker stats

# Enter container
docker exec -it nextcloud-admin bash
```

### Network Configuration

#### Firewall (UFW)
```bash
# Check status
ufw status

# Should show:
# 22/tcp (SSH)
# 80/tcp (HTTP)
# 443/tcp (HTTPS)
```

#### Internal Network
- All services bind to localhost (127.0.0.1)
- Only Caddy listens on public interfaces
- Docker uses bridge network (172.17.0.0/16)

## Deployment

### GitHub Repository
- Clone with: `git clone [repository-url]`
- Deploy user: deploy

### PM2 Process Manager
- View processes: `pm2 list`
- Restart portal: `pm2 restart mga-portal`
- View logs: `pm2 logs mga-portal`

## SSL Certificates
- Managed by: Caddy (automatic Let's Encrypt)
- Config: /etc/caddy/Caddyfile

## System Services
- Caddy: `systemctl status caddy`
- Docker: `systemctl status docker`
- PM2: `pm2 status`

## Backup Locations
- Nextcloud data: Docker volume
- Portal data: Supabase (external)
- Configs: /etc/caddy/Caddyfile

## Important Notes
1. Always backup before making changes
2. Nextcloud uses app passwords for WebDAV access
3. Portal uses JWT for session management
4. All services run behind Caddy reverse proxy
5. SSL certificates auto-renew via Caddy

## System Maintenance

### Server Monitoring
```bash
# Check system resources
htop
df -h  # Disk usage
free -h  # Memory usage

# Check service status
systemctl status caddy
pm2 status
docker ps

# View system logs
journalctl -xe
journalctl -u caddy -f  # Follow Caddy logs
```

### Backup Procedures
```bash
# Backup MGA Portal database (via Supabase dashboard)
# Backup Nextcloud
docker exec nextcloud-admin tar -czf /backup.tar.gz /var/www/html/data
docker cp nextcloud-admin:/backup.tar.gz /root/nextcloud-backup-$(date +%Y%m%d).tar.gz

# Backup Caddy config
cp /etc/caddy/Caddyfile /root/Caddyfile.backup
```

### Common Troubleshooting

#### If Portal is down:
```bash
pm2 logs mga-portal
pm2 restart mga-portal
cd /var/www/mga-portal && npm run build && pm2 restart mga-portal
```

#### If Nextcloud is down:
```bash
docker logs nextcloud-admin
docker restart nextcloud-admin
```

#### If SSL issues:
```bash
systemctl restart caddy
caddy validate --config /etc/caddy/Caddyfile
```

## Domain Configuration

### DNS Records (at your domain provider)
```
A    @                    157.90.232.184
A    portal               157.90.232.184
A    cloud                157.90.232.184
A    analytics            157.90.232.184
A    status               157.90.232.184
```

### Domain Registrar
- Check with: `whois marcelgladbach.at`

## Emergency Contacts
- **Hetzner Support**: via Hetzner Cloud Console (https://console.hetzner.cloud/)
- **Supabase Support**: via Supabase Dashboard (https://app.supabase.com/)
- **Domain Support**: (check domain registrar)

## Security Notes
1. **NEVER** share the SSH private key
2. **ALWAYS** use strong passwords
3. **REGULARLY** update all services
4. **BACKUP** before major changes
5. **MONITOR** logs for suspicious activity