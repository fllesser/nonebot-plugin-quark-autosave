# 构建阶段
FROM ghcr.io/astral-sh/uv:0.8.14-python3.12-bookworm

RUN apt-get update && apt-get install -y git curl ffmpeg && apt-get clean && rm -rf /var/lib/apt/lists/*

# Install nbr (ensure we get the correct architecture)
RUN curl -Lf https://github.com/fllesser/nbr/releases/latest/download/nbr-Linux-musl-x86_64.tar.gz | \
    tar -xzf - -C /usr/local/bin/ nbr && \
    chmod +x /usr/local/bin/nbr

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project --link-mode copy

COPY . .

RUN echo "telegram_bots=$telegram_bots" > .env.prod

# RUN uv tool run --from nb-cli nb orm upgrade
EXPOSE 8080

ENV TZ=Asia/Shanghai

CMD ["nbr", "run"]