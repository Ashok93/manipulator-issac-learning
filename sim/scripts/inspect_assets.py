"""Inspect USD asset dimensions using usd-core (no Isaac Lab needed).

Usage:
    uv run --with usd-core python scripts/inspect_assets.py
"""

from pathlib import Path
from pxr import Usd, UsdGeom

REPO_ROOT = Path(__file__).resolve().parents[1]
ASSETS = REPO_ROOT / "assets" / "toy_sorting"

FILES = {
    "table":     ASSETS / "Table049/Table049.usd",
    "box":       ASSETS / "Kit1/Kit1_Box.usd",
    "cube":      ASSETS / "Kit1/Kit1_Cube3x3.usd",
    "cylinder":  ASSETS / "Kit1/Kit1_Cylinder.usd",
    "sphere":    ASSETS / "Kit1/Kit1_Sphere.usd",
    "torus":     ASSETS / "Kit1/Kit1_Torus.usd",
    "triangle":  ASSETS / "Kit1/Kit1_Triangle.usd",
    "cross":     ASSETS / "Kit1/Kit1_Cross.usd",
    "cuboid":    ASSETS / "Kit1/Kit1_Cuboid6x3.usd",
    "bridge":    ASSETS / "Kit1/Kit1_Bridge.usd",
    "icosphere": ASSETS / "Kit1/Kit1_Icosphere.usd",
}

for name, path in FILES.items():
    if not path.exists():
        print(f"{name}: NOT FOUND at {path}")
        continue

    stage = Usd.Stage.Open(str(path))
    mpu      = UsdGeom.GetStageMetersPerUnit(stage)
    up_axis  = UsdGeom.GetStageUpAxis(stage)

    bbox_cache = UsdGeom.BBoxCache(Usd.TimeCode.Default(), [UsdGeom.Tokens.default_])
    bbox  = bbox_cache.ComputeWorldBound(stage.GetPseudoRoot())
    rng   = bbox.GetRange()
    mn, mx = rng.GetMin(), rng.GetMax()
    size  = (mx[0]-mn[0], mx[1]-mn[1], mx[2]-mn[2])

    # Isaac Sim is Z-up. If asset is Y-up, Isaac converts Y→Z (rotates -90° around X).
    # After conversion: asset_Y becomes world_Z (height), asset_Z becomes world_-Y.
    if up_axis == UsdGeom.Tokens.y:
        up_idx, up_label = 1, "Y (will be converted to Z by Isaac Sim)"
    else:
        up_idx, up_label = 2, "Z (matches Isaac Sim, no conversion needed)"

    height_in_usd  = size[up_idx]
    surface_in_usd = mx[up_idx]   # top of the bounding box in the up direction

    print(f"\n=== {name} ===")
    print(f"  upAxis        : {up_axis}  →  {up_label}")
    print(f"  metersPerUnit : {mpu}")
    print(f"  bbox min      : ({mn[0]:.3f}, {mn[1]:.3f}, {mn[2]:.3f})")
    print(f"  bbox max      : ({mx[0]:.3f}, {mx[1]:.3f}, {mx[2]:.3f})")
    print(f"  size (x,y,z)  : ({size[0]:.3f}, {size[1]:.3f}, {size[2]:.3f})")
    print(f"  HEIGHT axis   : {'Y' if up_idx==1 else 'Z'} = {height_in_usd:.3f} USD units")
    print(f"  surface (top) : {surface_in_usd:.3f} USD units")
    print(f"  => at scale=1.0: surface at world_Z = {surface_in_usd * mpu:.4f} m")
    print(f"  => REAL size (W x D x H): {size[0]*mpu:.3f} x {size[2 if up_idx==1 else 1]*mpu:.3f} x {height_in_usd*mpu:.3f} m")
