cmake_minimum_required(VERSION 3.22)
project(rc-library-ok VERSION 1.0.0 LANGUAGES CXX)

find_package(jrl-cmakemodules CONFIG REQUIRED)
jrl_configure_defaults()

add_library(rc-library-ok SHARED src/mylib.cpp)

# Set a standard, valid INSTALL_RPATH that does not contain references to the build directory.
set_target_properties(rc-library-ok PROPERTIES INSTALL_RPATH "${CMAKE_INSTALL_PREFIX}/lib")

target_include_directories(
    rc-library-ok
    PUBLIC $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include> $<INSTALL_INTERFACE:include>
)

jrl_target_headers(rc-library-ok PUBLIC
    HEADERS
        include/rc-library/mylib.hpp
    BASE_DIRS
        include
)

jrl_add_export_component(NAME mycomponent TARGETS rc-library-ok)
jrl_export_package()

jrl_include_ctest()
enable_testing()
