
set -euo pipefail

# 1) подгружаем .env
set -a
[ -f "$HOME/.env" ] && . "$HOME/.env"
set +a

# 2) диагностика окружения
{
  echo "[$(date -Is)] DIAG: whoami=$(id -un) HOME=$HOME"
  echo "[$(date -Is)] DIAG: TOKEN_LEN=${#TELEGRAM_TOKEN} CHAT_ID=${TELEGRAM_CHAT_ID:-<empty>}"
  echo "[$(date -Is)] DIAG: PATH=$PATH"
} >> /root/habitsmith/cron.log
export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

cd /root/habitsmith
/usr/bin/python3 -m auto_updater.scheduler >> /root/habitsmith/cron.log 2>&1

