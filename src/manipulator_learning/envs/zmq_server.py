"""ZMQ REP server — exposes the toy-sorting env over TCP.

Protocol
--------
All messages are msgpack-encoded dicts sent over a ZMQ REP socket.

Request types
~~~~~~~~~~~~~
reset:
    {"type": "reset"}
    → {"obs": <encoded_obs>}

step:
    {"type": "step", "action": [float, ...]}  # 6 joint positions
    → {"obs": <encoded_obs>, "reward": float, "terminated": bool, "truncated": bool}

close:
    {"type": "close"}
    → {"status": "ok"}

Observation encoding
~~~~~~~~~~~~~~~~~~~~
Each observation key maps to {"data": bytes, "dtype": str, "shape": [int, ...]}.
The client reconstructs arrays with np.frombuffer(data, dtype=dtype).reshape(shape).
"""

from __future__ import annotations

import numpy as np


def _encode_obs(obs: dict) -> dict:
    return {
        k: {"data": v.tobytes(), "dtype": str(v.dtype), "shape": list(v.shape)}
        for k, v in obs.items()
    }


class ZmqServer:
    """ZMQ REP server wrapping a ToySortingEnv.

    Runs a non-blocking poll loop so the Isaac Sim GUI stays responsive.
    Each step request maps to exactly one call to env.step().
    """

    def __init__(self, env, port: int = 5555):
        self.env = env
        self.port = port

    def serve_forever(self, simulation_app) -> None:
        """Start the REP loop.  Returns when a 'close' message is received
        or the simulation window is closed.

        Parameters
        ----------
        simulation_app:
            The Isaac Sim SimulationApp instance (from AppLauncher.app).
            Called every iteration to keep the GUI responsive.
        """
        import msgpack
        import zmq

        ctx = zmq.Context()
        sock = ctx.socket(zmq.REP)
        sock.bind(f"tcp://*:{self.port}")
        print(f"[ZmqServer] Listening on tcp://*:{self.port}")

        try:
            while simulation_app.is_running():
                try:
                    raw = sock.recv(zmq.NOBLOCK)
                except zmq.Again:
                    simulation_app.update()
                    continue

                msg = msgpack.unpackb(raw, raw=False)
                msg_type = msg["type"]

                if msg_type == "reset":
                    obs, _ = self.env.reset()
                    reply = {"obs": _encode_obs(obs)}

                elif msg_type == "step":
                    action = np.array(msg["action"], dtype=np.float32)
                    obs, reward, terminated, truncated, _ = self.env.step(action)
                    reply = {
                        "obs": _encode_obs(obs),
                        "reward": float(reward),
                        "terminated": bool(terminated),
                        "truncated": bool(truncated),
                    }

                elif msg_type == "close":
                    sock.send(msgpack.packb({"status": "ok"}))
                    break

                else:
                    raise ValueError(f"[ZmqServer] Unknown message type: {msg_type!r}")

                sock.send(msgpack.packb(reply))
                simulation_app.update()

        finally:
            sock.close()
            ctx.term()
            print("[ZmqServer] Shut down.")
