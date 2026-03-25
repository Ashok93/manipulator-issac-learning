from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from .paths import resolve_isaaclab_root


@dataclass(slots=True)
class IsaacLabInvocation:
    command: list[str]
    cwd: Path


def build_annotate_command(
    *,
    isaaclab_root: str | Path | None,
    input_file: str | Path,
    output_file: str | Path,
    task: str,
    device: str = "cpu",
    enable_cameras: bool = False,
    auto: bool = True,
) -> IsaacLabInvocation:
    root = resolve_isaaclab_root(isaaclab_root)
    command = [
        str(root / "isaaclab.sh"),
        "-p",
        "scripts/imitation_learning/isaaclab_mimic/annotate_demos.py",
        "--device",
        device,
        "--task",
        task,
        "--input_file",
        str(Path(input_file)),
        "--output_file",
        str(Path(output_file)),
    ]
    if enable_cameras:
        command.append("--enable_cameras")
    if auto:
        command.append("--auto")
    return IsaacLabInvocation(command=command, cwd=root)


def build_generate_command(
    *,
    isaaclab_root: str | Path | None,
    input_file: str | Path,
    output_file: str | Path,
    task: str,
    device: str = "cpu",
    enable_cameras: bool = False,
    headless: bool = True,
    num_envs: int = 10,
    generation_num_trials: int = 1000,
    rendering_mode: str | None = "performance",
    extra_args: Sequence[str] = (),
) -> IsaacLabInvocation:
    root = resolve_isaaclab_root(isaaclab_root)
    command = [
        str(root / "isaaclab.sh"),
        "-p",
        "scripts/imitation_learning/isaaclab_mimic/generate_dataset.py",
        "--device",
        device,
        "--num_envs",
        str(num_envs),
        "--generation_num_trials",
        str(generation_num_trials),
        "--input_file",
        str(Path(input_file)),
        "--output_file",
        str(Path(output_file)),
        "--task",
        task,
    ]
    if headless:
        command.append("--headless")
    if enable_cameras:
        command.append("--enable_cameras")
    if rendering_mode:
        command.extend(["--rendering_mode", rendering_mode])
    command.extend(str(arg) for arg in extra_args)
    return IsaacLabInvocation(command=command, cwd=root)


def run_invocation(invocation: IsaacLabInvocation, *, dry_run: bool = False) -> None:
    print("Running:", " ".join(invocation.command))
    if dry_run:
        return
    subprocess.run(invocation.command, cwd=invocation.cwd, check=True)

