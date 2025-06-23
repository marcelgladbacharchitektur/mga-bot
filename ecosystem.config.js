module.exports = {
  apps: [{
    name: 'mga-bot',
    script: 'src/bot/telegram_agent_google.py',
    interpreter: 'python3',
    cwd: '/var/www/mga-portal',
    instances: 1,
    autorestart: true,
    watch: false,
    max_memory_restart: '500M',
    env: {
      NODE_ENV: 'production'
    },
    error_file: 'logs/mga-bot-error.log',
    out_file: 'logs/mga-bot-out.log',
    log_file: 'logs/mga-bot-combined.log',
    time: true
  }]
};