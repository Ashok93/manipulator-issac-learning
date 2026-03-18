# Train container — Python 3.12 + LeRobot.
# The sim runs natively on the host via: uv sync --extra sim
FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    git curl build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /workspace

COPY pyproject.toml ./
COPY src/ ./src/

RUN uv sync --extra train --no-dev

CMD ["/bin/bash"]
