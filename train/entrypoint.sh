#!/bin/bash
set -e

cd /workspace/train
uv sync

# libhebi.so requires an executable stack which modern Linux kernels reject.
# patchelf --clear-execstack removes the flag. Idempotent — safe to run every time.
HEBI_SO=".venv/lib/python3.12/site-packages/hebi/lib/linux_x86_64/libhebi.so.2.21"
[ -f "$HEBI_SO" ] && patchelf --clear-execstack "$HEBI_SO"

source .venv/bin/activate
exec "$@"
