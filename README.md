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

# SO-ARM 101 Toy Sorting — Isaac Lab + LeRobot

The SO-ARM 101 sorts colored toys into matching colored boxes on a table,
trained via imitation learning from phone-teleoperated demonstrations.

Two containers communicate via ZMQ: `sim` runs Isaac Lab (Python 3.11),
`lerobot` runs LeRobot demo collection (Python 3.12).
Teleoperation runs locally on your Mac/laptop via iPhone + HEBI.

## Prerequisites

| What | Where |
|------|-------|
| Linux server with NVIDIA GPU | Remote (e.g. vast.ai) |
| Docker + NVIDIA Container Toolkit | Remote server |
| Mac/laptop with Python 3.12 + `uv` | Local |
| iPhone + [HEBI Mobile I/O](https://apps.apple.com/app/hebi-mobile-i-o/id1455735469) | Local (same WiFi as Mac) |
| [Tailscale](https://tailscale.com) | Installed on both server and Mac |

## Network Setup

Install Tailscale on the remote server and your local Mac so they can reach
each other. The iPhone talks to your Mac over local WiFi (HEBI uses mDNS
discovery), and the Mac talks to the sim server over Tailscale.

```
iPhone  ──(WiFi/HEBI)──>  Mac  ──(Tailscale/ZMQ)──>  Server (sim)
```

**Server:**
```bash
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up
tailscale ip -4          # note this IP, e.g. 100.x.y.z
```

**Mac:**
Install Tailscale from https://tailscale.com/download and sign in with the
same account.

## Server Setup (Sim)

```bash
git clone https://github.com/Ashok93/manipulator-issac-learning
cd manipulator-issac-learning

# Build the sim container
docker compose build sim

# Allow X forwarding (only needed if running with GUI)
xhost +local:docker

# Start the sim server
# First run installs Isaac Lab (~15 GB) and downloads assets from HF Hub.
# The venv is saved to sim/.venv/ via bind mount and reused on subsequent runs.

# With GUI:
docker compose run sim uv run --extra sim python scripts/sim_server.py

# Headless (no monitor):
docker compose run sim uv run --extra sim python scripts/sim_server.py --headless
```

Wait for:
```
[sim_server] Ready — waiting for lerobot container on port 5555
```

## Local Setup (Teleop + Data Collection)

On your Mac, in a separate terminal:

```bash
cd manipulator-issac-learning/train

# Install dependencies (first time only)
uv sync

# Start demo collection — replace SIM_HOST with your server's Tailscale IP
SIM_HOST=100.x.y.z uv run python scripts/collect_demos.py \
    --repo-id AshDash93/toy-sorting-demos \
    --num-episodes 20
```

## iPhone Controls

1. Open HEBI Mobile I/O on your iPhone (same WiFi as your Mac).
2. The app auto-discovers the server — no IP entry needed.

**Calibration:** Hold the phone screen-up, top edge toward the robot, then hold B1.

| Control | Action |
|---------|--------|
| B1 (hold) | Enable teleoperation (calibrates on first press) |
| A3 (push forward) | Close gripper |
| A3 (pull back) | Open gripper |

**Per episode:** Press Enter when prompted → hold B1 to control the robot →
sort toys into matching boxes → Ctrl+C to end the episode.

## LeRobot EnvHub

This repo follows the [LeRobot EnvHub](https://huggingface.co/docs/lerobot/envhub) standard.
Load the environment directly from HuggingFace Hub:

```python
from lerobot.envs.factory import make_env
envs = make_env("AshDash93/toy-sorting-env", trust_remote_code=True)
```

Assets are hosted on HF Hub and auto-downloaded on first run.
No HF token needed for download — only for `push_to_hub()`.

## Project Layout

```
sim/
  env.py                            # EnvHub entrypoint (make_env)
  pyproject.toml                    # Isaac Lab + sim dependencies (Python 3.11)
  Dockerfile
  scripts/
    sim_server.py                   # ZMQ server — exposes env to lerobot
  assets/
    download.py                     # extract/upload/download assets (HF Hub)
  src/manipulator_learning/
    envhub.py                       # make_env() factory
    envs/
      toy_sorting_env.py            # ToySortingEnv (gymnasium.Env)
      toy_sorting_scene_cfg.py      # scene: table + robot + toys + boxes + camera
      so_arm101_cfg.py              # SO-ARM 101 ArticulationCfg
      zmq_server.py                 # ZMQ REP server
train/
  pyproject.toml                    # LeRobot + teleop dependencies (Python 3.12)
  Dockerfile
  scripts/
    collect_demos.py                # iPhone teleop → IK → ZMQ → dataset
docker-compose.yml
```

## Attribution

- Table (`Table049/`) — Lightwheel Kitchen pack by Lightwheel AI, [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/)
- Toy shapes and containers (`Kit1/`) — Lightwheel Toyroom pack by Lightwheel AI, [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/)
- SO-ARM 101 URDF and meshes — [TheRobotStudio/SO-ARM100](https://github.com/TheRobotStudio/SO-ARM100)
