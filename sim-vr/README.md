# sim-vr: VR Teleoperation for Isaac Lab

Bare-metal VR teleop stack for Isaac Lab on a Linux GPU VM (tested on Vast.ai KVM, Ubuntu 22.04/24.04).

Uses **Quest 3** (or Quest 2) with **ALVR** streaming to **SteamVR** on the VM, and Isaac Lab's OpenXR hand tracking teleop.

## Quick Start

```bash
# 1. Run the install script on a fresh VM with NVIDIA drivers
bash sim-vr/bare-install.sh

# 2. Complete the manual steps below

# 3. Launch VR teleop
bash sim-vr/scripts/start_vr_teleop.sh --task Isaac-Stack-Cube-Franka-IK-Abs-v0
```

## Manual Steps After bare-install.sh

### 1. Log in to Steam

```bash
steam
```

Sign in with your Steam account. This must be done interactively at least once.

### 2. Install SteamVR

```bash
steam steam://install/250820
```

Or install from the Steam Library UI.

### 3. Set SteamVR Launch Options

This is required so SteamVR starts correctly on headless Linux:

1. Open Steam Library
2. Right-click **SteamVR** -> **Properties**
3. In **Launch Options**, paste:

```
~/.local/share/Steam/steamapps/common/SteamVR/bin/vrmonitor.sh %command%
```

### 4. Configure ALVR Settings

Open the ALVR dashboard (`~/alvr_streamer_linux/bin/alvr_dashboard`) and under the **Headset** tab, ensure:

- **Hand skeleton** -> ON
- **Hand tracking interaction** -> ON
- **SteamVR Input 2.0** -> ON

### 5. Enable SteamVR Hand Tracking

`bare-install.sh` does this automatically, but verify in `~/.local/share/Steam/config/steamvr.vrsettings`:

```json
{
   "steamvr": {
      "enableHandTracking": true,
      "handTrackingEnabled": true
   },
   "driver_alvr_server": {
      "handTrackingEnabled": true
   }
}
```

### 6. OpenXR XCR Capture Layer

`bare-install.sh` runs `scripts/fix_xcr_layer.sh` to register Isaac Sim's OpenXR API layer. If you get `xrCreateInstance failed` errors, re-run:

```bash
sudo bash sim-vr/scripts/fix_xcr_layer.sh
```

This copies the XCR capture layer JSON to `/usr/share/openxr/1/api_layers/implicit.d/` with the correct absolute path to `libxcr-capture-oxr-layer.so`.

### 7. Tailscale (optional, for ALVR connection)

If the Quest and VM are not on the same LAN:

```bash
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up
```

Install Tailscale on the Quest as well, then connect ALVR using the Tailscale IP.

## Usage

### Full launch (SteamVR + ALVR + teleop)

```bash
bash sim-vr/scripts/start_vr_teleop.sh --task Isaac-Stack-Cube-Franka-IK-Abs-v0
```

This starts SteamVR, ALVR, waits for Quest connection, then launches teleop.

### Teleop only (SteamVR + ALVR already running)

```bash
bash sim-vr/run_teleop.sh
```

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `xrCreateInstance failed` | Run `sudo bash sim-vr/scripts/fix_xcr_layer.sh` |
| `vrstartup.sh: no steam runtime environment set` | Install full Steam client (not steamcmd), set launch options per step 3 |
| ALVR dashboard won't start | Install missing GUI libs: `sudo apt install libva2 libva-drm2 libva-x11-2 libxcursor1 libxrender1 libxfixes3` |
| `XR_RUNTIME_JSON` not set | `export XR_RUNTIME_JSON=$(find ~/.local/share/Steam -name "steamxr_linux64.json" 2>/dev/null \| head -1)` |
| Vulkan errors | Verify `nvidia_icd.json` exists at `/etc/vulkan/icd.d/` and `VK_DRIVER_FILES` is set |

## File Structure

```
sim-vr/
  bare-install.sh          # One-time setup for fresh VMs
  run_teleop.sh            # Quick-launch teleop (assumes SteamVR running)
  pyproject.toml           # Python deps (isaaclab via uv)
  scripts/
    start_vr_teleop.sh     # Full launch: SteamVR + ALVR + teleop
    fix_xcr_layer.sh       # Register OpenXR XCR capture layer
```
