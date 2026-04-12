cmake_minimum_required(VERSION 3.22)
project(FindmatioQuietTest LANGUAGES NONE)

find_package(jrl-cmakemodules CONFIG REQUIRED)

set(CMAKE_FIND_USE_CMAKE_PATH FALSE)
set(CMAKE_FIND_USE_CMAKE_ENVIRONMENT_PATH FALSE)
set(CMAKE_FIND_USE_SYSTEM_ENVIRONMENT_PATH FALSE)
set(CMAKE_FIND_USE_CMAKE_SYSTEM_PATH FALSE)
set(CMAKE_FIND_USE_PACKAGE_REGISTRY FALSE)
set(CMAKE_FIND_USE_SYSTEM_PACKAGE_REGISTRY FALSE)

jrl_find_package(matio QUIET)

if(matio_FOUND)
    message(FATAL_ERROR "matio_FOUND should be FALSE when no search paths are available")
endif()
