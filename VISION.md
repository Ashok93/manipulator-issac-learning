# Vision: Sim-to-Real Manipulation Pipeline

## End Goal

Build a full sim-only pipeline for manipulation policy training using VR hand tracking for data collection, imitation learning, and sim evaluation — all sticking with LeRobot standards.

The target task is **toy sorting** (colored objects → matching trays), but we're developing and proving the pipeline using **Franka cube stacking** in Isaac Lab as a well-supported benchmark environment.

## Pipeline

```
┌─────────────────────────────────────────────────────────────────────┐
│  1. Simulate                                                         │
│     Isaac Lab (Python 3.11, Isaac Lab 2.3.2 / Isaac Sim 5.1)        │
│     Current: FrankaCubeStack env (IK-Rel mode)                      │
│     Target:  ToySortingEnv (custom, SO-ARM 101)                      │
└─────────────────┬───────────────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│  2. Collect Demos via VR Hand Tracking                               │
│     Quest 3 → ALVR → SteamVR → OpenXR → Isaac Lab OpenXRDevice      │
│     • Bare-metal on Vast.ai KVM GPU VM                              │
│     • teleop_se3_agent.py --dataset_file --num_demos                 │
│     • Records HDF5 with images (cameras TBD) + state + actions       │
└─────────────────┬───────────────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│  3. Augment with Isaac Lab Mimic                                     │
│     • Few human VR demos (~10-20) → thousands of augmented demos     │
│     • Trajectory generalization across object positions              │
└─────────────────┬───────────────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│  4. Convert to LeRobot Format                                        │
│     HDF5 → LeRobot Dataset v3                                        │
│     Push to HuggingFace Hub (AshDash93)                              │
└─────────────────┬───────────────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│  5. Train Policy                                                     │
│     lerobot train policy=act (or diffusion_policy)                   │
│     Loads dataset from HuggingFace Hub, saves checkpoint             │
└─────────────────┬───────────────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│  6. Evaluate in Sim                                                  │
│     Roll out policy in Isaac Lab env                                 │
│     Log success rate, push metrics to HuggingFace Hub                │
└─────────────────────────────────────────────────────────────────────┘
```

## Current Status

| Phase | Status | Description |
|-------|--------|-------------|
| VR Teleop | **Done** | Quest 3 + ALVR + SteamVR + OpenXR hand tracking working |
| Sim env | **Done** | Franka cube stacking in Isaac Sim VR, relative mode |
| Cameras | Next | Add front + wrist cameras to env config |
| Demo collection | Next | Record HDF5 demos with `--dataset_file --num_demos` |
| Mimic augmentation | Planned | Isaac Lab Mimic to scale demos |
| HDF5 → LeRobot | Planned | Converter script |
| Training | Planned | ACT / Diffusion Policy via LeRobot |
| Evaluation | Planned | Closed-loop policy rollout in sim |

## Infrastructure

- **VR teleop:** Vast.ai KVM GPU VM, bare-metal (no Docker for teleop-vr)
- **Sim runtime:** `teleop-vr/` package — `bare-install.sh` + `run_teleop.sh`
- **Training:** `train/` package — LeRobot (Python 3.12, uv)
- **HuggingFace user:** AshDash93

## Original Approach (On Hold)

Phone teleoperation via iPhone HEBI app + ZMQ + SO-ARM 101 toy sorting env. Built and working but complex and fragile. VR hand tracking is a superior teleop method and takes priority.

## Key Technical Decisions

- **Relative mode teleop** — avoids robot jump-to-hand on startup
- **Isaac Lab native recording** → HDF5 → convert to LeRobot (simpler than recording directly in LeRobot format)
- **Isaac Lab Mimic** for demo augmentation (few real demos → large dataset)
- **No LeIsaac dependency** — their data pipeline is useful reference but we build directly on Isaac Lab + LeRobot
- **Possible contribution to LeIsaac** — add VR/OpenXR as a teleop device option

## Success Metric (Target)

> Franka arm stacks 3 cubes correctly in simulation, trained purely from VR-collected demos, evaluated over 50 random seeds. Target success rate ≥ 80%.
