"""Collect toy-sorting demonstrations via iPhone teleoperation (HEBI).

Connects to the sim server (ZMQ) running on a remote GPU server, drives it
with phone teleoperation via HEBI Mobile I/O, and records a LeRobotDataset.

Architecture
------------
  iPhone (HEBI Mobile I/O, local WiFi)
    → LeRobot Phone teleop → 6-DoF EE deltas
    → Processor pipeline (matching LeRobot exactly):
        MapPhoneActionToRobotAction → EEReferenceAndDelta
        → EEBoundsAndSafety → GripperVelocityToJoint
        → InverseKinematicsEEToJoints
    → joint position targets
    → ZMQ → sim server → env.step()
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
# Episode recording — follows LeRobot processor pipeline exactly:
#   MapPhoneActionToRobotAction → EEReferenceAndDelta
#   → EEBoundsAndSafety → GripperVelocityToJoint
#   → InverseKinematicsEEToJoints
#
# Source: lerobot/teleoperators/phone/phone_processor.py
#         lerobot/robots/so_follower/robot_kinematic_processor.py
# ---------------------------------------------------------------------------

def record_episode(
    sim: SimClient,
    teleop: Phone,
    kinematics: RobotKinematics,
    dataset: LeRobotDataset,
    task: str,
    ee_step_sizes: dict[str, float],
    gripper_speed: float,
    max_ee_step_m: float,
    ee_bounds: dict[str, list[float]],
    phone_os: PhoneOS,
) -> int:
    """Record one episode.  Returns frame count."""
    print("[collect_demos] Resetting sim …")
    obs = sim.reset()

    # Sim uses radians, kinematics uses degrees (LeRobot SO-101 convention)
    current_joints_deg = np.rad2deg(obs["observation.state"].astype(np.float64))

    # --- EEReferenceAndDelta state (matches lerobot source) ---
    reference_ee_pose: np.ndarray | None = None
    prev_enabled = False
    command_when_disabled: np.ndarray | None = None

    # --- EEBoundsAndSafety state ---
    last_ee_pos: np.ndarray | None = None

    frames = 0

    print("[collect_demos] Hold B1 to control robot. Tap B8 to end episode.")

    while True:
        # ----- Phone read -----
        phone_action = teleop.get_action()
        if not phone_action:
            time.sleep(0.01)
            continue

        enabled = bool(phone_action.get("phone.enabled", False))
        pos = phone_action.get("phone.pos")
        rot = phone_action.get("phone.rot")
        raw_inputs = phone_action.get("phone.raw_inputs", {})

        if pos is None or rot is None:
            time.sleep(0.01)
            continue

        # Check B8 to end episode
        if int(raw_inputs.get("b8", 0)):
            print("[collect_demos] B8 pressed — ending episode.")
            break

        # =====================================================================
        # Step 1: MapPhoneActionToRobotAction
        # (lerobot/teleoperators/phone/phone_processor.py)
        # =====================================================================
        rotvec = rot.as_rotvec()

        target_x = -pos[1] if enabled else 0.0
        target_y = pos[0] if enabled else 0.0
        target_z = pos[2] if enabled else 0.0
        target_wx = rotvec[1] if enabled else 0.0
        target_wy = rotvec[0] if enabled else 0.0
        target_wz = -rotvec[2] if enabled else 0.0

        if phone_os == PhoneOS.IOS:
            gripper_vel = float(raw_inputs.get("a3", 0.0))
        else:
            a = float(raw_inputs.get("reservedButtonA", 0.0))
            b = float(raw_inputs.get("reservedButtonB", 0.0))
            gripper_vel = a - b

        # =====================================================================
        # Step 2: EEReferenceAndDelta
        # (lerobot/robots/so_follower/robot_kinematic_processor.py)
        # =====================================================================
        t_curr = kinematics.forward_kinematics(current_joints_deg)

        if enabled:
            ref = t_curr
            # Latched reference: capture on rising edge
            if not prev_enabled or reference_ee_pose is None:
                reference_ee_pose = t_curr.copy()
            ref = reference_ee_pose

            delta_p = np.array([
                target_x * ee_step_sizes["x"],
                target_y * ee_step_sizes["y"],
                target_z * ee_step_sizes["z"],
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

        # =====================================================================
        # Step 3: EEBoundsAndSafety
        # (lerobot/robots/so_follower/robot_kinematic_processor.py)
        # Clip EE position to workspace bounds, rate-limit large jumps.
        # =====================================================================
        ee_pos = desired[:3, 3].copy()

        # Clip to workspace bounds
        ee_pos = np.clip(ee_pos, ee_bounds["min"], ee_bounds["max"])

        # Rate-limit: clamp step size to max_ee_step_m
        if last_ee_pos is not None:
            dpos = ee_pos - last_ee_pos
            step_norm = float(np.linalg.norm(dpos))
            if step_norm > max_ee_step_m and step_norm > 0:
                ee_pos = last_ee_pos + dpos * (max_ee_step_m / step_norm)

        last_ee_pos = ee_pos.copy()
        desired[:3, 3] = ee_pos

        # =====================================================================
        # Step 4: GripperVelocityToJoint
        # (lerobot/robots/so_follower/robot_kinematic_processor.py)
        # =====================================================================
        gripper_delta = gripper_vel * gripper_speed
        gripper_pos = float(np.clip(current_joints_deg[-1] + gripper_delta, 0.0, 100.0))

        # =====================================================================
        # Step 5: InverseKinematicsEEToJoints (closed-loop)
        # (lerobot/robots/so_follower/robot_kinematic_processor.py)
        # =====================================================================
        q_curr_deg = current_joints_deg.copy()  # closed-loop: measured joints as IK guess
        joint_targets_deg = kinematics.inverse_kinematics(q_curr_deg, desired)
        joint_targets_deg[-1] = gripper_pos  # replace gripper with velocity-integrated value

        # Convert to radians for sim
        action = np.deg2rad(joint_targets_deg).astype(np.float32)

        if frames % 30 == 0:
            print(f"  frame={frames} enabled={enabled} ee={ee_pos}")

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
    parser.add_argument("--gripper-speed", type=float, default=20.0,
                        help="GripperVelocityToJoint speed_factor (default: 20.0)")
    parser.add_argument("--max-ee-step", type=float, default=0.05,
                        help="EEBoundsAndSafety max step in meters (default: 0.05)")
    parser.add_argument(
        "--phone-os", choices=["ios", "android"], default="ios",
        help="Phone platform: 'ios' (HEBI) or 'android' (WebXR)",
    )
    args = parser.parse_args()

    phone_os = PhoneOS.IOS if args.phone_os == "ios" else PhoneOS.ANDROID

    # EEReferenceAndDelta step sizes (same as LeRobot default)
    ee_step_sizes = {"x": 0.5, "y": 0.5, "z": 0.5}

    # EEBoundsAndSafety workspace bounds (in robot local frame, meters)
    # SO-ARM 101 reach ~25cm, generous bounds to avoid clipping valid motions
    ee_bounds = {
        "min": [-0.30, -0.30, -0.05],
        "max": [0.30, 0.30, 0.35],
    }

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
            task=args.task,
            ee_step_sizes=ee_step_sizes,
            gripper_speed=args.gripper_speed,
            max_ee_step_m=args.max_ee_step,
            ee_bounds=ee_bounds,
            phone_os=phone_os,
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
