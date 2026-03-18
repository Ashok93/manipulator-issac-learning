"""Minimal robot test — mirrors teleop.py structure exactly.

No wrappers. Just robot + ground + light, same pattern as soarm-teleop.
"""

import argparse
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--headless", action="store_true")
args_cli = parser.parse_args()

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
    ground = AssetBaseCfg(prim_path="/World/ground", spawn=sim_utils.GroundPlaneCfg())
    light = AssetBaseCfg(
        prim_path="/World/light",
        spawn=sim_utils.DomeLightCfg(intensity=2000.0, color=(0.75, 0.75, 0.75)),
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
            joint_pos={".*": 0.0},
            joint_vel={".*": 0.0},
        ),
        actuators={
            "arm": ImplicitActuatorCfg(
                joint_names_expr=["shoulder_.*", "elbow_flex", "wrist_.*"],
                effort_limit_sim=1.9,
                velocity_limit_sim=1.5,
                stiffness=40.0,
                damping=10.0,
            ),
            "gripper": ImplicitActuatorCfg(
                joint_names_expr=["gripper"],
                effort_limit_sim=2.5,
                velocity_limit_sim=1.5,
                stiffness=40.0,
                damping=10.0,
            ),
        },
    )


def main():
    sim_cfg = sim_utils.SimulationCfg(dt=1.0 / 60.0, device="cuda:0")
    sim = SimulationContext(sim_cfg)
    sim.set_camera_view([2.5, 2.5, 2.5], [0.0, 0.0, 0.0])

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


if __name__ == "__main__":
    main()
    simulation_app.close()
