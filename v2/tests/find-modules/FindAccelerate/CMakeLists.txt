cmake_minimum_required(VERSION 3.22)
project(FindAccelerateTest LANGUAGES NONE)

find_package(jrl-cmakemodules 1.2.0 CONFIG REQUIRED)

jrl_find_package(Accelerate REQUIRED)

if(NOT TARGET Accelerate::Accelerate)
    message(FATAL_ERROR "Accelerate::Accelerate imported target was not created")
endif()
