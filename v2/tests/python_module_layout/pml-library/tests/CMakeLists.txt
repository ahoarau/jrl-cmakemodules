# What the mirrored layout promises, spelled out independently of the function
# under test.
if(UNIX)
    set(expected_module_dir "${CMAKE_BINARY_DIR}/lib/python3/site-packages/pml")
else()
    # No RPATH on Windows: the module keeps the plain build layout.
    set(expected_module_dir "${CMAKE_BINARY_DIR}/lib/site-packages/pml")
endif()

# Most checks compare a value only known at generate time (a target property, a
# target file path) against what it should be.
function(add_layout_check)
    cmake_parse_arguments(PARSE_ARGV 0 arg "" "NAME;ACTUAL;EXPECTED" "")
    string(MAKE_C_IDENTIFIER "${arg_NAME}" id)
    set(actual_file "${CMAKE_CURRENT_BINARY_DIR}/checks/${id}.actual")
    set(expected_file "${CMAKE_CURRENT_BINARY_DIR}/checks/${id}.expected")

    file(GENERATE OUTPUT "${actual_file}" CONTENT "${arg_ACTUAL}")
    file(GENERATE OUTPUT "${expected_file}" CONTENT "${arg_EXPECTED}")
    add_test(
        NAME "python_module_layout: ${arg_NAME}"
        COMMAND ${CMAKE_COMMAND} -E compare_files "${actual_file}" "${expected_file}"
    )
endfunction()

add_layout_check(
    NAME "the module is built in the expected directory"
    ACTUAL "$<TARGET_FILE:pml_pywrap>"
    EXPECTED "${expected_module_dir}/$<TARGET_FILE_NAME:pml_pywrap>"
)

add_layout_check(
    NAME "the reported build site-packages dir is the one used"
    ACTUAL "${python_build_dir}/pml"
    EXPECTED "${expected_module_dir}"
)

# Everything below is about the RPATH, which Windows does not have.
if(NOT UNIX)
    return()
endif()

if(APPLE)
    set(expected_rpath "@loader_path/../../..")
else()
    set(expected_rpath "$ORIGIN/../../..")
endif()

add_layout_check(
    NAME "the module has a loader-relative RPATH"
    ACTUAL
        "$<TARGET_PROPERTY:pml_pywrap,INSTALL_RPATH> $<TARGET_PROPERTY:pml_pywrap,BUILD_WITH_INSTALL_RPATH>"
    EXPECTED "${expected_rpath} ON"
)

add_layout_check(
    NAME "an RPATH the project asked for is kept"
    ACTUAL "$<TARGET_PROPERTY:pml_pywrap_kept_rpath,INSTALL_RPATH>"
    EXPECTED "${expected_rpath};/opt/extra/lib"
)

add_layout_check(
    NAME "a layout that cannot be mirrored falls back"
    ACTUAL
        "$<TARGET_FILE:pml_pywrap_fallback>|$<TARGET_PROPERTY:pml_pywrap_fallback,INSTALL_RPATH>"
    EXPECTED "${CMAKE_BINARY_DIR}/lib/site-packages/pml/$<TARGET_FILE_NAME:pml_pywrap_fallback>|"
)

add_layout_check(
    NAME "the fallback reports the plain build site-packages dir"
    ACTUAL "${fallback_build_dir}"
    EXPECTED "${CMAKE_BINARY_DIR}/lib/site-packages"
)

add_test(
    NAME "python_module_layout: installing the module does not rewrite it"
    COMMAND
        ${CMAKE_COMMAND} -D BUILT_MODULE=$<TARGET_FILE:pml_pywrap> -D
        INSTALLED_MODULE=${CMAKE_INSTALL_PREFIX}/${python_install_dir}/pml/$<TARGET_FILE_NAME:pml_pywrap>
        -P ${CMAKE_CURRENT_SOURCE_DIR}/check_module_not_rewritten.cmake
)

add_executable(pml_loader loader.cpp)
target_link_libraries(pml_loader PRIVATE ${CMAKE_DL_LIBS})

add_test(
    NAME "python_module_layout: the module finds its library in the build tree"
    COMMAND $<TARGET_FILE:pml_loader> $<TARGET_FILE:pml_pywrap>
)

add_test(
    NAME "python_module_layout: the installed module finds its library, even moved"
    COMMAND
        ${CMAKE_COMMAND} -D LOADER=$<TARGET_FILE:pml_loader> -D
        INSTALL_PREFIX=${CMAKE_INSTALL_PREFIX} -D
        MODULE_REL_PATH=${python_install_dir}/pml/$<TARGET_FILE_NAME:pml_pywrap> -D
        RELOCATED_DIR=${CMAKE_BINARY_DIR}/relocated-install -P
        ${CMAKE_CURRENT_SOURCE_DIR}/check_relocatable.cmake
)
