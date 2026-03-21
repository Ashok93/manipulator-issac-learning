#!/bin/bash
set -e

# ---------------------------------------------------------------------------
# 1. Install SteamVR via steamcmd on first run
# ---------------------------------------------------------------------------
STEAMVR_DIR="/root/.local/share/Steam/steamapps/common/SteamVR"
if [ ! -d "$STEAMVR_DIR" ]; then
    echo "[sim-vr] === First run: installing SteamVR ==="
    if [ -z "$STEAM_USER" ]; then
        echo "[sim-vr] Set STEAM_USER env var or pass it interactively."
        read -rp "Steam username: " STEAM_USER
    fi
    /opt/steamcmd/steamcmd.sh \
        +@sSteamCmdForcePlatformType linux \
        +login "$STEAM_USER" \
        +app_update 250820 validate \
        +quit
    echo "[sim-vr] SteamVR installed."
fi

# ---------------------------------------------------------------------------
# 2. Register ALVR driver with SteamVR (idempotent)
# ---------------------------------------------------------------------------
VRPATHREG="$STEAMVR_DIR/bin/linux64/vrpathreg"
if [ -x "$VRPATHREG" ]; then
    export LD_LIBRARY_PATH="$STEAMVR_DIR/bin/linux64:${LD_LIBRARY_PATH:-}"
    "$VRPATHREG" adddriver /opt/alvr/lib64/alvr 2>/dev/null || true
fi

# ---------------------------------------------------------------------------
# 3. Enable hand tracking in SteamVR config (ALVR settings)
# ---------------------------------------------------------------------------
VRSETTINGS="/root/.local/share/Steam/config/steamvr.vrsettings"
if [ -f "$VRSETTINGS" ]; then
    python3.11 -c "
import json, sys
path = '$VRSETTINGS'
with open(path) as f:
    cfg = json.load(f)
cfg.setdefault('driver_alvr_server', {})['handTrackingEnabled'] = True
cfg.setdefault('steamvr', {}).update({'enableHandTracking': True, 'handTrackingEnabled': True})
with open(path, 'w') as f:
    json.dump(cfg, f, indent=3)
" 2>/dev/null || true
fi

# ---------------------------------------------------------------------------
# 4. Install Python deps via uv
# ---------------------------------------------------------------------------
cd /workspace/sim-vr
uv sync --extra sim

# ---------------------------------------------------------------------------
# 5. Fix OpenXR XCR capture layer (needs isaaclab installed)
# ---------------------------------------------------------------------------
bash /workspace/sim-vr/scripts/fix_xcr_layer.sh 2>/dev/null || true

# ---------------------------------------------------------------------------
# 6. Set XR_RUNTIME_JSON to SteamVR
# ---------------------------------------------------------------------------
STEAMXR_JSON="$STEAMVR_DIR/steamxr_linux64.json"
if [ -f "$STEAMXR_JSON" ]; then
    export XR_RUNTIME_JSON="$STEAMXR_JSON"
else
    # Fallback: search for it
    FOUND=$(find /root/.local/share/Steam -name "steamxr_linux64.json" 2>/dev/null | head -1)
    [ -n "$FOUND" ] && export XR_RUNTIME_JSON="$FOUND"
fi

source .venv/bin/activate
exec "$@"
