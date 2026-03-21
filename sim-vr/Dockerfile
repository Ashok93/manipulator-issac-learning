FROM nvcr.io/nvidia/base/ubuntu:noble-20250619

ENV NVIDIA_VISIBLE_DEVICES=all \
    NVIDIA_DRIVER_CAPABILITIES=all \
    VK_DRIVER_FILES=/etc/vulkan/icd.d/nvidia_icd.json \
    ACCEPT_EULA=Y \
    OMNI_KIT_ACCEPT_EULA=YES \
    DEBIAN_FRONTEND=noninteractive

RUN touch /etc/ld.so.nohwcap

# ---------------------------------------------------------------------------
# System deps (Isaac Sim base + Steam/SteamVR/ALVR requirements)
# ---------------------------------------------------------------------------
RUN dpkg --add-architecture i386 && apt-get update && apt-get install -y --no-install-recommends \
        curl ca-certificates wget \
        libatomic1 libegl1 libgl1 libglu1-mesa libglx0 libgomp1 \
        libsm6 libxi6 libxrandr2 libxt6 libglib2.0-0 libnghttp2-14 \
        unzip software-properties-common \
        # Steam 32-bit deps
        libgl1-mesa-dri:i386 libglx-mesa0:i386 lib32gcc-s1 lib32stdc++6 \
        # OpenXR loader
        libopenxr-loader1 libopenxr-dev \
        # ALVR dashboard GUI deps
        libva2 libva-drm2 libva-x11-2 \
        libxcursor1 libxrender1 libxfixes3 libxkbcommon0 libxkbcommon-x11-0 \
        # Capabilities for vrcompositor
        libcap2-bin \
    && add-apt-repository ppa:deadsnakes/ppa \
    && apt-get update && apt-get install -y --no-install-recommends \
        python3.11 python3.11-venv python3.11-dev \
    && apt-get autoremove -y && apt-get clean && rm -rf /var/lib/apt/lists/*

# ---------------------------------------------------------------------------
# EGL + Vulkan ICD config (mirrors sim/Dockerfile exactly)
# ---------------------------------------------------------------------------
RUN mkdir -p /usr/share/glvnd/egl_vendor.d /etc/vulkan/icd.d /etc/vulkan/implicit_layer.d
RUN printf '{\n    "file_format_version" : "1.0.0",\n    "ICD" : {\n        "library_path" : "libEGL_nvidia.so.0"\n    }\n}\n' \
        > /usr/share/glvnd/egl_vendor.d/10_nvidia.json
RUN printf '{\n    "file_format_version" : "1.0.0",\n    "ICD" : {\n        "library_path" : "libEGL_mesa.so.0"\n    }\n}\n' \
        > /usr/share/glvnd/egl_vendor.d/50_mesa.json
RUN printf '{\n    "file_format_version" : "1.0.0",\n    "ICD" : {\n        "library_path" : "libGLX_nvidia.so.0",\n        "api_version" : "1.3.194"\n    }\n}\n' \
        > /etc/vulkan/icd.d/nvidia_icd.json
RUN printf '{\n    "file_format_version" : "1.0.0",\n    "layer": {\n        "name": "VK_LAYER_NV_optimus",\n        "type": "INSTANCE",\n        "library_path": "libGLX_nvidia.so.0",\n        "api_version" : "1.3.194",\n        "implementation_version" : "1",\n        "description" : "NVIDIA Optimus layer",\n        "functions": {\n            "vkGetInstanceProcAddr": "vk_optimusGetInstanceProcAddr",\n            "vkGetDeviceProcAddr": "vk_optimusGetDeviceProcAddr"\n        },\n        "enable_environment": {\n            "__NV_PRIME_RENDER_OFFLOAD": "1"\n        },\n        "disable_environment": {\n            "DISABLE_LAYER_NV_OPTIMUS_1": ""\n        }\n    }\n}\n' \
        > /etc/vulkan/implicit_layer.d/nvidia_layers.json

# ---------------------------------------------------------------------------
# Create non-root user (Steam refuses to run as root)
# ---------------------------------------------------------------------------
RUN apt-get update && apt-get install -y --no-install-recommends sudo \
    && apt-get clean && rm -rf /var/lib/apt/lists/*
RUN useradd -m -s /bin/bash -G video,audio,sudo vruser \
    && echo "vruser ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers
ENV HOME=/home/vruser

# ---------------------------------------------------------------------------
# Install uv (for vruser)
# ---------------------------------------------------------------------------
USER vruser
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/home/vruser/.local/bin:$PATH"
USER root

# ---------------------------------------------------------------------------
# Install ALVR streamer v20.14.1 (Steam + SteamVR are bind-mounted from host)
# ---------------------------------------------------------------------------
RUN mkdir -p /opt/alvr \
    && cd /tmp \
    && wget -q https://github.com/alvr-org/ALVR/releases/download/v20.14.1/alvr_streamer_linux.tar.gz \
    && tar -xzf alvr_streamer_linux.tar.gz -C /opt/alvr --strip-components=1 \
    && rm alvr_streamer_linux.tar.gz

# ---------------------------------------------------------------------------
# Prepare OpenXR implicit layer directory
# ---------------------------------------------------------------------------
RUN mkdir -p /usr/share/openxr/1/api_layers/implicit.d

# ---------------------------------------------------------------------------
# Clone IsaacLab for teleop scripts
# ---------------------------------------------------------------------------
RUN apt-get update && apt-get install -y --no-install-recommends git \
    && git clone --depth 1 https://github.com/isaac-sim/IsaacLab.git /opt/IsaacLab \
    && apt-get autoremove -y && apt-get clean && rm -rf /var/lib/apt/lists/*

# ---------------------------------------------------------------------------
# Set permissions and copy project files
# ---------------------------------------------------------------------------
RUN mkdir -p /workspace/sim-vr /opt/IsaacLab \
    && chown -R vruser:vruser /workspace/sim-vr /opt/IsaacLab /opt/alvr

WORKDIR /workspace/sim-vr
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

USER vruser
ENTRYPOINT ["/entrypoint.sh"]
