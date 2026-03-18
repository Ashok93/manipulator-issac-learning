"""ZMQ REP server stub for Phase 2 sim↔train bridge.

Phase 2 will replace this stub with a real implementation that:
- Serialises observations (numpy arrays) and sends them as msgpack over ZMQ.
- Receives action tensors from the train container and forwards them to the env.
- Supports reset / step / close RPC messages.

Usage (Phase 2):
    server = ZmqServer(env, port=5555)
    server.serve_forever()
"""

from __future__ import annotations


class ZmqServer:
    """Stub ZMQ REP server.  Replace body in Phase 2."""

    def __init__(self, env, port: int = 5555):
        self.env = env
        self.port = port

    def serve_forever(self) -> None:
        raise NotImplementedError(
            "ZmqServer is a Phase 2 stub.  "
            "Implement with pyzmq REP socket + msgpack serialisation."
        )
