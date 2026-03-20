"""Collect toy-sorting demonstrations via iPhone teleoperation (HEBI).

Connects to the sim server (ZMQ) running on a remote GPU server, drives it
with phone teleoperation via HEBI Mobile I/O, and records a LeRobotDataset.

Uses LeRobot's actual processor pipeline classes — no manual reimplementation:
  Pipeline 1 (phone → EE pose):
    MapPhoneActionToRobotAction → EEReferenceAndDelta
    → EEBoundsAndSafety → GripperVelocityToJoint
  Pipeline 2 (EE pose → joint targets):
    InverseKinematicsEEToJoints

Architecture
------------
  iPhone (HEBI Mobile I/O, local WiFi)
    → LeRobot Phone teleop → raw phone action dict
    → Pipeline 1 → EE pose action dict
    → Pipeline 2 → joint position targets (degrees)
    → deg→rad → ZMQ → sim server → env.step()
    → ZMQ ← obs (image + state)
    → LeRobotDataset frame

Prerequisites
-------------
1. Start the sim server on the remote GPU server:
     docker compose run sim uv run --extra sim python scripts/sim_server.py

2. On your local Mac:
     cd train
     SIM_HOST=<tailscale-ip> uv run python scripts/collect_demos.py \\
         --repo-id AshDash93/toy-sorting-demos --num-episodes 20

3. Open HEBI Mobile I/O on your iPhone (same WiFi as Mac).

Controls (iOS / HEBI)
---------------------
  B1 (hold)         — enable teleoperation (calibrates on first press)
  B1 (release)      — freeze robot in place
  A3 (push forward) — close gripper
  A3 (pull back)    — open gripper
  B8 (tap)          — end current episode and save

Calibration: hold phone screen-up, top edge toward the robot, press B1.
"""

from __future__ import annotations

import argparse
import os
import time
from pathlib import Path

import msgpack
import numpy as np
import zmq

from lerobot.teleoperators.phone import Phone
from lerobot.teleoperators.phone.config_phone import PhoneConfig, PhoneOS
from lerobot.teleoperators.phone.phone_processor import MapPhoneActionToRobotAction
from lerobot.robots.so_follower.robot_kinematic_processor import (
    EEBoundsAndSafety,
    EEReferenceAndDelta,
    GripperVelocityToJoint,
    InverseKinematicsEEToJoints,
)
from lerobot.model.kinematics import RobotKinematics
from lerobot.processor.pipeline import RobotProcessorPipeline
from lerobot.processor.converters import (
    robot_action_observation_to_transition,
    transition_to_robot_action,
)
from lerobot.datasets.lerobot_dataset import LeRobotDataset

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
_TRAIN_ROOT = Path(__file__).resolve().parents[1]  # train/scripts/ → train/
_REPO_ROOT = _TRAIN_ROOT.parent                    # repo root
_URDF = str(_REPO_ROOT / "sim" / "assets" / "toy_sorting" / "so_arm101" / "urdf" / "so_arm101.urdf")
_EE_FRAME = "gripper_frame_link"
_MOTOR_NAMES = ["shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll", "gripper"]


# ---------------------------------------------------------------------------
# ZMQ client
# ---------------------------------------------------------------------------

def _decode_obs(encoded: dict) -> dict:
    obs = {}
    for k, v in encoded.items():
        arr = np.frombuffer(v["data"], dtype=v["dtype"]).reshape(v["shape"])
        obs[k] = arr.copy()
    return obs


class SimClient:
    """ZMQ REQ client for the sim server."""

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
# Sim obs ↔ LeRobot obs conversion
# ---------------------------------------------------------------------------

def sim_obs_to_robot_obs(obs: dict) -> dict:
    """Convert sim observation (radians) to LeRobot robot observation (degrees).

    LeRobot processors expect observation keys like "shoulder_pan.pos" in degrees.
    """
    joint_pos_rad = obs["observation.state"].astype(np.float64)
    joint_pos_deg = np.rad2deg(joint_pos_rad)
    return {f"{name}.pos": float(joint_pos_deg[i]) for i, name in enumerate(_MOTOR_NAMES)}


def robot_action_to_sim_action(action: dict) -> np.ndarray:
    """Convert LeRobot robot action (degrees) to sim action (radians).

    After pipeline 2, action dict has "shoulder_pan.pos", etc. in degrees.
    """
    joint_targets_deg = np.array([action[f"{name}.pos"] for name in _MOTOR_NAMES])
    return np.deg2rad(joint_targets_deg).astype(np.float32)


# ---------------------------------------------------------------------------
# Dataset
# ---------------------------------------------------------------------------

def build_dataset(repo_id: str, fps: int) -> LeRobotDataset:
    features = {
        "observation.state": {
            "dtype": "float32",
            "shape": (6,),
            "names": _MOTOR_NAMES,
        },
        "observation.images.top": {
            "dtype": "video",
            "shape": (480, 640, 3),
            "names": ["height", "width", "channel"],
        },
        "action": {
            "dtype": "float32",
            "shape": (6,),
            "names": _MOTOR_NAMES,
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
# Episode recording using LeRobot's actual processor pipeline
# ---------------------------------------------------------------------------

def record_episode(
    sim: SimClient,
    teleop: Phone,
    dataset: LeRobotDataset,
    task: str,
    teleop_action_processor: RobotProcessorPipeline,
    robot_action_processor: RobotProcessorPipeline,
) -> int:
    """Record one episode.  Returns frame count."""
    print("[collect_demos] Resetting sim …")
    obs = sim.reset()
    robot_obs = sim_obs_to_robot_obs(obs)

    frames = 0
    print("[collect_demos] Hold B1 to control robot. Tap B8 to end episode.")

    while True:
        # ----- Phone read -----
        phone_action = teleop.get_action()
        if not phone_action:
            time.sleep(0.01)
            continue

        raw_inputs = phone_action.get("phone.raw_inputs", {})

        # Check B8 to end episode
        if int(raw_inputs.get("b8", 0)):
            print("[collect_demos] B8 pressed — ending episode.")
            break

        if phone_action.get("phone.pos") is None:
            time.sleep(0.01)
            continue

        # ----- Pipeline 1: phone action → EE pose -----
        ee_action = teleop_action_processor((phone_action, robot_obs))

        # ----- Pipeline 2: EE pose → joint targets (degrees) -----
        joint_action = robot_action_processor((ee_action, robot_obs))

        # ----- Convert to radians and send to sim -----
        sim_action = robot_action_to_sim_action(joint_action)

        if frames % 30 == 0:
            enabled = phone_action.get("phone.enabled", False)
            print(f"  frame={frames} enabled={enabled}")

        obs, _reward, terminated, truncated = sim.step(sim_action)
        robot_obs = sim_obs_to_robot_obs(obs)

        dataset.add_frame({
            "observation.state": obs["observation.state"],
            "observation.images.top": obs["observation.images.top"],
            "action": sim_action,
            "task": task,
        })
        frames += 1

        if terminated or truncated:
            break

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
    parser.add_argument("--sim-host", default=os.environ.get("SIM_HOST", "localhost"))
    parser.add_argument("--sim-port", type=int, default=int(os.environ.get("SIM_PORT", "5555")))
    parser.add_argument(
        "--phone-os", choices=["ios", "android"], default="ios",
        help="Phone platform: 'ios' (HEBI) or 'android' (WebXR)",
    )
    args = parser.parse_args()

    phone_os = PhoneOS.IOS if args.phone_os == "ios" else PhoneOS.ANDROID

    print(f"[collect_demos] Connecting to sim at {args.sim_host}:{args.sim_port} …")
    sim = SimClient(host=args.sim_host, port=args.sim_port)

    print(f"[collect_demos] Starting phone teleop ({args.phone_os} mode) …")
    teleop = Phone(PhoneConfig(phone_os=phone_os))
    teleop.connect()
    print("[collect_demos] Phone connected.")

    kinematics = RobotKinematics(
        urdf_path=_URDF,
        target_frame_name=_EE_FRAME,
        joint_names=_MOTOR_NAMES,
    )

    # Pipeline 1: phone action → EE pose (same as LeRobot phone_to_so100 examples)
    teleop_action_processor = RobotProcessorPipeline(
        steps=[
            MapPhoneActionToRobotAction(platform=phone_os),
            EEReferenceAndDelta(
                kinematics=kinematics,
                end_effector_step_sizes={"x": 0.5, "y": 0.5, "z": 0.5},
                motor_names=_MOTOR_NAMES,
            ),
            EEBoundsAndSafety(
                end_effector_bounds={"min": [-1.0, -1.0, -1.0], "max": [1.0, 1.0, 1.0]},
                max_ee_step_m=0.10,
            ),
            GripperVelocityToJoint(speed_factor=20.0),
        ],
        to_transition=robot_action_observation_to_transition,
        to_output=transition_to_robot_action,
    )

    # Pipeline 2: EE pose → joint targets (closed-loop IK)
    robot_action_processor = RobotProcessorPipeline(
        steps=[
            InverseKinematicsEEToJoints(
                kinematics=kinematics,
                motor_names=_MOTOR_NAMES,
                initial_guess_current_joints=True,
            ),
        ],
        to_transition=robot_action_observation_to_transition,
        to_output=transition_to_robot_action,
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
            dataset=dataset,
            task=args.task,
            teleop_action_processor=teleop_action_processor,
            robot_action_processor=robot_action_processor,
        )
        total_frames += frames

    print(f"\n[collect_demos] {args.num_episodes} episodes, {total_frames} total frames.")
    print(f"[collect_demos] Dataset saved locally. To push to HuggingFace Hub run:")
    print(f"[collect_demos]   dataset.push_to_hub()  # repo: {args.repo_id}")
    print("[collect_demos] Done.")

    teleop.disconnect()
    sim.close()


if __name__ == "__main__":
    main()
