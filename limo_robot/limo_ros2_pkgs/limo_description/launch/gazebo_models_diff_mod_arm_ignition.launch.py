
# gz-sim (Ignition Fortress) port of gazebo_models_diff_mod_arm.launch.py.
# See gazebo_models_diff_mod_arm.launch.py for the Gazebo-Classic original,
# which is left untouched. Differences:
#   - gzserver.launch.py + gzclient.launch.py -> ros_gz_sim's gz_sim.launch.py
#   - gazebo_ros/spawn_entity.py -> ros_gz_sim's "create" executable
#   - adds a ros_gz_bridge parameter_bridge node (config/ros_gz_bridge_limo_arm.yaml)
#   - points at the _ignition xacro/world variants

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
    urdf_file_path = 'urdf/limo_four_diff_arm_ignition.xacro'
    world_file = 'turtlebot3_tc_office_grasp_ignition.world'
    bridge_config_file_path = 'config/ros_gz_bridge_limo_arm.yaml'

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

    # The LaserScan/Image/PointCloud2 messages bridged above carry gz-sim's
    # internal scoped sensor frame names (e.g.
    # "<robot_name_in_model>/base_footprint/laser") rather than the URDF
    # link names robot_state_publisher publishes on /tf, so rviz can't
    # transform them into the robot's TF tree. Both sensors are mounted
    # with an identity pose in their SDF <sensor> block, so bridge them
    # onto the corresponding URDF frames with a zero static transform:
    # gpu_lidar keeps the physical (REP103) convention -> laser_link;
    # rgbd_camera publishes in optical (Z-forward) convention -> the
    # camera's *_optical_frame link, not the physical camera link.
    start_laser_frame_bridge_cmd = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='laser_frame_bridge',
        arguments=['--frame-id', 'laser_link',
                   '--child-frame-id', robot_name_in_model + '/base_footprint/laser'],
        parameters=[{'use_sim_time': use_sim_time}])

    start_camera_frame_bridge_cmd = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='camera_frame_bridge',
        arguments=['--frame-id', 'camera_depth_optical_frame',
                   '--child-frame-id', robot_name_in_model + '/base_footprint/sensor_camera'],
        parameters=[{'use_sim_time': use_sim_time}])

    # Resource resolution for gz-sim: the world's local models
    # (ground_plane_invisible, office, perception_table) are found via
    # model:// URIs, and libsdformat also rewrites the URDF's package://
    # mesh URIs to model://<pkg>/... -- both are resolved by scanning
    # GZ_SIM_RESOURCE_PATH for a directory literally named <pkg>, so each
    # package's install "share" dir (which contains a <pkg>/ subdir) needs
    # to be on this path, mirroring Classic's GAZEBO_MODEL_PATH setup in
    # gazebo_models_diff_mod_arm.launch.py.
    description_package_name = 'limo_description'
    install_dir = get_package_prefix(description_package_name)
    mycobot_description_install_dir = get_package_prefix('mycobot_description')
    robotiq_85_description_install_dir = get_package_prefix('robotiq_85_description')
    models_path = os.path.join(pkg_share, 'models')
    resource_paths = [
        install_dir + '/share',
        mycobot_description_install_dir + '/share',
        robotiq_85_description_install_dir + '/share',
        models_path,
    ]
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
    ld.add_action(start_laser_frame_bridge_cmd)
    ld.add_action(start_camera_frame_bridge_cmd)

    return ld
