# 构建阶段
FROM ghcr.io/astral-sh/uv:0.8.14-python3.12-bookworm

# RUN apt-get update && apt-get install -y git curl ffmpeg && apt-get clean && rm -rf /var/lib/apt/lists/*
WORKDIR /app

ENV TELEGRAM_BOT_TOKEN=[]
ENV SUPERUSERS=[]
ENV PORT=8080

RUN echo " \
    PORT=${PORT}\n \
    SUPERUSERS=${SUPERUSERS}\n \
    COMMAND_START=["", "/"]\n \
    telegram_bots=[{"token": "${TELEGRAM_BOT_TOKEN}"}] \
    > .env.prod

COPY requirements.txt .

RUN uv pip install -r requirements.txt

COPY bot.py .

EXPOSE ${PORT}

ENV TZ=Asia/Shanghai

CMD ["uv", "run", "bot.py"]