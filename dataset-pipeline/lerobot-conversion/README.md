# LeRobot Conversion

This package converts the final Mimic-generated HDF5 into a local LeRobot dataset.

## Local Setup

```bash
cd dataset-pipeline/lerobot-conversion
uv sync
```

## Usage

From the repo root:

```bash
docker compose run --rm dataset-convert dataset-convert \
  --input-file ../outputs/mimic/franka_demos_mimic.hdf5 \
  --repo-id AshDash93/franka-stack-cube \
  --output-root ../outputs/lerobot/AshDash93__franka-stack-cube \
  --robot-type franka \
  --fps 30
```
