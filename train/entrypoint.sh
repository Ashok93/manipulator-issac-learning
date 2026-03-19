#!/bin/bash
set -e

# Install/sync deps into the bind-mounted workspace venv at runtime.
uv sync

# libhebi.so is compiled with an executable stack requirement which the Linux
# kernel rejects. Clear the flag once after installation so dlopen() works.
HEBI_SO=$(find /workspace/train/.venv -name "libhebi.so.2.*" -type f 2>/dev/null | head -1)
if [ -n "$HEBI_SO" ]; then
    patchelf --clear-execstack "$HEBI_SO"
fi

exec "$@"
