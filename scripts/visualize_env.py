"""Run the toy-sorting environment for 600 steps with random joint actions.

Follows the official Isaac Lab standalone script pattern:
  1. Parse args and add AppLauncher args
  2. Launch AppLauncher (starts Isaac Sim)
  3. Import isaaclab.* modules ONLY after app is running
  4. Run the environment loop

Usage:
    uv run python scripts/visualize_env.py --headless
    uv run python scripts/visualize_env.py             # with GUI
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
# 1. Parse args — AppLauncher adds --headless, --livestream, --enable_cameras
# ---------------------------------------------------------------------------
parser = argparse.ArgumentParser(description="Visualise the toy-sorting scene.")
parser.add_argument("--steps", type=int, default=600, help="Number of sim steps.")

from isaaclab.app import AppLauncher  # noqa: E402
AppLauncher.add_app_launcher_args(parser)
args_cli = parser.parse_args()

# ---------------------------------------------------------------------------
# 2. Launch Isaac Sim — must happen before ANY isaaclab.* import
# ---------------------------------------------------------------------------
app_launcher = AppLauncher(args_cli)
simulation_app = app_launcher.app

# ---------------------------------------------------------------------------
# 3. Now safe to import Isaac Lab / omni modules
# ---------------------------------------------------------------------------
import torch  # noqa: E402

from isaaclab.sim import SimulationCfg, SimulationContext  # noqa: E402
from manipulator_learning.envhub import make_env  # noqa: E402


def main() -> None:
    sim_cfg = SimulationCfg(dt=0.01)
    sim = SimulationContext(sim_cfg)

    # Point camera at the table (x=2m back, z=1.5m up, looking at origin)
    sim.set_camera_view(eye=[1.5, -1.5, 1.5], target=[0.0, 0.0, 0.5])

    print("[visualize_env] Creating ToySortingEnv …")
    envs_dict = make_env(n_envs=1)
    env = envs_dict["toy_sorting"][0]

    print("[visualize_env] Resetting …")
    sim.reset()

    # Debug: list top-level stage prims so we know what's loaded
    import omni.usd
    stage = omni.usd.get_context().get_stage()
    prims = [str(p.GetPath()) for p in stage.Traverse()]
    print(f"[visualize_env] Stage prims ({len(prims)}): {prims[:20]}")

    obs, _ = env.reset()
    print(f"[visualize_env] Observation keys: {list(obs.keys())}")

    print(f"[visualize_env] Running {args_cli.steps} random-action steps …")
    for step in range(args_cli.steps):
        action = torch.zeros(6).uniform_(-0.5, 0.5)
        obs, reward, terminated, truncated, info = env.step(action)

        if terminated.any() or truncated.any():
            print(f"[visualize_env] Episode ended at step {step}, resetting.")
            obs, _ = env.reset()

        if step % 100 == 0:
            print(f"[visualize_env] step {step}/{args_cli.steps}")

        sim.step()

    env.close()
    print("[visualize_env] Done.")


if __name__ == "__main__":
    main()
    simulation_app.close()
