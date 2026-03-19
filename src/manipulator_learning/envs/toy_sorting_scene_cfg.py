"""Isaac Lab InteractiveSceneCfg for the toy-sorting task.

Asset notes (measured with scripts/inspect_assets.py, all Z-up, mpu=1.0):
  Table049       height=0.80 m   → placed at z=-0.80 so surface lands at z=0
  Kit1_Box       base at z=0     → place at z=0 (open-top 15×15×5 cm container)
  Kit1 toys      base at z=0     → place at z=0 (sizes range 1.5–5.4 cm tall)

All objects sit on the table surface = world z=0.
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
_KIT1      = _ASSETS / "Kit1"


def _asset(rel: str) -> str:
    p = _ASSETS / rel
    if not p.exists():
        raise FileNotFoundError(
            f"Asset not found: {p}\n"
            "Run: uv run python assets/download.py --extract"
        )
    return str(p)


_TABLE_USD  = _asset("Table049/Table049.usd")
_BOX_USD    = _asset("Kit1/Kit1_Box.usd")        # open-top sorting container
_ROBOT_URDF = _asset("so_arm101/urdf/so_arm101.urdf")

# Nine distinct toy shapes — one per slot, all base at z=0.
_TOY_USDS = [
    _asset("Kit1/Kit1_Cube3x3.usd"),
    _asset("Kit1/Kit1_Cylinder.usd"),
    _asset("Kit1/Kit1_Sphere.usd"),
    _asset("Kit1/Kit1_Torus.usd"),
    _asset("Kit1/Kit1_Triangle.usd"),
    _asset("Kit1/Kit1_Cross.usd"),
    _asset("Kit1/Kit1_Cuboid6x3.usd"),
    _asset("Kit1/Kit1_Bridge.usd"),
    _asset("Kit1/Kit1_Icosphere.usd"),
]

# ---------------------------------------------------------------------------
# Table surface = world z=0.
# All Kit1 assets have their base face at z=0 in local space, so init pos z=0
# places them flush on the table with no offset required.
# ---------------------------------------------------------------------------

# 3 sorting boxes — spread along the back edge of the table (y=+0.22)
_BOX_POSITIONS = [
    (-0.22, 0.22, 0.0),
    ( 0.00, 0.22, 0.0),
    ( 0.22, 0.22, 0.0),
]

# 3×3 toy grid in front of the boxes, centred on the table
_TOY_XY = [
    (-0.15, -0.10), (0.00, -0.10), (0.15, -0.10),
    (-0.15,  0.02), (0.00,  0.02), (0.15,  0.02),
    (-0.15,  0.13), (0.00,  0.13), (0.15,  0.13),
]
_TOY_POSITIONS = [(*xy, 0.0) for xy in _TOY_XY]


@configclass
class ToySortingSceneCfg(InteractiveSceneCfg):
    """Table + SO-ARM 101 + 3 Kit1_Box sorting containers + 9 Kit1 toy shapes."""

    ground = AssetBaseCfg(
        prim_path="/World/ground",
        spawn=sim_utils.GroundPlaneCfg(),
        init_state=AssetBaseCfg.InitialStateCfg(pos=(0.0, 0.0, -0.85)),
    )
    light = AssetBaseCfg(
        prim_path="/World/light",
        spawn=sim_utils.DomeLightCfg(intensity=2000.0, color=(0.9, 0.9, 1.0)),
    )

    # Table: lowered by 0.80 m so the top surface lands at world z=0
    table = AssetBaseCfg(
        prim_path="{ENV_REGEX_NS}/Table",
        spawn=sim_utils.UsdFileCfg(usd_path=_TABLE_USD, scale=(1.0, 1.0, 1.0)),
        init_state=AssetBaseCfg.InitialStateCfg(pos=(0.0, 0.0, -0.80)),
    )

    robot: ArticulationCfg = make_so_arm101_cfg(_ROBOT_URDF).replace(
        prim_path="{ENV_REGEX_NS}/Robot"
    )

    # Sorting containers: Kit1_Box (15×15×5 cm open-top box), base at z=0.
    # Colors (red / green / blue) applied at reset via ToySortingEnv._apply_colors().
    box_0 = AssetBaseCfg(
        prim_path="{ENV_REGEX_NS}/Box_0",
        spawn=sim_utils.UsdFileCfg(usd_path=_BOX_USD, scale=(1.0, 1.0, 1.0)),
        init_state=AssetBaseCfg.InitialStateCfg(pos=_BOX_POSITIONS[0]),
    )
    box_1 = AssetBaseCfg(
        prim_path="{ENV_REGEX_NS}/Box_1",
        spawn=sim_utils.UsdFileCfg(usd_path=_BOX_USD, scale=(1.0, 1.0, 1.0)),
        init_state=AssetBaseCfg.InitialStateCfg(pos=_BOX_POSITIONS[1]),
    )
    box_2 = AssetBaseCfg(
        prim_path="{ENV_REGEX_NS}/Box_2",
        spawn=sim_utils.UsdFileCfg(usd_path=_BOX_USD, scale=(1.0, 1.0, 1.0)),
        init_state=AssetBaseCfg.InitialStateCfg(pos=_BOX_POSITIONS[2]),
    )

    # Toy shapes: each slot uses a distinct Kit1 shape.
    # Colors (red / green / blue, 3 toys each) applied at reset.
    toy_0 = AssetBaseCfg(prim_path="{ENV_REGEX_NS}/Toy_0", spawn=sim_utils.UsdFileCfg(usd_path=_TOY_USDS[0]), init_state=AssetBaseCfg.InitialStateCfg(pos=_TOY_POSITIONS[0]))  # noqa: E501
    toy_1 = AssetBaseCfg(prim_path="{ENV_REGEX_NS}/Toy_1", spawn=sim_utils.UsdFileCfg(usd_path=_TOY_USDS[1]), init_state=AssetBaseCfg.InitialStateCfg(pos=_TOY_POSITIONS[1]))  # noqa: E501
    toy_2 = AssetBaseCfg(prim_path="{ENV_REGEX_NS}/Toy_2", spawn=sim_utils.UsdFileCfg(usd_path=_TOY_USDS[2]), init_state=AssetBaseCfg.InitialStateCfg(pos=_TOY_POSITIONS[2]))  # noqa: E501
    toy_3 = AssetBaseCfg(prim_path="{ENV_REGEX_NS}/Toy_3", spawn=sim_utils.UsdFileCfg(usd_path=_TOY_USDS[3]), init_state=AssetBaseCfg.InitialStateCfg(pos=_TOY_POSITIONS[3]))  # noqa: E501
    toy_4 = AssetBaseCfg(prim_path="{ENV_REGEX_NS}/Toy_4", spawn=sim_utils.UsdFileCfg(usd_path=_TOY_USDS[4]), init_state=AssetBaseCfg.InitialStateCfg(pos=_TOY_POSITIONS[4]))  # noqa: E501
    toy_5 = AssetBaseCfg(prim_path="{ENV_REGEX_NS}/Toy_5", spawn=sim_utils.UsdFileCfg(usd_path=_TOY_USDS[5]), init_state=AssetBaseCfg.InitialStateCfg(pos=_TOY_POSITIONS[5]))  # noqa: E501
    toy_6 = AssetBaseCfg(prim_path="{ENV_REGEX_NS}/Toy_6", spawn=sim_utils.UsdFileCfg(usd_path=_TOY_USDS[6]), init_state=AssetBaseCfg.InitialStateCfg(pos=_TOY_POSITIONS[6]))  # noqa: E501
    toy_7 = AssetBaseCfg(prim_path="{ENV_REGEX_NS}/Toy_7", spawn=sim_utils.UsdFileCfg(usd_path=_TOY_USDS[7]), init_state=AssetBaseCfg.InitialStateCfg(pos=_TOY_POSITIONS[7]))  # noqa: E501
    toy_8 = AssetBaseCfg(prim_path="{ENV_REGEX_NS}/Toy_8", spawn=sim_utils.UsdFileCfg(usd_path=_TOY_USDS[8]), init_state=AssetBaseCfg.InitialStateCfg(pos=_TOY_POSITIONS[8]))  # noqa: E501
