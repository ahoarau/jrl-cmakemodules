# Copyright 2026 Inria

# Finds MPFR (https://www.mpfr.org), which ships no MPFRConfig.cmake, and defines
# the MPFR::MPFR imported target.

find_path(MPFR_INCLUDE_DIR NAMES mpfr.h)
find_library(MPFR_LIBRARY NAMES mpfr libmpfr)

mark_as_advanced(MPFR_INCLUDE_DIR MPFR_LIBRARY)

if(MPFR_INCLUDE_DIR)
    # `#define MPFR_VERSION_MAJOR 4`
    # `#define MPFR_VERSION_MINOR 2`
    # `#define MPFR_VERSION_PATCHLEVEL 2`
    file(READ "${MPFR_INCLUDE_DIR}/mpfr.h" mpfr_h)
    string(REGEX MATCH "#[ \t]*define[ \t]+MPFR_VERSION_MAJOR[ \t]+([0-9]+)" _ "${mpfr_h}")
    set(MPFR_VERSION_MAJOR "${CMAKE_MATCH_1}")
    string(REGEX MATCH "#[ \t]*define[ \t]+MPFR_VERSION_MINOR[ \t]+([0-9]+)" _ "${mpfr_h}")
    set(MPFR_VERSION_MINOR "${CMAKE_MATCH_1}")
    string(REGEX MATCH "#[ \t]*define[ \t]+MPFR_VERSION_PATCHLEVEL[ \t]+([0-9]+)" _ "${mpfr_h}")
    set(MPFR_VERSION_PATCH "${CMAKE_MATCH_1}")
    unset(mpfr_h)

    if(
        MPFR_VERSION_MAJOR
        AND NOT MPFR_VERSION_MINOR STREQUAL ""
        AND NOT MPFR_VERSION_PATCH STREQUAL ""
    )
        set(MPFR_VERSION "${MPFR_VERSION_MAJOR}.${MPFR_VERSION_MINOR}.${MPFR_VERSION_PATCH}")
    endif()
endif()

# MPFR is built on GMP. Keep this lookup soft: find_package_handle_standard_args() below
# turns it into a hard error only when the caller asked for MPFR REQUIRED. Run it
# unconditionally, as GMP::GMP may come from a scope where GMP_FOUND is not visible.
set(MPFR_cmake_module_path_backup "${CMAKE_MODULE_PATH}")
list(PREPEND CMAKE_MODULE_PATH "${CMAKE_CURRENT_LIST_DIR}")
find_package(GMP QUIET)
# Ship FindGMP.cmake with the exported package: without it find_package(MPFR) cannot work for
# a consumer. Guarded so this module stays usable outside jrl-cmakemodules.
if(COMMAND jrl_export_find_module)
    jrl_export_find_module(GMP)
endif()
set(CMAKE_MODULE_PATH "${MPFR_cmake_module_path_backup}")
unset(MPFR_cmake_module_path_backup)

include(FindPackageHandleStandardArgs)
find_package_handle_standard_args(
    MPFR
    REQUIRED_VARS MPFR_LIBRARY MPFR_INCLUDE_DIR GMP_FOUND
    VERSION_VAR MPFR_VERSION
)

if(MPFR_FOUND AND NOT TARGET MPFR::MPFR)
    add_library(MPFR::MPFR UNKNOWN IMPORTED)
    set_target_properties(
        MPFR::MPFR
        PROPERTIES
            IMPORTED_LOCATION "${MPFR_LIBRARY}"
            VERSION "${MPFR_VERSION}"
            INTERFACE_INCLUDE_DIRECTORIES "${MPFR_INCLUDE_DIR}"
            INTERFACE_LINK_LIBRARIES GMP::GMP
    )
endif()
