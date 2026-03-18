"""Run the toy-sorting environment for N steps with random joint actions.

Follows the same pattern as the SO-ARM teleop script:
  1. AppLauncher → SimulationContext → InteractiveScene
  2. sim.reset() → scene.reset() → run loop

Usage:
    uv run python scripts/visualize_env.py
    uv run python scripts/visualize_env.py --headless
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
# 1. AppLauncher — before any isaaclab.* import
# ---------------------------------------------------------------------------
parser = argparse.ArgumentParser(description="Visualise the toy-sorting scene.")
parser.add_argument("--steps", type=int, default=600)
parser.add_argument("--headless", action="store_true")
args_cli = parser.parse_args()

from isaaclab.app import AppLauncher  # noqa: E402
app_launcher = AppLauncher(headless=args_cli.headless)
simulation_app = app_launcher.app

# ---------------------------------------------------------------------------
# 2. Isaac Lab imports (safe after AppLauncher)
# ---------------------------------------------------------------------------
import torch  # noqa: E402
import isaaclab.sim as sim_utils  # noqa: E402
from isaaclab.sim import SimulationContext  # noqa: E402
from manipulator_learning.envhub import make_env  # noqa: E402


def main() -> None:
    sim_cfg = sim_utils.SimulationCfg(dt=1.0 / 60.0)
    sim = SimulationContext(sim_cfg)
    sim.set_camera_view(eye=[1.5, -1.5, 1.5], target=[0.0, 0.0, 0.5])

    print("[visualize_env] Building scene …")
    envs_dict = make_env(n_envs=1)
    env = envs_dict["toy_sorting"][0]

    # Reset sim first, then scene (same order as teleop script)
    print("[visualize_env] Resetting …")
    sim.reset()
    obs, _ = env.reset()
    print(f"[visualize_env] Observation keys: {list(obs.keys())}")

    print(f"[visualize_env] Running {args_cli.steps} steps …")
    for step in range(args_cli.steps):
        action = torch.zeros(6).uniform_(-0.3, 0.3)
        obs, reward, terminated, truncated, info = env.step(action)

        if terminated.any() or truncated.any():
            obs, _ = env.reset()

        sim.step()

        if step % 100 == 0:
            print(f"[visualize_env] step {step}/{args_cli.steps}")

    env.close()
    print("[visualize_env] Done.")


if __name__ == "__main__":
    main()
    simulation_app.close()
