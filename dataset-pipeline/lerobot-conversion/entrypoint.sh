#!/bin/bash
set -euo pipefail

cd /workspace/dataset-pipeline/lerobot-conversion

uv sync
source .venv/bin/activate
exec "$@"
