# VR Teleop Test — Quest 3 + Isaac Lab on Vast.ai KVM

Minimal test: control a stock Franka arm in Isaac Lab using Quest 3
hand tracking, streamed via ALVR over Tailscale. No custom code needed —
just infra setup to prove the pipeline works.

**Architecture:**
```
Quest 3 (your room)
  → ALVR client (Meta Store)
    → Tailscale
      → Vast.ai KVM VM
        → ALVR streamer → SteamVR (OpenXR)
          → Isaac Lab (teleop_se3_agent.py)
            → Franka IK teleop with hand tracking
```

---

## Part 1 — Quest 3 Setup

Nothing to install from sideloading. Everything from stores.

1. **Tailscale** — already installed
2. **ALVR** — install from Meta Store (search "ALVR")
3. Make sure both are on the same Tailscale network as your Vast.ai VM

---

## Part 2 — Vast.ai KVM VM Setup

SSH into your VM. These steps assume Ubuntu 22.04 with NVIDIA GPU.

### 2.1 — Tailscale

```bash
# Skip if already installed
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up
# Note your VM's Tailscale IP
tailscale ip -4
```

### 2.2 — Vulkan / EGL / GPU Renderer Setup

Isaac Sim needs Vulkan ICD and EGL configs to initialize the GPU renderer.
Without these, simulations hang at "Starting the simulation...".

```bash
# Create config directories
sudo mkdir -p /etc/vulkan/icd.d /etc/vulkan/implicit_layer.d /usr/share/glvnd/egl_vendor.d

# NVIDIA Vulkan ICD
echo '{
    "file_format_version" : "1.0.0",
    "ICD" : {
        "library_path" : "libGLX_nvidia.so.0",
        "api_version" : "1.3.194"
    }
}' | sudo tee /etc/vulkan/icd.d/nvidia_icd.json

# NVIDIA EGL vendor
echo '{
    "file_format_version" : "1.0.0",
    "ICD" : {
        "library_path" : "libEGL_nvidia.so.0"
    }
}' | sudo tee /usr/share/glvnd/egl_vendor.d/10_nvidia.json

# Set env var (add to ~/.bashrc too)
export VK_DRIVER_FILES=/etc/vulkan/icd.d/nvidia_icd.json
echo 'export VK_DRIVER_FILES=/etc/vulkan/icd.d/nvidia_icd.json' >> ~/.bashrc

# Install Vulkan tools and verify
sudo apt install -y vulkan-tools
vulkaninfo --summary
# Should show your GPU (e.g. RTX 4080)
```

### 2.3 — Virtual Display (headless VM needs this)

```bash
# Check if you already have a display
echo $DISPLAY

# If empty or no physical monitor, set up a virtual one:
sudo apt update
sudo apt install -y xvfb x11-xserver-utils

# Start virtual display
Xvfb :1 -screen 0 1920x1080x24 &
export DISPLAY=:1

# Make it persist — add to ~/.bashrc:
echo 'export DISPLAY=:1' >> ~/.bashrc

# Alternative: if the above doesn't work with SteamVR, try nvidia virtual display:
# sudo nvidia-xconfig --allow-empty-initial-configuration --virtual=1920x1080
# sudo X :1 &
# export DISPLAY=:1
```

### 2.4 — Install Steam

```bash
sudo dpkg --add-architecture i386
sudo apt update
sudo apt install -y software-properties-common wget gdebi-core libgl1-mesa-glx:i386

# Download and install Steam
wget https://cdn.akamai.steamstatic.com/client/installer/steam.deb
sudo dpkg -i steam.deb
sudo apt install -f -y

# Login to Steam (use a throwaway free account — don't use your main!)
# Interactive login (password not visible in process list):
steam -no-browser
```

### 2.5 — Install SteamVR

```bash
# SteamVR app ID = 250820
# Install via steamcmd or Steam CLI:
steamcmd +@sSteamCmdForcePlatformType linux +login YOUR_STEAM_USERNAME +app_update 250820 validate +quit

# OR if steamcmd isn't available, install via Steam:
steam steam://install/250820
```

### 2.6 — Install ALVR Streamer (v20.14.1)

```bash
cd ~
wget https://github.com/alvr-org/ALVR/releases/download/v20.14.1/alvr_streamer_linux.tar.gz
tar -xzf alvr_streamer_linux.tar.gz

# Also grab the launcher (dashboard UI):
wget https://github.com/alvr-org/ALVR/releases/download/v20.14.1/alvr_launcher_linux.tar.gz
tar -xzf alvr_launcher_linux.tar.gz
```

### 2.7 — Register ALVR Driver with SteamVR

```bash
# The ALVR driver lives at:
ls ~/alvr_streamer_linux/lib64/alvr/

# Register it with SteamVR (two separate commands — vrpathreg needs LD_LIBRARY_PATH):
export LD_LIBRARY_PATH="$HOME/.local/share/Steam/steamapps/common/SteamVR/bin/linux64:$LD_LIBRARY_PATH"

~/.local/share/Steam/steamapps/common/SteamVR/bin/linux64/vrpathreg adddriver ~/alvr_streamer_linux/lib64/alvr
```

### 2.8 — Set VR Compositor Capabilities

```bash
# SteamVR compositor needs CAP_SYS_NICE for proper scheduling:
sudo setcap CAP_SYS_NICE+eip ~/.local/share/Steam/steamapps/common/SteamVR/bin/linux64/vrcompositor-launcher
```

---

## Part 3 — Install Isaac Lab

### 3.1 — Python Environment

```bash
# Isaac Sim 5.1 needs Python 3.11
# Install miniconda if not already installed:
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh -b -p ~/miniconda3
eval "$(~/miniconda3/bin/conda shell.bash hook)"
conda init

# Create env with Python 3.11:
conda create -n isaaclab python=3.11 -y
conda activate isaaclab
```

### 3.2 — Install Isaac Sim + Isaac Lab

```bash
# Isaac Sim
pip install "isaacsim[all,extscache]==5.1.0" --extra-index-url https://pypi.nvidia.com

# PyTorch (CUDA 12.8)
pip install -U torch==2.7.0 torchvision==0.22.0 --index-url https://download.pytorch.org/whl/cu128

# Clone Isaac Lab
cd ~
git clone https://github.com/isaac-sim/IsaacLab.git
cd IsaacLab

# Install Isaac Lab
./isaaclab.sh --install

# Quick sanity check (should open a sim window):
./isaaclab.sh -p scripts/tutorials/00_sim/create_empty.py --headless
```

---

## Part 4 — Connect and Test

### 4.1 — Start ALVR + SteamVR on VM

```bash
# Terminal 1: Start ALVR dashboard
cd ~/alvr_streamer_linux
./bin/alvr_dashboard

# ALVR should start SteamVR automatically.
# If not, start SteamVR manually in Terminal 2:
steam steam://run/250820
```

### 4.2 — Connect Quest 3

1. Put on Quest 3
2. Open **ALVR** app on Quest
3. It should auto-discover the VM via Tailscale, or manually enter VM's Tailscale IP
4. Click **Connect**
5. In ALVR dashboard on VM: go to **Devices** tab → click **Trust** next to the Quest
6. You should see the SteamVR home environment in your headset

### 4.3 — Run Isaac Lab Franka Teleop

```bash
# On the VM, in the IsaacLab directory:
cd ~/IsaacLab

./isaaclab.sh -p scripts/environments/teleoperation/teleop_se3_agent.py \
    --task Isaac-Stack-Cube-Franka-IK-Abs-v0 \
    --teleop_device handtracking
```

7. In the sim window on the VM, click **"Start VR"** button
8. The Franka sim should appear in your Quest headset
9. Use your hands to control the robot arm!

---

## Troubleshooting

**ALVR doesn't find Quest:**
- Confirm both VM and Quest are on same Tailscale network: `tailscale status`
- Try entering VM's Tailscale IP manually in ALVR Quest app
- Check firewall: ALVR uses UDP ports 9943-9944 by default

**SteamVR won't start:**
- Make sure `DISPLAY` is set: `echo $DISPLAY`
- Try nvidia virtual display instead of Xvfb
- Check GPU is accessible: `nvidia-smi`

**"Start VR" button missing in Isaac Lab:**
- The `--teleop_device handtracking` flag must be set (it enables `xr=True`)
- Make sure SteamVR is running and Quest is connected BEFORE launching the script

**High latency / choppy:**
- ALVR settings → Video tab → reduce resolution and bitrate
- Check Tailscale latency: `tailscale ping <quest-ip>`
- Wired connection (USB-C) is more stable but not possible with cloud VM

**Steam login issues on headless:**
- Steam Guard may block headless login — temporarily disable or use Steam app to approve
- Use a throwaway Steam account so you don't risk your main credentials
