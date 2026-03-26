#!/bin/bash
# Bare-metal install of VR teleop stack on a Vast.ai KVM VM (Ubuntu 22.04/24.04 + NVIDIA GPU).
# Run once on a fresh VM. After this, use run_teleop.sh to launch.
#
# Prerequisites: NVIDIA GPU + drivers already installed (nvidia-smi works).
# Usage: bash teleop-vr/bare-install.sh
set -e

echo "=== [1/6] Vulkan / EGL / GPU Renderer ==="

# Install vulkan-tools if missing (needed for vulkaninfo check)
if ! command -v vulkaninfo &>/dev/null; then
    sudo apt-get update
    sudo apt-get install -y vulkan-tools
fi

# Write NVIDIA Vulkan ICD only if no ICD exists in either standard location
if [ ! -f /etc/vulkan/icd.d/nvidia_icd.json ] && [ ! -f /usr/share/vulkan/icd.d/nvidia_icd.json ]; then
    echo "[INFO] No NVIDIA Vulkan ICD found, writing to /etc/vulkan/icd.d/..."
    sudo mkdir -p /etc/vulkan/icd.d
    echo '{
    "file_format_version" : "1.0.0",
    "ICD" : {
        "library_path" : "libGLX_nvidia.so.0",
        "api_version" : "1.3.194"
    }
}' | sudo tee /etc/vulkan/icd.d/nvidia_icd.json > /dev/null
else
    echo "[INFO] NVIDIA Vulkan ICD already present, skipping."
fi

# Write EGL vendor config only if missing
if [ ! -f /usr/share/glvnd/egl_vendor.d/10_nvidia.json ]; then
    echo "[INFO] No NVIDIA EGL vendor config found, writing..."
    sudo mkdir -p /usr/share/glvnd/egl_vendor.d
    echo '{
    "file_format_version" : "1.0.0",
    "ICD" : {
        "library_path" : "libEGL_nvidia.so.0"
    }
}' | sudo tee /usr/share/glvnd/egl_vendor.d/10_nvidia.json > /dev/null
else
    echo "[INFO] NVIDIA EGL vendor config already present, skipping."
fi

# Set VK_DRIVER_FILES only if pointing to our manually written ICD
if [ -f /etc/vulkan/icd.d/nvidia_icd.json ]; then
    grep -q VK_DRIVER_FILES ~/.bashrc 2>/dev/null || \
        echo 'export VK_DRIVER_FILES=/etc/vulkan/icd.d/nvidia_icd.json' >> ~/.bashrc
    export VK_DRIVER_FILES=/etc/vulkan/icd.d/nvidia_icd.json
fi

vulkaninfo --summary &>/dev/null && echo "[INFO] Vulkan OK." || echo "[WARN] Vulkan check failed — may need driver re-install."

echo "=== [2/6] System dependencies ==="
sudo dpkg --add-architecture i386
sudo apt-get update
sudo apt-get install -y \
    curl ca-certificates wget unzip software-properties-common \
    libgl1-mesa-glx:i386 lib32gcc-s1 lib32stdc++6 \
    libopenxr-loader1 libopenxr-dev \
    libva2 libva-drm2 libva-x11-2 \
    libxcursor1 libxrender1 libxfixes3 libxkbcommon0 libxkbcommon-x11-0 \
    libcap2-bin \
    || true

echo "=== [3/6] Steam ==="
if ! command -v steam &>/dev/null; then
    wget -q https://cdn.akamai.steamstatic.com/client/installer/steam.deb
    sudo dpkg -i steam.deb || true
    sudo apt-get install -f -y
    rm -f steam.deb
    echo "[INFO] Steam installed. You need to log in manually: run 'steam' and sign in."
else
    echo "[INFO] Steam already installed."
fi

echo "=== [4/6] SteamVR ==="
STEAMVR_DIR="$HOME/.local/share/Steam/steamapps/common/SteamVR"
if [ ! -d "$STEAMVR_DIR" ]; then
    echo "[INFO] SteamVR not found. Install it from Steam Library (app ID 250820)."
    echo "[INFO] Run: steam steam://install/250820"
else
    echo "[INFO] SteamVR already installed at $STEAMVR_DIR"
    # Set vrcompositor capabilities
    sudo setcap CAP_SYS_NICE+eip "$STEAMVR_DIR/bin/linux64/vrcompositor-launcher" 2>/dev/null || true
fi

echo "=== [5/6] ALVR streamer v20.14.1 ==="
if [ ! -d "$HOME/alvr_streamer_linux" ]; then
    cd ~
    wget -q https://github.com/alvr-org/ALVR/releases/download/v20.14.1/alvr_streamer_linux.tar.gz
    tar -xzf alvr_streamer_linux.tar.gz
    rm -f alvr_streamer_linux.tar.gz
    echo "[INFO] ALVR extracted to ~/alvr_streamer_linux"
else
    echo "[INFO] ALVR already installed."
fi

# Register ALVR driver with SteamVR
if [ -d "$STEAMVR_DIR" ]; then
    export LD_LIBRARY_PATH="$STEAMVR_DIR/bin/linux64:${LD_LIBRARY_PATH:-}"
    "$STEAMVR_DIR/bin/linux64/vrpathreg" adddriver ~/alvr_streamer_linux/lib64/alvr 2>/dev/null || true
    echo "[INFO] ALVR driver registered with SteamVR."
fi

echo "=== [6/6] uv + Isaac Lab (teleop-vr package) ==="
if ! command -v uv &>/dev/null; then
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
uv sync

if [ ! -d "$HOME/IsaacLab" ]; then
    git clone --depth 1 https://github.com/isaac-sim/IsaacLab.git "$HOME/IsaacLab"
else
    echo "[INFO] IsaacLab already cloned at ~/IsaacLab"
fi

echo ""
echo "=== DONE ==="
echo "Steps remaining:"
echo "  1. Log in to Steam if not done: steam"
echo "  2. Install SteamVR if not done: steam steam://install/250820"
echo "  3. Install Tailscale if needed: curl -fsSL https://tailscale.com/install.sh | sh && sudo tailscale up"
echo "  4. Start VR teleop: bash teleop-vr/run_teleop.sh Isaac-Stack-Cube-Franka-IK-Abs-v0"
