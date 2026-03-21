#!/bin/bash
cd ~/manipulator-issac-learning/sim-vr
source .venv/bin/activate
export XR_RUNTIME_JSON=$(find ~/.local/share/Steam -name "steamxr_linux64.json" 2>/dev/null | head -1)
cd ~/IsaacLab
python3 scripts/environments/teleoperation/teleop_se3_agent.py --task Isaac-Stack-Cube-Franka-IK-Abs-v0 --teleop_device handtracking --device cpu "$@"
