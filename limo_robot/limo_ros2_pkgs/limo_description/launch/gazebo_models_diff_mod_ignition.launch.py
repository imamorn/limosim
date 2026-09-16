
# gz-sim (Ignition Fortress) port of gazebo_models_diff_mod.launch.py.
# See gazebo_models_diff_mod_arm_ignition.launch.py for the full rationale
# of each Classic -> gz-sim substitution; this is the same pattern applied
# to the plain (no arm/gripper) limo_four_diff variant.

import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from ament_index_python.packages import get_package_prefix


def generate_launch_description():

    package_name = 'limo_description'
    robot_name_in_model = 'limo_description'
    urdf_file_path = 'urdf/limo_four_diff_ignition.xacro'
    world_file = 'turtlebot3_tc_office_ignition.world'
    bridge_config_file_path = 'config/ros_gz_bridge_limo_diff.yaml'

    spawn_x_val = '0.0'
    spawn_y_val = '0.0'
    spawn_z_val = '0.1'
    spawn_yaw_val = '0.00'

    pkg_share = FindPackageShare(package=package_name).find(package_name)
    default_urdf_model_path = os.path.join(pkg_share, urdf_file_path)
    world_path = os.path.join(pkg_share, 'worlds', world_file)
    bridge_config_path = os.path.join(pkg_share, bridge_config_file_path)

    use_sim_time = LaunchConfiguration('use_sim_time', default='true')
    urdf_model = LaunchConfiguration('urdf_model')
    use_robot_state_pub = LaunchConfiguration('use_robot_state_pub')
    use_simulator = LaunchConfiguration('use_simulator')
    world = LaunchConfiguration('world')

    declare_use_sim_time_cmd = DeclareLaunchArgument(
        name='use_sim_time', default_value='True',
        description='Use simulation (Gazebo) clock if true')

    declare_urdf_model_path_cmd = DeclareLaunchArgument(
        name='urdf_model', default_value=default_urdf_model_path,
        description='Absolute path to robot urdf file')

    declare_use_robot_state_pub_cmd = DeclareLaunchArgument(
        name='use_robot_state_pub', default_value='True',
        description='Whether to start the robot state publisher')

    declare_use_simulator_cmd = DeclareLaunchArgument(
        name='use_simulator', default_value='True',
        description='Whether to start the simulator')

    declare_world_cmd = DeclareLaunchArgument(
        name='world', default_value=world_path,
        description='Full path to the world sdf file to load')

    start_robot_state_publisher_cmd = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[{'robot_description': Command(['xacro ', urdf_model]), 'use_sim_time': use_sim_time}]
    )

    start_gz_sim_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(FindPackageShare('ros_gz_sim').find('ros_gz_sim'), 'launch', 'gz_sim.launch.py')),
        condition=IfCondition(use_simulator),
        launch_arguments={'gz_args': [world, ' -r -v 4']}.items())

    spawn_entity_cmd = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=['-world', 'default',
                   '-topic', 'robot_description',
                   '-name', robot_name_in_model,
                   '-x', spawn_x_val,
                   '-y', spawn_y_val,
                   '-z', spawn_z_val,
                   '-Y', spawn_yaw_val],
        output='screen')

    start_bridge_cmd = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=[],
        parameters=[{'config_file': bridge_config_path, 'use_sim_time': use_sim_time}],
        output='screen')

    # Local models (ground_plane_invisible, office) and the package://mesh ->
    # model://<pkg> rewrite both resolve via GZ_SIM_RESOURCE_PATH; see
    # gazebo_models_diff_mod_arm_ignition.launch.py for the full rationale.
    install_dir = get_package_prefix(package_name)
    models_path = os.path.join(pkg_share, 'models')
    resource_paths = [install_dir + '/share', models_path]
    if 'GZ_SIM_RESOURCE_PATH' in os.environ:
        os.environ['GZ_SIM_RESOURCE_PATH'] = os.environ['GZ_SIM_RESOURCE_PATH'] + ':' + ':'.join(resource_paths)
    else:
        os.environ['GZ_SIM_RESOURCE_PATH'] = ':'.join(resource_paths)

    ld = LaunchDescription()

    ld.add_action(declare_use_sim_time_cmd)
    ld.add_action(declare_urdf_model_path_cmd)
    ld.add_action(declare_use_robot_state_pub_cmd)
    ld.add_action(declare_use_simulator_cmd)
    ld.add_action(declare_world_cmd)

    ld.add_action(start_gz_sim_cmd)
    ld.add_action(spawn_entity_cmd)
    ld.add_action(start_robot_state_publisher_cmd)
    ld.add_action(start_bridge_cmd)

    return ld
