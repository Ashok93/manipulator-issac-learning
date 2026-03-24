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
import select
import sys
import termios
import threading
import tty
from collections.abc import Callable

from isaaclab.app import AppLauncher


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


def _spawn_stdin_reader(command_queue: "queue.SimpleQueue[str]", stop_event: threading.Event) -> threading.Thread:
    """Read single-key commands from stdin without blocking the sim loop."""

    def _reader() -> None:
        if not sys.stdin.isatty():
            return

        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setcbreak(fd)
            while not stop_event.is_set():
                ready, _, _ = select.select([sys.stdin], [], [], 0.1)
                if not ready:
                    continue
                ch = sys.stdin.read(1)
                if ch:
                    command_queue.put(ch.lower())
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

    thread = threading.Thread(target=_reader, name="teleop-stdin-reader", daemon=True)
    thread.start()
    return thread


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
    import logging
    import torch
    import isaaclab_tasks  # noqa: F401
    from isaaclab.devices import Se3Gamepad, Se3GamepadCfg, Se3Keyboard, Se3KeyboardCfg, Se3SpaceMouse, Se3SpaceMouseCfg
    from isaaclab.devices.openxr import remove_camera_configs
    from isaaclab.devices.teleop_device_factory import create_teleop_device
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

    if args_cli.xr:
        env_cfg = remove_camera_configs(env_cfg)
        env_cfg.sim.render.antialiasing_mode = "DLSS"

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

    teleop_interface = None
    try:
        if hasattr(env_cfg, "teleop_devices") and args_cli.teleop_device in env_cfg.teleop_devices.devices:
            teleop_interface = create_teleop_device(
                args_cli.teleop_device,
                env_cfg.teleop_devices.devices,
                teleoperation_callbacks,
            )
        else:
            logger.warning(
                "No teleop device '%s' found in environment config. Creating default.",
                args_cli.teleop_device,
            )
            sensitivity = args_cli.sensitivity
            if args_cli.teleop_device.lower() == "keyboard":
                teleop_interface = Se3Keyboard(
                    Se3KeyboardCfg(pos_sensitivity=0.05 * sensitivity, rot_sensitivity=0.05 * sensitivity)
                )
            elif args_cli.teleop_device.lower() == "spacemouse":
                teleop_interface = Se3SpaceMouse(
                    Se3SpaceMouseCfg(pos_sensitivity=0.05 * sensitivity, rot_sensitivity=0.05 * sensitivity)
                )
            elif args_cli.teleop_device.lower() == "gamepad":
                teleop_interface = Se3Gamepad(
                    Se3GamepadCfg(pos_sensitivity=0.1 * sensitivity, rot_sensitivity=0.1 * sensitivity)
                )
            else:
                logger.error("Unsupported teleop device: %s", args_cli.teleop_device)
                logger.error("Configure the teleop device in the environment config.")
                env.close()
                simulation_app.close()
                return

        for key, callback in teleoperation_callbacks.items():
            try:
                teleop_interface.add_callback(key, callback)
            except (ValueError, TypeError) as exc:
                logger.warning("Failed to add callback for key %s: %s", key, exc)
    except Exception as exc:
        logger.error("Failed to create teleop interface: %s", exc)
        env.close()
        simulation_app.close()
        return

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
    _spawn_stdin_reader(command_queue, stop_event)

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
