FROM ghcr.io/astral-sh/uv:alpine

WORKDIR /app
COPY . .

RUN uv sync

CMD ["uv", "run", "python", "-u", "main.py"]
