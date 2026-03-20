"""Isaac Lab InteractiveSceneCfg for the toy-sorting task.

Layout
------
Robot at back-center (0, -0.10) facing +Y.  All toys and boxes are in a
forward arc within the SO-ARM 101's ~22 cm practical reach.  Positions are
defaults — the env randomizes them on every reset().

Asset notes (measured with scripts/inspect_assets.py, all Z-up, mpu=1.0):
  Table049       height=0.80 m   → placed at z=-0.80 so surface lands at z=0
  Kit1_Box       base at z=0     → place at z=0 (open-top 15×15×5 cm container)
  Kit1 toys      base at z=0     → place at z=0 (sizes range 1.5–5.4 cm tall)

All objects sit on the table surface = world z=0.
"""

from __future__ import annotations

from pathlib import Path

import isaaclab.sim as sim_utils
from isaaclab.assets import ArticulationCfg, AssetBaseCfg, RigidObjectCfg
from isaaclab.scene import InteractiveSceneCfg
from isaaclab.sensors import CameraCfg
from isaaclab.utils import configclass

NUM_BOXES = 3
NUM_TOYS = 9

from manipulator_learning.envs.so_arm101_cfg import make_so_arm101_cfg


def _find_repo_root() -> Path:
    """Walk up from this file until we find pyproject.toml (repo root sentinel)."""
    for parent in Path(__file__).resolve().parents:
        if (parent / "pyproject.toml").exists():
            return parent
    raise RuntimeError("Could not locate repo root (pyproject.toml not found)")


_REPO_ROOT = _find_repo_root()
_ASSETS    = _REPO_ROOT / "assets" / "toy_sorting"


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
# Table surface = world z=0.  Robot at back-center, everything in front.
# All Kit1 assets have their base face at z=0 in local space, so init pos z=0
# places them flush on the table with no offset required.
# ---------------------------------------------------------------------------

# Robot base is at (0, -0.10, 0) facing +Y. All objects in front, within reach.
# SO-ARM 101 practical reach ~20-22cm, shoulder pan ±110°.

# 3 sorting boxes — arc at far reach (~20-22cm from robot base)
_BOX_POSITIONS = [
    (-0.12,  0.08, 0.0),   # left
    ( 0.00,  0.12, 0.0),   # center (slightly further, dead ahead)
    ( 0.12,  0.08, 0.0),   # right
]

# 3×3 toy grid — compact cluster in front of robot (~8-16cm from base)
_TOY_XY = [
    (-0.06, -0.02), (0.00, -0.02), (0.06, -0.02),   # near row
    (-0.06,  0.02), (0.00,  0.02), (0.06,  0.02),   # middle row
    (-0.06,  0.06), (0.00,  0.06), (0.06,  0.06),   # far row
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

    # Top-down RGB camera — static above table centre, looking straight down.
    # convention="world" + identity quaternion → camera -Z aligns with world -Z (downward).
    camera = CameraCfg(
        prim_path="{ENV_REGEX_NS}/Camera",
        update_period=0,
        height=480,
        width=640,
        data_types=["rgb"],
        spawn=sim_utils.PinholeCameraCfg(
            focal_length=24.0,
            focus_distance=400.0,
            horizontal_aperture=20.955,
            clipping_range=(0.1, 2.0),
        ),
        offset=CameraCfg.OffsetCfg(
            pos=(0.0, 0.0, 1.2),
            rot=(1.0, 0.0, 0.0, 0.0),
            convention="world",
        ),
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
    # Physics (rigid body, mass=155g, collision) baked into the USD.
    # Colors (red / green / blue) applied at reset via ToySortingEnv._apply_colors().
    box_0: RigidObjectCfg = RigidObjectCfg(
        prim_path="{ENV_REGEX_NS}/Box_0",
        spawn=sim_utils.UsdFileCfg(usd_path=_BOX_USD),
        init_state=RigidObjectCfg.InitialStateCfg(pos=_BOX_POSITIONS[0]),
    )
    box_1: RigidObjectCfg = RigidObjectCfg(
        prim_path="{ENV_REGEX_NS}/Box_1",
        spawn=sim_utils.UsdFileCfg(usd_path=_BOX_USD),
        init_state=RigidObjectCfg.InitialStateCfg(pos=_BOX_POSITIONS[1]),
    )
    box_2: RigidObjectCfg = RigidObjectCfg(
        prim_path="{ENV_REGEX_NS}/Box_2",
        spawn=sim_utils.UsdFileCfg(usd_path=_BOX_USD),
        init_state=RigidObjectCfg.InitialStateCfg(pos=_BOX_POSITIONS[2]),
    )

    # Toy shapes: each slot uses a distinct Kit1 shape.
    # Physics (rigid body, mass ~10-21g, collision) baked into each USD.
    # Colors (red / green / blue, 3 toys each) applied at reset.
    toy_0: RigidObjectCfg = RigidObjectCfg(prim_path="{ENV_REGEX_NS}/Toy_0", spawn=sim_utils.UsdFileCfg(usd_path=_TOY_USDS[0]), init_state=RigidObjectCfg.InitialStateCfg(pos=_TOY_POSITIONS[0]))  # noqa: E501
    toy_1: RigidObjectCfg = RigidObjectCfg(prim_path="{ENV_REGEX_NS}/Toy_1", spawn=sim_utils.UsdFileCfg(usd_path=_TOY_USDS[1]), init_state=RigidObjectCfg.InitialStateCfg(pos=_TOY_POSITIONS[1]))  # noqa: E501
    toy_2: RigidObjectCfg = RigidObjectCfg(prim_path="{ENV_REGEX_NS}/Toy_2", spawn=sim_utils.UsdFileCfg(usd_path=_TOY_USDS[2]), init_state=RigidObjectCfg.InitialStateCfg(pos=_TOY_POSITIONS[2]))  # noqa: E501
    toy_3: RigidObjectCfg = RigidObjectCfg(prim_path="{ENV_REGEX_NS}/Toy_3", spawn=sim_utils.UsdFileCfg(usd_path=_TOY_USDS[3]), init_state=RigidObjectCfg.InitialStateCfg(pos=_TOY_POSITIONS[3]))  # noqa: E501
    toy_4: RigidObjectCfg = RigidObjectCfg(prim_path="{ENV_REGEX_NS}/Toy_4", spawn=sim_utils.UsdFileCfg(usd_path=_TOY_USDS[4]), init_state=RigidObjectCfg.InitialStateCfg(pos=_TOY_POSITIONS[4]))  # noqa: E501
    toy_5: RigidObjectCfg = RigidObjectCfg(prim_path="{ENV_REGEX_NS}/Toy_5", spawn=sim_utils.UsdFileCfg(usd_path=_TOY_USDS[5]), init_state=RigidObjectCfg.InitialStateCfg(pos=_TOY_POSITIONS[5]))  # noqa: E501
    toy_6: RigidObjectCfg = RigidObjectCfg(prim_path="{ENV_REGEX_NS}/Toy_6", spawn=sim_utils.UsdFileCfg(usd_path=_TOY_USDS[6]), init_state=RigidObjectCfg.InitialStateCfg(pos=_TOY_POSITIONS[6]))  # noqa: E501
    toy_7: RigidObjectCfg = RigidObjectCfg(prim_path="{ENV_REGEX_NS}/Toy_7", spawn=sim_utils.UsdFileCfg(usd_path=_TOY_USDS[7]), init_state=RigidObjectCfg.InitialStateCfg(pos=_TOY_POSITIONS[7]))  # noqa: E501
    toy_8: RigidObjectCfg = RigidObjectCfg(prim_path="{ENV_REGEX_NS}/Toy_8", spawn=sim_utils.UsdFileCfg(usd_path=_TOY_USDS[8]), init_state=RigidObjectCfg.InitialStateCfg(pos=_TOY_POSITIONS[8]))  # noqa: E501
