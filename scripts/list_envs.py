"""List available LeIsaac EnvHub environments."""

from __future__ import annotations

from manipulator_learning.leisaac_tools import run_list_envs


def main() -> None:
    run_list_envs()


if __name__ == "__main__":
    main()
