ARG SIM_BASE_IMAGE=nvidia/cuda:12.8.0-devel-ubuntu22.04
FROM ${SIM_BASE_IMAGE}

SHELL ["/bin/bash", "-lc"]

USER root
RUN mkdir -p /var/lib/apt/lists/partial \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
        git \
        curl \
        ca-certificates \
        build-essential \
        cmake \
        pkg-config \
        libgl1 \
        libglib2.0-0 \
        libsm6 \
        libxext6 \
        libxrender1 \
        libxi6 \
        libxrandr2 \
        libxss1 \
        libxtst6 \
        libatk1.0-0 \
        libgtk-3-0 \
        libnss3 \
        libasound2 \
        libxdamage1 \
        libxfixes3 \
        libxkbcommon0 \
        libxkbcommon-x11-0 \
        libdrm2 \
        libegl1 \
        libglvnd0 \
        ffmpeg \
        libavformat-dev \
        libavcodec-dev \
        libavdevice-dev \
        libavutil-dev \
        libswscale-dev \
        libswresample-dev \
        libavfilter-dev \
    && rm -rf /var/lib/apt/lists/*

RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:${PATH}"
RUN uv python install 3.11 \
    && uv venv /opt/venv --python 3.11
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="/opt/venv/bin:${PATH}"

WORKDIR /workspace
COPY pyproject.toml requirements-sim.txt /workspace/
RUN python -m pip install -U pip setuptools wheel
RUN python -m pip install --no-build-isolation --pre \
    --index-url https://pypi.nvidia.com/ \
    --extra-index-url https://pypi.org/simple \
    -r /workspace/requirements-sim.txt

ENV PYTHONPATH=/workspace/src
CMD ["bash"]
