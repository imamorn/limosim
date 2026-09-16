#!/usr/bin/env python3

# VelocityControl drives limo_omni's chassis (base_footprint) kinematically
# and never commands the wheel joints, so with only that plugin the wheels
# sit undriven. This node approximates wheel spin from forward speed
# (wheel_angular_velocity = cmd_vel.linear.x / wheel_radius) and republishes
# it to the per-wheel topics that limo_multi_omni_ignition.xacro's
# JointController plugins consume, so the wheels visually roll while moving
# and stop with the chassis. It ignores linear.y/angular.z: these are plain
# round wheels, not Mecanum rollers, so lateral/rotational holonomic motion
# has no physically meaningful wheel-spin equivalent to show.

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from std_msgs.msg import Float64

WHEEL_JOINTS = (
    "front_left_wheel",
    "front_right_wheel",
    "rear_left_wheel",
    "rear_right_wheel",
)


class OmniWheelSpinPublisher(Node):

    def __init__(self):
        super().__init__("omni_wheel_spin_publisher")

        self.declare_parameter("robot_name", "limo_omni")
        self.declare_parameter("wheel_radius", 0.045)

        robot_name = self.get_parameter("robot_name").value
        self.wheel_radius = self.get_parameter("wheel_radius").value

        self.wheel_publishers = [
            self.create_publisher(Float64, f"{robot_name}/{joint}/cmd_vel", 10)
            for joint in WHEEL_JOINTS
        ]

        self.create_subscription(
            Twist, f"{robot_name}/cmd_vel", self.on_cmd_vel, 10
        )

    def on_cmd_vel(self, msg):
        wheel_velocity = Float64()
        wheel_velocity.data = msg.linear.x / self.wheel_radius
        for publisher in self.wheel_publishers:
            publisher.publish(wheel_velocity)


def main():
    rclpy.init()
    node = OmniWheelSpinPublisher()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
