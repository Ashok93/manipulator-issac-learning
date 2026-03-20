"""EnvHub task factory for toy sorting.

This is the stable entrypoint used by env.py at the repo root.
It drives the native Isaac Lab ToySortingEnv directly — no LeIsaac required.
"""

from __future__ import annotations

import gymnasium

from manipulator_learning.envs.toy_sorting_env import ToySortingEnv, ToySortingEnvCfg

TASK_ID = "ToySorting-v0"


def make_env(
    task: str = TASK_ID,
    n_envs: int = 1,
    **kwargs,
) -> gymnasium.vector.SyncVectorEnv:
    """Create and return a ``gymnasium.vector.SyncVectorEnv`` wrapping a single
    ``ToySortingEnv`` instance.

    The Isaac Lab environment is not fork-safe, so we wrap the pre-created
    instance rather than constructing it inside the worker lambda.

    Parameters
    ----------
    task:
        Task identifier. Must be ``"ToySorting-v0"``.
    n_envs:
        Number of parallel environments (currently only 1 is supported).
    **kwargs:
        Additional fields forwarded to ``ToySortingEnvCfg``.
        Raises ``TypeError`` for unrecognised keys.
    """
    if task != TASK_ID:
        raise ValueError(f"Unknown task '{task}'. Expected '{TASK_ID}'.")

    cfg = ToySortingEnvCfg(num_envs=n_envs)
    for key, val in kwargs.items():
        if not hasattr(cfg, key):
            raise TypeError(f"make_env() got unexpected keyword argument '{key}'")
        setattr(cfg, key, val)

    env = ToySortingEnv(cfg)
    return gymnasium.vector.SyncVectorEnv([lambda: env])
