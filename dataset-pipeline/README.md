# Dataset Pipeline

This folder holds the offline part of the Isaac Lab data workflow.

## Inputs

- Raw Isaac Lab HDF5 demos recorded in `teleop-vr/`

## Outputs

- Annotated HDF5 demos
- Mimic-augmented visual datasets
- LeRobot-formatted datasets for training

## Planned Utilities

- wrappers around Isaac Lab `annotate_demos.py`
- wrappers around Isaac Lab Mimic dataset generation
- conversion helpers from Isaac HDF5 to LeRobot format
- dataset validation / sanity checks

This is the offline path for turning raw state-based demos into annotated and augmented datasets for training.
