#!/bin/bash
VENV="$(cd "$(dirname "$0")" && pwd)/.venv"
REPO="$(cd "$(dirname "$0")/.." && pwd)"
source "$VENV/bin/activate"
export XR_RUNTIME_JSON=$(find ~/.local/share/Steam ~/.steam -name "steamxr_linux64.json" 2>/dev/null | head -1)

cd ~/IsaacLab
"$VENV/bin/python" "$REPO/teleop-vr/scripts/record_demos_with_hotkeys.py" "$@"
