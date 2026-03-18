"""Isaac Lab DirectRLEnv: SO-ARM 101 toy sorting scene.

Scene layout
------------
- Wooden table (Table049 USD) at world origin.
- SO-ARM 101 mounted at the table edge (negative-Y side).
- 3 × SM_P_Tray_01 sorted left-to-right: red | green | blue.
- 9 toy objects (mix of Kitchen_Box / Kitchen_Disk) randomized on the table surface.
  Colors: 3 red, 3 green, 3 blue — re-shuffled at every reset.

Asset paths (all under assets/toy_sorting/, populated by assets/download.py)
-----------------------------------------------------------------------------
  Table049/Table049.usd
  InteractiveAsset/SM_P_Flavour_02/Collected_SM_P_Flavour_02/Props/SM_P_Tray_01.usd
  Kitchen_Other/Kitchen_Box.usd
  Kitchen_Other/Kitchen_Disk001.usd
  Kitchen_Other/Kitchen_Disk002.usd
  so_arm101/urdf/so_arm101.urdf  (+ STL meshes)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence

import torch

# ---------------------------------------------------------------------------
# Asset path helpers
# ---------------------------------------------------------------------------
_REPO_ROOT = Path(__file__).resolve().parents[3]
_ASSETS = _REPO_ROOT / "assets" / "toy_sorting"


def _asset(rel: str) -> str:
    """Return absolute string path to an asset, ensuring it exists."""
    p = _ASSETS / rel
    if not p.exists():
        raise FileNotFoundError(
            f"Asset not found: {p}\n"
            "Run `python assets/download.py --extract` (local) or "
            "`python assets/download.py --download` (from HuggingFace Hub)."
        )
    return str(p)


# ---------------------------------------------------------------------------
# Configuration dataclass
# ---------------------------------------------------------------------------

@dataclass
class ToySortingEnvCfg:
    # USD asset paths (resolved at construction time)
    table_usd: str = field(default_factory=lambda: _asset("Table049/Table049.usd"))
    tray_usd: str = field(
        default_factory=lambda: _asset(
            "InteractiveAsset/SM_P_Flavour_02/Collected_SM_P_Flavour_02/Props/SM_P_Tray_01.usd"
        )
    )
    toy_box_usd: str = field(default_factory=lambda: _asset("Kitchen_Other/Kitchen_Box.usd"))
    toy_disk_usd: str = field(default_factory=lambda: _asset("Kitchen_Other/Kitchen_Disk001.usd"))

    # SO-ARM 101 URDF path — resolved from assets/toy_sorting/so_arm101/urdf/
    robot_urdf: str = field(
        default_factory=lambda: _asset("so_arm101/urdf/so_arm101.urdf")
    )

    # Scene parameters
    num_toys: int = 9       # must be divisible by len(colors)
    num_envs: int = 1
    episode_length_s: float = 60.0

    # Color definitions (RGB 0-1 tuples)
    colors: tuple = (
        (0.85, 0.15, 0.15),   # red
        (0.15, 0.80, 0.20),   # green
        (0.20, 0.35, 0.90),   # blue
    )

    # Table surface area where toys spawn [x_min, x_max, y_min, y_max] in metres
    toy_spawn_area: tuple = (-0.25, 0.25, -0.10, 0.20)
    toy_spawn_height: float = 0.82   # z just above table top

    # Tray positions on table (x, y, z) in metres
    tray_positions: tuple = (
        (-0.20, 0.05, 0.78),   # red tray (left)
        ( 0.00, 0.05, 0.78),   # green tray (center)
        ( 0.20, 0.05, 0.78),   # blue tray (right)
    )


# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------

class ToySortingEnv:
    """Isaac Lab-style DirectRLEnv for the toy-sorting task.

    This class follows the Isaac Lab DirectRLEnv interface but does NOT
    inherit from it directly so the file can be imported and unit-tested
    without a full Isaac Sim install.  When running inside Isaac Sim,
    swap the base class to ``omni.isaac.lab.envs.DirectRLEnv``.
    """

    def __init__(self, cfg: ToySortingEnvCfg | None = None):
        self.cfg = cfg or ToySortingEnvCfg()
        self._stage = None
        self._toy_prims: list = []
        self._tray_prims: list = []
        self._toy_color_assignments: list[int] = []  # index into cfg.colors
        self._rng = torch.Generator()
        self._setup_scene()

    # ------------------------------------------------------------------
    # Scene setup
    # ------------------------------------------------------------------

    def _setup_scene(self) -> None:
        """Build the USD stage: ground, lights, table, robot, trays, toys."""
        self._setup_scene_isaac()

    def _setup_scene_isaac(self) -> None:
        import omni.usd
        import isaaclab.sim as sim_utils
        from isaaclab.assets import Articulation
        from pxr import Gf, UsdGeom

        from manipulator_learning.envs.so_arm101_cfg import make_so_arm101_cfg

        stage = omni.usd.get_context().get_stage()
        self._stage = stage

        # 1. Ground plane
        ground_cfg = sim_utils.GroundPlaneCfg()
        ground_cfg.func("/World/GroundPlane", ground_cfg)

        # 2. Dome light
        light_cfg = sim_utils.DomeLightCfg(intensity=2000.0, color=(0.9, 0.9, 1.0))
        light_cfg.func("/World/DomeLight", light_cfg)

        # 3. Table (static visual reference via UsdFileCfg)
        table_cfg = sim_utils.UsdFileCfg(usd_path=self.cfg.table_usd)
        table_cfg.func("/World/Table", table_cfg)

        # 4. SO-ARM 101 robot
        robot_cfg = make_so_arm101_cfg(self.cfg.robot_urdf)
        robot_cfg.prim_path = "/World/Robot"
        self._robot = Articulation(cfg=robot_cfg)

        # 5. Trays (3× SM_P_Tray_01)
        for idx, pos in enumerate(self.cfg.tray_positions):
            prim_path = f"/World/Tray_{idx}"
            tray_cfg = sim_utils.UsdFileCfg(usd_path=self.cfg.tray_usd)
            tray_cfg.func(prim_path, tray_cfg, translation=tuple(pos))
            self._tray_prims.append(stage.GetPrimAtPath(prim_path))

        # 6. Toys (alternating box/disk)
        for idx in range(self.cfg.num_toys):
            usd_path = self.cfg.toy_box_usd if idx % 2 == 0 else self.cfg.toy_disk_usd
            prim_path = f"/World/Toy_{idx}"
            toy_cfg = sim_utils.UsdFileCfg(usd_path=usd_path)
            toy_cfg.func(prim_path, toy_cfg)
            self._toy_prims.append(stage.GetPrimAtPath(prim_path))

        # Initial color assignment and placement
        self._assign_colors()
        self._place_toys_random()
        self._apply_colors()

    # ------------------------------------------------------------------
    # Color helpers
    # ------------------------------------------------------------------

    def _assign_colors(self) -> None:
        """Assign each toy a color index; shuffle among toys but keep trays fixed."""
        n_colors = len(self.cfg.colors)
        per_color = self.cfg.num_toys // n_colors
        assignments = []
        for c in range(n_colors):
            assignments.extend([c] * per_color)
        # Any remainder gets color 0
        while len(assignments) < self.cfg.num_toys:
            assignments.append(0)
        import random
        random.shuffle(assignments)
        self._toy_color_assignments = assignments

    def _apply_color(self, prim, color_rgb: tuple) -> None:
        """Set USD displayColor on a geometric primitive."""
        try:
            from pxr import Gf, UsdGeom
            gprim = UsdGeom.Gprim(prim)
            if gprim:
                gprim.GetDisplayColorAttr().Set([Gf.Vec3f(*color_rgb)])
        except Exception as exc:
            print(f"[WARN] _apply_color failed for {prim}: {exc}")

    def _apply_colors(self) -> None:
        """Paint trays with fixed colors and toys with their assignments."""
        for idx, tray_prim in enumerate(self._tray_prims):
            self._apply_color(tray_prim, self.cfg.colors[idx % len(self.cfg.colors)])
        for idx, toy_prim in enumerate(self._toy_prims):
            color_idx = self._toy_color_assignments[idx]
            self._apply_color(toy_prim, self.cfg.colors[color_idx])

    # ------------------------------------------------------------------
    # Physics / placement helpers
    # ------------------------------------------------------------------

    def _place_toys_random(self) -> None:
        """Scatter toys uniformly on the table surface."""
        try:
            from pxr import Gf, UsdGeom
        except ImportError:
            return

        x_min, x_max, y_min, y_max = self.cfg.toy_spawn_area
        z = self.cfg.toy_spawn_height
        for idx, toy_prim in enumerate(self._toy_prims):
            x = x_min + (x_max - x_min) * (idx % 3) / 2.0
            y = y_min + (y_max - y_min) * (idx // 3) / (self.cfg.num_toys // 3)
            xformable = UsdGeom.Xformable(toy_prim)
            xformable.ClearXformOpOrder()
            op = xformable.AddTranslateOp()
            op.Set(Gf.Vec3d(x, y, z))

    # ------------------------------------------------------------------
    # DirectRLEnv interface
    # ------------------------------------------------------------------

    def reset(self, env_ids: Sequence[int] | None = None):
        """Reset scene: re-randomize toy positions and color assignments."""
        self._assign_colors()
        self._place_toys_random()
        self._apply_colors()
        obs = self._get_observations()
        return obs, {}

    def step(self, actions: torch.Tensor):
        """Apply joint position targets and step physics."""
        self._pre_physics_step(actions)
        # In Isaac Lab the physics step is managed by the base class;
        # here we just return observations.
        obs = self._get_observations()
        rewards = self._get_rewards()
        terminated = self._get_terminated()
        truncated = torch.zeros_like(terminated)
        return obs, rewards, terminated, truncated, {}

    def close(self) -> None:
        pass

    # ------------------------------------------------------------------
    # Observation / reward / termination (Phase 1 stubs)
    # ------------------------------------------------------------------

    def _get_observations(self) -> dict:
        """Return minimal observation dict (Phase 1: static poses only)."""
        tray_poses = torch.zeros(len(self._tray_prims), 7)  # pos(3) + quat(4)
        toy_poses = torch.zeros(len(self._toy_prims), 7)
        return {"tray_poses": tray_poses, "toy_poses": toy_poses}

    def _get_rewards(self) -> torch.Tensor:
        return torch.zeros(self.cfg.num_envs)

    def _get_terminated(self) -> torch.Tensor:
        return torch.zeros(self.cfg.num_envs, dtype=torch.bool)

    def _pre_physics_step(self, actions: torch.Tensor) -> None:
        """Apply joint position targets to the robot articulation."""
        # Phase 1: no-op (robot articulation integration is Phase 2).
        pass
