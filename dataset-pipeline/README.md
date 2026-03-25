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
  --device cpu \
  --isaaclab-root ~/IsaacLab

dataset-pipeline convert \
  --input-file ./generated_dataset.hdf5 \
  --repo-id AshDash93/franka-stack-cube \
  --output-root ./lerobot/AshDash93__franka-stack-cube \
  --robot-type franka \
  --fps 30
```

If you prefer Docker, run the offline pipeline container for inspection and conversion:

```bash
docker compose run --rm dataset-pipeline dataset-pipeline inspect franka_demos.hdf5
docker compose run --rm dataset-pipeline dataset-pipeline convert \
  --input-file franka_demos.hdf5 \
  --repo-id AshDash93/franka-stack-cube \
  --output-root ./lerobot/AshDash93__franka-stack-cube \
  --robot-type franka \
  --fps 30
```

The Mimic stage needs access to your Isaac Lab checkout because it shells out to:

```bash
~/IsaacLab/isaaclab.sh -p scripts/imitation_learning/isaaclab_mimic/annotate_demos.py ...
~/IsaacLab/isaaclab.sh -p scripts/imitation_learning/isaaclab_mimic/generate_dataset.py ...
```

If you run `dataset-pipeline mimic` in Docker, mount the Isaac Lab checkout into the container and pass `--isaaclab-root` accordingly.

## Recommended sequence

For the current Isaac Lab workflow:

1. Collect 10 successful raw demos in `teleop-vr/`.
2. Inspect the raw HDF5 in `dataset-pipeline/`.
3. Run `dataset-pipeline mimic` to annotate and generate the visuomotor dataset.
4. Run `dataset-pipeline convert` to write a local LeRobot dataset under a mounted folder.
5. Point `train/` at that LeRobot dataset later.

## Planned Utilities

- wrappers around Isaac Lab `annotate_demos.py`
- wrappers around Isaac Lab Mimic dataset generation
- conversion helpers from Isaac HDF5 to LeRobot format
- dataset validation / sanity checks

This is the offline path for turning raw state-based demos into annotated and augmented datasets for training.
