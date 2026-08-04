jrl_test_case(
  NAME "_jrl_get_library_output_dirs: nothing configured gives an empty list"
  CODE [[
    _jrl_get_library_output_dirs(DIRS_VAR dirs)
    list(LENGTH dirs count)
    _jrl_check(count EQUAL 0)
  ]]
)

jrl_test_case(
  NAME "_jrl_get_library_output_dirs: single-config uses the directory as is"
  CODE [[
    set(CMAKE_LIBRARY_OUTPUT_DIRECTORY "/build/lib")
    _jrl_get_library_output_dirs(DIRS_VAR dirs)
    list(JOIN dirs " " joined)
    _jrl_check("${joined}" STREQUAL "/build/lib")
  ]]
)

jrl_test_case(
  NAME "_jrl_get_library_output_dirs: multi-config appends the configuration name"
  CODE [[
    # Only the configuration-agnostic variable set: the generator appends the
    # configuration name, so libraries land in lib/Debug and lib/Release.
    set(CMAKE_CONFIGURATION_TYPES Debug Release)
    set(CMAKE_LIBRARY_OUTPUT_DIRECTORY "/build/lib")
    _jrl_get_library_output_dirs(DIRS_VAR dirs)
    list(JOIN dirs " " joined)
    _jrl_check("${joined}" STREQUAL "/build/lib/Debug /build/lib/Release")
  ]]
)

jrl_test_case(
  NAME "_jrl_get_library_output_dirs: multi-config with per-config dirs collapses to one entry"
  CODE [[
    # What jrl_configure_default_binary_dirs() sets up.
    set(CMAKE_CONFIGURATION_TYPES Debug Release)
    set(CMAKE_LIBRARY_OUTPUT_DIRECTORY "/build/lib")
    set(CMAKE_LIBRARY_OUTPUT_DIRECTORY_DEBUG "/build/lib")
    set(CMAKE_LIBRARY_OUTPUT_DIRECTORY_RELEASE "/build/lib")
    _jrl_get_library_output_dirs(DIRS_VAR dirs)
    list(JOIN dirs " " joined)
    _jrl_check("${joined}" STREQUAL "/build/lib")
  ]]
)

jrl_test_case(
  NAME "_jrl_get_library_output_dirs: a per-config dir set for one configuration only is reported"
  CODE [[
    set(CMAKE_CONFIGURATION_TYPES Debug Release)
    set(CMAKE_LIBRARY_OUTPUT_DIRECTORY "/build/lib")
    set(CMAKE_LIBRARY_OUTPUT_DIRECTORY_RELEASE "/build/lib")
    _jrl_get_library_output_dirs(DIRS_VAR dirs)
    list(JOIN dirs " " joined)
    _jrl_check("${joined}" STREQUAL "/build/lib/Debug /build/lib")
  ]]
)

jrl_test_case(
  NAME "_jrl_get_library_output_dirs: per-config dirs alone are enough"
  CODE [[
    set(CMAKE_CONFIGURATION_TYPES Debug Release)
    set(CMAKE_LIBRARY_OUTPUT_DIRECTORY_DEBUG "/build/lib")
    set(CMAKE_LIBRARY_OUTPUT_DIRECTORY_RELEASE "/build/lib")
    _jrl_get_library_output_dirs(DIRS_VAR dirs)
    list(JOIN dirs " " joined)
    _jrl_check("${joined}" STREQUAL "/build/lib")
  ]]
)

jrl_test_case(
  NAME "_jrl_get_library_output_dirs: a missing output variable is reported"
  CODE [[
    _jrl_get_library_output_dirs()
  ]]
  PROPERTIES PASS_REGULAR_EXPRESSION "Variable 'arg_DIRS_VAR' is not defined"
)

jrl_test_case(
  NAME "_jrl_get_library_output_dirs: an unknown argument is rejected"
  CODE [[
    _jrl_get_library_output_dirs(DIRS_VAR dirs NOT_AN_ARGUMENT whatever)
  ]]
  PROPERTIES PASS_REGULAR_EXPRESSION "Unrecognized arguments: NOT_AN_ARGUMENT whatever"
)
