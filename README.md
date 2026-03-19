---
license: cc-by-nc-4.0
library_name: lerobot
tags:
  - robotics
  - manipulation
  - isaac-lab
  - lerobot
  - so-arm101
  - simulation
---

# SO-ARM 101 Toy Sorting — Isaac Lab EnvHub

Simulation-first manipulation learning with Isaac Lab + LeRobot.
SO-ARM 101 sorts colored toys into matching trays on a wooden kitchen table.

## LeRobot EnvHub

This repo follows the [LeRobot EnvHub](https://huggingface.co/docs/lerobot/en/envhub) standard.
`env.py` at the root exposes `make_env()` and is loadable via `trust_remote_code=True`.

```python
from lerobot.envs.factory import make_env
envs = make_env("AshDash93/toy-sorting-env", trust_remote_code=True)
```

## Quick Start

```bash
# 1. Download scene assets from HuggingFace Hub
docker compose run sim uv run python assets/download.py --download

# 2. Install Isaac Lab + Isaac Sim (pip, Linux only)
docker compose run sim uv sync --extra sim

# 3. Visualise (headless)
docker compose run sim uv run python scripts/visualize_env.py --headless

# 3b. Visualise with GUI (X forwarding — run these on the server first)
#     ssh -X user@your-server-ip
#     xhost +local:docker
docker compose run sim uv run python scripts/visualize_env.py
```

## Assets

On a developer machine with the original Lightwheel packs, extract assets locally:

```bash
uv run python assets/download.py --extract   # populate assets/toy_sorting/
uv run python assets/download.py --upload    # push to HF Hub (needs HF_TOKEN in .env)
```

## Layout

```
env.py                          # EnvHub entrypoint (make_env)
src/manipulator_learning/
  envhub.py                     # thin factory
  envs/
    toy_sorting_env.py          # ToySortingEnv (InteractiveScene-backed gym env)
    toy_sorting_scene_cfg.py    # InteractiveSceneCfg: table + robot + bowls + toys
    so_arm101_cfg.py            # ArticulationCfg for SO-ARM 101
    test_scene_cfg.py           # minimal scene for robot-only testing (no USD assets)
    zmq_server.py               # Phase 2 stub (sim↔train bridge)
  tasks/toy_sorting/
    task_spec.py                # high-level task spec (colors, bin names, instruction)
assets/
  download.py                   # asset extract / upload / download
scripts/
  visualize_env.py              # run full toy-sorting scene until window closed
  layout_editor.py              # physics-frozen scene editor; exports layout to USDA
  test_robot.py                 # minimal robot URDF test (no scene assets required)
  inspect_assets.py             # inspect USD asset bounding boxes (usd-core only)
```

## Attribution

Table asset (`assets/toy_sorting/Table049/`) is from the Lightwheel Kitchen pack
by Lightwheel AI, licensed under
[CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/).

Toy shapes and sorting containers (`assets/toy_sorting/Kit1/`) are from the
Lightwheel Toyroom pack by Lightwheel AI, licensed under
[CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/).

SO-ARM 101 URDF and meshes are from
[TheRobotStudio/SO-ARM100](https://github.com/TheRobotStudio/SO-ARM100).
