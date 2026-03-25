from __future__ import annotations

import argparse
from pathlib import Path

from .hdf5 import print_summary, summarize
from .isaaclab import build_annotate_command, build_generate_command, run_invocation


def _add_shared_isaaclab_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--isaaclab-root",
        type=str,
        default=None,
        help="Optional path to an Isaac Lab source tree or installed package root.",
    )
    parser.add_argument("--device", type=str, default="cpu", help="Isaac Lab device.")


def _ensure_parent(path: str | Path) -> Path:
    resolved = Path(path).expanduser().resolve()
    resolved.parent.mkdir(parents=True, exist_ok=True)
    return resolved


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="dataset-mimic")
    subparsers = parser.add_subparsers(dest="command", required=True)

    inspect_parser = subparsers.add_parser("inspect", help="Print a summary of an Isaac Lab HDF5 file.")
    inspect_parser.add_argument("input_file", type=str)

    annotate_parser = subparsers.add_parser("annotate", help="Run Isaac Lab Mimic annotation.")
    _add_shared_isaaclab_args(annotate_parser)
    annotate_parser.add_argument("--task", required=True, type=str)
    annotate_parser.add_argument("--input-file", required=True, type=str)
    annotate_parser.add_argument("--output-file", required=True, type=str)
    annotate_parser.add_argument("--enable-cameras", action=argparse.BooleanOptionalAction, default=True)
    annotate_parser.add_argument("--auto", action=argparse.BooleanOptionalAction, default=True)

    generate_parser = subparsers.add_parser("generate", help="Run Isaac Lab Mimic dataset generation.")
    _add_shared_isaaclab_args(generate_parser)
    generate_parser.add_argument("--task", required=True, type=str)
    generate_parser.add_argument("--input-file", required=True, type=str)
    generate_parser.add_argument("--output-file", required=True, type=str)
    generate_parser.add_argument("--enable-cameras", action=argparse.BooleanOptionalAction, default=True)
    generate_parser.add_argument("--headless", action=argparse.BooleanOptionalAction, default=True)
    generate_parser.add_argument("--num-envs", type=int, default=10)
    generate_parser.add_argument("--generation-num-trials", type=int, default=1000)
    generate_parser.add_argument("--rendering-mode", type=str, default="performance")
    generate_parser.add_argument("--extra-arg", action="append", default=[], help="Forward extra args to Isaac Lab.")

    mimic_parser = subparsers.add_parser(
        "mimic",
        help="Run annotation followed by Isaac Lab Mimic generation.",
    )
    _add_shared_isaaclab_args(mimic_parser)
    mimic_parser.add_argument("--task", required=True, type=str)
    mimic_parser.add_argument("--input-file", required=True, type=str)
    mimic_parser.add_argument("--annotated-file", required=True, type=str)
    mimic_parser.add_argument("--generated-file", required=True, type=str)
    mimic_parser.add_argument("--enable-cameras", action=argparse.BooleanOptionalAction, default=True)
    mimic_parser.add_argument("--auto", action=argparse.BooleanOptionalAction, default=True)
    mimic_parser.add_argument("--headless", action=argparse.BooleanOptionalAction, default=True)
    mimic_parser.add_argument("--num-envs", type=int, default=10)
    mimic_parser.add_argument("--generation-num-trials", type=int, default=1000)
    mimic_parser.add_argument("--rendering-mode", type=str, default="performance")
    mimic_parser.add_argument("--extra-arg", action="append", default=[], help="Forward extra args to Isaac Lab.")

    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "inspect":
        summary = summarize(args.input_file)
        print_summary(summary)
        return

    if args.command == "annotate":
        input_file = Path(args.input_file).expanduser().resolve()
        output_file = _ensure_parent(args.output_file)
        invocation = build_annotate_command(
            isaaclab_root=args.isaaclab_root,
            input_file=input_file,
            output_file=output_file,
            task=args.task,
            device=args.device,
            enable_cameras=args.enable_cameras,
            auto=args.auto,
        )
        run_invocation(invocation)
        return

    if args.command == "generate":
        input_file = Path(args.input_file).expanduser().resolve()
        output_file = _ensure_parent(args.output_file)
        invocation = build_generate_command(
            isaaclab_root=args.isaaclab_root,
            input_file=input_file,
            output_file=output_file,
            task=args.task,
            device=args.device,
            enable_cameras=args.enable_cameras,
            headless=args.headless,
            num_envs=args.num_envs,
            generation_num_trials=args.generation_num_trials,
            rendering_mode=args.rendering_mode,
            extra_args=args.extra_arg,
        )
        run_invocation(invocation)
        return

    if args.command == "mimic":
        input_file = Path(args.input_file).expanduser().resolve()
        annotated_file = _ensure_parent(args.annotated_file)
        generated_file = _ensure_parent(args.generated_file)
        annotate_invocation = build_annotate_command(
            isaaclab_root=args.isaaclab_root,
            input_file=input_file,
            output_file=annotated_file,
            task=args.task,
            device=args.device,
            enable_cameras=args.enable_cameras,
            auto=args.auto,
        )
        run_invocation(annotate_invocation)

        generate_invocation = build_generate_command(
            isaaclab_root=args.isaaclab_root,
            input_file=annotated_file,
            output_file=generated_file,
            task=args.task,
            device=args.device,
            enable_cameras=args.enable_cameras,
            headless=args.headless,
            num_envs=args.num_envs,
            generation_num_trials=args.generation_num_trials,
            rendering_mode=args.rendering_mode,
            extra_args=args.extra_arg,
        )
        run_invocation(generate_invocation)
        return

    raise AssertionError(f"Unhandled command: {args.command}")


if __name__ == "__main__":
    main()
