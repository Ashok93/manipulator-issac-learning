#!/bin/bash
set -e

# ---------------------------------------------------------------------------
# 1. First run: launch Steam to login and install SteamVR
# ---------------------------------------------------------------------------
# SteamVR can end up in either /root/Steam or /root/.local/share/Steam
STEAMVR_DIR=$(find /root -path "*/steamapps/common/SteamVR" -type d 2>/dev/null | head -1)
if [ -z "$STEAMVR_DIR" ]; then
    echo "[sim-vr] === First run: SteamVR not found ==="
    echo "[sim-vr] Launching Steam — log in and install SteamVR (app ID 250820)."
    echo "[sim-vr] After SteamVR is installed, close Steam and re-run the container."
    steam
    exit 0
fi
echo "[sim-vr] SteamVR found at: $STEAMVR_DIR"

# ---------------------------------------------------------------------------
# 2. Register ALVR driver with SteamVR (idempotent)
# ---------------------------------------------------------------------------
VRPATHREG="$STEAMVR_DIR/bin/linux64/vrpathreg"
if [ -x "$VRPATHREG" ]; then
    export LD_LIBRARY_PATH="$STEAMVR_DIR/bin/linux64:${LD_LIBRARY_PATH:-}"
    "$VRPATHREG" adddriver /opt/alvr/lib64/alvr 2>/dev/null || true
fi

# ---------------------------------------------------------------------------
# 3. Enable hand tracking in SteamVR config
# ---------------------------------------------------------------------------
# Find steamvr.vrsettings wherever Steam put it
VRSETTINGS=$(find /root -name "steamvr.vrsettings" 2>/dev/null | head -1)
if [ -n "$VRSETTINGS" ]; then
    python3.11 -c "
import json
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
STEAMXR_JSON=$(find /root -name "steamxr_linux64.json" 2>/dev/null | head -1)
if [ -n "$STEAMXR_JSON" ]; then
    export XR_RUNTIME_JSON="$STEAMXR_JSON"
fi

source .venv/bin/activate
exec "$@"
