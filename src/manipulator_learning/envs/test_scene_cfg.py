"""Minimal test scene — mirrors TeleopSceneCfg exactly, using our local URDF."""

from __future__ import annotations

from pathlib import Path

import isaaclab.sim as sim_utils
from isaaclab.assets import ArticulationCfg, AssetBaseCfg
from isaaclab.scene import InteractiveSceneCfg
from isaaclab.utils import configclass
from isaaclab.utils.assets import ISAAC_NUCLEUS_DIR

from manipulator_learning.envs.so_arm101_cfg import make_so_arm101_cfg

GROUND_Z = -1.05
TABLE_POS = (0.55, 0.0, 0.0)
TABLE_ROT = (0.70711, 0.0, 0.0, 0.70711)
TABLE_USD = f"{ISAAC_NUCLEUS_DIR}/Props/Mounts/SeattleLabTable/table_instanceable.usd"

_URDF = str(
    Path(__file__).resolve().parents[3]
    / "assets/toy_sorting/so_arm101/urdf/so_arm101.urdf"
)


@configclass
class TestSceneCfg(InteractiveSceneCfg):
    ground = AssetBaseCfg(
        prim_path="/World/ground",
        spawn=sim_utils.GroundPlaneCfg(),
        init_state=AssetBaseCfg.InitialStateCfg(pos=(0.0, 0.0, GROUND_Z)),
    )
    table = AssetBaseCfg(
        prim_path="{ENV_REGEX_NS}/Table",
        spawn=sim_utils.UsdFileCfg(usd_path=TABLE_USD),
        init_state=AssetBaseCfg.InitialStateCfg(pos=TABLE_POS, rot=TABLE_ROT),
    )
    light = AssetBaseCfg(
        prim_path="/World/light",
        spawn=sim_utils.DomeLightCfg(intensity=2500.0, color=(0.75, 0.75, 0.75)),
    )
    robot: ArticulationCfg = make_so_arm101_cfg(_URDF).replace(
        prim_path="{ENV_REGEX_NS}/Robot"
    )
