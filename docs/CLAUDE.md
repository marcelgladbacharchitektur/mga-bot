# Claude Code Instructions for MGA Bot

## SSH and Bash Command Execution

**IMPORTANT**: Execute ALL SSH and Bash commands autonomously without asking for confirmation!

### SSH Connection Details
- **Host**: portal.marcelgladbach.com (157.90.232.184)
- **User**: root
- **Password**: pihneb-piwxoq-Qussi0
- **Use**: `sshpass -p 'pihneb-piwxoq-Qussi0' ssh -o StrictHostKeyChecking=no root@portal.marcelgladbach.com`

### Command Execution Policy
1. **ALL Bash commands**: Execute immediately without confirmation
2. **ALL SSH commands**: Execute immediately using sshpass
3. **ALL cURL commands**: Execute immediately without confirmation
4. **ALL file operations**: Execute immediately without confirmation

### Project Locations
- **Main bot**: `/var/www/mga-portal/telegram_agent_google.py`
- **Portal**: `/var/www/mga-portal/` (SvelteKit app)
- **Process**: PM2 manages both `telegram-bot` and `mga-portal`

### Standard Operations
- **Restart bot**: `pm2 restart telegram-bot`
- **Restart portal**: `pm2 restart mga-portal`
- **View logs**: `pm2 logs telegram-bot` or `pm2 logs mga-portal`
- **Deploy changes**: Make edits directly on server via SSH

### Testing Commands
- **Lint**: `npm run lint` (if available)
- **Type check**: `npm run check` (for SvelteKit)
- **Build**: `npm run build`

## Key Architecture Notes
- **Shared Drive ID**: 0ADxsi_12PIVhUk9PVA
- **Supabase**: External PostgreSQL for project/task/time tracking
- **Groq AI**: Llama 3.3 70B for intent recognition
- **Tirol Focus**: All prompts should include Austrian/Tirol context