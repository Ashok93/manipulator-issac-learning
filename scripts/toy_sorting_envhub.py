"""Run the toy-sorting EnvHub task with random actions.

Thin wrapper around visualize_env.py kept for backwards compatibility.
Prefer using visualize_env.py directly for new work.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

# Ensure repo src/ is importable.
_HERE = Path(__file__).resolve()
_REPO_ROOT = _HERE.parents[1]
_SRC = _REPO_ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from manipulator_learning.envhub import make_env


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run toy sorting task via EnvHub.")
    parser.add_argument("--headless", action="store_true", help="Run headless.")
    parser.add_argument("--steps", type=int, default=600, help="Steps to run.")
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    import torch

    envs_dict = make_env(n_envs=1)
    env = envs_dict["toy_sorting"][0]
    obs, _ = env.reset()

    for step in range(args.steps):
        action = torch.zeros(6).uniform_(-0.5, 0.5)
        obs, reward, terminated, truncated, info = env.step(action)
        if terminated.any() or truncated.any():
            obs, _ = env.reset()

    env.close()


if __name__ == "__main__":
    main()
