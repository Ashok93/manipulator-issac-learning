"""EnvHub task factory for toy sorting.

This is the stable entrypoint used by env.py at the repo root.
It now drives the native Isaac Lab ToySortingEnv directly — no LeIsaac required.
"""

from __future__ import annotations

from manipulator_learning.envs.toy_sorting_env import ToySortingEnv, ToySortingEnvCfg

DEFAULT_TASK_ID = "ToySorting-v0"


def make_env(
    task: str | None = None,
    n_envs: int = 1,
    seed: int | None = None,
    **kwargs,
):
    """Create and return a ToySortingEnv.

    Returns a dict ``{suite_name: [env]}`` to stay compatible with the
    LeRobot EnvHub convention expected by callers.

    Parameters
    ----------
    task:
        Task identifier.  Only ``"ToySorting-v0"``, ``"toy_sorting"``, and
        ``"toy-sorting"`` are accepted.
    n_envs:
        Number of parallel environments (passed to ``ToySortingEnvCfg``).
    seed:
        Random seed (stored but not yet wired into Isaac Lab physics seed).
    **kwargs:
        Forwarded to ``ToySortingEnvCfg`` if they match known fields,
        otherwise ignored.
    """

    requested_task = task or DEFAULT_TASK_ID
    if requested_task not in {DEFAULT_TASK_ID, "toy_sorting", "toy-sorting"}:
        raise ValueError(
            f"Unsupported task '{requested_task}'. Expected '{DEFAULT_TASK_ID}'."
        )

    cfg = ToySortingEnvCfg(num_envs=n_envs)
    # Pass through any recognised cfg fields from kwargs
    for key, val in kwargs.items():
        if hasattr(cfg, key):
            setattr(cfg, key, val)

    env = ToySortingEnv(cfg)
    return {"toy_sorting": [env]}
