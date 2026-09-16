// limo_acker's main_steering_link is a purely cosmetic steering-rack visual
// with no drive of its own (see limo_multi_acker_ignition.xacro): the
// Classic gazebo_ros_ackermann_drive plugin used to animate it via a
// <steering_wheel_joint> parameter that has no equivalent in gz-sim's native
// AckermannSteering system. This relays the real front_left_steering joint
// angle (published by a JointStatePublisher) onto main_steering's
// JointPositionController so the visual tracks the actual steering angle.
//
// Plain gz-transport, not ROS: ros_gz_bridge has no mapping for
// ignition::msgs::Model, so bridging the state topic to ROS isn't an option.
//
// Optionally also republishes that same angle on a ROS std_msgs/Float32
// topic, matching the Classic gazebo_ros_ackermann_drive plugin's
// <publish_steerangle> "steerangle" topic (average of left/right steering
// angle there; here it's simply front_left_steering's angle, since that's
// the value already available from the JointStatePublisher above).

#include <iostream>
#include <memory>
#include <string>
#include <vector>

#include <ignition/msgs/double.pb.h>
#include <ignition/msgs/model.pb.h>
#include <ignition/transport/Node.hh>

#include <rclcpp/rclcpp.hpp>
#include <std_msgs/msg/float32.hpp>

namespace
{
std::string g_sourceJoint;
ignition::transport::Node::Publisher g_publisher;
rclcpp::Publisher<std_msgs::msg::Float32>::SharedPtr g_steerAnglePub;

void OnState(const ignition::msgs::Model &_msg)
{
  for (int i = 0; i < _msg.joint_size(); ++i)
  {
    const auto &joint = _msg.joint(i);
    if (joint.name() == g_sourceJoint)
    {
      const double position = joint.axis1().position();

      ignition::msgs::Double out;
      out.set_data(position);
      g_publisher.Publish(out);

      if (g_steerAnglePub)
      {
        std_msgs::msg::Float32 steerAngle;
        steerAngle.data = static_cast<float>(position);
        g_steerAnglePub->publish(steerAngle);
      }
      break;
    }
  }
}
}  // namespace

int main(int argc, char **argv)
{
  // ros2 launch's Node/<node> actions always append "--ros-args" (and any
  // remap/param args) to the executable's argv, so plain argc/argv counting
  // here would misparse or reject every invocation from a launch file.
  // Strip those out first and count only the args this program defines.
  rclcpp::init(argc, argv);
  const std::vector<std::string> args = rclcpp::remove_ros_arguments(argc, argv);

  if (args.size() != 4 && args.size() != 5)
  {
    std::cerr << "Usage: " << args[0]
              << " <joint_state_topic> <position_cmd_topic> <source_joint_name>"
                 " [ros_steerangle_topic]"
              << std::endl;
    rclcpp::shutdown();
    return 1;
  }

  const std::string stateTopic = args[1];
  const std::string cmdTopic = args[2];
  g_sourceJoint = args[3];

  auto rosNode = std::make_shared<rclcpp::Node>("main_steering_mirror");
  if (args.size() == 5)
  {
    g_steerAnglePub = rosNode->create_publisher<std_msgs::msg::Float32>(args[4], 1);
  }

  ignition::transport::Node node;
  g_publisher = node.Advertise<ignition::msgs::Double>(cmdTopic);
  if (!g_publisher)
  {
    std::cerr << "Failed to advertise [" << cmdTopic << "]" << std::endl;
    rclcpp::shutdown();
    return 1;
  }

  if (!node.Subscribe(stateTopic, &OnState))
  {
    std::cerr << "Failed to subscribe to [" << stateTopic << "]" << std::endl;
    rclcpp::shutdown();
    return 1;
  }

  ignition::transport::waitForShutdown();

  rclcpp::shutdown();
  return 0;
}
