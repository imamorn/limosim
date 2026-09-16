#!/usr/bin/python3
# -*- coding: utf-8 -*-
# gz-sim (Ignition Fortress) port of start_world.launch.py.
# See limo_description/launch/start_world_ignition.launch.py for the same pattern.
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from ament_index_python.packages import get_package_prefix
from launch.substitutions import LaunchConfiguration


def generate_launch_description():

    pkg_ros_gz_sim = get_package_share_directory('ros_gz_sim')
    pkg_mycobot_gazebo = get_package_share_directory('mycobot_gazebo')

    description_package_name = "mycobot_description"
    install_dir = get_package_prefix(description_package_name)

    gazebo_models_path = os.path.join(pkg_mycobot_gazebo, 'models')

    if 'GZ_SIM_RESOURCE_PATH' in os.environ:
        os.environ['GZ_SIM_RESOURCE_PATH'] = os.environ['GZ_SIM_RESOURCE_PATH'] + ':' + install_dir + \
            '/share' + ':' + gazebo_models_path
    else:
        os.environ['GZ_SIM_RESOURCE_PATH'] = install_dir + \
            "/share" + ':' + gazebo_models_path

    print("GZ_SIM_RESOURCE_PATH=="+str(os.environ["GZ_SIM_RESOURCE_PATH"]))

    world = LaunchConfiguration('world')

    gz_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_ros_gz_sim, 'launch', 'gz_sim.launch.py'),
        ),
        launch_arguments={'gz_args': [world, ' -r -v 4']}.items(),
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            'world',
            default_value=[os.path.join(
                pkg_mycobot_gazebo, 'worlds', 'simple_ignition.world'), ''],
            description='SDF world file'),
        DeclareLaunchArgument(
            'verbose', default_value='true',
            description='Set "true" to increase messages written to the terminal.'
        ),
        gz_sim,
    ])
