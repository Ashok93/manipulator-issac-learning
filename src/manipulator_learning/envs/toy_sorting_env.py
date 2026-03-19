"""Isaac Lab toy-sorting environment using InteractiveScene."""

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

    def __init__(self, cfg: ToySortingEnvCfg | None = None):
        self.cfg = cfg or ToySortingEnvCfg()
        self._toy_color_assignments: list[int] = []
        self._setup_scene()

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
        """Bind a UsdPreviewSurface material with the given color to every
        visual mesh under prim_path.

        UsdPreviewSurface is standard USD and works regardless of whether the
        full Omniverse MDL library is installed (pip-based Isaac Lab included).
        The material is created once per prim_path and reused/updated on
        subsequent resets.
        """
        import omni.usd
        from pxr import Gf, Sdf, Usd, UsdShade

        stage = omni.usd.get_context().get_stage()
        prim = stage.GetPrimAtPath(prim_path)
        if not prim.IsValid():
            raise RuntimeError(f"Prim not found in stage: {prim_path}")

        # Deterministic material path derived from the prim path
        safe_name = prim_path.replace("/", "_").lstrip("_")
        mat_path = f"/World/Looks/{safe_name}"

        mat_prim = stage.GetPrimAtPath(mat_path)
        if mat_prim.IsValid():
            # Material already exists — just update the diffuse color
            shader = UsdShade.Shader(stage.GetPrimAtPath(f"{mat_path}/Shader"))
            shader.GetInput("diffuseColor").Set(Gf.Vec3f(*color_rgb))
        else:
            # First reset: create a new UsdPreviewSurface material
            mat = UsdShade.Material.Define(stage, mat_path)
            shader = UsdShade.Shader.Define(stage, f"{mat_path}/Shader")
            shader.CreateIdAttr("UsdPreviewSurface")
            shader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).Set(Gf.Vec3f(*color_rgb))
            shader.CreateInput("roughness", Sdf.ValueTypeNames.Float).Set(0.4)
            mat.CreateSurfaceOutput().ConnectToSource(shader.ConnectableAPI(), "surface")

        # Bind directly to every visual mesh (skipping collision meshes)
        mat = UsdShade.Material(stage.GetPrimAtPath(mat_path))
        for desc_prim in Usd.PrimRange(prim):
            if desc_prim.GetTypeName() == "Mesh" and "Collisions" not in str(desc_prim.GetPath()):
                UsdShade.MaterialBindingAPI(desc_prim).Bind(mat)

    def _apply_colors(self) -> None:
        env_prefix = "/World/envs/env_0"
        box_colors = [(0.85, 0.15, 0.15), (0.15, 0.80, 0.20), (0.20, 0.35, 0.90)]
        for i, color in enumerate(box_colors):
            self._apply_color(f"{env_prefix}/Box_{i}", color)
        for i in range(self.cfg.num_toys):
            self._apply_color(f"{env_prefix}/Toy_{i}", self.cfg.colors[self._toy_color_assignments[i]])

    # ------------------------------------------------------------------
    # Gym-style interface
    # ------------------------------------------------------------------

    def reset(self, env_ids: Sequence[int] | None = None):
        self._scene.reset()
        self._assign_colors()
        self._apply_colors()
        return self._get_observations(), {}

    def step(self, actions: torch.Tensor):
        from isaaclab.sim import SimulationContext
        robot = self._scene["robot"]
        robot.set_joint_position_target(actions.unsqueeze(0))
        robot.write_data_to_sim()
        self._scene.update(SimulationContext.instance().get_physics_dt())
        return (
            self._get_observations(),
            torch.zeros(self.cfg.num_envs),
            torch.zeros(self.cfg.num_envs, dtype=torch.bool),
            torch.zeros(self.cfg.num_envs, dtype=torch.bool),
            {},
        )

    def close(self) -> None:
        pass

    def _get_observations(self) -> dict:
        return {
            "box_poses": torch.zeros(3, 7),
            "toy_poses": torch.zeros(self.cfg.num_toys, 7),
        }
