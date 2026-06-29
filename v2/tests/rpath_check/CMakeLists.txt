add_cmake_test(
    NAME rc-library-ok
    DEPENDS jrl-cmakemodules
)

add_cmake_test(
    NAME rc-library-fail
    DEPENDS jrl-cmakemodules
    WILL_FAIL TRUE
)
