#!/bin/bash
set -euo pipefail

cd /workspace/dataset-pipeline/isaac-mimic

if [[ -d /opt/IsaacLab ]]; then
    export ISAACLAB_ROOT=/opt/IsaacLab
fi

SYNC_ARGS=()
if [[ "${DATASET_MIMIC_WITH_MIMIC:-1}" == "1" ]]; then
    SYNC_ARGS+=(--extra mimic)
fi

uv sync "${SYNC_ARGS[@]}"
source .venv/bin/activate
exec "$@"
