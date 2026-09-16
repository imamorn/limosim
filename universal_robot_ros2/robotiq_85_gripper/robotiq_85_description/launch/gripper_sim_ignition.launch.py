# gz-sim (Ignition Fortress) port of gripper_sim.launch.py.
# gazebo_ros/gazebo.launch.py -> ros_gz_sim's gz_sim.launch.py (gz-sim's
# built-in empty.sdf world, matching Classic's default empty world here);
# gazebo_ros/spawn_entity.py -> ros_gz_sim's "create" executable.

from launch import LaunchDescription
from launch.actions import ExecuteProcess, IncludeLaunchDescription, RegisterEventHandler
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, FindExecutable, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
import launch_ros.descriptions


def generate_launch_description():

    robot_description_content = Command(
        [
            PathJoinSubstitution([FindExecutable(name='xacro')]),
            ' ',
            PathJoinSubstitution(
                [FindPackageShare(
                    'robotiq_85_description'),
                    'urdf',
                    'robotiq_85_gripper_ignition.urdf.xacro']
            ),
        ]
    )
    robot_description_content=launch_ros.descriptions.ParameterValue(robot_description_content, value_type=str)
    robot_description = {'robot_description': robot_description_content}

    node_robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[robot_description]
    )

    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [FindPackageShare('ros_gz_sim'), '/launch', '/gz_sim.launch.py']
        ),
        launch_arguments={'gz_args': 'empty.sdf -r -v 4'}.items(),
    )

    spawn_entity = Node(package='ros_gz_sim', executable='create',
                        arguments=['-world', 'empty',
                                   '-topic', 'robot_description',
                                   '-name', 'gripper'],
                        output='screen')

    load_joint_state_controller = ExecuteProcess(
        cmd=['ros2', 'control', 'load_controller', '--set-state', 'active',
             'joint_state_broadcaster'],
        output='screen'
    )

    load_gripper_controller = ExecuteProcess(
        cmd=['ros2', 'control', 'load_controller', '--set-state', 'active',
             'gripper_controller'],
        output='screen'
    )

    return LaunchDescription([
        RegisterEventHandler(
          event_handler=OnProcessExit(
                target_action=spawn_entity,
                on_exit=[load_joint_state_controller],
            )
        ),
        RegisterEventHandler(
            event_handler=OnProcessExit(
                target_action=load_joint_state_controller,
                on_exit=[load_gripper_controller],
            )
        ),
        gazebo,
        node_robot_state_publisher,
        spawn_entity,
    ])
