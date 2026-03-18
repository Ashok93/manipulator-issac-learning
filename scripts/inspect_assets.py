"""Inspect USD asset dimensions using usd-core (no Isaac Lab needed).

Usage:
    uv run --with usd-core python scripts/inspect_assets.py
"""

from pathlib import Path
from pxr import Usd, UsdGeom

REPO_ROOT = Path(__file__).resolve().parents[1]
ASSETS = REPO_ROOT / "assets" / "toy_sorting"

FILES = {
    "table":  ASSETS / "Table049/Table049.usd",
    "tray":   ASSETS / "InteractiveAsset/SM_P_Flavour_02/Collected_SM_P_Flavour_02/Props/SM_P_Tray_01.usd",
    "box":    ASSETS / "Kitchen_Other/Kitchen_Box.usd",
    "disk":   ASSETS / "Kitchen_Other/Kitchen_Disk001.usd",
}

for name, path in FILES.items():
    if not path.exists():
        print(f"{name}: NOT FOUND at {path}")
        continue

    stage = Usd.Stage.Open(str(path))
    mpu   = UsdGeom.GetStageMetersPerUnit(stage)

    bbox_cache = UsdGeom.BBoxCache(Usd.TimeCode.Default(), [UsdGeom.Tokens.default_])
    bbox  = bbox_cache.ComputeWorldBound(stage.GetPseudoRoot())
    rng   = bbox.GetRange()
    mn, mx = rng.GetMin(), rng.GetMax()
    size  = (mx[0]-mn[0], mx[1]-mn[1], mx[2]-mn[2])

    print(f"\n=== {name} ===")
    print(f"  metersPerUnit : {mpu}")
    print(f"  bbox min (USD units): ({mn[0]:.1f}, {mn[1]:.1f}, {mn[2]:.1f})")
    print(f"  bbox max (USD units): ({mx[0]:.1f}, {mx[1]:.1f}, {mx[2]:.1f})")
    print(f"  size (USD units)    : ({size[0]:.1f}, {size[1]:.1f}, {size[2]:.1f})")
    print(f"  => real-world size  : ({size[0]*mpu:.3f}m, {size[1]*mpu:.3f}m, {size[2]*mpu:.3f}m)")
    print(f"  => at scale=0.01    : ({size[0]*0.01:.3f}m, {size[1]*0.01:.3f}m, {size[2]*0.01:.3f}m)")
    print(f"  origin z={mn[2]:.1f} → surface at z_usd={mx[2]:.1f}")
    print(f"  surface @ scale=0.01: z = {mx[2]*0.01:.3f}m  (if base placed at world z=0)")
