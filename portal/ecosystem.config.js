module.exports = {
  apps: [{
    name: "mga-portal-svelte",
    script: "npm",
    args: "run start",
    cwd: "/var/www/mga-portal/portal",
    env: {
      NODE_ENV: "production",
      PORT: 3002
    }
  }]
};