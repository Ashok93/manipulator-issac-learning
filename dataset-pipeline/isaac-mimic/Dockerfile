FROM nvcr.io/nvidia/base/ubuntu:noble-20250619

ENV NVIDIA_VISIBLE_DEVICES=all \
    NVIDIA_DRIVER_CAPABILITIES=all \
    VK_DRIVER_FILES=/etc/vulkan/icd.d/nvidia_icd.json \
    ACCEPT_EULA=Y \
    OMNI_KIT_ACCEPT_EULA=YES \
    DEBIAN_FRONTEND=noninteractive

RUN touch /etc/ld.so.nohwcap

RUN apt-get update && apt-get install -y --no-install-recommends \
        curl ca-certificates \
        libatomic1 libegl1 libgl1 libglu1-mesa libglx0 libgomp1 \
        libsm6 libxi6 libxrandr2 libxt6 libglib2.0-0 libnghttp2-14 \
        unzip software-properties-common \
    && add-apt-repository ppa:deadsnakes/ppa \
    && apt-get update && apt-get install -y --no-install-recommends \
        python3.11 python3.11-venv python3.11-dev \
    && apt-get autoremove -y && apt-get clean && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /usr/share/glvnd/egl_vendor.d /etc/vulkan/icd.d /etc/vulkan/implicit_layer.d
RUN printf '{\n    "file_format_version" : "1.0.0",\n    "ICD" : {\n        "library_path" : "libEGL_nvidia.so.0"\n    }\n}\n' \
        > /usr/share/glvnd/egl_vendor.d/10_nvidia.json
RUN printf '{\n    "file_format_version" : "1.0.0",\n    "ICD" : {\n        "library_path" : "libEGL_mesa.so.0"\n    }\n}\n' \
        > /usr/share/glvnd/egl_vendor.d/50_mesa.json
RUN printf '{\n    "file_format_version" : "1.0.0",\n    "ICD" : {\n        "library_path" : "libGLX_nvidia.so.0",\n        "api_version" : "1.3.194"\n    }\n}\n' \
        > /etc/vulkan/icd.d/nvidia_icd.json
RUN printf '{\n    "file_format_version" : "1.0.0",\n    "layer": {\n        "name": "VK_LAYER_NV_optimus",\n        "type": "INSTANCE",\n        "library_path": "libGLX_nvidia.so.0",\n        "api_version" : "1.3.194",\n        "implementation_version" : "1",\n        "description" : "NVIDIA Optimus layer",\n        "functions": {\n            "vkGetInstanceProcAddr": "vk_optimusGetInstanceProcAddr",\n            "vkGetDeviceProcAddr": "vk_optimusGetDeviceProcAddr"\n        },\n        "enable_environment": {\n            "__NV_PRIME_RENDER_OFFLOAD": "1"\n        },\n        "disable_environment": {\n            "DISABLE_LAYER_NV_OPTIMUS_1": ""\n        }\n    }\n}\n' \
        > /etc/vulkan/implicit_layer.d/nvidia_layers.json

RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

WORKDIR /workspace/dataset-pipeline/isaac-mimic
ENTRYPOINT ["/entrypoint.sh"]
