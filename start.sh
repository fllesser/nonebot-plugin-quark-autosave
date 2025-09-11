cat > .env.prod <<EOF
DRIVER=~httpx
PORT=${PORT}
SUPERUSERS=${SUPERUSERS}
COMMAND_START=["", "/"]
telegram_bots=[{"token": "${TELEGRAM_BOT_TOKEN}"}]
qas_endpoint=${QAS_ENDPOINT}
qas_token=${QAS_TOKEN}
EOF
uv run --no-sync bot.py