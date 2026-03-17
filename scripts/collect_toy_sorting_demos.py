"""Launch LeIsaac teleop recorder for toy sorting demos."""

from __future__ import annotations

import argparse
from manipulator_learning.leisaac_tools import run_teleop_se3_agent


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


def main() -> None:
    args = _parse_args()

    cmd = [
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

    run_teleop_se3_agent(cmd)


if __name__ == "__main__":
    main()
