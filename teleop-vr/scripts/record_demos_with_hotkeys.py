"""Isaac Lab demo recorder with local keyboard session controls.

This is a local wrapper around Isaac Lab-style demo collection that keeps
the source tree untouched and adds terminal hotkeys for ALVR handtracking
sessions that do not emit Isaac Lab's START/STOP/RESET messages.

Hotkeys
-------
s: start recording
p: pause recording
r: reset / finalize episode
q: quit
"""

from __future__ import annotations

import argparse
import logging
import os
import queue
import threading
import time
from pathlib import Path

from isaaclab.app import AppLauncher
from isaaclab_session_utils import build_teleop_interface, configure_xr_env, spawn_stdin_reader


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Record demonstrations for Isaac Lab environments.")
    parser.add_argument("--task", type=str, required=True, help="Name of the task.")
    parser.add_argument(
        "--teleop_device",
        type=str,
        default="handtracking",
        help=(
            "Teleop device. Set here (legacy) or via the environment config. "
            "For ALVR handtracking, use the environment-configured device name."
        ),
    )
    parser.add_argument(
        "--dataset_file",
        type=str,
        default="./datasets/dataset.hdf5",
        help="File path to export recorded demos.",
    )
    parser.add_argument("--step_hz", type=int, default=30, help="Environment stepping rate in Hz.")
    parser.add_argument("--num_demos", type=int, default=0, help="Number of demonstrations to record. Set to 0 for infinite.")
    parser.add_argument(
        "--num_success_steps",
        type=int,
        default=10,
        help="Number of continuous steps with task success for concluding a demo as successful.",
    )
    parser.add_argument(
        "--enable_pinocchio",
        action="store_true",
        default=False,
        help="Enable Pinocchio.",
    )
    AppLauncher.add_app_launcher_args(parser)
    return parser


class RateLimiter:
    """Enforce a fixed loop frequency while still rendering the sim."""

    def __init__(self, hz: int):
        self._sleep_duration = 1.0 / hz
        self._render_period = min(0.033, self._sleep_duration)
        self._last_time = time.time()

    def sleep(self, env) -> None:
        next_wakeup_time = self._last_time + self._sleep_duration
        while time.time() < next_wakeup_time:
            time.sleep(self._render_period)
            env.sim.render()
        self._last_time += self._sleep_duration
        while self._last_time < time.time():
            self._last_time += self._sleep_duration


def _setup_output(dataset_file: str) -> tuple[str, str]:
    output_dir = os.path.dirname(dataset_file) or "."
    output_name = os.path.splitext(os.path.basename(dataset_file))[0]
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    return output_dir, output_name


def _build_env_cfg(args_cli, output_dir: str, output_name: str):
    from isaaclab.envs import DirectRLEnvCfg, ManagerBasedRLEnvCfg
    from isaaclab.envs.mdp.recorders.recorders_cfg import ActionStateRecorderManagerCfg
    from isaaclab.managers import DatasetExportMode
    import isaaclab_tasks  # noqa: F401
    from isaaclab_tasks.utils import parse_env_cfg

    env_cfg = parse_env_cfg(args_cli.task, device=args_cli.device, num_envs=1)
    env_cfg.env_name = args_cli.task.split(":")[-1]

    success_term = None
    if hasattr(env_cfg.terminations, "success"):
        success_term = env_cfg.terminations.success
        env_cfg.terminations.success = None

    if args_cli.xr:
        env_cfg = configure_xr_env(env_cfg, enable_cameras=args_cli.enable_cameras)

    env_cfg.terminations.time_out = None
    env_cfg.observations.policy.concatenate_terms = False
    env_cfg.recorders = ActionStateRecorderManagerCfg()
    env_cfg.recorders.dataset_export_dir_path = output_dir
    env_cfg.recorders.dataset_filename = output_name
    env_cfg.recorders.dataset_export_mode = DatasetExportMode.EXPORT_SUCCEEDED_ONLY

    if not isinstance(env_cfg, (ManagerBasedRLEnvCfg, DirectRLEnvCfg)):
        raise ValueError(f"Unsupported environment config type: {type(env_cfg).__name__}")

    return env_cfg, success_term


def main() -> None:
    parser = _build_parser()
    args_cli = parser.parse_args()
    app_launcher_args = vars(args_cli)

    if args_cli.enable_pinocchio:
        import pinocchio  # noqa: F401

    if "handtracking" in args_cli.teleop_device.lower():
        app_launcher_args["xr"] = True

    app_launcher = AppLauncher(app_launcher_args)
    simulation_app = app_launcher.app

    import gymnasium as gym
    import torch
    from isaaclab.managers import TerminationTermCfg as DoneTerm
    from isaaclab_tasks.manager_based.manipulation.lift import mdp

    if args_cli.enable_pinocchio:
        import isaaclab_tasks.manager_based.locomanipulation.pick_place  # noqa: F401
        import isaaclab_tasks.manager_based.manipulation.pick_place  # noqa: F401

    logger = logging.getLogger(__name__)
    output_dir, output_name = _setup_output(args_cli.dataset_file)
    env_cfg, success_term = _build_env_cfg(args_cli, output_dir, output_name)

    if "Lift" in args_cli.task:
        env_cfg.commands.object_pose.resampling_time_range = (1.0e9, 1.0e9)
        env_cfg.terminations.object_reached_goal = DoneTerm(func=mdp.object_reached_goal)

    try:
        env = gym.make(args_cli.task, cfg=env_cfg).unwrapped
    except Exception as exc:
        logger.error("Failed to create environment: %s", exc)
        simulation_app.close()
        return

    teleoperation_active = not args_cli.xr
    recording_active = not args_cli.xr
    should_reset_recording_instance = False
    success_step_count = 0
    rate_limiter = RateLimiter(args_cli.step_hz)

    def reset_recording_instance() -> None:
        nonlocal should_reset_recording_instance
        should_reset_recording_instance = True
        print("Reset requested")

    def start_recording_instance() -> None:
        nonlocal recording_active, teleoperation_active
        recording_active = True
        teleoperation_active = True
        print("Recording started")

    def stop_recording_instance() -> None:
        nonlocal recording_active, teleoperation_active
        recording_active = False
        teleoperation_active = False
        print("Recording paused")

    teleoperation_callbacks = {
        "R": reset_recording_instance,
        "START": start_recording_instance,
        "STOP": stop_recording_instance,
        "RESET": reset_recording_instance,
    }

    teleop_interface = build_teleop_interface(args_cli, env_cfg, teleoperation_callbacks, logger)
    if teleop_interface is None:
        env.close()
        simulation_app.close()
        return

    print(f"Using teleop device: {teleop_interface}")
    print(f"Saving demos to: {args_cli.dataset_file}")
    print("Hotkeys: s=start, p=pause, r=reset, q=quit")

    env.sim.reset()
    env.recorder_manager.reset()
    env.reset()
    teleop_interface.reset()

    command_queue: "queue.SimpleQueue[str]" = queue.SimpleQueue()
    stop_event = threading.Event()
    spawn_stdin_reader(command_queue, stop_event)

    def _process_success_condition() -> bool:
        nonlocal success_step_count
        if success_term is None:
            return False
        if bool(success_term.func(env, **success_term.params)[0]):
            success_step_count += 1
            if success_step_count >= args_cli.num_success_steps:
                env.recorder_manager.record_pre_reset([0], force_export_or_skip=False)
                env.recorder_manager.set_success_to_episodes(
                    [0], torch.tensor([[True]], dtype=torch.bool, device=env.device)
                )
                env.recorder_manager.export_episodes([0])
                print(
                    "Success condition met. Episode exported. "
                    f"Total demos: {env.recorder_manager.exported_successful_episode_count}"
                )
                return True
        else:
            success_step_count = 0
        return False

    def _handle_reset() -> None:
        nonlocal success_step_count, should_reset_recording_instance
        env.sim.reset()
        env.recorder_manager.reset()
        env.reset()
        teleop_interface.reset()
        success_step_count = 0
        should_reset_recording_instance = False
        print("Environment reset complete")

    try:
        while simulation_app.is_running() and not stop_event.is_set():
            while True:
                try:
                    command = command_queue.get_nowait()
                except queue.Empty:
                    break
                if command == "s":
                    start_recording_instance()
                elif command == "p":
                    stop_recording_instance()
                elif command == "r":
                    reset_recording_instance()
                elif command == "q":
                    stop_event.set()
                    break

            with torch.inference_mode():
                action = teleop_interface.advance()
                actions = action.repeat(env.num_envs, 1)

                if recording_active and teleoperation_active:
                    env.step(actions)
                    if _process_success_condition():
                        should_reset_recording_instance = True
                    if args_cli.num_demos > 0 and env.recorder_manager.exported_successful_episode_count >= args_cli.num_demos:
                        print(
                            f"Recorded {env.recorder_manager.exported_successful_episode_count} demos. Exiting."
                        )
                        stop_event.set()
                else:
                    env.sim.render()

                if should_reset_recording_instance:
                    _handle_reset()

            if recording_active:
                rate_limiter.sleep(env)
    except KeyboardInterrupt:
        pass
    except Exception as exc:
        logger.error("Error during recording loop: %s", exc)
    finally:
        env.close()
        print("Environment closed")
        simulation_app.close()


if __name__ == "__main__":
    main()
