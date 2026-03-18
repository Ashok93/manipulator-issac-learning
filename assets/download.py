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
SO_ARM_SRC_DIR = REPO_ROOT / "so_arm101"
OUT_DIR = REPO_ROOT / "assets" / "toy_sorting"

HF_ENV_REPO = os.environ.get("HF_ENV_REPO", "AshDash93/toy-sorting-env")

# Files to extract from LIGHTWHEEL_DIR → OUT_DIR (preserving relative structure)
LIGHTWHEEL_FILES = [
    "Table049/Table049.usd",
    "Table049/texture/T_Table049_BC001.png",
    "Table049/texture/T_Table049_N001.png",
    "Table049/texture/T_Table049_ORM001.png",
    "InteractiveAsset/SM_P_Flavour_02/Collected_SM_P_Flavour_02/Props/SM_P_Tray_01.usd",
    "Kitchen_Other/Kitchen_Box.usd",
    "Kitchen_Other/Kitchen_Disk001.usd",
    "Kitchen_Other/Kitchen_Disk002.usd",
]

LIGHTWHEEL_GLOBS = [
    "InteractiveAsset/SM_P_Flavour_02/Collected_SM_P_Flavour_02/Materials/**/*",
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
    if not LIGHTWHEEL_DIR.exists():
        sys.exit(
            f"[ERROR] Lightwheel directory not found: {LIGHTWHEEL_DIR}\n"
            "Download the pack and place it next to this repo first."
        )

    print(f"Extracting Lightwheel assets → {OUT_DIR}")
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    for rel in LIGHTWHEEL_FILES:
        src = LIGHTWHEEL_DIR / rel
        if not src.exists():
            print(f"  [WARN] missing: {rel}")
            continue
        _copy_file(src, OUT_DIR / rel)

    for pattern in LIGHTWHEEL_GLOBS:
        for src in LIGHTWHEEL_DIR.glob(pattern):
            if src.is_file():
                _copy_file(src, OUT_DIR / src.relative_to(LIGHTWHEEL_DIR))

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
    print("  [2/2] uploading binary assets (USD, STL, PNG) …")
    api.upload_folder(
        repo_id=HF_ENV_REPO,
        repo_type="model",
        folder_path=str(OUT_DIR),
        path_in_repo="assets/toy_sorting",
        commit_message="Upload binary assets (USD, STL, PNG)",
    )

    print(f"Upload complete → https://huggingface.co/{HF_ENV_REPO}")


def download() -> None:
    """Download assets/toy_sorting/ from the HF env repo."""
    from huggingface_hub import snapshot_download

    print(f"Downloading assets from {HF_ENV_REPO} → {OUT_DIR}")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    snapshot_download(
        repo_id=HF_ENV_REPO,
        repo_type="model",
        local_dir=str(OUT_DIR),
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
