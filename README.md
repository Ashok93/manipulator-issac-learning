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
# 1. Install
uv sync --extra sim

# 2. Visualise (requires Isaac Sim)
/isaac-sim/python.sh scripts/visualize_env.py

# 3. Or via Docker
docker compose run sim /isaac-sim/python.sh /workspace/scripts/visualize_env.py
```

## Assets

Scene assets (USD, STL, textures) are stored in this repo via Git LFS and downloaded
automatically when the environment initialises.

On a developer machine with the original Lightwheel pack:

```bash
uv run assets/download.py --extract   # populate assets/toy_sorting/ locally
uv run assets/download.py --upload    # push to HF Hub (needs HF_TOKEN in .env)
```

On a server / Docker container — assets are pulled automatically from HF Hub
(`AshDash93/toy-sorting-env`) at env startup.

## Layout

```
env.py                          # EnvHub entrypoint (make_env)
src/manipulator_learning/
  envhub.py                     # thin factory
  envs/
    toy_sorting_env.py          # Isaac Lab DirectRLEnv
    so_arm101_cfg.py            # ArticulationCfg for SO-ARM 101
    zmq_server.py               # Phase 2 stub (sim↔train bridge)
assets/
  download.py                   # asset extract / upload / download
scripts/
  visualize_env.py              # run 600 steps, X11 GUI
```

## Docker

```bash
docker compose build sim
docker compose run sim /isaac-sim/python.sh /workspace/scripts/visualize_env.py
```

## Attribution

3D kitchen scene assets (`assets/toy_sorting/Table049/`, `SM_P_Tray_01.usd`,
`Kitchen_Box.usd`, `Kitchen_Disk*.usd`) are derived from the
[Lightwheel Kitchen](https://github.com/parzival2108/Lightwheel_Kitchen) pack
by Lightwheel AI, licensed under
[CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/).

SO-ARM 101 URDF and meshes are from
[TheRobotStudio/SO-ARM100](https://github.com/TheRobotStudio/SO-ARM100).
