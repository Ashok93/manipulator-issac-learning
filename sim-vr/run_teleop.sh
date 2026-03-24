#!/bin/bash
VENV="$HOME/manipulator-issac-learning/sim-vr/.venv"
REPO="$(cd "$(dirname "$0")/.." && pwd)"
source "$VENV/bin/activate"
export XR_RUNTIME_JSON=$(find ~/.local/share/Steam ~/.steam -name "steamxr_linux64.json" 2>/dev/null | head -1)

cd ~/IsaacLab
TASK="${1:-Isaac-Stack-Cube-Franka-IK-Rel-v0}"
shift 2>/dev/null || true
"$VENV/bin/python" "$REPO/sim-vr/scripts/teleop_se3_agent_hotkeys.py" --task "$TASK" --teleop_device handtracking --device cpu "$@"
