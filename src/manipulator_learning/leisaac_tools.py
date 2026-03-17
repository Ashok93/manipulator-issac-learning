"""Helpers for invoking LeIsaac tooling without subprocess calls."""

from __future__ import annotations

import runpy
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Iterable


def _find_leisaac_script(filename: str) -> Path:
    import leisaac

    root = Path(leisaac.__file__).resolve().parent
    candidates = list(root.rglob(filename))
    if not candidates:
        raise FileNotFoundError(
            f"{filename} not found in leisaac package. "
            "Ensure leisaac is installed from source with scripts included."
        )
    return candidates[0]


@contextmanager
def _argv(args: Iterable[str]):
    original = sys.argv
    sys.argv = list(args)
    try:
        yield
    finally:
        sys.argv = original


def _run_script(path: Path, args: Iterable[str]) -> None:
    with _argv([str(path), *args]):
        runpy.run_path(str(path), run_name="__main__")


def run_list_envs() -> None:
    script_path = _find_leisaac_script("list_envs.py")
    _run_script(script_path, [])


def run_teleop_se3_agent(args: Iterable[str]) -> None:
    script_path = _find_leisaac_script("teleop_se3_agent.py")
    _run_script(script_path, list(args))
