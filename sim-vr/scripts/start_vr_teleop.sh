#!/bin/bash
# Start SteamVR + ALVR, then launch Isaac Lab teleop.
# Usage (from repo root):
#   bash sim-vr/scripts/start_vr_teleop.sh --task Isaac-Stack-Cube-Franka-IK-Abs-v0
set -e

STEAMVR_DIR=$(find "$HOME" -path "*/steamapps/common/SteamVR" -type d 2>/dev/null | head -1)
ALVR_DIR="$HOME/alvr_streamer_linux"
SIMVR_DIR="$(cd "$(dirname "$0")/.." && pwd)"

if [ -z "$STEAMVR_DIR" ]; then
    echo "[start_vr] ERROR: SteamVR not found. Run bare-install.sh first."
    exit 1
fi

# Export XR runtime
export XR_RUNTIME_JSON=$(find "$HOME" -name "steamxr_linux64.json" 2>/dev/null | head -1)

# ---------------------------------------------------------------------------
# 1. Start SteamVR
# ---------------------------------------------------------------------------
if ! pgrep -f vrserver > /dev/null 2>&1; then
    echo "[start_vr] Starting SteamVR ..."
    steam steam://run/250820 &
    sleep 8
fi

# ---------------------------------------------------------------------------
# 2. Start ALVR dashboard
# ---------------------------------------------------------------------------
if ! pgrep -f alvr_dashboard > /dev/null 2>&1; then
    echo "[start_vr] Starting ALVR dashboard ..."
    "$ALVR_DIR/bin/alvr_dashboard" &
    sleep 3
fi

echo "[start_vr] === SteamVR + ALVR running ==="
echo "[start_vr] Connect Quest via ALVR, then press Enter to launch teleop."
read -r

# ---------------------------------------------------------------------------
# 3. Launch Isaac Lab teleop
# ---------------------------------------------------------------------------
cd "$SIMVR_DIR"
source .venv/bin/activate

python "$(find .venv -path '*/teleoperation/teleop_se3_agent.py' 2>/dev/null | head -1)" \
    --teleop_device handtracking \
    --device cpu \
    "$@"
