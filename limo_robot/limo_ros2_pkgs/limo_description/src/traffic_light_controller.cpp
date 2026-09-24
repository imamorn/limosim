// Drives the traffic_light model's 12 lamp_<color>_<face> lamps (see
// models/traffic_light/model.sdf: red/yellow/green on each of the n/s/e/w
// faces, each lamp a single "_dome" visual) through gz-sim's
// /world/<world>/visual_config service. There's no
// ros_gz_bridge mapping for that service (it isn't a plain topic), so this
// talks gz-transport directly -- the same approach main_steering_mirror.cpp
// uses for the state it can't get over ROS.
//
// n/s are one road's two approaches and e/w are the crossing road's; each
// pair is driven in lockstep (both faces of a pair always show the same
// color) and the two pairs run a standard intersection cycle -- green on
// one axis while the other holds red, a yellow transition, then swap -- so
// the two axes never both show green.
//
// Publishing "red", "yellow", "green" or "off" on /traffic_light/state
// forces every face on all 4 sides to that one color immediately (e.g. for
// an all-red flashing-fault look) and permanently disables the automatic
// cycle for the rest of the run.

#include <array>
#include <string>

#include <ignition/msgs/boolean.pb.h>
#include <ignition/msgs/visual.pb.h>
#include <ignition/transport/Node.hh>

#include <rclcpp/rclcpp.hpp>
#include <std_msgs/msg/string.hpp>

using namespace std::chrono_literals;

namespace
{
struct Rgb
{
  float r;
  float g;
  float b;
};
// Dim/unlit base colors, matching models/traffic_light/model.sdf's default
// lamp materials.
constexpr Rgb kRedOff{0.15f, 0.02f, 0.02f};
constexpr Rgb kYellowOff{0.15f, 0.13f, 0.02f};
constexpr Rgb kGreenOff{0.02f, 0.15f, 0.02f};
constexpr Rgb kRedOn{1.0f, 0.0f, 0.0f};
constexpr Rgb kYellowOn{1.0f, 0.8f, 0.0f};
constexpr Rgb kGreenOn{0.0f, 1.0f, 0.0f};

const std::array<std::string, 2> kAxisNS{"n", "s"};
const std::array<std::string, 2> kAxisEW{"e", "w"};
}  // namespace

class TrafficLightController : public rclcpp::Node
{
public:
  TrafficLightController()
  : rclcpp::Node("traffic_light_controller")
  {
    const std::string worldName = declare_parameter<std::string>("world_name", "default");
    greenDuration_ = declare_parameter<double>("green_duration", 4.0);
    yellowDuration_ = declare_parameter<double>("yellow_duration", 1.0);

    service_ = "/world/" + worldName + "/visual_config";

    stateSub_ = create_subscription<std_msgs::msg::String>(
      "/traffic_light/state", 10,
      std::bind(&TrafficLightController::OnState, this, std::placeholders::_1));

    // ns starts green, ew starts red -- matches the phase order below.
    SetAxis(kAxisNS, "green");
    SetAxis(kAxisEW, "red");

    tick_ = create_wall_timer(200ms, std::bind(&TrafficLightController::Tick, this));
  }

private:
  void OnState(const std_msgs::msg::String::SharedPtr msg)
  {
    const std::string &color = msg->data;
    if (color != "red" && color != "yellow" && color != "green" && color != "off")
    {
      RCLCPP_WARN(get_logger(), "Ignoring unknown traffic light state '%s'", color.c_str());
      return;
    }

    manual_ = true;
    SetAxis(kAxisNS, color);
    SetAxis(kAxisEW, color);
  }

  void Tick()
  {
    if (manual_)
    {
      return;
    }

    elapsed_ += 0.2;
    const double duration = (phase_ == 1 || phase_ == 3) ? yellowDuration_ : greenDuration_;
    if (elapsed_ < duration)
    {
      return;
    }
    elapsed_ = 0.0;

    phase_ = (phase_ + 1) % 4;
    switch (phase_)
    {
      case 0:  // ns green, ew red
        SetAxis(kAxisNS, "green");
        SetAxis(kAxisEW, "red");
        break;
      case 1:  // ns yellow, ew red
        SetAxis(kAxisNS, "yellow");
        break;
      case 2:  // ns red, ew green
        SetAxis(kAxisNS, "red");
        SetAxis(kAxisEW, "green");
        break;
      case 3:  // ns red, ew yellow
        SetAxis(kAxisEW, "yellow");
        break;
    }
  }

  // Sets both faces of one axis (e.g. n+s) to the same color, all other
  // colors on those faces off.
  void SetAxis(const std::array<std::string, 2> &faces, const std::string &color)
  {
    for (const auto &face : faces)
    {
      SetVisual("lamp_red_" + face + "_dome", color == "red" ? kRedOn : kRedOff);
      SetVisual("lamp_yellow_" + face + "_dome", color == "yellow" ? kYellowOn : kYellowOff);
      SetVisual("lamp_green_" + face + "_dome", color == "green" ? kGreenOn : kGreenOff);
    }
  }

  void SetVisual(const std::string &visualName, const Rgb &rgb)
  {
    ignition::msgs::Visual req;
    req.set_name(visualName);
    // Must match models/traffic_light/model.sdf's link name -- visual_config
    // resolves parent_name via a *global* name search, so a generic name
    // like "link" would silently match the wrong entity (e.g. ground_plane's
    // link) and the request would be dropped server-side.
    req.set_parent_name("lamp_link");

    auto *material = req.mutable_material();
    material->mutable_ambient()->set_r(rgb.r);
    material->mutable_ambient()->set_g(rgb.g);
    material->mutable_ambient()->set_b(rgb.b);
    material->mutable_ambient()->set_a(1.0f);
    material->mutable_diffuse()->set_r(rgb.r);
    material->mutable_diffuse()->set_g(rgb.g);
    material->mutable_diffuse()->set_b(rgb.b);
    material->mutable_diffuse()->set_a(1.0f);
    material->mutable_emissive()->set_r(rgb.r);
    material->mutable_emissive()->set_g(rgb.g);
    material->mutable_emissive()->set_b(rgb.b);
    material->mutable_emissive()->set_a(1.0f);

    ignition::msgs::Boolean rep;
    bool result = false;
    // visual_config always replies true as soon as the request is queued --
    // it does not reflect whether the visual was actually found and
    // updated (that happens later, off-thread, and only logs to the
    // server's own console on failure). Requesting is still the correct
    // call; there's just nothing more useful to check here.
    if (!node_.Request(service_, req, 500u, rep, result))
    {
      RCLCPP_WARN(get_logger(), "visual_config request for '%s' timed out (is %s loaded?)",
        visualName.c_str(), service_.c_str());
    }
  }

  ignition::transport::Node node_;
  std::string service_;
  bool manual_ = false;
  int phase_ = 0;
  double elapsed_ = 0.0;
  double greenDuration_ = 4.0;
  double yellowDuration_ = 1.0;
  rclcpp::Subscription<std_msgs::msg::String>::SharedPtr stateSub_;
  rclcpp::TimerBase::SharedPtr tick_;
};

int main(int argc, char **argv)
{
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<TrafficLightController>());
  rclcpp::shutdown();
  return 0;
}
