#!/bin/bash
set -euo pipefail

cd /workspace/dataset-pipeline

SYNC_ARGS=()
if [[ "${DATASET_PIPELINE_WITH_MIMIC:-1}" == "1" ]]; then
    SYNC_ARGS+=(--extra mimic)
fi
if [[ "${DATASET_PIPELINE_WITH_CONVERT:-0}" == "1" ]]; then
    SYNC_ARGS+=(--extra convert)
fi

uv sync "${SYNC_ARGS[@]}"
source .venv/bin/activate
exec "$@"
