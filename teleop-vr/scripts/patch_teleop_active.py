"""Patch teleop_se3_agent.py to auto-activate teleoperation.

Isaac Lab's teleop script defaults to teleoperation_active=False for XR devices,
waiting for a "start" message from NVIDIA's IsaacXRTeleopClient. Since we use
ALVR + SteamVR (no IsaacXRTeleopClient), the start message never arrives.

This patch forces teleoperation_active=True so hand tracking works immediately.
"""
import sys

path = sys.argv[1] if len(sys.argv) > 1 else None
if not path:
    import subprocess
    result = subprocess.run(
        ["find", "/home", "-path", "*/teleoperation/teleop_se3_agent.py", "-not", "-path", "*/.venv/*"],
        capture_output=True, text=True
    )
    path = result.stdout.strip().split("\n")[0] if result.stdout.strip() else None

if not path:
    print("[patch] ERROR: teleop_se3_agent.py not found")
    sys.exit(1)

with open(path) as f:
    code = f.read()

old = """    if args_cli.xr:
        # Default to inactive for hand tracking
        teleoperation_active = False
    else:
        # Always active for other devices
        teleoperation_active = True"""

new = """    # Always active - we don't have IsaacXRTeleopClient to send "start"
    teleoperation_active = True"""

if old in code:
    code = code.replace(old, new)
    with open(path, "w") as f:
        f.write(code)
    print(f"[patch] OK - patched {path}")
elif "# Always active - we don't have IsaacXRTeleopClient" in code:
    print(f"[patch] Already patched: {path}")
else:
    print(f"[patch] WARNING: pattern not found in {path}")
