from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence


@dataclass(slots=True)
class IsaacLabInvocation:
    command: list[str]
    cwd: Path


_ANNOTATE_SCRIPT = Path("scripts/imitation_learning/isaaclab_mimic/annotate_demos.py")
_GENERATE_SCRIPT = Path("scripts/imitation_learning/isaaclab_mimic/generate_dataset.py")


def _candidate_roots(explicit_root: str | os.PathLike[str] | None) -> list[Path]:
    roots: list[Path] = []

    if explicit_root is not None:
        roots.append(Path(explicit_root).expanduser().resolve())

    env_root = os.environ.get("ISAACLAB_ROOT")
    if env_root:
        roots.append(Path(env_root).expanduser().resolve())

    for entry in sys.path:
        candidate = Path(entry).expanduser()
        if candidate.exists():
            roots.append(candidate.resolve())

    try:
        import isaaclab  # type: ignore

        package_root = Path(isaaclab.__file__).resolve().parents[1]
        roots.append(package_root)
    except ImportError:
        pass

    unique_roots: list[Path] = []
    seen: set[Path] = set()
    for root in roots:
        if root not in seen:
            seen.add(root)
            unique_roots.append(root)
    return unique_roots


def _resolve_script_path(script_relative: Path, explicit_root: str | os.PathLike[str] | None) -> tuple[Path, Path]:
    for root in _candidate_roots(explicit_root):
        candidate = root / script_relative
        if candidate.exists():
            return root, candidate

    raise FileNotFoundError(
        f"Could not locate Isaac Lab script '{script_relative}'. "
        "Install Isaac Lab in the uv environment or pass --isaaclab-root to a source tree."
    )


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
    root, script = _resolve_script_path(_ANNOTATE_SCRIPT, isaaclab_root)
    command = [
        sys.executable,
        str(script),
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
    root, script = _resolve_script_path(_GENERATE_SCRIPT, isaaclab_root)
    command = [
        sys.executable,
        str(script),
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
    import subprocess

    print("Running:", " ".join(invocation.command))
    if dry_run:
        return
    subprocess.run(invocation.command, cwd=invocation.cwd, check=True)
