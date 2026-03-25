from __future__ import annotations

from pathlib import Path


def resolve_repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def resolve_dataset_path(value: str | os.PathLike[str]) -> Path:
    path = Path(value).expanduser().resolve()
    if not path.parent.exists():
        raise FileNotFoundError(f"Parent directory does not exist: {path.parent}")
    return path
