"""Interactive layout editor for the toy-sorting scene.

Spawns the full scene with physics frozen so you can reposition objects
freely using the Isaac Sim viewport transform gizmos (press W to activate).
When you close the window the current stage is exported to a USDA file.

Usage:
    uv run python scripts/layout_editor.py
    uv run python scripts/layout_editor.py --export assets/my_layout.usda

Physics is intentionally NOT stepped — only the GUI update loop runs.
Objects stay wherever you drag them.  Close the window to export and exit.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SRC = _REPO_ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

# ---------------------------------------------------------------------------
# AppLauncher must be created before any other isaaclab.* import
# ---------------------------------------------------------------------------
parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
parser.add_argument(
    "--export",
    default="assets/scene_layout.usda",
    help="Path to write the exported USDA layout (default: assets/scene_layout.usda)",
)
args_cli = parser.parse_args()

from isaaclab.app import AppLauncher  # noqa: E402
app_launcher = AppLauncher(headless=False)
simulation_app = app_launcher.app

# ---------------------------------------------------------------------------
# Isaac Lab imports (safe after AppLauncher)
# ---------------------------------------------------------------------------
import isaaclab.sim as sim_utils  # noqa: E402
from isaaclab.sim import SimulationContext  # noqa: E402
from manipulator_learning.envhub import make_env  # noqa: E402


def main() -> None:
    export_path = (_REPO_ROOT / args_cli.export).resolve()

    sim_cfg = sim_utils.SimulationCfg(dt=1.0 / 60.0)
    sim = SimulationContext(sim_cfg)
    sim.set_camera_view(eye=[0.8, -0.8, 1.2], target=[0.0, 0.0, 0.2])

    print("[layout_editor] Building scene …")
    envs_dict = make_env(n_envs=1)
    env = envs_dict["toy_sorting"][0]

    print("[layout_editor] Resetting (physics will NOT be stepped) …")
    sim.reset()
    env.reset()

    print()
    print("=" * 60)
    print("  Physics is FROZEN.  Drag objects freely in the viewport.")
    print("  Press W  → translate gizmo")
    print("  Press E  → rotate gizmo")
    print("  Press R  → scale gizmo")
    print(f"  Close window to export layout → {export_path}")
    print("=" * 60)
    print()

    # Run GUI update loop without stepping physics
    while simulation_app.is_running():
        simulation_app.update()

    # Export current stage state to USDA
    import omni.usd
    stage = omni.usd.get_context().get_stage()
    export_path.parent.mkdir(parents=True, exist_ok=True)
    stage.Export(str(export_path))
    print(f"[layout_editor] Layout exported → {export_path}")

    env.close()


if __name__ == "__main__":
    main()
    simulation_app.close()
