#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Single ros_gz_bridge parameter_bridge for all robots spawned by
# spawn_robots_ignition.launch.xml, mirroring the start_bridge_cmd Node in
# gazebo_models_diff_mod_ignition.launch.py but covering the whole
# multi-robot topic set (see ros_gz_bridge_limo_multi.yaml).
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():

    pkg_limo_description = get_package_share_directory('limo_description')
    bridge_config_path = os.path.join(
        pkg_limo_description, 'config', 'ros_gz_bridge_limo_multi.yaml')

    use_sim_time = LaunchConfiguration('use_sim_time', default='true')

    start_bridge_cmd = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=[],
        parameters=[{'config_file': bridge_config_path, 'use_sim_time': use_sim_time}],
        output='screen')

    return LaunchDescription([
        start_bridge_cmd,
    ])
