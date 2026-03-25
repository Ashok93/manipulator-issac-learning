# Dataset Pipeline

This directory is split into two separate Python packages so the toolchains stay cleanly separated:

- `isaac-mimic/` for Isaac Lab annotation and Mimic generation
- `lerobot-conversion/` for HDF5 -> LeRobot conversion

The `dataset-mimic` container clones Isaac Lab into `/opt/IsaacLab` during image build, so the normal Mimic commands do not need a host checkout mount.

The shared folder-level convention is:

- raw demos: `dataset-pipeline/franka_demos.hdf5`
- intermediate outputs: `dataset-pipeline/outputs/mimic/`
- final LeRobot outputs: `dataset-pipeline/outputs/lerobot/`

## Local Setup

Use `uv` inside each package directory:

```bash
cd dataset-pipeline/isaac-mimic
uv sync --extra mimic

cd ../lerobot-conversion
uv sync
```

## Workflow

1. Collect raw demos in `teleop-vr/`.
2. Run `dataset-mimic inspect`, `dataset-mimic annotate`, and `dataset-mimic generate`.
3. Run `dataset-convert` on the Mimic-generated HDF5.
4. Train later from the LeRobot dataset.

## Package Entry Points

- `dataset-pipeline/isaac-mimic/README.md`
- `dataset-pipeline/lerobot-conversion/README.md`

## Compose Services

- `dataset-mimic` -> Isaac Lab / Mimic pipeline
- `dataset-convert` -> LeRobot conversion pipeline
