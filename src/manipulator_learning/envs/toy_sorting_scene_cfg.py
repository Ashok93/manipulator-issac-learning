"""Isaac Lab InteractiveSceneCfg for the toy-sorting task.

Asset notes (from scripts/inspect_assets.py):
  Table049  metersPerUnit=1.0, height=0.80m  → placed at z=-0.80 so surface lands at z=0
  Disk      metersPerUnit=1.0, half-h=0.012m → bowl origin at centre, place at z=+0.012
  Box       metersPerUnit=1.0, half-h=0.087m → toy  origin at centre, place at z=+0.026 (scale=0.3)
"""

from __future__ import annotations

from pathlib import Path

import isaaclab.sim as sim_utils
from isaaclab.assets import ArticulationCfg, AssetBaseCfg
from isaaclab.scene import InteractiveSceneCfg
from isaaclab.utils import configclass

from manipulator_learning.envs.so_arm101_cfg import make_so_arm101_cfg

_REPO_ROOT = Path(__file__).resolve().parents[3]
_ASSETS    = _REPO_ROOT / "assets" / "toy_sorting"


def _asset(rel: str) -> str:
    p = _ASSETS / rel
    if not p.exists():
        raise FileNotFoundError(f"Asset not found: {p}\nRun: uv run python assets/download.py --download")
    return str(p)


_TABLE_USD  = _asset("Table049/Table049.usd")
_BOWL_USD   = _asset("Kitchen_Other/Kitchen_Disk001.usd")   # round dish → sorting bowl
_TOY_USD    = _asset("Kitchen_Other/Kitchen_Box.usd")        # small box  → sorting toy
_ROBOT_URDF = _asset("so_arm101/urdf/so_arm101.urdf")

# ---------------------------------------------------------------------------
# All objects sit on the table surface = world z=0.
# Table is lowered by its own height (0.80 m) so its top face lands at z=0.
# ---------------------------------------------------------------------------
_S  = 0.0     # table surface world z
_BZ = _S + 0.012   # bowl  (Disk, half-h=0.012 m at scale=1.0)
_TZ = _S + 0.026   # toy   (Box,  half-h=0.087*0.3=0.026 m at scale=0.3)

# 3×3 toy grid in front of the bowls, within table footprint (±0.4 m)
_TOY_XY = [
    (-0.15, -0.10), (0.00, -0.10), (0.15, -0.10),
    (-0.15,  0.02), (0.00,  0.02), (0.15,  0.02),
    (-0.15,  0.13), (0.00,  0.13), (0.15,  0.13),
]
_TOY_POSITIONS = [(*xy, _TZ) for xy in _TOY_XY]


@configclass
class ToySortingSceneCfg(InteractiveSceneCfg):
    """Table + SO-ARM 101 + 3 colored bowls + 9 colored toy boxes."""

    ground = AssetBaseCfg(
        prim_path="/World/ground",
        spawn=sim_utils.GroundPlaneCfg(),
        init_state=AssetBaseCfg.InitialStateCfg(pos=(0.0, 0.0, -0.85)),
    )
    light = AssetBaseCfg(
        prim_path="/World/light",
        spawn=sim_utils.DomeLightCfg(intensity=2000.0, color=(0.9, 0.9, 1.0)),
    )

    # Table: lower by 0.80 m so the top face lands exactly at world z=0
    table = AssetBaseCfg(
        prim_path="{ENV_REGEX_NS}/Table",
        spawn=sim_utils.UsdFileCfg(usd_path=_TABLE_USD, scale=(1.0, 1.0, 1.0)),
        init_state=AssetBaseCfg.InitialStateCfg(pos=(0.0, 0.0, -0.80)),
    )

    robot: ArticulationCfg = make_so_arm101_cfg(_ROBOT_URDF).replace(
        prim_path="{ENV_REGEX_NS}/Robot"
    )

    # Bowls: Disk USD, scale=1.0 → 14 cm diameter.  Placed at back of table.
    bowl_red = AssetBaseCfg(
        prim_path="{ENV_REGEX_NS}/Bowl_0",
        spawn=sim_utils.UsdFileCfg(usd_path=_BOWL_USD, scale=(1.0, 1.0, 1.0)),
        init_state=AssetBaseCfg.InitialStateCfg(pos=(-0.20, 0.22, _BZ)),
    )
    bowl_green = AssetBaseCfg(
        prim_path="{ENV_REGEX_NS}/Bowl_1",
        spawn=sim_utils.UsdFileCfg(usd_path=_BOWL_USD, scale=(1.0, 1.0, 1.0)),
        init_state=AssetBaseCfg.InitialStateCfg(pos=( 0.00, 0.22, _BZ)),
    )
    bowl_blue = AssetBaseCfg(
        prim_path="{ENV_REGEX_NS}/Bowl_2",
        spawn=sim_utils.UsdFileCfg(usd_path=_BOWL_USD, scale=(1.0, 1.0, 1.0)),
        init_state=AssetBaseCfg.InitialStateCfg(pos=( 0.20, 0.22, _BZ)),
    )

    # Toys: Box USD, scale=0.3 → ~10×3×5 cm blocks.  3×3 grid in front of bowls.
    toy_0 = AssetBaseCfg(prim_path="{ENV_REGEX_NS}/Toy_0", spawn=sim_utils.UsdFileCfg(usd_path=_TOY_USD, scale=(0.3, 0.3, 0.3)), init_state=AssetBaseCfg.InitialStateCfg(pos=_TOY_POSITIONS[0]))  # noqa: E501
    toy_1 = AssetBaseCfg(prim_path="{ENV_REGEX_NS}/Toy_1", spawn=sim_utils.UsdFileCfg(usd_path=_TOY_USD, scale=(0.3, 0.3, 0.3)), init_state=AssetBaseCfg.InitialStateCfg(pos=_TOY_POSITIONS[1]))  # noqa: E501
    toy_2 = AssetBaseCfg(prim_path="{ENV_REGEX_NS}/Toy_2", spawn=sim_utils.UsdFileCfg(usd_path=_TOY_USD, scale=(0.3, 0.3, 0.3)), init_state=AssetBaseCfg.InitialStateCfg(pos=_TOY_POSITIONS[2]))  # noqa: E501
    toy_3 = AssetBaseCfg(prim_path="{ENV_REGEX_NS}/Toy_3", spawn=sim_utils.UsdFileCfg(usd_path=_TOY_USD, scale=(0.3, 0.3, 0.3)), init_state=AssetBaseCfg.InitialStateCfg(pos=_TOY_POSITIONS[3]))  # noqa: E501
    toy_4 = AssetBaseCfg(prim_path="{ENV_REGEX_NS}/Toy_4", spawn=sim_utils.UsdFileCfg(usd_path=_TOY_USD, scale=(0.3, 0.3, 0.3)), init_state=AssetBaseCfg.InitialStateCfg(pos=_TOY_POSITIONS[4]))  # noqa: E501
    toy_5 = AssetBaseCfg(prim_path="{ENV_REGEX_NS}/Toy_5", spawn=sim_utils.UsdFileCfg(usd_path=_TOY_USD, scale=(0.3, 0.3, 0.3)), init_state=AssetBaseCfg.InitialStateCfg(pos=_TOY_POSITIONS[5]))  # noqa: E501
    toy_6 = AssetBaseCfg(prim_path="{ENV_REGEX_NS}/Toy_6", spawn=sim_utils.UsdFileCfg(usd_path=_TOY_USD, scale=(0.3, 0.3, 0.3)), init_state=AssetBaseCfg.InitialStateCfg(pos=_TOY_POSITIONS[6]))  # noqa: E501
    toy_7 = AssetBaseCfg(prim_path="{ENV_REGEX_NS}/Toy_7", spawn=sim_utils.UsdFileCfg(usd_path=_TOY_USD, scale=(0.3, 0.3, 0.3)), init_state=AssetBaseCfg.InitialStateCfg(pos=_TOY_POSITIONS[7]))  # noqa: E501
    toy_8 = AssetBaseCfg(prim_path="{ENV_REGEX_NS}/Toy_8", spawn=sim_utils.UsdFileCfg(usd_path=_TOY_USD, scale=(0.3, 0.3, 0.3)), init_state=AssetBaseCfg.InitialStateCfg(pos=_TOY_POSITIONS[8]))  # noqa: E501
