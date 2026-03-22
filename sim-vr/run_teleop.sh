#!/bin/bash
VENV="$HOME/manipulator-issac-learning/sim-vr/.venv"
REPO="$(cd "$(dirname "$0")/.." && pwd)"
source "$VENV/bin/activate"
export XR_RUNTIME_JSON=$(find ~/.local/share/Steam ~/.steam -name "steamxr_linux64.json" 2>/dev/null | head -1)

# Patch teleop to auto-activate (ALVR has no IsaacXRTeleopClient to send "start")
"$VENV/bin/python" "$REPO/scripts/patch_teleop_active.py" ~/IsaacLab/scripts/environments/teleoperation/teleop_se3_agent.py

cd ~/IsaacLab
TASK="${1:-Isaac-Stack-Cube-Franka-IK-Rel-v0}"
shift 2>/dev/null || true
"$VENV/bin/python" scripts/environments/teleoperation/teleop_se3_agent.py --task "$TASK" --teleop_device handtracking --device cpu "$@"
