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

# ---------------------------------------------------------------------------
# 1. AppLauncher — before any isaaclab.* import
# ---------------------------------------------------------------------------
parser = argparse.ArgumentParser(description="Visualise the toy-sorting scene.")
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
    sim.set_camera_view(eye=[0.8, -0.8, 1.2], target=[0.0, 0.0, 0.2])

    print("[visualize_env] Building scene …")
    envs_dict = make_env(n_envs=1)
    env = envs_dict["toy_sorting"][0]

    print("[visualize_env] Resetting …")
    sim.reset()
    obs, _ = env.reset()
    print(f"[visualize_env] Observation keys: {list(obs.keys())}")

    print("[visualize_env] Running … (Ctrl+C or close window to stop)")
    while simulation_app.is_running():
        action = torch.zeros(6)
        obs, reward, terminated, truncated, info = env.step(action)

        if terminated.any() or truncated.any():
            obs, _ = env.reset()

        sim.step()

    env.close()
    print("[visualize_env] Done.")


if __name__ == "__main__":
    main()
    simulation_app.close()
