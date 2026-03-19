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

Simulation-first manipulation learning.
The SO-ARM 101 sorts colored toys into matching colored boxes on a wooden table.

**Architecture:** Two Docker containers communicate via ZMQ — `sim` runs Isaac Lab (Python 3.11), `lerobot` runs LeRobot demo collection with iPhone teleoperation (Python 3.12).

---

## Prerequisites

- Linux host with NVIDIA GPU (tested on vast.ai A100/RTX nodes)
- Docker + NVIDIA Container Toolkit (`nvidia-docker2`)
- `docker compose` (v2)
- iPhone with [HEBI Mobile I/O](https://apps.apple.com/app/hebi-mobile-i-o/id1455735469) (free, App Store)
- [Tailscale](https://tailscale.com) if iPhone and server are on different networks (e.g. vast.ai)

---

## Fresh vast.ai VM Setup

```bash
# 1. Clone the repo
git clone https://github.com/AshDash93/manipulator-issac-learning
cd manipulator-issac-learning

# 2. Install Tailscale (so your iPhone can reach the VM)
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up

# 3. Note your Tailscale IP — you will enter this in the HEBI app
tailscale ip -4
# e.g. 100.x.y.z

# 4. Build containers
docker compose build

# 5. Assets are auto-downloaded on first run — no manual step needed.
#    (pulled from HuggingFace Hub: AshDash93/toy-sorting-env)
```

No HuggingFace token is needed for asset download or demo collection.
A token is only required when you later run `push_to_hub()` to publish your dataset.

---

## Collecting Demonstrations

Open **two terminals** on the VM.

**Terminal 1 — start the sim server:**

`--extra sim` is required — it installs Isaac Lab + Isaac Sim into the venv on first run
(~15 GB download from nvidia's PyPI, takes a while). The venv is saved to `.venv/` on
the host via the bind mount and reused on all subsequent runs.

```bash
# Headless (no GUI) — use this on vast.ai with no monitor attached
docker compose run sim uv run --extra sim python scripts/sim_server.py --headless

# With Isaac UI forwarded to your local machine — see X Forwarding section below
docker compose run sim uv run --extra sim python scripts/sim_server.py
```

The server downloads assets automatically on first run, then prints:
```
[sim_server] Ready — waiting for lerobot container on port 5555
```

**Terminal 2 — start demo collection:**

```bash
docker compose run lerobot uv run python scripts/collect_demos.py \
    --repo-id AshDash93/toy-sorting-demos \
    --num-episodes 20
```

The script connects to the sim server and waits for your iPhone.

---

## Isaac UI (with display)

To run with the Isaac Sim GUI, allow Docker to use the host display first:

```bash
xhost +local:docker
docker compose run sim uv run --extra sim python scripts/sim_server.py
```

For headless servers (no display attached) just use `--headless` — no xhost needed.

---

## iPhone / Tailscale Setup

### One-time Tailscale setup

1. Install [Tailscale](https://tailscale.com/download) on your iPhone.
2. Sign in with the same account you used on the VM.
3. Both devices will appear in your tailnet — they can reach each other directly.

### HEBI Mobile I/O app

1. Install [HEBI Mobile I/O](https://apps.apple.com/app/hebi-mobile-i-o/id1455735469) (free).
2. Open the app → tap the **+** button → enter your VM's Tailscale IP (e.g. `100.x.y.z`).
3. The app connects automatically when `collect_demos.py` starts (it starts its own HEBI server).

### Calibration

Hold the phone **screen-up**, **top edge pointing toward the robot**, then **hold B1**.
This sets the current phone orientation as the zero reference.
After calibration the phone controls the robot end-effector in Cartesian space.

### Controls

| Control | Action |
|---------|--------|
| B1 (hold) | Enable teleoperation. Release to freeze. |
| A3 (analog, push forward) | Close gripper |
| A3 (analog, pull back) | Open gripper |

### Recording workflow per episode

1. Press **Enter** in Terminal 2 when prompted.
2. Pick up phone, hold B1 to calibrate, then control the robot.
3. Sort all toys into matching colored boxes.
4. Press **Ctrl+C** in Terminal 2 (or let episode time out) to end the episode.
5. Repeat for the next episode.

---

## Viewing Collected Data

Demos are saved locally inside the lerobot container at `/data/<repo-id>/`.
Mount a host volume in `docker-compose.yml` (already configured as `./data`) to access them:

```bash
ls ./data/
# AshDash93/toy-sorting-demos/
```

To push to HuggingFace Hub when ready, uncomment `dataset.push_to_hub()` in
`train/scripts/collect_demos.py` and set `HF_TOKEN` in your `.env` file:

```bash
echo "HF_TOKEN=hf_..." >> .env
docker compose run lerobot uv run python scripts/collect_demos.py \
    --repo-id AshDash93/toy-sorting-demos \
    --num-episodes 20
```

---

## LeRobot EnvHub

This repo follows the [LeRobot EnvHub](https://huggingface.co/docs/lerobot/en/envhub) standard.
`env.py` at the root exposes `make_env()`:

```python
from lerobot.envs.factory import make_env
envs = make_env("AshDash93/toy-sorting-env", trust_remote_code=True)
```

---

## Project Layout

```
env.py                              # EnvHub entrypoint (make_env)
scripts/
  sim_server.py                     # Isaac Lab sim server — exposes env via ZMQ
assets/
  download.py                       # auto-download assets from HF Hub on first run
src/manipulator_learning/
  envhub.py                         # make_env() factory (LeRobot EnvHub standard)
  envs/
    toy_sorting_env.py              # ToySortingEnv (gymnasium.Env, InteractiveScene)
    toy_sorting_scene_cfg.py        # scene: table + robot + toys + boxes + camera
    so_arm101_cfg.py                # SO-ARM 101 ArticulationCfg
    zmq_server.py                   # ZMQ REP server (sim side)
train/
  Dockerfile                        # Python 3.12 + LeRobot container
  pyproject.toml                    # lerobot, pyzmq, msgpack deps
  scripts/
    collect_demos.py                # iPhone teleop → ZMQ → dataset recording
```

---

## Attribution

Table asset (`assets/toy_sorting/Table049/`) — Lightwheel Kitchen pack by Lightwheel AI,
[CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/).

Toy shapes and sorting containers (`assets/toy_sorting/Kit1/`) — Lightwheel Toyroom pack by
Lightwheel AI, [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/).

SO-ARM 101 URDF and meshes — [TheRobotStudio/SO-ARM100](https://github.com/TheRobotStudio/SO-ARM100).
