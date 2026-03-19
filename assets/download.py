"""Asset management for the toy-sorting EnvHub repo.

Three modes
-----------
--extract   Copy the needed USD/STL/texture files from local source dirs
            (Lightwheel_Xx8T7EPOMd_KitchenRoom/ and so_arm101/) into
            assets/toy_sorting/.  Run once on a developer machine.

--upload    Push the full environment repo (code + assets) to HuggingFace Hub
            as AshDash93/toy-sorting-env (model repo, CC BY-NC 4.0).
            Requires HF_TOKEN in .env.

--download  Pull only assets/toy_sorting/ from the HF env repo into the local
            assets/toy_sorting/ directory.  Used automatically at env startup
            when running on a server without the source asset packs.

If no flag is given, checks whether assets/toy_sorting/ is populated and runs
--download automatically if not.
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

REPO_ROOT = Path(__file__).resolve().parents[1]
LIGHTWHEEL_DIR = REPO_ROOT / "Lightwheel_Xx8T7EPOMd_KitchenRoom"
TOYROOM_DIR    = REPO_ROOT / "lightwheel_toyroom"
SO_ARM_SRC_DIR = REPO_ROOT / "so_arm101"
OUT_DIR = REPO_ROOT / "assets" / "toy_sorting"

HF_ENV_REPO = os.environ.get("HF_ENV_REPO", "AshDash93/toy-sorting-env")

# Files to extract from LIGHTWHEEL_DIR → OUT_DIR (preserving relative structure)
LIGHTWHEEL_FILES = [
    "Table049/Table049.usd",
    "Table049/texture/T_Table049_BC001.png",
    "Table049/texture/T_Table049_N001.png",
    "Table049/texture/T_Table049_ORM001.png",
]

LIGHTWHEEL_GLOBS: list[str] = []

# Files to extract from TOYROOM_DIR/Assets → OUT_DIR/Kit1
# These are self-contained USDs (no external texture/MDL dependencies).
TOYROOM_FILES = [
    "Kit1/Kit1_Box.usd",       # open-top sorting container (15×15×5 cm)
    "Kit1/Kit1_Cube3x3.usd",   # 3 cm cube
    "Kit1/Kit1_Cylinder.usd",  # cylinder
    "Kit1/Kit1_Sphere.usd",    # sphere
    "Kit1/Kit1_Torus.usd",     # torus / ring
    "Kit1/Kit1_Triangle.usd",  # triangular prism
    "Kit1/Kit1_Cross.usd",     # plus / cross shape
    "Kit1/Kit1_Cuboid6x3.usd", # flat rectangular block
    "Kit1/Kit1_Bridge.usd",    # arch / bridge shape
    "Kit1/Kit1_Icosphere.usd", # icosphere
]

# Files/dirs to exclude when uploading to HF Hub.
# Only env code + assets belong there — no dev/deployment/secrets files.
UPLOAD_IGNORE = [
    ".git/**",
    ".cache/**",
    ".venv/**",
    ".claude/**",
    "__pycache__/**",
    "*.pyc",
    ".env",
    "uv.lock",
    "Lightwheel_Xx8T7EPOMd_KitchenRoom/**",
    "lightwheel_toyroom/**",
    "so_arm101/**",
    ".DS_Store",
    "datasets/**",
    "outputs/**",
    "wandb/**",
    "logs/**",
    "prompt.md",
    "Dockerfile",
    "docker-compose.yml",
    "assets/download.py",
]


def _copy_file(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    print(f"  copied  {dst.relative_to(REPO_ROOT)}")


def extract() -> None:
    """Copy asset subset into assets/toy_sorting/ from local source packs."""
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # --- Lightwheel kitchen pack (table) ---
    if not LIGHTWHEEL_DIR.exists():
        print(f"[WARN] Lightwheel kitchen dir not found: {LIGHTWHEEL_DIR} — skipping table assets")
    else:
        print(f"Extracting Lightwheel kitchen assets → {OUT_DIR}")
        for rel in LIGHTWHEEL_FILES:
            src = LIGHTWHEEL_DIR / rel
            if not src.exists():
                print(f"  [WARN] missing: {rel}")
                continue
            _copy_file(src, OUT_DIR / rel)

    # --- Lightwheel toyroom pack (Kit1 toys + sorting box) ---
    if not TOYROOM_DIR.exists():
        print(f"[WARN] Toyroom dir not found: {TOYROOM_DIR} — skipping Kit1 assets")
    else:
        print(f"Extracting Lightwheel toyroom assets → {OUT_DIR}")
        src_base = TOYROOM_DIR / "Assets"
        for rel in TOYROOM_FILES:
            src = src_base / rel
            if not src.exists():
                print(f"  [WARN] missing: {rel}")
                continue
            _copy_file(src, OUT_DIR / rel)

    # --- SO-ARM 101 URDF ---
    if SO_ARM_SRC_DIR.exists():
        print(f"Extracting SO-ARM 101 URDF → {OUT_DIR}")
        for src in SO_ARM_SRC_DIR.rglob("*"):
            if src.is_file() and src.suffix in {".urdf", ".stl", ".part"}:
                _copy_file(src, OUT_DIR / src.relative_to(REPO_ROOT))
    else:
        print(f"  [WARN] so_arm101/ not found — skipping robot URDF")

    print("Extraction complete.")


def upload() -> None:
    """Upload full env repo (code + assets) to HuggingFace Hub."""
    from huggingface_hub import HfApi

    token = os.environ.get("HF_TOKEN") or os.environ.get("HUGGING_FACE_HUB_TOKEN")
    if not token:
        sys.exit("[ERROR] Set HF_TOKEN in .env before uploading.")
    if not OUT_DIR.exists() or not any(OUT_DIR.iterdir()):
        sys.exit("[ERROR] assets/toy_sorting/ is empty. Run --extract first.")

    print(f"Uploading env repo → HuggingFace Hub: {HF_ENV_REPO}")
    api = HfApi(token=token)
    api.create_repo(repo_id=HF_ENV_REPO, repo_type="model", exist_ok=True, private=False)

    # Step 1: upload source code (text files, no binary assets).
    # assets/toy_sorting/ is in .gitignore so we explicitly exclude it here
    # and handle it separately in step 2.
    print("  [1/2] uploading source code …")
    api.upload_folder(
        repo_id=HF_ENV_REPO,
        repo_type="model",
        folder_path=str(REPO_ROOT),
        ignore_patterns=UPLOAD_IGNORE + ["assets/toy_sorting/**"],
        commit_message="Upload env source code",
    )

    # Step 2: upload binary assets explicitly — bypasses .gitignore entirely
    # because we point folder_path directly at the assets directory.
    # delete_patterns removes stale files from previous uploads that no longer
    # exist locally (e.g. old Kitchen_Other/, InteractiveAsset/ folders).
    print("  [2/2] uploading binary assets (USD, STL, PNG) …")
    api.upload_folder(
        repo_id=HF_ENV_REPO,
        repo_type="model",
        folder_path=str(OUT_DIR),
        path_in_repo="assets/toy_sorting",
        delete_patterns=["assets/toy_sorting/Kitchen_Other/**", "assets/toy_sorting/InteractiveAsset/**"],
        commit_message="Upload binary assets (USD, STL, PNG)",
    )

    print(f"Upload complete → https://huggingface.co/{HF_ENV_REPO}")


def download() -> None:
    """Download assets/toy_sorting/ from the HF env repo."""
    from huggingface_hub import snapshot_download

    print(f"Downloading assets from {HF_ENV_REPO} → {OUT_DIR}")
    # local_dir=REPO_ROOT so the repo path assets/toy_sorting/... maps to
    # REPO_ROOT/assets/toy_sorting/... without double-nesting.
    snapshot_download(
        repo_id=HF_ENV_REPO,
        repo_type="model",
        local_dir=str(REPO_ROOT),
        allow_patterns=["assets/toy_sorting/**"],
    )
    print("Download complete.")


def ensure_assets() -> None:
    """Auto-download assets at env startup if missing."""
    if OUT_DIR.exists() and any(OUT_DIR.iterdir()):
        return
    print("[assets] assets/toy_sorting/ not found — downloading from HF Hub...")
    download()


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--extract", action="store_true", help="Extract from local source packs")
    group.add_argument("--upload", action="store_true", help="Upload env repo to HuggingFace Hub")
    group.add_argument("--download", action="store_true", help="Download assets from HuggingFace Hub")
    args = parser.parse_args()

    if args.extract:
        extract()
    elif args.upload:
        upload()
    elif args.download:
        download()
    else:
        ensure_assets()


if __name__ == "__main__":
    main()
