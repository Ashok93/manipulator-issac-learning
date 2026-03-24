"""Isaac Lab teleoperation launcher with local keyboard session controls.

This keeps Isaac Lab source untouched and adds a small terminal control layer
for XR handtracking sessions that do not emit Isaac Lab's START/STOP/RESET
messages.

Hotkeys
-------
s: start teleoperation
p: pause teleoperation
r: reset environment
q: quit
"""

from __future__ import annotations

import argparse
import logging
import queue
import threading
from collections.abc import Callable

from isaaclab.app import AppLauncher
from isaaclab_session_utils import build_teleop_interface, configure_xr_env, spawn_stdin_reader


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Teleoperation for Isaac Lab environments.")
    parser.add_argument("--num_envs", type=int, default=1, help="Number of environments to simulate.")
    parser.add_argument(
        "--teleop_device",
        type=str,
        default="keyboard",
        help=(
            "Teleop device. Set here (legacy) or via the environment config. "
            "Built-ins: keyboard, spacemouse, gamepad. For XR handtracking use the "
            "environment-configured device name."
        ),
    )
    parser.add_argument("--task", type=str, default=None, help="Name of the task.")
    parser.add_argument("--sensitivity", type=float, default=1.0, help="Sensitivity factor.")
    parser.add_argument(
        "--enable_pinocchio",
        action="store_true",
        default=False,
        help="Enable Pinocchio.",
    )
    AppLauncher.add_app_launcher_args(parser)
    return parser


def main() -> None:
    parser = _build_parser()
    args_cli = parser.parse_args()
    app_launcher_args = vars(args_cli)

    if not args_cli.task:
        raise ValueError("--task is required.")

    if args_cli.enable_pinocchio:
        import pinocchio  # noqa: F401

    if "handtracking" in args_cli.teleop_device.lower():
        app_launcher_args["xr"] = True

    app_launcher = AppLauncher(app_launcher_args)
    simulation_app = app_launcher.app

    import gymnasium as gym
    import torch
    import isaaclab_tasks  # noqa: F401
    from isaaclab.envs import ManagerBasedRLEnvCfg
    from isaaclab.managers import TerminationTermCfg as DoneTerm
    from isaaclab_tasks.manager_based.manipulation.lift import mdp
    from isaaclab_tasks.utils import parse_env_cfg

    if args_cli.enable_pinocchio:
        import isaaclab_tasks.manager_based.locomanipulation.pick_place  # noqa: F401
        import isaaclab_tasks.manager_based.manipulation.pick_place  # noqa: F401

    logger = logging.getLogger(__name__)

    env_cfg = parse_env_cfg(args_cli.task, device=args_cli.device, num_envs=args_cli.num_envs)
    env_cfg.env_name = args_cli.task
    if not isinstance(env_cfg, ManagerBasedRLEnvCfg):
        raise ValueError(
            "Teleoperation is only supported for ManagerBasedRLEnv environments. "
            f"Received environment config type: {type(env_cfg).__name__}"
        )

    env_cfg.terminations.time_out = None
    if "Lift" in args_cli.task:
        env_cfg.commands.object_pose.resampling_time_range = (1.0e9, 1.0e9)
        env_cfg.terminations.object_reached_goal = DoneTerm(func=mdp.object_reached_goal)

    env_cfg = configure_xr_env(env_cfg, enable_cameras=args_cli.enable_cameras)

    try:
        env = gym.make(args_cli.task, cfg=env_cfg).unwrapped
    except Exception as exc:
        logger.error("Failed to create environment: %s", exc)
        simulation_app.close()
        return

    should_reset_recording_instance = False
    teleoperation_active = True

    def reset_recording_instance() -> None:
        nonlocal should_reset_recording_instance
        should_reset_recording_instance = True
        print("Reset triggered - environment will reset on next step")

    def start_teleoperation() -> None:
        nonlocal teleoperation_active
        teleoperation_active = True
        print("Teleoperation activated")

    def stop_teleoperation() -> None:
        nonlocal teleoperation_active
        teleoperation_active = False
        print("Teleoperation deactivated")

    teleoperation_callbacks: dict[str, Callable[[], None]] = {
        "R": reset_recording_instance,
        "START": start_teleoperation,
        "STOP": stop_teleoperation,
        "RESET": reset_recording_instance,
    }

    if args_cli.xr:
        teleoperation_active = False

    teleop_interface = build_teleop_interface(args_cli, env_cfg, teleoperation_callbacks, logger)

    if teleop_interface is None:
        logger.error("Failed to create teleop interface")
        env.close()
        simulation_app.close()
        return

    print(f"Using teleop device: {teleop_interface}")
    env.reset()
    teleop_interface.reset()
    print("Teleoperation started.")
    print("Hotkeys: s=start, p=pause, r=reset, q=quit")

    command_queue: "queue.SimpleQueue[str]" = queue.SimpleQueue()
    stop_event = threading.Event()
    spawn_stdin_reader(command_queue, stop_event)

    try:
        while simulation_app.is_running() and not stop_event.is_set():
            while True:
                try:
                    command = command_queue.get_nowait()
                except queue.Empty:
                    break
                if command == "s":
                    start_teleoperation()
                elif command == "p":
                    stop_teleoperation()
                elif command == "r":
                    reset_recording_instance()
                elif command == "q":
                    stop_event.set()
                    break

            with torch.inference_mode():
                action = teleop_interface.advance()
                if teleoperation_active:
                    env.step(action.repeat(env.num_envs, 1))
                else:
                    env.sim.render()

                if should_reset_recording_instance:
                    env.reset()
                    teleop_interface.reset()
                    should_reset_recording_instance = False
                    print("Environment reset complete")
    except Exception as exc:
        logger.error("Error during simulation step: %s", exc)
    finally:
        env.close()
        print("Environment closed")
        simulation_app.close()


if __name__ == "__main__":
    main()
