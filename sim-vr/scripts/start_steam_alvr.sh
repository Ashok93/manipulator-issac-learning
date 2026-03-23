#!/bin/bash
# Start SteamVR and ALVR dashboard.
# After connecting Quest in ALVR, run: bash sim-vr/run_teleop.sh
set -e

STEAMVR_DIR=$(find "$HOME" -path "*/steamapps/common/SteamVR" -type d 2>/dev/null | head -1)
ALVR_DIR="$HOME/alvr_streamer_linux"

if [ -z "$STEAMVR_DIR" ]; then
    echo "[start_steam_alvr] ERROR: SteamVR not found. Run bare-install.sh and install SteamVR first."
    exit 1
fi

# Start SteamVR
if ! pgrep -f vrserver > /dev/null 2>&1; then
    echo "[start_steam_alvr] Starting SteamVR ..."
    steam steam://run/250820 &
    sleep 8
else
    echo "[start_steam_alvr] SteamVR already running."
fi

# Start ALVR dashboard
if ! pgrep -f alvr_dashboard > /dev/null 2>&1; then
    echo "[start_steam_alvr] Starting ALVR dashboard ..."
    "$ALVR_DIR/bin/alvr_dashboard" &
else
    echo "[start_steam_alvr] ALVR already running."
fi

echo ""
echo "[start_steam_alvr] SteamVR + ALVR are running."
echo "[start_steam_alvr] Connect your Quest in the ALVR dashboard, then run:"
echo ""
echo "    bash sim-vr/run_teleop.sh"
echo ""
