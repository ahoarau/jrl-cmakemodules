# Copyright 2026 Inria

# Finds CppADCodeGen (https://github.com/joaoleal/CppADCodeGen), which ships no
# cppadcgConfig.cmake, and defines the cppadcg::cppadcg imported target.

find_path(cppadcg_INCLUDE_DIR NAMES cppad/cg.hpp)

mark_as_advanced(cppadcg_INCLUDE_DIR)

if(cppadcg_INCLUDE_DIR AND EXISTS "${cppadcg_INCLUDE_DIR}/cppad/cg/configure.hpp")
    # `#define CPPAD_CG_VERSION "cppadcg-2.5.0"`
    file(READ "${cppadcg_INCLUDE_DIR}/cppad/cg/configure.hpp" cppadcg_configure_hpp)
    string(
        REGEX MATCH "#[ \t]*define[ \t]+CPPAD_CG_VERSION[ \t]+\"cppadcg-([0-9.]+)\""
        _
        "${cppadcg_configure_hpp}"
    )
    set(cppadcg_VERSION "${CMAKE_MATCH_1}")
    unset(cppadcg_configure_hpp)
endif()

# CppADCodeGen is built on CppAD. Keep this lookup soft: find_package_handle_standard_args()
# below turns it into a hard error only when the caller asked for cppadcg REQUIRED. Run it
# unconditionally, as cppad::cppad may come from a scope where cppad_FOUND is not visible.
set(cppadcg_cmake_module_path_backup "${CMAKE_MODULE_PATH}")
list(PREPEND CMAKE_MODULE_PATH "${CMAKE_CURRENT_LIST_DIR}")
find_package(cppad QUIET)
# Ship Findcppad.cmake with the exported package: without it find_package(cppadcg) cannot work
# for a consumer. Guarded so this module stays usable outside jrl-cmakemodules.
if(COMMAND jrl_export_find_module)
    jrl_export_find_module(cppad)
endif()
set(CMAKE_MODULE_PATH "${cppadcg_cmake_module_path_backup}")
unset(cppadcg_cmake_module_path_backup)

include(FindPackageHandleStandardArgs)
find_package_handle_standard_args(
    cppadcg
    REQUIRED_VARS cppadcg_INCLUDE_DIR cppad_FOUND
    VERSION_VAR cppadcg_VERSION
)

if(cppadcg_FOUND AND NOT TARGET cppadcg::cppadcg)
    add_library(cppadcg::cppadcg INTERFACE IMPORTED)
    set_target_properties(
        cppadcg::cppadcg
        PROPERTIES
            INTERFACE_INCLUDE_DIRECTORIES "${cppadcg_INCLUDE_DIR}"
            INTERFACE_VERSION "${cppadcg_VERSION}"
            INTERFACE_LINK_LIBRARIES cppad::cppad
    )
endif()
