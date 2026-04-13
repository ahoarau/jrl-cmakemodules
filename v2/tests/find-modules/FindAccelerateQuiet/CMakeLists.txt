cmake_minimum_required(VERSION 3.22)
project(FindAccelerateQuietTest LANGUAGES NONE)

find_package(jrl-cmakemodules 1.2.0 CONFIG REQUIRED)

if(NOT CMAKE_SYSTEM_NAME STREQUAL "Darwin")
    message(STATUS "Accelerate is only available on macOS, skipping test")
    return()
endif()

jrl_find_package(Accelerate QUIET)

if(Accelerate_FOUND)
    message(FATAL_ERROR "Accelerate_FOUND should be FALSE when no search paths are available")
endif()
