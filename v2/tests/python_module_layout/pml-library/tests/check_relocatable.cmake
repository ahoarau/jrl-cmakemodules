# The installed module finds its library through a path relative to itself, not
# one baked in at build time, so it must still load once moved elsewhere.

foreach(var LOADER INSTALL_PREFIX MODULE_REL_PATH RELOCATED_DIR)
    if(NOT DEFINED ${var})
        message(FATAL_ERROR "${var} must be defined")
    endif()
endforeach()

function(load_module module)
    if(NOT EXISTS "${module}")
        message(
            FATAL_ERROR
            "Module not found: '${module}'. Run 'cmake --install' before this test."
        )
    endif()

    execute_process(
        COMMAND "${LOADER}" "${module}"
        RESULT_VARIABLE result
        OUTPUT_VARIABLE output
        ERROR_VARIABLE error
    )
    if(NOT result EQUAL 0)
        message(FATAL_ERROR "Loading '${module}' failed:\n${output}${error}")
    endif()
    message(STATUS "${output}")
endfunction()

load_module("${INSTALL_PREFIX}/${MODULE_REL_PATH}")

# ... and once the whole install tree has moved somewhere else.
file(REMOVE_RECURSE "${RELOCATED_DIR}")
file(COPY "${INSTALL_PREFIX}/" DESTINATION "${RELOCATED_DIR}")
load_module("${RELOCATED_DIR}/${MODULE_REL_PATH}")
