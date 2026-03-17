"""Launch LeIsaac EnvHub task and apply toy/bin color sorting overlays."""

from __future__ import annotations

import argparse
import random
import time
from typing import Iterable

from manipulator_learning.tasks.toy_sorting import ToySortingTaskSpec


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run toy sorting task in LeIsaac EnvHub.")
    parser.add_argument(
        "--task",
        default="LightwheelAI/leisaac_env:envs/so101_clean_toytable.py",
        help="EnvHub task path to launch.",
    )
    parser.add_argument("--headless", action="store_true", help="Run headless.")
    parser.add_argument("--steps", type=int, default=600, help="Steps to run.")
    return parser.parse_args()


def _iter_prims_with_names(stage, name_hints: Iterable[str]):
    name_hints = {name.lower() for name in name_hints}
    for prim in stage.Traverse():
        if not prim.IsValid():
            continue
        name = prim.GetName().lower()
        if any(hint in name for hint in name_hints):
            yield prim


def _apply_color(prim, color_rgb):
    from pxr import UsdGeom, Gf

    gprim = UsdGeom.Gprim(prim)
    if not gprim:
        return
    color_attr = gprim.GetDisplayColorAttr()
    color_attr.Set([Gf.Vec3f(*color_rgb)])


def _colorize_scene(stage, spec: ToySortingTaskSpec) -> None:
    toy_prims = list(_iter_prims_with_names(stage, ["toy", "block", "cube", "duck"]))
    bin_prims = list(_iter_prims_with_names(stage, ["bin", "box", "tray", "basket"]))
    if not toy_prims or not bin_prims:
        print("[WARN] Could not find toy/bin prims by name. Update name hints if needed.")
        return

    color_map = {
        "red": (0.85, 0.15, 0.15),
        "green": (0.15, 0.8, 0.2),
        "blue": (0.2, 0.35, 0.9),
    }
    colors = list(spec.colors)
    random.shuffle(colors)

    for idx, prim in enumerate(toy_prims):
        color = colors[idx % len(colors)]
        _apply_color(prim, color_map[color])

    for idx, prim in enumerate(bin_prims):
        color = colors[idx % len(colors)]
        _apply_color(prim, color_map[color])


def main() -> None:
    args = _parse_args()
    spec = ToySortingTaskSpec()

    try:
        from lerobot.envs.factory import make_env
    except Exception as exc:
        raise RuntimeError("LeRobot is required. Install dependencies first.") from exc

    import torch

    envs_dict = make_env(args.task, n_envs=1, trust_remote_code=True)
    suite_name = next(iter(envs_dict))
    sync_vector_env = envs_dict[suite_name][0]
    env = sync_vector_env.envs[0].unwrapped
    _obs, _info = env.reset()

    if not args.headless:
        try:
            import omni.usd

            stage = omni.usd.get_context().get_stage()
            _colorize_scene(stage, spec)
        except Exception as exc:
            print(f"[WARN] Failed to recolor toys/bins: {exc}")

    for _ in range(args.steps):
        action = torch.tensor(env.action_space.sample())
        _obs, _reward, terminated, truncated, _info = env.step(action)
        if terminated or truncated:
            _obs, _info = env.reset()
        time.sleep(0.0)

    env.close()


if __name__ == "__main__":
    main()
