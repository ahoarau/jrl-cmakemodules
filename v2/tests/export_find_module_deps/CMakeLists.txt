add_cmake_test(NAME efmd-library DEPENDS jrl-cmakemodules)
add_cmake_test(NAME efmd-consumer DEPENDS efmd-library BUILD_TARGET all)
