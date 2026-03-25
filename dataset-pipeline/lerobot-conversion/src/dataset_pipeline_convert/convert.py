from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import h5py
import numpy as np


@dataclass(slots=True)
class ImageStream:
    source_key: str
    feature_key: str
    shape: tuple[int, int, int]


@dataclass(slots=True)
class ConversionLayout:
    state_key: str
    action_key: str
    image_streams: list[ImageStream] = field(default_factory=list)
    task_name: str = "unknown-task"


def _is_image_dataset(dataset: h5py.Dataset) -> bool:
    return dataset.ndim == 4 and dataset.shape[-1] in (3, 4) and dataset.dtype.kind in {"u", "f"}


def _is_state_like(dataset: h5py.Dataset) -> bool:
    return dataset.ndim >= 2 and dataset.shape[0] > 0 and dataset.dtype.kind in {"u", "i", "f"}


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


def _pick_first_dataset(group: h5py.Group, predicate) -> str | None:
    for key, item in group.items():
        if isinstance(item, h5py.Dataset) and predicate(item):
            return key
    return None


def _discover_layout(
    handle: h5py.File,
    *,
    state_key: str | None,
    action_key: str | None,
    image_keys: list[str] | None,
) -> ConversionLayout:
    data_group = handle["data"]
    demo_name = next(name for name in sorted(data_group.keys()) if isinstance(data_group[name], h5py.Group))
    demo_group = data_group[demo_name]
    obs_group = demo_group["obs"]
    if not isinstance(obs_group, h5py.Group):
        raise KeyError("Expected 'obs' group under the first demo")

    selected_state_key = state_key or "joint_pos"
    if selected_state_key not in obs_group or not isinstance(obs_group[selected_state_key], h5py.Dataset):
        picked = _pick_first_dataset(obs_group, _is_state_like)
        if picked is None:
            raise KeyError("Could not auto-detect a state dataset in the HDF5 file")
        selected_state_key = picked

    selected_action_key = action_key or "actions"
    if selected_action_key not in demo_group or not isinstance(demo_group[selected_action_key], h5py.Dataset):
        for candidate in ("actions", "processed_actions"):
            if candidate in demo_group and isinstance(demo_group[candidate], h5py.Dataset):
                selected_action_key = candidate
                break
        else:
            raise KeyError("Could not auto-detect an action dataset in the HDF5 file")

    if image_keys:
        discovered = [key for key in image_keys if key in obs_group and isinstance(obs_group[key], h5py.Dataset)]
    else:
        discovered = [key for key, item in obs_group.items() if isinstance(item, h5py.Dataset) and _is_image_dataset(item)]

    streams: list[ImageStream] = []
    for key in discovered:
        dataset = obs_group[key]
        shape = tuple(int(dim) for dim in dataset.shape[1:4])
        streams.append(
            ImageStream(
                source_key=key,
                feature_key=f"observation.images.{key.replace('/', '_')}",
                shape=shape[:3],
            )
        )

    env_args = _decode_env_args(data_group.attrs.get("env_args"))
    task_name = str(env_args.get("env_name")) if env_args and env_args.get("env_name") else demo_name
    return ConversionLayout(
        state_key=selected_state_key,
        action_key=selected_action_key,
        image_streams=streams,
        task_name=task_name,
    )


def _build_features(layout: ConversionLayout, state_shape: tuple[int, ...], action_shape: tuple[int, ...]) -> dict[str, dict[str, Any]]:
    features: dict[str, dict[str, Any]] = {
        "observation.state": {
            "dtype": "float32",
            "shape": tuple(int(dim) for dim in state_shape),
            "names": [f"state_{i}" for i in range(state_shape[0])],
        },
        "action": {
            "dtype": "float32",
            "shape": tuple(int(dim) for dim in action_shape),
            "names": [f"action_{i}" for i in range(action_shape[0])],
        },
    }
    for stream in layout.image_streams:
        features[stream.feature_key] = {
            "dtype": "video",
            "shape": stream.shape,
            "names": ["height", "width", "channel"],
        }
    return features


def _normalize_image(frame: np.ndarray) -> np.ndarray:
    if frame.dtype == np.uint8:
        return frame
    if np.issubdtype(frame.dtype, np.floating):
        if frame.max(initial=0.0) <= 1.0:
            frame = frame * 255.0
        return np.clip(frame, 0, 255).astype(np.uint8)
    return np.clip(frame, 0, 255).astype(np.uint8)


def _default_output_root(input_file: Path, repo_id: str) -> Path:
    safe_repo_id = repo_id.replace("/", "__")
    base_dir = input_file.parent.parent if input_file.parent.name == "mimic" else input_file.parent
    if base_dir.name == "outputs":
        return base_dir / "lerobot" / safe_repo_id
    return base_dir / "outputs" / "lerobot" / safe_repo_id


def convert_hdf5_to_lerobot(
    *,
    input_file: str | Path,
    repo_id: str,
    output_root: str | Path | None = None,
    fps: int,
    robot_type: str,
    state_key: str | None = None,
    action_key: str | None = None,
    image_keys: list[str] | None = None,
    push_to_hub: bool = False,
) -> None:
    try:
        from lerobot.datasets.lerobot_dataset import LeRobotDataset
    except ImportError as exc:  # pragma: no cover - dependency controlled by extra
        raise RuntimeError(
            "LeRobot is not installed. Re-run uv sync with the 'convert' extra."
        ) from exc

    input_path = Path(input_file)
    root = Path(output_root).expanduser().resolve() if output_root is not None else _default_output_root(input_path, repo_id).resolve()
    root.mkdir(parents=True, exist_ok=True)
    with h5py.File(input_path, "r") as handle:
        layout = _discover_layout(handle, state_key=state_key, action_key=action_key, image_keys=image_keys)
        first_demo = handle["data"][sorted(handle["data"].keys())[0]]
        state_shape = tuple(int(dim) for dim in first_demo["obs"][layout.state_key].shape[1:])
        action_shape = tuple(int(dim) for dim in first_demo[layout.action_key].shape[1:])
        features = _build_features(layout, state_shape, action_shape)

        dataset = LeRobotDataset.create(
            repo_id=repo_id,
            root=root,
            fps=fps,
            robot_type=robot_type,
            features=features,
            use_videos=bool(layout.image_streams),
        )

        for demo_name in sorted(handle["data"].keys()):
            demo = handle["data"][demo_name]
            if not isinstance(demo, h5py.Group):
                continue
            obs = demo["obs"]
            if not isinstance(obs, h5py.Group):
                continue

            state_ds = obs[layout.state_key]
            action_ds = demo[layout.action_key]
            length = int(action_ds.shape[0])
            for index in range(length):
                frame: dict[str, Any] = {
                    "observation.state": np.asarray(state_ds[index], dtype=np.float32),
                    "action": np.asarray(action_ds[index], dtype=np.float32),
                    "task": layout.task_name,
                }
                for stream in layout.image_streams:
                    frame[stream.feature_key] = _normalize_image(np.asarray(obs[stream.source_key][index]))
                dataset.add_frame(frame)
            dataset.save_episode()

        if push_to_hub:
            dataset.push_to_hub()

    print(f"LeRobot dataset written to: {root}")
