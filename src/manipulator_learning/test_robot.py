"""Entry point for test_robot — delegates to scripts/test_robot.py:main."""

from __future__ import annotations

import argparse


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--sim_device", default="cuda")
    return parser.parse_args()


def main() -> None:
    args_cli = _parse_args()

    from isaaclab.app import AppLauncher
    app_launcher = AppLauncher(headless=args_cli.headless)
    simulation_app = app_launcher.app

    import isaaclab.sim as sim_utils
    from isaaclab.scene import InteractiveScene
    from isaaclab.sim import SimulationContext

    from manipulator_learning.envs.test_scene_cfg import TestSceneCfg

    sim_cfg = sim_utils.SimulationCfg(dt=1.0 / 60.0, device=args_cli.sim_device)
    sim = SimulationContext(sim_cfg)
    sim.set_camera_view([1.5, 0.0, 1.0], [0.0, 0.0, 0.3])

    scene_cfg = TestSceneCfg(num_envs=1, env_spacing=2.0)
    scene = InteractiveScene(scene_cfg)

    # Pump the event loop so the renderer finishes initializing before sim.reset()
    for _ in range(10):
        simulation_app.update()

    print("[test_robot] Calling sim.reset() ...")
    sim.reset()
    print("[test_robot] sim.reset() done!")
    scene.reset()
    print("[test_robot] Running ...")

    while simulation_app.is_running():
        sim.step()
        scene.update(sim.get_physics_dt())

    simulation_app.close()
