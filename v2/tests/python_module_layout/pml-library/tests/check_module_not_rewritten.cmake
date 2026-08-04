# When the RPATH a file is built with differs from the one it needs once
# installed, CMake rewrites the file while installing it: file(RPATH_CHANGE) on
# ELF platforms, install_name_tool on macOS, which breaks the module signature.
# A mirrored layout uses the same RPATH in both trees, so there is nothing to
# rewrite and the installed module must be the very file that was built.

foreach(var BUILT_MODULE INSTALLED_MODULE)
    if(NOT DEFINED ${var})
        message(FATAL_ERROR "${var} must be defined")
    endif()
    if(NOT EXISTS "${${var}}")
        message(
            FATAL_ERROR
            "${var} not found: '${${var}}'. Run 'cmake --install' before this test."
        )
    endif()
endforeach()

file(SHA256 "${BUILT_MODULE}" built_hash)
file(SHA256 "${INSTALLED_MODULE}" installed_hash)

if(NOT built_hash STREQUAL installed_hash)
    message(
        FATAL_ERROR
        "The installed module is not the file that was built, so installing it rewrote it (and on macOS broke its signature):
    built     '${BUILT_MODULE}' (sha256 ${built_hash})
    installed '${INSTALLED_MODULE}' (sha256 ${installed_hash})"
    )
endif()

message(STATUS "The installed module is byte for byte the file that was built.")
