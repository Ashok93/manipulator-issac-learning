from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import h5py


@dataclass(slots=True)
class DemoSummary:
    path: Path
    demo_names: list[str]
    total_steps: int
    env_args: dict[str, Any] | None
    has_images: bool
    state_keys: list[str] = field(default_factory=list)
    action_keys: list[str] = field(default_factory=list)
    image_keys: list[str] = field(default_factory=list)


def _decode_env_args(raw: Any) -> dict[str, Any] | None:
    if raw is None:
        return None
    if isinstance(raw, (bytes, bytearray)):
        raw = raw.decode("utf-8")
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            return {"raw": raw}
        return parsed if isinstance(parsed, dict) else {"raw": parsed}
    return None


def _is_image_dataset(dataset: h5py.Dataset) -> bool:
    return dataset.ndim == 4 and dataset.shape[-1] in (3, 4) and dataset.dtype.kind in {"u", "f"}


def _is_state_like(dataset: h5py.Dataset) -> bool:
    return dataset.ndim >= 2 and dataset.shape[0] > 0 and dataset.dtype.kind in {"u", "i", "f"}


def summarize(path: str | Path) -> DemoSummary:
    file_path = Path(path)
    with h5py.File(file_path, "r") as handle:
        if "data" not in handle:
            raise KeyError(f"Expected top-level group 'data' in {file_path}")

        data_group = handle["data"]
        demo_names = [name for name in data_group.keys() if isinstance(data_group[name], h5py.Group)]
        total_steps = 0
        state_keys: set[str] = set()
        action_keys: set[str] = set()
        image_keys: set[str] = set()

        env_args = _decode_env_args(data_group.attrs.get("env_args"))

        for demo_name in demo_names:
            demo = data_group[demo_name]
            if "actions" in demo and isinstance(demo["actions"], h5py.Dataset):
                total_steps += int(demo["actions"].shape[0])

            obs = demo.get("obs")
            if isinstance(obs, h5py.Group):
                for key, item in obs.items():
                    if not isinstance(item, h5py.Dataset):
                        continue
                    if _is_image_dataset(item):
                        image_keys.add(key)
                    elif _is_state_like(item):
                        state_keys.add(key)

            for candidate in ("actions", "processed_actions"):
                if candidate in demo and isinstance(demo[candidate], h5py.Dataset):
                    action_keys.add(candidate)

        return DemoSummary(
            path=file_path,
            demo_names=demo_names,
            total_steps=total_steps,
            env_args=env_args,
            has_images=bool(image_keys),
            state_keys=sorted(state_keys),
            action_keys=sorted(action_keys),
            image_keys=sorted(image_keys),
        )


def print_summary(summary: DemoSummary) -> None:
    print(f"file: {summary.path}")
    print(f"demos: {len(summary.demo_names)} -> {', '.join(summary.demo_names)}")
    print(f"total steps: {summary.total_steps}")
    print(f"has images: {summary.has_images}")
    if summary.env_args:
        print(f"env args: {summary.env_args}")
    if summary.state_keys:
        print(f"state keys: {summary.state_keys}")
    if summary.action_keys:
        print(f"action keys: {summary.action_keys}")
    if summary.image_keys:
        print(f"image keys: {summary.image_keys}")
