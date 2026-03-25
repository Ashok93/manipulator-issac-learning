from __future__ import annotations

import os
from pathlib import Path


def resolve_repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def resolve_isaaclab_root(explicit: str | os.PathLike[str] | None = None) -> Path:
    if explicit is not None:
        root = Path(explicit).expanduser().resolve()
    else:
        env_root = os.environ.get("ISAACLAB_ROOT")
        root = Path(env_root).expanduser().resolve() if env_root else (Path.home() / "IsaacLab").resolve()

    if not root.exists():
        raise FileNotFoundError(
            f"Isaac Lab root not found: {root}. Set ISAACLAB_ROOT or pass --isaaclab-root."
        )
    return root


def resolve_dataset_path(value: str | os.PathLike[str]) -> Path:
    path = Path(value).expanduser().resolve()
    if not path.parent.exists():
        raise FileNotFoundError(f"Parent directory does not exist: {path.parent}")
    return path

