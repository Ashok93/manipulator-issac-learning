# Single Dockerfile for the sim container.
# Base image ships Isaac Lab 2.3.2 (Python 3.11) with Isaac Sim pre-installed.
FROM nvcr.io/nvidia/isaac-lab:2.3.2

# Install our package and sim extras into the Isaac Lab Python environment.
# Isaac Sim uses /isaac-sim/python.sh which activates its own venv; we install
# into that same site-packages so imports work without PYTHONPATH tricks.
WORKDIR /workspace

# Copy package metadata only (assets are volume-mounted, never COPYed).
COPY pyproject.toml ./
COPY src/ ./src/

RUN /isaac-sim/python.sh -m pip install --no-cache-dir -e ".[sim]"

# Default: drop into an interactive shell so users can run scripts manually.
CMD ["/bin/bash"]
