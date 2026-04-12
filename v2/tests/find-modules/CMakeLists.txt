# Copyright 2025-2026 Inria

if(APPLE)
    add_cmake_test(NAME FindAccelerate BUILD_TARGET all DEPENDS jrl-cmakemodules)
    add_cmake_test(NAME FindAccelerateQuiet BUILD_TARGET all DEPENDS jrl-cmakemodules)
endif()

add_cmake_test(NAME Findmatio BUILD_TARGET all DEPENDS jrl-cmakemodules)
add_cmake_test(NAME FindmatioQuiet BUILD_TARGET all DEPENDS jrl-cmakemodules)

add_cmake_test(NAME Findsimde BUILD_TARGET all DEPENDS jrl-cmakemodules)
add_cmake_test(NAME FindsimdeQuiet BUILD_TARGET all DEPENDS jrl-cmakemodules)

add_cmake_test(NAME FindPytest BUILD_TARGET all DEPENDS jrl-cmakemodules)
add_cmake_test(NAME FindPytestQuiet BUILD_TARGET all DEPENDS jrl-cmakemodules)
