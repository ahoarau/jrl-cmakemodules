# Copyright 2025-2026 Inria

cmake_minimum_required(VERSION 3.22)

# Description: This script lists all functions and macros defined in a given CMake file,
# excluding those whose names start with an underscore (_), which are considered private.
#
# Usage: cmake -DINPUT_FILE=path/to/CMakeLists.txt -P ListFunctionsAndMacros.cmake
# Example: cmake -DINPUT_FILE=jrl.cmake -P ListFunctionsAndMacros.cmake

if(NOT CMAKE_SCRIPT_MODE_FILE)
    message(FATAL_ERROR "This script is intended to be run in script mode only. Use -P <script>.")
endif()

if(NOT DEFINED INPUT_FILE)
    message(
        FATAL_ERROR
        "INPUT_FILE is not defined. Please specify it using -DINPUT_FILE=<path/to/file> BEFORE -P ListFunctionsAndMacros.cmake"
    )
endif()

get_filename_component(INPUT_FILE_ABS "${INPUT_FILE}" ABSOLUTE)

if(NOT EXISTS "${INPUT_FILE_ABS}")
    message(FATAL_ERROR "File not found: ${INPUT_FILE_ABS}")
endif()

file(STRINGS "${INPUT_FILE_ABS}" file_content)

foreach(line IN LISTS file_content)
    # Check for function definitions (case insensitive for keyword)
    if("${line}" MATCHES "^[ \t]*[Ff][Uu][Nn][Cc][Tt][Ii][Oo][Nn][ \t]*\\([ \t]*([A-Za-z0-9_]+)")
        set(func_name "${CMAKE_MATCH_1}")
        if(NOT "${func_name}" MATCHES "^_")
            message("${func_name}")
        endif()
    endif()

    # Check for macro definitions (case insensitive for keyword)
    if("${line}" MATCHES "^[ \t]*[Mm][Aa][Cc][Rr][Oo][ \t]*\\([ \t]*([A-Za-z0-9_]+)")
        set(macro_name "${CMAKE_MATCH_1}")
        if(NOT "${macro_name}" MATCHES "^_")
            message("${macro_name}")
        endif()
    endif()
endforeach()
