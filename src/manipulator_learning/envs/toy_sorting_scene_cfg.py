"""Isaac Lab InteractiveSceneCfg for the toy-sorting task.

Must be imported AFTER AppLauncher starts (isaaclab.* unavailable before that).
"""

from __future__ import annotations

from pathlib import Path

import isaaclab.sim as sim_utils
from isaaclab.assets import ArticulationCfg, AssetBaseCfg
from isaaclab.scene import InteractiveSceneCfg
from isaaclab.utils import configclass

from manipulator_learning.envs.so_arm101_cfg import make_so_arm101_cfg

# ---------------------------------------------------------------------------
# Asset path helpers (resolved at import time — assets must be downloaded)
# ---------------------------------------------------------------------------
_REPO_ROOT = Path(__file__).resolve().parents[3]
_ASSETS = _REPO_ROOT / "assets" / "toy_sorting"


def _asset(rel: str) -> str:
    p = _ASSETS / rel
    if not p.exists():
        raise FileNotFoundError(
            f"Asset not found: {p}\n"
            "Run: uv run python assets/download.py --download"
        )
    return str(p)


_TABLE_USD = _asset("Table049/Table049.usd")
_TRAY_USD = _asset(
    "InteractiveAsset/SM_P_Flavour_02/Collected_SM_P_Flavour_02/Props/SM_P_Tray_01.usd"
)
_BOX_USD = _asset("Kitchen_Other/Kitchen_Box.usd")
_DISK_USD = _asset("Kitchen_Other/Kitchen_Disk001.usd")
_ROBOT_URDF = _asset("so_arm101/urdf/so_arm101.urdf")

# Toy positions: 3×3 grid on table surface (x, y, z)
_TOY_POSITIONS = [
    (-0.15, -0.05, 0.82), (0.00, -0.05, 0.82), (0.15, -0.05, 0.82),
    (-0.15,  0.05, 0.82), (0.00,  0.05, 0.82), (0.15,  0.05, 0.82),
    (-0.15,  0.15, 0.82), (0.00,  0.15, 0.82), (0.15,  0.15, 0.82),
]


@configclass
class ToySortingSceneCfg(InteractiveSceneCfg):
    """Scene: table, SO-ARM 101, 3 colored trays, 9 toys."""

    # Static scene elements
    ground = AssetBaseCfg(
        prim_path="/World/ground",
        spawn=sim_utils.GroundPlaneCfg(),
    )
    light = AssetBaseCfg(
        prim_path="/World/light",
        spawn=sim_utils.DomeLightCfg(intensity=2000.0, color=(0.9, 0.9, 1.0)),
    )
    table = AssetBaseCfg(
        prim_path="{ENV_REGEX_NS}/Table",
        spawn=sim_utils.UsdFileCfg(usd_path=_TABLE_USD),
        init_state=AssetBaseCfg.InitialStateCfg(pos=(0.0, 0.0, 0.0)),
    )

    # Robot
    robot: ArticulationCfg = make_so_arm101_cfg(_ROBOT_URDF).replace(
        prim_path="{ENV_REGEX_NS}/Robot"
    )

    # Trays and toys commented out for isolation test — see if table+robot works first
    # tray_red = AssetBaseCfg(prim_path="{ENV_REGEX_NS}/Tray_0", spawn=sim_utils.UsdFileCfg(usd_path=_TRAY_USD), init_state=AssetBaseCfg.InitialStateCfg(pos=(-0.20, 0.05, 0.78)))  # noqa: E501
    # tray_green = AssetBaseCfg(prim_path="{ENV_REGEX_NS}/Tray_1", spawn=sim_utils.UsdFileCfg(usd_path=_TRAY_USD), init_state=AssetBaseCfg.InitialStateCfg(pos=(0.00, 0.05, 0.78)))  # noqa: E501
    # tray_blue = AssetBaseCfg(prim_path="{ENV_REGEX_NS}/Tray_2", spawn=sim_utils.UsdFileCfg(usd_path=_TRAY_USD), init_state=AssetBaseCfg.InitialStateCfg(pos=(0.20, 0.05, 0.78)))  # noqa: E501
    # toy_0 = AssetBaseCfg(prim_path="{ENV_REGEX_NS}/Toy_0", spawn=sim_utils.UsdFileCfg(usd_path=_BOX_USD),  init_state=AssetBaseCfg.InitialStateCfg(pos=_TOY_POSITIONS[0]))  # noqa: E501
    # toy_1 = AssetBaseCfg(prim_path="{ENV_REGEX_NS}/Toy_1", spawn=sim_utils.UsdFileCfg(usd_path=_DISK_USD), init_state=AssetBaseCfg.InitialStateCfg(pos=_TOY_POSITIONS[1]))  # noqa: E501
    # toy_2 = AssetBaseCfg(prim_path="{ENV_REGEX_NS}/Toy_2", spawn=sim_utils.UsdFileCfg(usd_path=_BOX_USD),  init_state=AssetBaseCfg.InitialStateCfg(pos=_TOY_POSITIONS[2]))  # noqa: E501
    # toy_3 = AssetBaseCfg(prim_path="{ENV_REGEX_NS}/Toy_3", spawn=sim_utils.UsdFileCfg(usd_path=_DISK_USD), init_state=AssetBaseCfg.InitialStateCfg(pos=_TOY_POSITIONS[3]))  # noqa: E501
    # toy_4 = AssetBaseCfg(prim_path="{ENV_REGEX_NS}/Toy_4", spawn=sim_utils.UsdFileCfg(usd_path=_BOX_USD),  init_state=AssetBaseCfg.InitialStateCfg(pos=_TOY_POSITIONS[4]))  # noqa: E501
    # toy_5 = AssetBaseCfg(prim_path="{ENV_REGEX_NS}/Toy_5", spawn=sim_utils.UsdFileCfg(usd_path=_DISK_USD), init_state=AssetBaseCfg.InitialStateCfg(pos=_TOY_POSITIONS[5]))  # noqa: E501
    # toy_6 = AssetBaseCfg(prim_path="{ENV_REGEX_NS}/Toy_6", spawn=sim_utils.UsdFileCfg(usd_path=_BOX_USD),  init_state=AssetBaseCfg.InitialStateCfg(pos=_TOY_POSITIONS[6]))  # noqa: E501
    # toy_7 = AssetBaseCfg(prim_path="{ENV_REGEX_NS}/Toy_7", spawn=sim_utils.UsdFileCfg(usd_path=_DISK_USD), init_state=AssetBaseCfg.InitialStateCfg(pos=_TOY_POSITIONS[7]))  # noqa: E501
    # toy_8 = AssetBaseCfg(prim_path="{ENV_REGEX_NS}/Toy_8", spawn=sim_utils.UsdFileCfg(usd_path=_BOX_USD),  init_state=AssetBaseCfg.InitialStateCfg(pos=_TOY_POSITIONS[8]))  # noqa: E501
