#!/bin/bash
# Start SteamVR + ALVR, then launch Isaac Lab teleop.
# Usage:
#   bash scripts/start_vr_teleop.sh
#   bash scripts/start_vr_teleop.sh --task Isaac-Stack-Cube-Franka-IK-Abs-v0
set -e

STEAMVR_DIR="/root/.local/share/Steam/steamapps/common/SteamVR"
ISAACLAB_DIR="/opt/IsaacLab"

# ---------------------------------------------------------------------------
# 1. Start SteamVR
# ---------------------------------------------------------------------------
if ! pgrep -f vrserver > /dev/null 2>&1; then
    echo "[start_vr] Starting SteamVR ..."
    "$STEAMVR_DIR/bin/vrstartup.sh" &
    sleep 5
fi

# ---------------------------------------------------------------------------
# 2. Start ALVR dashboard
# ---------------------------------------------------------------------------
if ! pgrep -f alvr_dashboard > /dev/null 2>&1; then
    echo "[start_vr] Starting ALVR dashboard ..."
    /opt/alvr/bin/alvr_dashboard &
    sleep 3
fi

echo "[start_vr] === SteamVR + ALVR running ==="
echo "[start_vr] Connect Quest via ALVR, then press Enter to launch teleop."
read -r

# ---------------------------------------------------------------------------
# 3. Launch Isaac Lab teleop from cloned repo
# ---------------------------------------------------------------------------
cd "$ISAACLAB_DIR"

uv run python scripts/environments/teleoperation/teleop_se3_agent.py \
    --teleop_device handtracking \
    --device cpu \
    "$@"
