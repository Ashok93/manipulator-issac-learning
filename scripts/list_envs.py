"""List available LeIsaac EnvHub environments."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def _find_list_envs_script() -> Path:
    import leisaac

    root = Path(leisaac.__file__).resolve().parent
    candidates = list(root.rglob("list_envs.py"))
    if not candidates:
        raise FileNotFoundError(
            "list_envs.py not found in leisaac package. "
            "Ensure leisaac is installed from source with scripts included."
        )
    return candidates[0]


def main() -> None:
    script_path = _find_list_envs_script()
    subprocess.run([sys.executable, str(script_path)], check=True)


if __name__ == "__main__":
    main()
