"""Isaac Lab sim server — runs the toy-sorting env and exposes it via ZMQ.

The lerobot container connects to this server to step the simulation,
receive observations, and collect demonstration data.

Usage (inside sim container):
    uv run python scripts/sim_server.py
    uv run python scripts/sim_server.py --headless
    uv run python scripts/sim_server.py --port 5555

The server blocks until the lerobot container sends a 'close' message
or the simulation window is closed.
"""

from __future__ import annotations

import argparse
from pathlib import Path

# ---------------------------------------------------------------------------
# AppLauncher must be created before any other isaaclab.* import
# ---------------------------------------------------------------------------
parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
parser.add_argument("--headless", action="store_true")
parser.add_argument("--port", type=int, default=5555, help="ZMQ REP port (default: 5555)")
args_cli = parser.parse_args()

from isaaclab.app import AppLauncher  # noqa: E402

app_launcher = AppLauncher(headless=args_cli.headless)
simulation_app = app_launcher.app

# ---------------------------------------------------------------------------
# Safe to import Isaac Lab now
# ---------------------------------------------------------------------------
import isaaclab.sim as sim_utils  # noqa: E402
from isaaclab.sim import SimulationContext  # noqa: E402
from manipulator_learning.envs.toy_sorting_env import ToySortingEnv, ToySortingEnvCfg  # noqa: E402
from manipulator_learning.envs.zmq_server import ZmqServer  # noqa: E402


def main() -> None:
    sim_cfg = sim_utils.SimulationCfg(dt=1.0 / 60.0)
    sim = SimulationContext(sim_cfg)
    sim.set_camera_view(eye=[0.8, -0.8, 1.2], target=[0.0, 0.0, 0.2])

    print("[sim_server] Building scene …")
    env = ToySortingEnv(ToySortingEnvCfg(num_envs=1))

    print("[sim_server] Resetting simulation …")
    sim.reset()
    env.reset()

    print(f"[sim_server] Ready — waiting for lerobot container on port {args_cli.port}")
    ZmqServer(env, port=args_cli.port).serve_forever(simulation_app)

    env.close()


if __name__ == "__main__":
    main()
    simulation_app.close()
