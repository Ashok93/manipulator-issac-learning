"""Isaac Lab ArticulationCfg for SO-ARM 101.

The URDF and STL mesh files live in assets/toy_sorting/so_arm101/urdf/
(downloaded via assets/download.py — not committed to git).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class JointDefaults:
    shoulder_pan: float = 0.0
    shoulder_lift: float = 0.0
    elbow_flex: float = 0.0
    wrist_flex: float = 1.57
    wrist_roll: float = 0.0
    gripper: float = 0.0


JOINT_DEFAULTS = JointDefaults()

ARM_STIFFNESS = {
    "shoulder_pan": 200.0,
    "shoulder_lift": 170.0,
    "elbow_flex": 120.0,
    "wrist_flex": 80.0,
    "wrist_roll": 50.0,
}
ARM_DAMPING = {
    "shoulder_pan": 80.0,
    "shoulder_lift": 65.0,
    "elbow_flex": 45.0,
    "wrist_flex": 30.0,
    "wrist_roll": 20.0,
}

# 6 controllable joints (5 arm + 1 gripper)
NUM_JOINTS = 6


def make_so_arm101_cfg(urdf_path: str):
    """Return an ``ArticulationCfg`` for SO-ARM 101 given a resolved URDF path.

    Import is deferred so this file can be read without Isaac Lab installed.
    """
    import isaaclab.sim as sim_utils
    from isaaclab.actuators import ImplicitActuatorCfg
    from isaaclab.assets.articulation import ArticulationCfg

    return ArticulationCfg(
        spawn=sim_utils.UrdfFileCfg(
            asset_path=urdf_path,
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
                gains=sim_utils.UrdfConverterCfg.JointDriveCfg.PDGainsCfg(
                    stiffness=0, damping=0
                )
            ),
        ),
        init_state=ArticulationCfg.InitialStateCfg(
            pos=(0.15, -0.20, 0.80),  # on table surface (z=0.80), front-right edge
            rot=(1.0, 0.0, 0.0, 0.0),
            joint_pos={
                "shoulder_pan": JOINT_DEFAULTS.shoulder_pan,
                "shoulder_lift": JOINT_DEFAULTS.shoulder_lift,
                "elbow_flex": JOINT_DEFAULTS.elbow_flex,
                "wrist_flex": JOINT_DEFAULTS.wrist_flex,
                "wrist_roll": JOINT_DEFAULTS.wrist_roll,
                "gripper": JOINT_DEFAULTS.gripper,
            },
            joint_vel={".*": 0.0},
        ),
        actuators={
            "arm": ImplicitActuatorCfg(
                joint_names_expr=["shoulder_.*", "elbow_flex", "wrist_.*"],
                effort_limit_sim=1.9,
                velocity_limit_sim=1.5,
                stiffness=ARM_STIFFNESS,
                damping=ARM_DAMPING,
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
