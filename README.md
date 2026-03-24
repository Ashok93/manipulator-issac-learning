---
license: cc-by-nc-4.0
library_name: lerobot
tags:
  - robotics
  - manipulation
  - isaac-lab
  - lerobot
  - simulation
---

# Manipulator Isaac Learning

This repository is now organized around an Isaac Lab-first pipeline:

1. `teleop-vr/` launches the VR runtime on a bare-metal GPU VM and records raw demonstrations.
2. `sim/` contains the custom Isaac Lab environments, scenes, assets, and env registration code.
3. `dataset-pipeline/` will expand raw Isaac HDF5 demos with Mimic and convert them to LeRobot format.
4. `train/` will consume the finished dataset and train policies with LeRobot.
5. `legacy-phone-teleop/` keeps the old iPhone/HEBI collection path around only as archived reference.

## Current Focus

The active path is:

`Quest 3 -> ALVR -> SteamVR -> OpenXR -> Isaac Lab env -> raw HDF5 demos -> Mimic -> LeRobot dataset -> training`

The old phone teleop flow is no longer the primary path.

## Folder Guide

| Folder | Purpose |
|--------|---------|
| `teleop-vr/` | Bare-metal VR install, launch, and recording session orchestration |
| `sim/` | Isaac Lab environment package: envs, tasks, assets, scene configs |
| `dataset-pipeline/` | Offline augmentation and dataset conversion tools |
| `train/` | Future LeRobot training-only code |
| `legacy-phone-teleop/` | Archived iPhone/HEBI collection code |

## Notes

- The repo still contains multiple phases of the pipeline because we are migrating from the old workflow to the Isaac Lab-first workflow.
- `teleop-vr/` is the main runtime entrypoint for demo collection.
- `dataset-pipeline/` is intentionally separate so Mimic, conversion, and validation can run headless.
- `train/` is kept for later; it should only matter once the final dataset format is settled.

