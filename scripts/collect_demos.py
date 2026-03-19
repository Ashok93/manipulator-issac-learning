"""Collect toy-sorting demonstration data via iPhone teleoperation.

Uses LeRobot's phone teleop pipeline:
  iPhone (HEBI Mobile I/O app)
    → 6-DoF EE pose deltas
    → RobotKinematics IK (Placo, SO-ARM 101 URDF)
    → joint position targets
    → env.step()
    → LeRobotDataset frame

Prerequisites
-------------
1. uv sync --extra sim
2. pip install "lerobot>=0.5.0"   # installs Placo IK + HEBI support
3. Install HEBI Mobile I/O app on iPhone (free, App Store)
4. Both devices on the same network (Tailscale works for remote servers)

iPhone calibration (first time each session)
--------------------------------------------
Hold the phone screen-up with the top edge pointing toward the robot.
Press and hold B1 until the app vibrates, then release.

Controls
--------
  B1 (hold)   — enable teleoperation / calibrate on first press
  A3 (analog) — gripper velocity (push forward = close, pull back = open)

Usage
-----
  uv run python scripts/collect_demos.py \\
      --repo-id YOUR_HF_USER/toy-sorting-demos \\
      --num-episodes 20 \\
      --fps 30
"""

from __future__ import annotations

import argparse
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]

# ---------------------------------------------------------------------------
# AppLauncher must be created before any other isaaclab.* import
# ---------------------------------------------------------------------------
parser = argparse.ArgumentParser(
    description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
)
parser.add_argument("--repo-id", required=True, help="HuggingFace dataset repo ID, e.g. user/toy-sorting-demos")
parser.add_argument("--num-episodes", type=int, default=20)
parser.add_argument("--fps", type=int, default=30)
parser.add_argument("--task", default="Sort toys by color into the matching coloured box.")
parser.add_argument("--ee-step-size", type=float, default=0.5, help="EE movement scale per phone delta")
parser.add_argument("--gripper-speed", type=float, default=20.0, help="Gripper velocity multiplier")
args_cli = parser.parse_args()

from isaaclab.app import AppLauncher  # noqa: E402

app_launcher = AppLauncher(headless=False)
simulation_app = app_launcher.app

# ---------------------------------------------------------------------------
# Safe to import everything else now
# ---------------------------------------------------------------------------
import numpy as np  # noqa: E402
import torch  # noqa: E402
import isaaclab.sim as sim_utils  # noqa: E402
from isaaclab.sim import SimulationContext  # noqa: E402
from manipulator_learning.envhub import make_env, TASK_ID  # noqa: E402

from lerobot.teleoperators.phone import Phone  # noqa: E402
from lerobot.teleoperators.phone.config_phone import PhoneConfig, PhoneOS  # noqa: E402
from lerobot.common.kinematics import RobotKinematics  # noqa: E402
from lerobot.common.datasets.lerobot_dataset import LeRobotDataset  # noqa: E402

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
_URDF = str(
    _REPO_ROOT / "assets" / "toy_sorting" / "so_arm101" / "urdf" / "so_arm101.urdf"
)
_EE_FRAME = "gripper_frame_link"
_JOINT_NAMES = [
    "shoulder_pan",
    "shoulder_lift",
    "elbow_flex",
    "wrist_flex",
    "wrist_roll",
    "gripper",
]


def build_dataset(repo_id: str, fps: int, task: str) -> LeRobotDataset:
    """Create a new LeRobotDataset for recording."""
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


def record_episode(
    env,
    teleop: Phone,
    kinematics: RobotKinematics,
    dataset: LeRobotDataset,
    fps: int,
    task: str,
) -> int:
    """Run one episode of phone teleoperation and record frames.

    Returns the number of frames recorded.
    """
    obs, _ = env.reset()

    # Reference EE pose latched on first enable press (EEReferenceAndDelta logic)
    ee_ref_pos: np.ndarray | None = None
    ee_ref_quat: np.ndarray | None = None

    # Current joint positions used as IK warm-start
    current_joints = obs["observation.state"].copy()

    frames = 0
    dt = 1.0 / fps

    print(f"\n[collect_demos] Episode starting. Hold B1 on iPhone to enable motion.")

    while simulation_app.is_running():
        phone_action = teleop.get_action()

        enabled: bool = bool(phone_action["enabled"])

        if enabled:
            if ee_ref_pos is None:
                # Latch current EE pose as reference on first enable
                ee_ref_pos, ee_ref_quat = kinematics.forward_kinematics(current_joints)

            # Accumulate EE target from phone deltas
            delta = np.array([
                phone_action["target_x"] * args_cli.ee_step_size,
                phone_action["target_y"] * args_cli.ee_step_size,
                phone_action["target_z"] * args_cli.ee_step_size,
            ], dtype=np.float32)
            ee_ref_pos = ee_ref_pos + delta

            # Gripper: integrate velocity → position (clamped 0–1)
            gripper_vel = float(phone_action.get("gripper_vel", 0.0))
            current_joints[-1] = float(
                np.clip(current_joints[-1] + gripper_vel * dt / args_cli.gripper_speed, 0.0, 1.0)
            )

            # IK: EE target → joint positions (warm-start from current joints)
            joint_targets = kinematics.inverse_kinematics(
                target_position=ee_ref_pos,
                target_orientation=ee_ref_quat,
                initial_joints=current_joints,
            )
        else:
            # Phone disabled: hold current joints
            ee_ref_pos = None
            ee_ref_quat = None
            joint_targets = current_joints

        action = np.array(joint_targets, dtype=np.float32)
        obs, _reward, terminated, truncated, _info = env.step(action)
        current_joints = obs["observation.state"].copy()

        dataset.add_frame({
            "observation.state": obs["observation.state"],
            "observation.images.top": obs["observation.images.top"],
            "action": action,
            "task": task,
        })
        frames += 1

        if bool(terminated) or bool(truncated):
            break

    dataset.save_episode(task=task)
    print(f"[collect_demos] Episode saved — {frames} frames.")
    return frames


def main() -> None:
    sim_cfg = sim_utils.SimulationCfg(dt=1.0 / 60.0)
    sim = SimulationContext(sim_cfg)
    sim.set_camera_view(eye=[0.8, -0.8, 1.2], target=[0.0, 0.0, 0.2])

    print("[collect_demos] Loading environment …")
    vec_env = make_env(n_envs=1)
    # Unwrap: SyncVectorEnv → gym.Env
    env = vec_env.envs[0]

    print("[collect_demos] Resetting simulation …")
    sim.reset()
    env.reset()

    print("[collect_demos] Connecting to iPhone (HEBI Mobile I/O app) …")
    teleop = Phone(PhoneConfig(phone_os=PhoneOS.IOS))
    teleop.connect()
    print("[collect_demos] iPhone connected.")

    kinematics = RobotKinematics(
        urdf_path=_URDF,
        target_frame_name=_EE_FRAME,
        joint_names=_JOINT_NAMES,
    )

    dataset = build_dataset(
        repo_id=args_cli.repo_id,
        fps=args_cli.fps,
        task=args_cli.task,
    )

    total_frames = 0
    for ep in range(args_cli.num_episodes):
        print(f"\n[collect_demos] === Episode {ep + 1}/{args_cli.num_episodes} ===")
        print("[collect_demos] Press Enter when ready …", end="", flush=True)
        input()
        frames = record_episode(
            env=env,
            teleop=teleop,
            kinematics=kinematics,
            dataset=dataset,
            fps=args_cli.fps,
            task=args_cli.task,
        )
        total_frames += frames

    print(f"\n[collect_demos] Recorded {args_cli.num_episodes} episodes, {total_frames} total frames.")
    print(f"[collect_demos] Pushing dataset to HuggingFace Hub: {args_cli.repo_id} …")
    dataset.push_to_hub()
    print("[collect_demos] Done.")

    teleop.disconnect()
    env.close()


if __name__ == "__main__":
    main()
    simulation_app.close()
