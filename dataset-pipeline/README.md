# Dataset Pipeline

This folder holds the offline part of the Isaac Lab data workflow.

## Inputs

- Raw Isaac Lab HDF5 demos recorded in `teleop-vr/`

## Outputs

- Annotated HDF5 demos
- Mimic-augmented visual datasets
- LeRobot-formatted datasets for training

## Environment

Use `uv` for Python dependencies. For local use:

```bash
cd dataset-pipeline
uv sync
```

For Docker:

```bash
docker build -t manipulator-dataset-pipeline .
docker run --rm -it -v "$PWD/..:/workspace" manipulator-dataset-pipeline dataset-pipeline inspect /workspace/dataset-pipeline/franka_demos.hdf5
```

If you need LeRobot conversion support, sync the optional `convert` extra:

```bash
uv sync --extra convert
```

## Workflow

1. Inspect the raw HDF5 demo file.
2. Run Isaac Lab Mimic annotation.
3. Run Isaac Lab Mimic generation with cameras enabled.
4. Convert the final HDF5 into LeRobot format.

Example commands:

```bash
dataset-pipeline inspect ./franka_demos.hdf5

dataset-pipeline mimic \
  --task Isaac-Stack-Cube-Franka-IK-Rel-Visuomotor-Mimic-v0 \
  --input-file ./franka_demos.hdf5 \
  --annotated-file ./annotated_dataset.hdf5 \
  --generated-file ./generated_dataset.hdf5 \
  --enable-cameras \
  --device cpu

dataset-pipeline convert \
  --input-file ./generated_dataset.hdf5 \
  --repo-id AshDash93/franka-stack-cube \
  --robot-type franka \
  --fps 30
```

## Planned Utilities

- wrappers around Isaac Lab `annotate_demos.py`
- wrappers around Isaac Lab Mimic dataset generation
- conversion helpers from Isaac HDF5 to LeRobot format
- dataset validation / sanity checks

This is the offline path for turning raw state-based demos into annotated and augmented datasets for training.
