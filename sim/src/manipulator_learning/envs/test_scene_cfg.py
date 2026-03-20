"""Minimal test scene — no external asset dependencies beyond the SO-ARM 101 URDF."""

from __future__ import annotations

from pathlib import Path

import isaaclab.sim as sim_utils
from isaaclab.assets import ArticulationCfg, AssetBaseCfg
from isaaclab.scene import InteractiveSceneCfg
from isaaclab.utils import configclass

from manipulator_learning.envs.so_arm101_cfg import make_so_arm101_cfg


def _find_repo_root() -> Path:
    """Walk up from this file until we find pyproject.toml (repo root sentinel)."""
    for parent in Path(__file__).resolve().parents:
        if (parent / "pyproject.toml").exists():
            return parent
    raise RuntimeError("Could not locate repo root (pyproject.toml not found)")


_URDF = str(
    _find_repo_root() / "assets" / "toy_sorting" / "so_arm101" / "urdf" / "so_arm101.urdf"
)

GROUND_Z = -1.05


@configclass
class TestSceneCfg(InteractiveSceneCfg):
    ground = AssetBaseCfg(
        prim_path="/World/ground",
        spawn=sim_utils.GroundPlaneCfg(),
        init_state=AssetBaseCfg.InitialStateCfg(pos=(0.0, 0.0, GROUND_Z)),
    )
    light = AssetBaseCfg(
        prim_path="/World/light",
        spawn=sim_utils.DomeLightCfg(intensity=2500.0, color=(0.75, 0.75, 0.75)),
    )
    robot: ArticulationCfg = make_so_arm101_cfg(_URDF).replace(
        prim_path="{ENV_REGEX_NS}/Robot"
    )
