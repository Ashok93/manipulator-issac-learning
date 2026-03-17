"""Launch LeIsaac EnvHub task and apply toy/bin color sorting overlays."""

from __future__ import annotations

import argparse
import time
from pathlib import Path

# Ensure local LeIsaac/IsaacLab and this repo are importable when running via Isaac Sim.
_HERE = Path(__file__).resolve()
_REPO_ROOT = _HERE.parents[1]
_SRC = _REPO_ROOT / "src"
_LEISAAC_SRC = Path.home() / "leisaac" / "source"
_ISAACLAB_SRC = Path.home() / "leisaac" / "dependencies" / "IsaacLab" / "source"
for _path in (_SRC, _LEISAAC_SRC, _ISAACLAB_SRC):
    _path_str = str(_path)
    if _path_str not in sys.path:
        sys.path.insert(0, _path_str)

from manipulator_learning.envhub import make_env


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run toy sorting task via EnvHub.")
    parser.add_argument(
        "--base-task",
        default="LightwheelAI/leisaac_env:envs/so101_clean_toytable.py",
        help="Base EnvHub task to wrap.",
    )
    parser.add_argument("--headless", action="store_true", help="Run headless.")
    parser.add_argument("--steps", type=int, default=600, help="Steps to run.")
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    import torch

    envs_dict = make_env(
        n_envs=1,
        base_task=args.base_task,
        apply_color_overlay=not args.headless,
    )
    suite_name = next(iter(envs_dict))
    sync_vector_env = envs_dict[suite_name][0]
    env = sync_vector_env.envs[0].unwrapped
    _obs, _info = env.reset()

    for _ in range(args.steps):
        action = torch.tensor(env.action_space.sample())
        _obs, _reward, terminated, truncated, _info = env.step(action)
        if terminated or truncated:
            _obs, _info = env.reset()
        time.sleep(0.0)

    env.close()


if __name__ == "__main__":
    main()
