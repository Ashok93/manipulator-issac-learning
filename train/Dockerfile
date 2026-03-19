FROM python:3.12

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
        curl ca-certificates build-essential \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

WORKDIR /app
COPY pyproject.toml .

# Install deps into the image, outside the bind-mounted workspace,
# so bundled .so files (e.g. libhebi.so) keep their execute permissions.
ENV UV_PROJECT_ENVIRONMENT=/opt/lerobot-venv
RUN uv sync --no-install-project

ENV VIRTUAL_ENV=/opt/lerobot-venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

WORKDIR /workspace/train
