ARG ISAACSIM_BASE_IMAGE=nvcr.io/nvidia/isaac-sim:5.1.0
FROM ${ISAACSIM_BASE_IMAGE}

SHELL ["/bin/bash", "-lc"]

USER root
RUN mkdir -p /var/lib/apt/lists/partial \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
        git \
        ffmpeg \
        build-essential \
        cmake \
        pkg-config \
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
ENV UV_PYTHON=/isaac-sim/python.sh

WORKDIR /workspace
COPY pyproject.toml README.md requirements-sim.txt /workspace/
COPY src /workspace/src
RUN uv pip install --python /isaac-sim/python.sh setuptools wheel uv_build
RUN uv pip install --python /isaac-sim/python.sh -r /workspace/requirements-sim.txt

ENV ACCEPT_EULA=Y
ENV OMNI_KIT_ACCEPT_EULA=YES
ENV PYTHONPATH=/workspace/src
CMD ["bash"]
