"""Collect toy-sorting demonstrations via phone/headset teleoperation (WebXR).

Connects to the sim server (ZMQ) running in the sim container, drives it
with phone teleoperation via WebXR, and records a LeRobotDataset.

Architecture
------------
  Phone / Meta Quest (WebXR browser)
    → LeRobot Phone teleop → 6-DoF EE deltas
    → RobotKinematics IK (Placo, SO-ARM 101 URDF)
    → joint position targets
    → ZMQ → sim container → env.step()
    → ZMQ ← obs (image + state)
    → LeRobotDataset frame

Prerequisites
-------------
1. Start the sim container first:
     docker compose run sim uv run python scripts/sim_server.py

2. Then in a second terminal, start this container:
     docker compose run lerobot uv run python scripts/collect_demos.py \\
         --repo-id YOUR_HF_USER/toy-sorting-demos \\
         --num-episodes 20

3. Open the printed HTTPS URL on your phone/Quest browser.
4. Both devices on the same network (Tailscale works for remote servers).

Controls (WebXR / Android mode)
-------------------------------
  Move (hold) — enable teleoperation (calibrates on first press)
  A button    — open gripper
  B button    — close gripper

Calibration: hold phone screen-up, top edge toward the robot, press Move.
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
from lerobot.model.kinematics import RobotKinematics
from lerobot.datasets.lerobot_dataset import LeRobotDataset
from lerobot.utils.rotation import Rotation

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
_TRAIN_ROOT = Path(__file__).resolve().parents[1]  # train/scripts/ → train/
_REPO_ROOT = _TRAIN_ROOT.parent                    # repo root
_URDF = str(_REPO_ROOT / "sim" / "assets" / "toy_sorting" / "so_arm101" / "urdf" / "so_arm101.urdf")
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
    phone_os: PhoneOS,
) -> int:
    """Record one episode using the same logic as LeRobot's processor pipeline:
    MapPhoneActionToRobotAction → EEReferenceAndDelta → GripperVelocityToJoint → IK
    """
    obs = sim.reset()

    # Sim uses radians, kinematics uses degrees
    current_joints_deg = np.rad2deg(obs["observation.state"].astype(np.float64))

    # --- EEReferenceAndDelta state ---
    reference_ee_pose: np.ndarray | None = None  # latched on rising edge of B1
    prev_enabled = False
    command_when_disabled: np.ndarray | None = None

    # --- IK state ---
    q_curr_deg = current_joints_deg.copy()

    frames = 0

    print("[collect_demos] Hold B1 to enable motion. Press Ctrl+C to end episode early.")

    try:
        while True:
            # ----- Phone read -----
            phone_action = teleop.get_action()
            if not phone_action:
                time.sleep(0.01)
                continue

            # ----- Step 1: MapPhoneActionToRobotAction -----
            enabled = bool(phone_action.get("phone.enabled", False))
            pos = phone_action.get("phone.pos")
            rot = phone_action.get("phone.rot")
            raw_inputs = phone_action.get("phone.raw_inputs", {})

            if pos is None or rot is None:
                time.sleep(0.01)
                continue

            rotvec = rot.as_rotvec()

            # Axis mapping (from LeRobot MapPhoneActionToRobotAction source)
            target_x = -pos[1] if enabled else 0.0
            target_y = pos[0] if enabled else 0.0
            target_z = pos[2] if enabled else 0.0
            target_wx = rotvec[1] if enabled else 0.0
            target_wy = rotvec[0] if enabled else 0.0
            target_wz = -rotvec[2] if enabled else 0.0

            # Gripper velocity (iOS: A3 analog, Android: A-B buttons)
            if phone_os == PhoneOS.IOS:
                gripper_vel = float(raw_inputs.get("a3", 0.0))
            else:
                a = float(raw_inputs.get("reservedButtonA", 0.0))
                b = float(raw_inputs.get("reservedButtonB", 0.0))
                gripper_vel = a - b

            # ----- Step 2: EEReferenceAndDelta -----
            # Current EE pose from FK
            t_curr = kinematics.forward_kinematics(current_joints_deg)

            if enabled:
                # Latch reference on rising edge
                if not prev_enabled or reference_ee_pose is None:
                    reference_ee_pose = t_curr.copy()
                ref = reference_ee_pose

                delta_p = np.array([
                    target_x * ee_step_size,
                    target_y * ee_step_size,
                    target_z * ee_step_size,
                ], dtype=float)
                r_abs = Rotation.from_rotvec([target_wx, target_wy, target_wz]).as_matrix()

                desired = np.eye(4, dtype=float)
                desired[:3, :3] = ref[:3, :3] @ r_abs
                desired[:3, 3] = ref[:3, 3] + delta_p

                command_when_disabled = desired.copy()
            else:
                if command_when_disabled is None:
                    command_when_disabled = t_curr.copy()
                desired = command_when_disabled.copy()

            prev_enabled = enabled

            # ----- Step 3: GripperVelocityToJoint -----
            gripper_delta = gripper_vel * gripper_speed
            gripper_pos = float(np.clip(current_joints_deg[-1] + gripper_delta, 0.0, 100.0))

            # ----- Step 4: InverseKinematicsEEToJoints -----
            q_curr_deg = current_joints_deg.copy()  # closed-loop: use measured joints
            joint_targets_deg = kinematics.inverse_kinematics(q_curr_deg, desired)

            # Replace gripper with velocity-integrated value
            joint_targets_deg[-1] = gripper_pos

            # Convert to radians for sim
            action = np.deg2rad(joint_targets_deg).astype(np.float32)

            if frames % 30 == 0:
                print(f"[debug] frame={frames} enabled={enabled} "
                      f"ee_target={desired[:3, 3]} joints_deg={joint_targets_deg}")

            obs, _reward, terminated, truncated = sim.step(action)
            current_joints_deg = np.rad2deg(obs["observation.state"].astype(np.float64))

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
    parser.add_argument("--sim-host", default=os.environ.get("SIM_HOST", "localhost"))
    parser.add_argument("--sim-port", type=int, default=int(os.environ.get("SIM_PORT", "5555")))
    parser.add_argument("--ee-step-size", type=float, default=0.5)
    parser.add_argument("--gripper-speed", type=float, default=20.0)
    parser.add_argument(
        "--phone-os", choices=["ios", "android"], default="ios",
        help="Phone platform: 'ios' (HEBI, local WiFi) or 'android' (WebXR URL)",
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
            phone_os=phone_os,
        )
        total_frames += frames

    print(f"\n[collect_demos] {args.num_episodes} episodes, {total_frames} total frames.")
    print(f"[collect_demos] Dataset saved locally. To push to HuggingFace Hub run:")
    print(f"[collect_demos]   dataset.push_to_hub()  # repo: {args.repo_id}")
    # dataset.push_to_hub()  # uncomment when ready to publish
    print("[collect_demos] Done.")

    teleop.disconnect()
    sim.close()


if __name__ == "__main__":
    main()
