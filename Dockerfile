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
RUN uv pip install setuptools wheel uv_build
RUN uv pip install --no-build-isolation \
    --index-url https://pypi.nvidia.com/ \
    --extra-index-url https://pypi.org/simple \
    -r /workspace/requirements-sim.txt

ENV PYTHONPATH=/workspace/src
CMD ["bash"]
