"""Minimal robot test — mirrors teleop.py structure exactly.

AppLauncher inside main(), all isaaclab imports after it, same as teleop.
"""

import argparse
from pathlib import Path


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--headless", action="store_true")
    return parser.parse_args()


def main() -> None:
    args_cli = _parse_args()

    from isaaclab.app import AppLauncher
    app_launcher = AppLauncher(headless=args_cli.headless)
    simulation_app = app_launcher.app

    # --- all isaaclab imports after AppLauncher ---
    import isaaclab.sim as sim_utils
    from isaaclab.actuators import ImplicitActuatorCfg
    from isaaclab.assets import ArticulationCfg, AssetBaseCfg
    from isaaclab.scene import InteractiveScene, InteractiveSceneCfg
    from isaaclab.sim import SimulationContext
    from isaaclab.utils import configclass

    _URDF = str(
        Path(__file__).resolve().parents[1]
        / "assets/toy_sorting/so_arm101/urdf/so_arm101.urdf"
    )

    @configclass
    class TestSceneCfg(InteractiveSceneCfg):
        ground = AssetBaseCfg(
            prim_path="/World/ground",
            spawn=sim_utils.GroundPlaneCfg(),
        )
        light = AssetBaseCfg(
            prim_path="/World/light",
            spawn=sim_utils.DomeLightCfg(intensity=2500.0, color=(0.75, 0.75, 0.75)),
        )
        robot: ArticulationCfg = ArticulationCfg(
            prim_path="{ENV_REGEX_NS}/Robot",
            spawn=sim_utils.UrdfFileCfg(
                asset_path=_URDF,
                fix_base=True,
                replace_cylinders_with_capsules=True,
                activate_contact_sensors=False,
                rigid_props=sim_utils.RigidBodyPropertiesCfg(
                    disable_gravity=False,
                    max_depenetration_velocity=5.0,
                ),
                articulation_props=sim_utils.ArticulationRootPropertiesCfg(
                    enabled_self_collisions=True,
                    solver_position_iteration_count=8,
                    solver_velocity_iteration_count=0,
                ),
                joint_drive=sim_utils.UrdfConverterCfg.JointDriveCfg(
                    gains=sim_utils.UrdfConverterCfg.JointDriveCfg.PDGainsCfg(stiffness=0, damping=0)
                ),
            ),
            init_state=ArticulationCfg.InitialStateCfg(
                rot=(1.0, 0.0, 0.0, 0.0),
                joint_pos={
                    "shoulder_pan": 0.0,
                    "shoulder_lift": 0.0,
                    "elbow_flex": 0.0,
                    "wrist_flex": 1.57,
                    "wrist_roll": 0.0,
                    "gripper": 0.0,
                },
                joint_vel={".*": 0.0},
            ),
            actuators={
                "arm": ImplicitActuatorCfg(
                    joint_names_expr=["shoulder_.*", "elbow_flex", "wrist_.*"],
                    effort_limit_sim=1.9,
                    velocity_limit_sim=1.5,
                    stiffness={
                        "shoulder_pan": 200.0,
                        "shoulder_lift": 170.0,
                        "elbow_flex": 120.0,
                        "wrist_flex": 80.0,
                        "wrist_roll": 50.0,
                    },
                    damping={
                        "shoulder_pan": 80.0,
                        "shoulder_lift": 65.0,
                        "elbow_flex": 45.0,
                        "wrist_flex": 30.0,
                        "wrist_roll": 20.0,
                    },
                ),
                "gripper": ImplicitActuatorCfg(
                    joint_names_expr=["gripper"],
                    effort_limit_sim=2.5,
                    velocity_limit_sim=1.5,
                    stiffness=60.0,
                    damping=20.0,
                ),
            },
            soft_joint_pos_limit_factor=0.9,
        )

    sim_cfg = sim_utils.SimulationCfg(dt=1.0 / 60.0, device="cuda")
    sim = SimulationContext(sim_cfg)
    sim.set_camera_view([1.5, 0.0, 1.0], [0.0, 0.0, 0.3])

    scene_cfg = TestSceneCfg(num_envs=1, env_spacing=2.0)
    scene = InteractiveScene(scene_cfg)

    print("[test_robot] Calling sim.reset() ...")
    sim.reset()
    print("[test_robot] sim.reset() done!")
    scene.reset()
    print("[test_robot] scene.reset() done! Running ...")

    while simulation_app.is_running():
        sim.step()
        scene.update(sim.get_physics_dt())

    simulation_app.close()


if __name__ == "__main__":
    main()
