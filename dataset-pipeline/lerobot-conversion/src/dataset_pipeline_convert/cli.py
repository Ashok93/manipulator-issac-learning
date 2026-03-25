from __future__ import annotations

import argparse
from pathlib import Path

from .convert import convert_hdf5_to_lerobot


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="dataset-convert")
    parser.add_argument("--input-file", required=True, type=str)
    parser.add_argument("--repo-id", required=True, type=str)
    parser.add_argument(
        "--output-root",
        type=str,
        default=None,
        help="Local directory where the LeRobot dataset should be written.",
    )
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--robot-type", required=True, type=str)
    parser.add_argument("--state-key", type=str, default=None)
    parser.add_argument("--action-key", type=str, default=None)
    parser.add_argument("--image-key", action="append", default=[])
    parser.add_argument("--push-to-hub", action=argparse.BooleanOptionalAction, default=False)
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    convert_hdf5_to_lerobot(
        input_file=Path(args.input_file),
        repo_id=args.repo_id,
        output_root=args.output_root,
        fps=args.fps,
        robot_type=args.robot_type,
        state_key=args.state_key,
        action_key=args.action_key,
        image_keys=args.image_key or None,
        push_to_hub=args.push_to_hub,
    )


if __name__ == "__main__":
    main()
