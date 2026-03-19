"""Collect toy-sorting demonstrations via iPhone teleoperation.

Connects to the sim server (ZMQ) running in the sim container, drives it
with iPhone phone teleoperation, and records a LeRobotDataset.

Architecture
------------
  iPhone (HEBI Mobile I/O app)
    → LeRobot Phone teleop → 6-DoF EE deltas
    → RobotKinematics IK (Placo, SO-ARM 101 URDF)
    → joint position targets
    → ZMQ → sim container → env.step()
    → ZMQ ← obs (image + state)
    → LeRobotDataset frame
    → push to HuggingFace Hub

Prerequisites
-------------
1. Start the sim container first:
     docker compose run sim uv run python scripts/sim_server.py

2. Then in a second terminal, start this container:
     docker compose run lerobot uv run python scripts/collect_demos.py \\
         --repo-id YOUR_HF_USER/toy-sorting-demos \\
         --num-episodes 20

3. Install HEBI Mobile I/O app on iPhone (free, App Store).
4. Both devices on the same network (Tailscale works for remote servers).

iPhone controls
---------------
  B1 (hold)   — enable teleoperation (calibrates on first press)
  A3 (analog) — gripper: push forward = close, pull back = open

Calibration: hold phone screen-up, top edge toward the robot, press B1.
"""

from __future__ import annotations

import argparse
import time
from pathlib import Path

import msgpack
import numpy as np
import zmq

from lerobot.teleoperators.phone import Phone
from lerobot.teleoperators.phone.config_phone import PhoneConfig, PhoneOS
from lerobot.common.kinematics import RobotKinematics
from lerobot.common.datasets.lerobot_dataset import LeRobotDataset

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
_REPO_ROOT = Path(__file__).resolve().parents[2]
_URDF = str(_REPO_ROOT / "assets" / "toy_sorting" / "so_arm101" / "urdf" / "so_arm101.urdf")
_EE_FRAME = "gripper_frame_link"
_JOINT_NAMES = ["shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll", "gripper"]


# ---------------------------------------------------------------------------
# ZMQ client helpers
# ---------------------------------------------------------------------------

def _decode_obs(encoded: dict) -> dict:
    obs = {}
    for k, v in encoded.items():
        arr = np.frombuffer(v["data"], dtype=v["dtype"]).reshape(v["shape"])
        obs[k] = arr.copy()  # frombuffer returns read-only view
    return obs


class SimClient:
    """ZMQ REQ client for the sim container."""

    def __init__(self, host: str, port: int):
        self._ctx = zmq.Context()
        self._sock = self._ctx.socket(zmq.REQ)
        self._sock.connect(f"tcp://{host}:{port}")

    def reset(self) -> dict:
        self._sock.send(msgpack.packb({"type": "reset"}))
        reply = msgpack.unpackb(self._sock.recv(), raw=False)
        return _decode_obs(reply["obs"])

    def step(self, action: np.ndarray) -> tuple[dict, float, bool, bool]:
        self._sock.send(msgpack.packb({"type": "step", "action": action.tolist()}))
        reply = msgpack.unpackb(self._sock.recv(), raw=False)
        return (
            _decode_obs(reply["obs"]),
            float(reply["reward"]),
            bool(reply["terminated"]),
            bool(reply["truncated"]),
        )

    def close(self) -> None:
        self._sock.send(msgpack.packb({"type": "close"}))
        self._sock.recv()
        self._sock.close()
        self._ctx.term()


# ---------------------------------------------------------------------------
# Dataset
# ---------------------------------------------------------------------------

def build_dataset(repo_id: str, fps: int) -> LeRobotDataset:
    features = {
        "observation.state": {
            "dtype": "float32",
            "shape": (6,),
            "names": _JOINT_NAMES,
        },
        "observation.images.top": {
            "dtype": "video",
            "shape": (480, 640, 3),
            "names": ["height", "width", "channel"],
        },
        "action": {
            "dtype": "float32",
            "shape": (6,),
            "names": _JOINT_NAMES,
        },
    }
    return LeRobotDataset.create(
        repo_id=repo_id,
        fps=fps,
        robot_type="so101",
        features=features,
        use_videos=True,
    )


# ---------------------------------------------------------------------------
# Episode recording
# ---------------------------------------------------------------------------

def record_episode(
    sim: SimClient,
    teleop: Phone,
    kinematics: RobotKinematics,
    dataset: LeRobotDataset,
    fps: int,
    task: str,
    ee_step_size: float,
    gripper_speed: float,
) -> int:
    obs = sim.reset()

    ee_ref_pos: np.ndarray | None = None
    ee_ref_quat: np.ndarray | None = None
    current_joints = obs["observation.state"].copy()

    frames = 0
    dt = 1.0 / fps

    print("[collect_demos] Hold B1 on iPhone to enable motion. Press Ctrl+C to end episode early.")

    try:
        while True:
            phone_action = teleop.get_action()
            enabled = bool(phone_action["enabled"])

            if enabled:
                if ee_ref_pos is None:
                    ee_ref_pos, ee_ref_quat = kinematics.forward_kinematics(current_joints)

                delta = np.array([
                    phone_action["target_x"] * ee_step_size,
                    phone_action["target_y"] * ee_step_size,
                    phone_action["target_z"] * ee_step_size,
                ], dtype=np.float32)
                ee_ref_pos = ee_ref_pos + delta

                gripper_vel = float(phone_action.get("gripper_vel", 0.0))
                current_joints[-1] = float(
                    np.clip(current_joints[-1] + gripper_vel * dt / gripper_speed, 0.0, 1.0)
                )

                joint_targets = kinematics.inverse_kinematics(
                    target_position=ee_ref_pos,
                    target_orientation=ee_ref_quat,
                    initial_joints=current_joints,
                )
            else:
                ee_ref_pos = None
                ee_ref_quat = None
                joint_targets = current_joints

            action = np.array(joint_targets, dtype=np.float32)
            obs, _reward, terminated, truncated, = sim.step(action)
            current_joints = obs["observation.state"].copy()

            dataset.add_frame({
                "observation.state": obs["observation.state"],
                "observation.images.top": obs["observation.images.top"],
                "action": action,
                "task": task,
            })
            frames += 1

            if terminated or truncated:
                break

    except KeyboardInterrupt:
        print("\n[collect_demos] Episode ended early by user.")

    dataset.save_episode(task=task)
    print(f"[collect_demos] Episode saved — {frames} frames.")
    return frames


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--repo-id", required=True, help="HuggingFace dataset repo ID")
    parser.add_argument("--num-episodes", type=int, default=20)
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--task", default="Sort toys by color into the matching coloured box.")
    parser.add_argument("--sim-host", default="sim", help="Sim container hostname (default: sim)")
    parser.add_argument("--sim-port", type=int, default=5555)
    parser.add_argument("--ee-step-size", type=float, default=0.5)
    parser.add_argument("--gripper-speed", type=float, default=20.0)
    args = parser.parse_args()

    print(f"[collect_demos] Connecting to sim at {args.sim_host}:{args.sim_port} …")
    sim = SimClient(host=args.sim_host, port=args.sim_port)

    print("[collect_demos] Connecting to iPhone (HEBI Mobile I/O app) …")
    teleop = Phone(PhoneConfig(phone_os=PhoneOS.IOS))
    teleop.connect()
    print("[collect_demos] iPhone connected.")

    kinematics = RobotKinematics(
        urdf_path=_URDF,
        target_frame_name=_EE_FRAME,
        joint_names=_JOINT_NAMES,
    )

    dataset = build_dataset(repo_id=args.repo_id, fps=args.fps)

    total_frames = 0
    for ep in range(args.num_episodes):
        print(f"\n[collect_demos] === Episode {ep + 1}/{args.num_episodes} ===")
        print("[collect_demos] Press Enter when ready …", end="", flush=True)
        input()
        frames = record_episode(
            sim=sim,
            teleop=teleop,
            kinematics=kinematics,
            dataset=dataset,
            fps=args.fps,
            task=args.task,
            ee_step_size=args.ee_step_size,
            gripper_speed=args.gripper_speed,
        )
        total_frames += frames

    print(f"\n[collect_demos] {args.num_episodes} episodes, {total_frames} total frames.")
    print(f"[collect_demos] Pushing to HuggingFace Hub: {args.repo_id} …")
    dataset.push_to_hub()
    print("[collect_demos] Done.")

    teleop.disconnect()
    sim.close()


if __name__ == "__main__":
    main()
