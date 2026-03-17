"""Launch LeIsaac teleop recorder for toy sorting demos."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Collect LeRobot demos via LeIsaac teleop.")
    parser.add_argument(
        "--task",
        default="LeIsaac-SO101-CleanToyTable-v0",
        help="EnvHub task id to launch.",
    )
    parser.add_argument(
        "--lerobot_dataset_repo_id",
        default="manipulator/toy-sorting-sim",
        help="LeRobot dataset repo_id (org/name).",
    )
    parser.add_argument("--lerobot_dataset_fps", type=float, default=30.0, help="Dataset FPS.")
    parser.add_argument("--headless", action="store_true", help="Run headless.")
    parser.add_argument("--device", default="keyboard", help="Teleop device.")
    return parser.parse_args()


def _find_leisaac_teleop_script() -> Path:
    import leisaac

    root = Path(leisaac.__file__).resolve().parent
    candidates = list(root.rglob("teleop_se3_agent.py"))
    if not candidates:
        raise FileNotFoundError(
            "teleop_se3_agent.py not found in leisaac package. "
            "Ensure leisaac is installed from source with scripts included."
        )
    return candidates[0]


def main() -> None:
    args = _parse_args()
    script_path = _find_leisaac_teleop_script()

    cmd = [
        sys.executable,
        str(script_path),
        "--task",
        args.task,
        "--teleop_device",
        args.device,
        "--enable_cameras",
        "--record",
        "--use_lerobot_recorder",
        "--lerobot_dataset_repo_id",
        args.lerobot_dataset_repo_id,
        "--lerobot_dataset_fps",
        str(args.lerobot_dataset_fps),
    ]
    if args.headless:
        cmd.append("--headless")

    subprocess.run(cmd, check=True)


if __name__ == "__main__":
    main()
