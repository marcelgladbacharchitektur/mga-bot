#!/bin/bash
# Setup Supabase Environment Variables

echo "🔧 Setting up Supabase environment variables..."
echo ""
echo "Please provide your Supabase credentials:"
echo "(You can find these in your Supabase project at https://app.supabase.com)"
echo ""

read -p "Enter SUPABASE_URL: " SUPABASE_URL
read -p "Enter SUPABASE_ANON_KEY: " SUPABASE_ANON_KEY

# Create .env file for bot
cat > /var/www/mga-portal/supabase.env << EOF
# Supabase Configuration
export SUPABASE_URL="${SUPABASE_URL}"
export SUPABASE_ANON_KEY="${SUPABASE_ANON_KEY}"
EOF

echo ""
echo "✅ Supabase configuration saved to /var/www/mga-portal/supabase.env"
echo ""
echo "To use these variables, run:"
echo "  source /var/www/mga-portal/supabase.env"
echo ""
echo "Or add to your bot startup script!"