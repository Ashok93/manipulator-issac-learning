# Vision: SO-ARM 101 Toy-Sorting Pipeline

## End Goal

Train a manipulation policy that picks up colored toy objects and drops them
into matching colored trays, using imitation learning from teleoperated demos
recorded in Isaac Sim.

## Pipeline

```
┌─────────────────────────────────────────────────────────────────────┐
│  1. Simulate                                                         │
│     Isaac Lab ToySortingEnv (Python 3.11 / Isaac Lab 2.3.2)         │
│     • Wooden table + SO-ARM 101                                      │
│     • 3 colored trays  (red | green | blue)                          │
│     • 9 colored toys   (3 per color, randomized each episode)        │
└─────────────────┬───────────────────────────────────────────────────┘
                  │  Phase 2: ZMQ REP :5555
                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│  2. Collect Demos                                                    │
│     LeRobot / SpaceMouse teleop client (Python 3.12)                 │
│     • Sends joint targets to sim via ZMQ                             │
│     • Streams obs/actions into LeRobot Dataset v3 format             │
│     • Pushes dataset to HuggingFace Hub                              │
└─────────────────┬───────────────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│  3. Augment Dataset (optional)                                       │
│     • Background swap, color jitter, domain randomization           │
│     • Re-label with reward signal for RL fine-tuning                 │
└─────────────────┬───────────────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│  4. Train Policy                                                     │
│     lerobot train policy=act  (or diffusion_policy)                  │
│     • Loads dataset from HuggingFace Hub                             │
│     • Saves checkpoint to Hub                                        │
└─────────────────┬───────────────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│  5. Evaluate in Sim                                                  │
│     • Roll out policy in ToySortingEnv                               │
│     • Log success rate (sort 3 toys correctly in <60 s)             │
│     • Push eval metrics to HuggingFace Hub                           │
└─────────────────────────────────────────────────────────────────────┘
```

## Container Architecture

```
┌────────────────────────────────────────┐    ┌──────────────────────────────────────┐
│  sim  (isaac-lab:2.3.2, Python 3.11)   │    │  train  (python:3.12-slim + lerobot) │
│  Isaac Lab ToySortingEnv               │◄──►│  LeRobot training / data collection  │
│  ZMQ REP server :5555  (Phase 2)       │ZMQ │  IsaacGymClient gymnasium wrapper    │
│  X11 GUI for visualization             │    │  HuggingFace dataset push            │
└────────────────────────────────────────┘    └──────────────────────────────────────┘
```

## Phases

| Phase | Status | Description |
|-------|--------|-------------|
| 1 | **Done** | Isaac Lab env with real USD assets; X11 visualization |
| 2 | Scaffolded | ZMQ bridge + LeRobot demo collection client |
| 3 | Planned | Dataset augmentation pipeline |
| 4 | Planned | ACT / Diffusion Policy training with LeRobot |
| 5 | Planned | Closed-loop evaluation + HF metrics push |

## Asset Strategy

Assets live outside git (large binary files).  Two distribution paths:

1. **Developer machine**: `python assets/download.py --extract` copies the
   needed USD files from the local `Lightwheel_Xx8T7EPOMd_KitchenRoom/` pack.
2. **Docker / CI**: `python assets/download.py --download` fetches the
   pre-extracted subset from HuggingFace Hub (`HF_ASSET_REPO` env var).

Neither the git repo nor the Docker image contains asset files directly.

## Success Metric (Phase 5 target)

> Place all 9 toys into their correct color-matched tray within 60 seconds,
> measured over 50 random seeds.  Target success rate ≥ 80 %.
