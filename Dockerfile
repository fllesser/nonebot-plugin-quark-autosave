# 构建阶段
FROM ghcr.io/astral-sh/uv:0.8.14-python3.12-bookworm

# RUN apt-get update && apt-get install -y git curl ffmpeg && apt-get clean && rm -rf /var/lib/apt/lists/*
WORKDIR /app

ENV TELEGRAM_BOT_TOKEN=[] \
    SUPERUSERS=[] \
    PORT=8080 \
    QAS_ENDPOINT="http://quark-auto-save:5005" \
    QAS_TOKEN="123456789"


COPY requirements.txt .

RUN uv venv && uv pip install -r requirements.txt

COPY . .

RUN chmod +x start.sh

RUN uv sync --no-dev --no-group test --group telebot --locked

EXPOSE ${PORT}

ENV TZ=Asia/Shanghai

CMD ["/bin/bash", "start.sh"]