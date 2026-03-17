"""EnvHub entrypoint for toy-sorting task.

This module follows the LeRobot EnvHub contract: provide a `make_env` function
at repo root so EnvHub can load the task via trust_remote_code.
"""

from __future__ import annotations

from manipulator_learning.envhub import make_env

__all__ = ["make_env"]
