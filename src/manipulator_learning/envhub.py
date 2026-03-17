"""EnvHub task factory for toy sorting.

This is the stable entrypoint used by env.py at the repo root.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Iterable

from manipulator_learning.tasks.toy_sorting import ToySortingTaskSpec

DEFAULT_BASE_TASK = "LightwheelAI/leisaac_env:envs/so101_clean_toytable.py"
DEFAULT_TASK_ID = "ToySorting-v0"


@dataclass(frozen=True)
class ToySortingOverlayConfig:
    base_task: str = DEFAULT_BASE_TASK
    apply_color_overlay: bool = True


def _iter_prims_with_names(stage, name_hints: Iterable[str]):
    name_hints = {name.lower() for name in name_hints}
    for prim in stage.Traverse():
        if not prim.IsValid():
            continue
        name = prim.GetName().lower()
        if any(hint in name for hint in name_hints):
            yield prim


def _apply_color(prim, color_rgb):
    from pxr import Gf, UsdGeom

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


class _ToySortingOverlayWrapper:
    """Applies scene color overlays once after reset."""

    def __init__(self, env, spec: ToySortingTaskSpec, config: ToySortingOverlayConfig):
        self.env = env
        self._spec = spec
        self._config = config
        self._overlay_applied = False

    def _maybe_apply_overlay(self) -> None:
        if self._overlay_applied or not self._config.apply_color_overlay:
            return
        try:
            import omni.usd

            stage = omni.usd.get_context().get_stage()
            _colorize_scene(stage, self._spec)
        except Exception as exc:
            print(f"[WARN] Failed to recolor toys/bins: {exc}")
        finally:
            self._overlay_applied = True

    def reset(self, **kwargs):
        obs, info = self.env.reset(**kwargs)
        self._maybe_apply_overlay()
        return obs, info

    def step(self, action):
        return self.env.step(action)

    def close(self):
        return self.env.close()

    def __getattr__(self, name):
        return getattr(self.env, name)


def _wrap_vector_env(sync_vector_env, spec: ToySortingTaskSpec, config: ToySortingOverlayConfig):
    try:
        envs = sync_vector_env.envs
    except Exception:
        return
    for idx, env in enumerate(envs):
        envs[idx] = _ToySortingOverlayWrapper(env, spec, config)


def make_env(
    task: str | None = None,
    n_envs: int = 1,
    seed: int | None = None,
    base_task: str = DEFAULT_BASE_TASK,
    apply_color_overlay: bool = True,
    **kwargs,
):
    """EnvHub entrypoint for toy sorting.

    Returns a dict mapping suite name to list of vector envs, matching LeRobot
    EnvHub conventions.
    """

    requested_task = task or DEFAULT_TASK_ID
    if requested_task not in {DEFAULT_TASK_ID, "toy_sorting", "toy-sorting"}:
        raise ValueError(
            f"Unsupported task '{requested_task}'. Expected '{DEFAULT_TASK_ID}'."
        )

    try:
        from lerobot.envs.factory import make_env as make_base_env
    except Exception as lerobot_exc:
        try:
            from leisaac.envs.factory import make_env as make_base_env
        except Exception as leisaac_exc:
            import sys
            import traceback

            print("[ERROR] Failed to import EnvHub factory.", file=sys.stderr)
            print("[ERROR] lerobot.envs.factory import error:", file=sys.stderr)
            traceback.print_exception(type(lerobot_exc), lerobot_exc, lerobot_exc.__traceback__)
            print("[ERROR] leisaac.envs.factory import error:", file=sys.stderr)
            traceback.print_exception(type(leisaac_exc), leisaac_exc, leisaac_exc.__traceback__)
            print("[ERROR] sys.path:", file=sys.stderr)
            for entry in sys.path:
                print(f"  - {entry}", file=sys.stderr)
            raise RuntimeError(
                "EnvHub factory not available. Install lerobot or a LeIsaac build with env factory."
            ) from leisaac_exc

    envs_dict = make_base_env(
        base_task,
        n_envs=n_envs,
        seed=seed,
        trust_remote_code=True,
        **kwargs,
    )

    suite_name = "toy_sorting"
    spec = ToySortingTaskSpec()
    config = ToySortingOverlayConfig(base_task=base_task, apply_color_overlay=apply_color_overlay)

    vector_envs = []
    for _suite, env_list in envs_dict.items():
        for sync_vector_env in env_list:
            _wrap_vector_env(sync_vector_env, spec, config)
            vector_envs.append(sync_vector_env)

    return {suite_name: vector_envs}
