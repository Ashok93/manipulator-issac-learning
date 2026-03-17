# Manipulator Isaac Learning

Learning stack for manipulation tasks in Isaac Sim using LeRobot + LeIsaac EnvHub.

## Scope

- Simulation-first imitation learning for manipulation tasks.
- LeRobot dataset format v3 for demos.
- LeIsaac EnvHub environments and training loops.

## Layout

- `src/manipulator_learning/tasks/` custom tasks and wrappers.
- `scripts/` entrypoints for data collection and training.
- `env.py` EnvHub entrypoint (loadable via `lerobot.envs.factory.make_env`).

## Docker

```bash
docker compose build
docker compose up -d
docker compose exec sim bash
```

### Split Services

- `sim`: Isaac Sim + LeIsaac for teleop and data collection.
- `train`: PyTorch + LeRobot for model training.

Build or run a single service:

```bash
docker compose build sim
docker compose up -d sim
docker compose exec sim bash

docker compose build train
docker compose up -d train
docker compose exec train bash
```

## Dependencies

This repo is split by environment:
- `sim` uses `leisaac[isaaclab]` per official LeIsaac install guidance.
- `train` uses `lerobot==0.4.1`.
- Base package only pins `numpy==1.26.0` to avoid cross-env conflicts.

## Toy Sorting Task

We base the task on LeIsaac EnvHub's `LeIsaac-SO101-CleanToyTable-v0` and overlay
color-sorting prompts and colored bins/toys at runtime.
The EnvHub loader uses `LightwheelAI/leisaac_env:envs/so101_clean_toytable.py`.

### EnvHub Packaging

This repo is an EnvHub-compatible task repo. The entrypoint is `env.py` with a
`make_env` function. Load it via LeRobot EnvHub by pointing at this repo (and
pin to a commit for reproducibility).

List available EnvHub tasks:

```bash
python scripts/list_envs.py
```

Run the environment via EnvHub (random actions, for visual inspection):

```bash
python scripts/toy_sorting_envhub.py
```

Collect teleop demos into LeRobot Dataset v3:

```bash
python scripts/collect_toy_sorting_demos.py --device keyboard
```

Note: `collect_toy_sorting_demos.py` expects LeIsaac's teleop script to be available in the
installed package. Install LeIsaac from source if needed.
When loading EnvHub tasks, `trust_remote_code=True` is used. Pin to a commit hash if you
need reproducibility/security.
