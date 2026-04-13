# Copyright 2025-2026 Inria

find_program(pixi pixi REQUIRED)

# add_test(NAME FindAccelerate COMMAND ${pixi} run configure WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}/FindAccelerate)
add_test(
    NAME FindAccelerateQuiet
    COMMAND ${pixi} run configure
    WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}/FindAccelerateQuiet
)

# add_cmake_test(NAME Findmatio BUILD_TARGET all DEPENDS jrl-cmakemodules)
# add_cmake_test(NAME FindmatioQuiet BUILD_TARGET all DEPENDS jrl-cmakemodules)

# add_cmake_test(NAME Findsimde BUILD_TARGET all DEPENDS jrl-cmakemodules)
# add_cmake_test(NAME FindsimdeQuiet BUILD_TARGET all DEPENDS jrl-cmakemodules)

# add_cmake_test(NAME FindPytest BUILD_TARGET all DEPENDS jrl-cmakemodules)
# add_cmake_test(NAME FindPytestQuiet BUILD_TARGET all DEPENDS jrl-cmakemodules)
