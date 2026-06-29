cmake_minimum_required(VERSION 3.22)
project(rc-library-fail VERSION 1.0.0 LANGUAGES CXX)

find_package(jrl-cmakemodules CONFIG REQUIRED)
jrl_configure_defaults()

add_library(rc-library-fail SHARED src/mylib.cpp)

# Force the RPATH to contain the build directory upon installation to trigger the check.
# We also include a standard prefix directory so there is a valid RPATH component too.
set_target_properties(
    rc-library-fail
    PROPERTIES INSTALL_RPATH "${CMAKE_INSTALL_PREFIX}/lib;${CMAKE_BINARY_DIR}"
)

target_include_directories(
    rc-library-fail
    PUBLIC $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include> $<INSTALL_INTERFACE:include>
)

jrl_target_headers(rc-library-fail PUBLIC
    HEADERS
        include/rc-library/mylib.hpp
    BASE_DIRS
        include
)

jrl_add_export_component(NAME mycomponent TARGETS rc-library-fail)
jrl_export_package()

jrl_include_ctest()
enable_testing()
