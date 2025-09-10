# 构建阶段
FROM ghcr.io/astral-sh/uv:0.8.14-python3.12-bookworm

# RUN apt-get update && apt-get install -y git curl ffmpeg && apt-get clean && rm -rf /var/lib/apt/lists/*
WORKDIR /app

ENV TELEGRAM_BOT_TOKEN=[] \
    SUPERUSERS=[] \
    PORT=8080 \
    QAS_ENDPOINT="http://quark-auto-save:5005" \
    QAS_TOKEN="123456789"

RUN echo "PORT=${PORT}\n" > .env.prod && \
    echo "SUPERUSERS=${SUPERUSERS}\n" >> .env.prod && \
    echo "COMMAND_START=["", "/"]\n" >> .env.prod && \
    echo "telegram_bots=[{"token": "${TELEGRAM_BOT_TOKEN}"}]\n" >> .env.prod && \
    echo "qas_endpoint=${QAS_ENDPOINT}\n" >> .env.prod && \
    echo "qas_token=${QAS_TOKEN}\n" >> .env.prod

COPY requirements.txt bot.py ./

RUN uv venv && uv pip install -r requirements.txt

EXPOSE ${PORT}

ENV TZ=Asia/Shanghai

CMD ["uv", "run", "bot.py"]