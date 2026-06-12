cmake_minimum_required(VERSION 3.22)
project(pm-project LANGUAGES NONE)

find_package(jrl-cmakemodules 1.2.0 CONFIG REQUIRED)

message(STATUS "CONDA_PREFIX: '$ENV{CONDA_PREFIX}'")

if(DEFINED ENV{CONDA_PREFIX})
    if(WIN32)
        set(Python_EXECUTABLE
            "$ENV{CONDA_PREFIX}/python.exe"
            CACHE FILEPATH
            "Python interpreter"
            FORCE
        )
    else()
        set(Python_EXECUTABLE
            "$ENV{CONDA_PREFIX}/bin/python"
            CACHE FILEPATH
            "Python interpreter"
            FORCE
        )
    endif()
endif()

jrl_find_python(REQUIRED COMPONENTS Interpreter)

jrl_generate_pyproject_metadata(
    PYPROJECT_TOML "${CMAKE_CURRENT_SOURCE_DIR}/pyproject.toml"
    OUTPUT_FILE "${CMAKE_CURRENT_BINARY_DIR}/METADATA"
    INSTALL_DESTINATION "dist-info"
)

# Test that the metadata file was generated and has expected content during the build
add_custom_target(
    verify_metadata
    ALL
    COMMAND ${CMAKE_COMMAND} -E echo "Checking generated metadata..."
    COMMAND
        ${CMAKE_COMMAND} -D METADATA_FILE=${CMAKE_CURRENT_BINARY_DIR}/METADATA -P
        ${CMAKE_CURRENT_SOURCE_DIR}/verify.cmake
)
