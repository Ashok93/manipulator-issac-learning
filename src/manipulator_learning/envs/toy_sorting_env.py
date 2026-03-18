"""Isaac Lab toy-sorting environment using InteractiveScene.

Scene layout
------------
- Wooden table (Table049 USD) at world origin.
- SO-ARM 101 mounted at the table edge.
- 3 × SM_P_Tray_01: red (left), green (center), blue (right).
- 9 toy objects (mix of Kitchen_Box / Kitchen_Disk), colored red/green/blue.

Must be used after AppLauncher has started (isaaclab.* unavailable before that).
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Sequence

import torch


@dataclass
class ToySortingEnvCfg:
    num_envs: int = 1
    env_spacing: float = 2.0
    episode_length_s: float = 60.0
    colors: tuple = (
        (0.85, 0.15, 0.15),  # red
        (0.15, 0.80, 0.20),  # green
        (0.20, 0.35, 0.90),  # blue
    )
    num_toys: int = 9


class ToySortingEnv:
    """Toy-sorting environment backed by Isaac Lab InteractiveScene."""

    # tray prim names match ToySortingSceneCfg fields
    TRAY_NAMES = ["tray_red", "tray_green", "tray_blue"]
    TOY_NAMES = [f"toy_{i}" for i in range(9)]

    def __init__(self, cfg: ToySortingEnvCfg | None = None):
        self.cfg = cfg or ToySortingEnvCfg()
        self._toy_color_assignments: list[int] = []
        self._setup_scene()

    # ------------------------------------------------------------------
    # Scene setup — uses InteractiveScene, same pattern as teleop script
    # ------------------------------------------------------------------

    def _setup_scene(self) -> None:
        from isaaclab.scene import InteractiveScene
        from manipulator_learning.envs.toy_sorting_scene_cfg import ToySortingSceneCfg

        scene_cfg = ToySortingSceneCfg(
            num_envs=self.cfg.num_envs,
            env_spacing=self.cfg.env_spacing,
        )
        self._scene = InteractiveScene(scene_cfg)

    # ------------------------------------------------------------------
    # Color helpers
    # ------------------------------------------------------------------

    def _assign_colors(self) -> None:
        n = len(self.cfg.colors)
        per_color = self.cfg.num_toys // n
        assignments = [c for c in range(n) for _ in range(per_color)]
        while len(assignments) < self.cfg.num_toys:
            assignments.append(0)
        random.shuffle(assignments)
        self._toy_color_assignments = assignments

    def _apply_color(self, prim_path: str, color_rgb: tuple) -> None:
        try:
            import omni.usd
            from pxr import Gf, Usd, UsdGeom
            stage = omni.usd.get_context().get_stage()
            prim = stage.GetPrimAtPath(prim_path)
            if not prim.IsValid():
                return
            for desc_prim in Usd.PrimRange(prim):
                gprim = UsdGeom.Gprim(desc_prim)
                if not gprim:
                    continue
                color_attr = gprim.GetDisplayColorAttr()
                color_attr.Set([Gf.Vec3f(*color_rgb)])
                interp_attr = desc_prim.GetAttribute("primvars:displayColor:interpolation")
                if interp_attr:
                    interp_attr.Set(UsdGeom.Tokens.constant)
                else:
                    pv = UsdGeom.PrimvarsAPI(desc_prim).CreatePrimvar(
                        "displayColor",
                        Gf.Vec3f,
                        UsdGeom.Tokens.constant,
                    )
                    pv.Set([Gf.Vec3f(*color_rgb)])
        except Exception as exc:
            print(f"[WARN] _apply_color({prim_path}): {exc}")

    def _apply_colors(self) -> None:
        # Prim paths follow Isaac Lab naming: /World/envs/env_0/<PrimName>
        env_prefix = "/World/envs/env_0"
        tray_colors = [(0.85, 0.15, 0.15), (0.15, 0.80, 0.20), (0.20, 0.35, 0.90)]
        for i in range(len(tray_colors)):
            self._apply_color(f"{env_prefix}/Tray_{i}", tray_colors[i])
        for i in range(self.cfg.num_toys):
            color_idx = self._toy_color_assignments[i]
            self._apply_color(f"{env_prefix}/Toy_{i}", self.cfg.colors[color_idx])

    # ------------------------------------------------------------------
    # DirectRLEnv-style interface
    # ------------------------------------------------------------------

    def reset(self, env_ids: Sequence[int] | None = None):
        self._scene.reset()
        self._assign_colors()
        self._apply_colors()
        obs = self._get_observations()
        return obs, {}

    def step(self, actions: torch.Tensor):
        robot = self._scene["robot"]
        robot.set_joint_position_target(actions.unsqueeze(0))
        robot.write_data_to_sim()
        self._scene.update(self._scene.cfg.sim.dt if hasattr(self._scene.cfg, "sim") else 0.01)
        obs = self._get_observations()
        rewards = torch.zeros(self.cfg.num_envs)
        terminated = torch.zeros(self.cfg.num_envs, dtype=torch.bool)
        truncated = torch.zeros(self.cfg.num_envs, dtype=torch.bool)
        return obs, rewards, terminated, truncated, {}

    def close(self) -> None:
        pass

    def _get_observations(self) -> dict:
        return {
            "tray_poses": torch.zeros(3, 7),
            "toy_poses": torch.zeros(self.cfg.num_toys, 7),
        }
