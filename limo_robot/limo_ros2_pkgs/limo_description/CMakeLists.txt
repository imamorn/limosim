cmake_minimum_required(VERSION 3.5)
project(limo_description)

# Default to C99
if(NOT CMAKE_C_STANDARD)
  set(CMAKE_C_STANDARD 99)
endif()

# Default to C++14
if(NOT CMAKE_CXX_STANDARD)
  set(CMAKE_CXX_STANDARD 14)
endif()

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# find dependencies
find_package(ament_cmake REQUIRED)
find_package(ignition-transport11 REQUIRED)
find_package(ignition-msgs8 REQUIRED)
find_package(rclcpp REQUIRED)
find_package(std_msgs REQUIRED)
# uncomment the following section in order to fill in
# further dependencies manually.
# find_package(<dependency> REQUIRED)
install(
  DIRECTORY launch  meshes rviz urdf worlds models config
  DESTINATION share/${PROJECT_NAME}
)
install(
  PROGRAMS scripts/omni_wheel_spin_publisher.py
  DESTINATION lib/${PROJECT_NAME}
)

add_executable(main_steering_mirror src/main_steering_mirror.cpp)
target_link_libraries(main_steering_mirror
  ignition-transport11::ignition-transport11
  ignition-msgs8::ignition-msgs8
)
ament_target_dependencies(main_steering_mirror rclcpp std_msgs)
install(
  TARGETS main_steering_mirror
  DESTINATION lib/${PROJECT_NAME}
)

add_executable(traffic_light_controller src/traffic_light_controller.cpp)
target_link_libraries(traffic_light_controller
  ignition-transport11::ignition-transport11
  ignition-msgs8::ignition-msgs8
)
ament_target_dependencies(traffic_light_controller rclcpp std_msgs)
install(
  TARGETS traffic_light_controller
  DESTINATION lib/${PROJECT_NAME}
)
if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  # the following line skips the linter which checks for copyrights
  # uncomment the line when a copyright and license is not present in all source files
  #set(ament_cmake_copyright_FOUND TRUE)
  # the following line skips cpplint (only works in a git repo)
  # uncomment the line when this package is not in a git repo
  #set(ament_cmake_cpplint_FOUND TRUE)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()
