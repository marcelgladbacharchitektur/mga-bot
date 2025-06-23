#!/bin/bash
# Deploy Supabase Integration to MGA Bot

echo "🚀 Deploying Supabase Integration..."
echo "===================================="
echo ""

# Check if credentials are provided as arguments
if [ $# -eq 2 ]; then
    SUPABASE_URL=$1
    SUPABASE_ANON_KEY=$2
    echo "✅ Using provided Supabase credentials"
else
    echo "Usage: $0 <SUPABASE_URL> <SUPABASE_ANON_KEY>"
    echo ""
    echo "You can find these in your Supabase project:"
    echo "1. Go to https://app.supabase.com"
    echo "2. Select your project"
    echo "3. Go to Settings → API"
    echo "4. Copy the Project URL and anon public key"
    exit 1
fi

# Create environment file
cat > supabase.env << EOF
# Supabase Configuration
export SUPABASE_URL="${SUPABASE_URL}"
export SUPABASE_ANON_KEY="${SUPABASE_ANON_KEY}"
EOF

echo "✅ Environment file created"

# Create systemd environment file for PM2
cat > supabase-env.conf << EOF
# Supabase environment variables for PM2
SUPABASE_URL=${SUPABASE_URL}
SUPABASE_ANON_KEY=${SUPABASE_ANON_KEY}
EOF

echo "✅ PM2 environment config created"
echo ""
echo "📝 Next steps:"
echo "1. Copy files to server:"
echo "   scp telegram_agent_google_supabase.py root@157.90.232.184:/var/www/mga-portal/"
echo "   scp supabase.env root@157.90.232.184:/var/www/mga-portal/"
echo ""
echo "2. SSH to server and deploy:"
echo "   ssh root@157.90.232.184"
echo "   cd /var/www/mga-portal"
echo "   source supabase.env"
echo "   pm2 delete telegram-google"
echo "   pm2 start telegram_agent_google_supabase.py --name telegram-google"
echo "   pm2 save"
echo ""
echo "3. Test the integration!"