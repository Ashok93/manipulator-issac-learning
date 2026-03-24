"""Shared helpers for Isaac Lab VR teleop and recording launchers."""

from __future__ import annotations

import queue
import select
import sys
import termios
import threading
import tty
from collections.abc import Callable


def spawn_stdin_reader(command_queue: "queue.SimpleQueue[str]", stop_event: threading.Event) -> threading.Thread:
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


def configure_xr_env(env_cfg, enable_cameras: bool):
    """Apply Isaac Lab XR-specific environment tweaks."""
    from isaaclab.devices.openxr import remove_camera_configs

    if not enable_cameras:
        env_cfg = remove_camera_configs(env_cfg)
        env_cfg.sim.render.antialiasing_mode = "DLSS"
    return env_cfg


def build_teleop_interface(args_cli, env_cfg, callbacks: dict[str, Callable[[], None]], logger):
    """Create a teleop device and attach session callbacks."""
    from isaaclab.devices import Se3Gamepad, Se3GamepadCfg, Se3Keyboard, Se3KeyboardCfg, Se3SpaceMouse, Se3SpaceMouseCfg
    from isaaclab.devices.teleop_device_factory import create_teleop_device

    teleop_interface = None
    try:
        if hasattr(env_cfg, "teleop_devices") and args_cli.teleop_device in env_cfg.teleop_devices.devices:
            teleop_interface = create_teleop_device(
                args_cli.teleop_device,
                env_cfg.teleop_devices.devices,
                callbacks,
            )
        else:
            logger.warning(
                "No teleop device '%s' found in environment config. Creating default.",
                args_cli.teleop_device,
            )
            sensitivity = args_cli.sensitivity
            device_name = args_cli.teleop_device.lower()
            if device_name == "keyboard":
                teleop_interface = Se3Keyboard(
                    Se3KeyboardCfg(pos_sensitivity=0.05 * sensitivity, rot_sensitivity=0.05 * sensitivity)
                )
            elif device_name == "spacemouse":
                teleop_interface = Se3SpaceMouse(
                    Se3SpaceMouseCfg(pos_sensitivity=0.05 * sensitivity, rot_sensitivity=0.05 * sensitivity)
                )
            elif device_name == "gamepad":
                teleop_interface = Se3Gamepad(
                    Se3GamepadCfg(pos_sensitivity=0.1 * sensitivity, rot_sensitivity=0.1 * sensitivity)
                )
            else:
                logger.error("Unsupported teleop device: %s", args_cli.teleop_device)
                logger.error("Configure the teleop device in the environment config.")
                return None

        for key, callback in callbacks.items():
            try:
                teleop_interface.add_callback(key, callback)
            except (ValueError, TypeError) as exc:
                logger.warning("Failed to add callback for key %s: %s", key, exc)
    except Exception as exc:
        logger.error("Failed to create teleop interface: %s", exc)
        return None

    return teleop_interface
