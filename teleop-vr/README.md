# teleop-vr: VR Teleoperation for Isaac Lab

VR hand tracking teleop for Isaac Lab on a Linux GPU VM (tested on Vast.ai KVM, Ubuntu 22.04/24.04).

**Stack:** Quest 3 → ALVR → SteamVR → OpenXR → Isaac Lab (Franka arm)

---

## Step 1 — Run bare-install.sh

On a fresh VM with NVIDIA drivers:

```bash
bash teleop-vr/bare-install.sh
```

This installs: Vulkan/EGL configs, Steam, ALVR v20.14.1, Python 3.11, uv, Isaac Lab, and registers the OpenXR XCR capture layer.

---

## Step 2 — Log in to Steam and install SteamVR

```bash
steam
```

Sign in interactively (required at least once). Then install SteamVR:

```bash
steam steam://install/250820
```

---

## Step 3 — Set SteamVR Launch Options

Find your vrmonitor.sh path:

```bash
find /home -path "*/SteamVR/bin/vrmonitor.sh" 2>/dev/null
```

Then in Steam Library → right-click **SteamVR** → **Properties** → **Launch Options**, paste:

```
/home/user/.steam/debian-installation/steamapps/common/SteamVR/bin/vrmonitor.sh %command%
```

(Use the actual path from the find command above.)

---

## Step 4 — Configure ALVR

Open the ALVR dashboard and under **Headset** tab, set:

- **Hand skeleton** → ON
- **SteamVR Input 2.0** → ON
- **Hand tracking interaction** → ON

---

## Step 5 — Start SteamVR + ALVR

```bash
bash teleop-vr/scripts/start_steam_alvr.sh
```

This starts SteamVR and the ALVR dashboard. Then:

1. Put on Quest
2. Open ALVR app on Quest
3. Connect to the VM (use Tailscale IP if not on same LAN)
4. Click **Trust** in the ALVR dashboard → Devices tab

---

## Step 6 — Launch Teleop

```bash
bash teleop-vr/run_teleop.sh
```

Defaults to relative mode (`Isaac-Stack-Cube-Franka-IK-Rel-v0`). To override the task:

```bash
bash teleop-vr/run_teleop.sh Isaac-Stack-Cube-Franka-IK-Abs-v0
```

**Use Rel (relative) mode** — Abs mode causes the robot to jump to your hand position on startup.

While the teleop terminal is focused, use:

- `s` to start teleoperation
- `p` to pause teleoperation
- `r` to reset the environment
- `q` to quit

## Step 7 — Record Demos

Use the recording launcher to write raw Isaac Lab HDF5 episodes:

```bash
bash teleop-vr/run_record_demos.sh --task Isaac-Stack-Cube-Franka-IK-Rel-v0 \
  --dataset_file ./datasets/franka_demos.hdf5 \
  --enable_cameras
```

For recording, the same hotkeys apply:

- `s` to start recording
- `p` to pause recording
- `r` to reset / finalize the current episode
- `q` to quit

Visuomotor annotation and Mimic generation happen later in `dataset-pipeline/isaac-mimic/`, and LeRobot conversion happens in `dataset-pipeline/lerobot-conversion/`, after the raw HDF5 demos are collected.

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `xrCreateInstance failed` | `sudo bash teleop-vr/scripts/fix_xcr_layer.sh` |
| `Failed to unblock ALVR driver: steamvr.vrsettings does not exist` | Launch SteamVR at least once first so it creates the config |
| SteamVR won't start | Check launch options path is correct (Step 3) |
| ALVR dashboard won't open | `sudo apt install libva2 libva-drm2 libva-x11-2 libxcursor1 libxrender1 libxfixes3` |
| Scene renders in VR but hands don't move robot | Press `s` in the teleop terminal to start teleoperation |
| Robot twists/jumps on startup | Use Rel mode (default), not Abs |
| `XR_RUNTIME_JSON` not set | `export XR_RUNTIME_JSON=$(find ~/.steam -name "steamxr_linux64.json" 2>/dev/null \| head -1)` |

---

## File Structure

```
teleop-vr/
  bare-install.sh                    # One-time VM setup
  run_teleop.sh                      # Launch Isaac Lab teleop (run after Step 5)
  run_record_demos.sh                # Launch Isaac Lab demo recording
  pyproject.toml                     # Python deps (isaaclab via uv)
  scripts/
    isaaclab_session_utils.py        # Shared hotkey / device helpers
    start_steam_alvr.sh              # Start SteamVR + ALVR (Step 5)
    fix_xcr_layer.sh                 # Register OpenXR XCR capture layer
    fix_steamvr_handtracking.py      # Enable hand tracking in steamvr.vrsettings
    teleop_se3_agent_hotkeys.py      # Local launcher with keyboard session controls
    record_demos_with_hotkeys.py     # Local demo recorder with keyboard session controls
```
