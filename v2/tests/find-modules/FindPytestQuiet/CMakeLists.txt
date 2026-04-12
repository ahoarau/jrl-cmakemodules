cmake_minimum_required(VERSION 3.22)
project(FindPytestQuietTest LANGUAGES NONE)

find_package(jrl-cmakemodules 1.2.0 CONFIG REQUIRED)

# Python::Interpreter is required by FindPytest.cmake before it can proceed.
# Find it with full search paths before restricting them.
find_package(Python REQUIRED COMPONENTS Interpreter)

set(CMAKE_FIND_USE_CMAKE_PATH FALSE)
set(CMAKE_FIND_USE_CMAKE_ENVIRONMENT_PATH FALSE)
set(CMAKE_FIND_USE_SYSTEM_ENVIRONMENT_PATH FALSE)
set(CMAKE_FIND_USE_CMAKE_SYSTEM_PATH FALSE)
set(CMAKE_FIND_USE_PACKAGE_REGISTRY FALSE)
set(CMAKE_FIND_USE_SYSTEM_PACKAGE_REGISTRY FALSE)

jrl_find_package(Pytest QUIET)

if(Pytest_FOUND)
    message(FATAL_ERROR "Pytest_FOUND should be FALSE when no search paths are available")
endif()
