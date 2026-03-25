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
uv sync --extra mimic --extra convert
```

For Docker:

```bash
docker build -t manipulator-dataset-pipeline .
docker run --rm -it -v "$PWD/..:/workspace" manipulator-dataset-pipeline dataset-pipeline inspect /workspace/dataset-pipeline/franka_demos.hdf5
```

If you need only the Isaac Lab Mimic tooling, sync the optional `mimic` extra:

```bash
uv sync --extra mimic
```

## Workflow

1. Inspect the raw HDF5 demo file.
2. Run Isaac Lab Mimic annotation.
3. Run Isaac Lab Mimic generation with cameras enabled.
4. Convert the final HDF5 into LeRobot format.

### 1. Inspect raw demos

```bash
docker compose run --rm dataset-pipeline dataset-pipeline inspect franka_demos.hdf5
```

### 2. Annotate demos

```bash
docker compose run --rm dataset-pipeline dataset-pipeline annotate \
  --task Isaac-Stack-Cube-Franka-IK-Rel-Visuomotor-Mimic-v0 \
  --input-file franka_demos.hdf5 \
  --output-file franka_demos_annotated.hdf5 \
  --enable-cameras \
  --device cpu
```

### 3. Generate Mimic dataset

```bash
docker compose run --rm dataset-pipeline dataset-pipeline generate \
  --task Isaac-Stack-Cube-Franka-IK-Rel-Visuomotor-Mimic-v0 \
  --input-file franka_demos_annotated.hdf5 \
  --output-file franka_demos_mimic.hdf5 \
  --enable-cameras \
  --headless \
  --device cpu
```

### 4. Convert to LeRobot

```bash
docker compose run --rm dataset-pipeline dataset-pipeline convert \
  --input-file franka_demos_mimic.hdf5 \
  --repo-id AshDash93/franka-stack-cube \
  --output-root ./lerobot/AshDash93__franka-stack-cube \
  --robot-type franka \
  --fps 30
```

The Dockerized `dataset-pipeline` service resolves Isaac Lab from its own uv-managed environment. No Isaac Lab checkout mount is needed.

## Recommended sequence

For the current Isaac Lab workflow:

1. Collect 10 successful raw demos in `teleop-vr/`.
2. Inspect the raw HDF5 in `dataset-pipeline/`.
3. Run `dataset-pipeline annotate` and `dataset-pipeline generate` to create the visuomotor HDF5.
4. Run `dataset-pipeline convert` to write a local LeRobot dataset under a mounted folder.
5. Point `train/` at that LeRobot dataset later.

## Planned Utilities

- wrappers around Isaac Lab `annotate_demos.py`
- wrappers around Isaac Lab Mimic dataset generation
- conversion helpers from Isaac HDF5 to LeRobot format
- dataset validation / sanity checks

This is the offline path for turning raw state-based demos into annotated and augmented datasets for training.
