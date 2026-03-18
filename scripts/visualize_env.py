"""Run the toy-sorting environment for 600 steps with random joint actions.

Isaac Sim's SimulationApp MUST be created before any omni.* / isaaclab imports.
This script follows the standard Isaac Sim application pattern.

Usage:
    uv run python scripts/visualize_env.py             # with GUI
    uv run python scripts/visualize_env.py --headless  # headless
    uv run python scripts/visualize_env.py --headless --steps 100
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Ensure the repo src/ is importable when running directly (no install).
_REPO_ROOT = Path(__file__).resolve().parents[1]
_SRC = _REPO_ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Visualise the toy-sorting scene.")
    parser.add_argument("--headless", action="store_true", help="Run without GUI.")
    parser.add_argument("--steps", type=int, default=600, help="Number of steps.")
    return parser.parse_args()


def main() -> None:
    args = _parse_args()

    # ------------------------------------------------------------------ #
    # 1. Start Isaac Sim — must happen before ANY omni.* / isaaclab import #
    # ------------------------------------------------------------------ #
    from isaacsim import SimulationApp
    simulation_app = SimulationApp({"headless": args.headless})

    # ------------------------------------------------------------------ #
    # 2. Now safe to import Isaac Lab / omni modules                       #
    # ------------------------------------------------------------------ #
    import torch
    from manipulator_learning.envhub import make_env

    print("[visualize_env] Creating ToySortingEnv …")
    envs_dict = make_env(n_envs=1)
    env = envs_dict["toy_sorting"][0]

    print("[visualize_env] Resetting …")
    obs, _ = env.reset()
    print(f"[visualize_env] Observation keys: {list(obs.keys())}")

    print(f"[visualize_env] Running {args.steps} random-action steps …")
    for step in range(args.steps):
        action = torch.zeros(6).uniform_(-0.5, 0.5)
        obs, reward, terminated, truncated, info = env.step(action)

        if terminated.any() or truncated.any():
            print(f"[visualize_env] Episode ended at step {step}, resetting.")
            obs, _ = env.reset()

        if step % 100 == 0:
            print(f"[visualize_env] step {step}/{args.steps}")

        simulation_app.update()  # pump the render loop

    env.close()
    simulation_app.close()
    print("[visualize_env] Done.")


if __name__ == "__main__":
    main()
