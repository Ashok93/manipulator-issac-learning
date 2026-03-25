# Isaac Mimic

This package owns the Isaac Lab-backed stages of the dataset workflow:

- inspect raw Isaac Lab HDF5 demos
- annotate demos for Mimic
- generate visuomotor Mimic datasets

## Local Setup

```bash
cd dataset-pipeline/isaac-mimic
uv sync --extra mimic
```

## Usage

From the repo root:

```bash
docker compose run --rm dataset-mimic dataset-mimic inspect ../franka_demos.hdf5
```

Annotate:

```bash
docker compose run --rm dataset-mimic dataset-mimic annotate \
  --task Isaac-Stack-Cube-Franka-IK-Rel-Visuomotor-Mimic-v0 \
  --input-file ../franka_demos.hdf5 \
  --output-file ../outputs/mimic/franka_demos_annotated.hdf5 \
  --enable-cameras \
  --device cpu
```

Generate:

```bash
docker compose run --rm dataset-mimic dataset-mimic generate \
  --task Isaac-Stack-Cube-Franka-IK-Rel-Visuomotor-Mimic-v0 \
  --input-file ../outputs/mimic/franka_demos_annotated.hdf5 \
  --output-file ../outputs/mimic/franka_demos_mimic.hdf5 \
  --enable-cameras \
  --headless \
  --device cpu
```

If your Isaac Lab install does not expose the Mimic runner scripts directly, pass `--isaaclab-root` to a source checkout that contains `scripts/imitation_learning/isaaclab_mimic/`.
