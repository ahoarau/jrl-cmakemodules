if(NOT EXISTS "${METADATA_FILE}")
    message(FATAL_ERROR "Metadata file not found: ${METADATA_FILE}")
endif()

file(READ "${METADATA_FILE}" content)
message(STATUS "Metadata content:\n${content}")

if(NOT content MATCHES "Name: test-pyproject-metadata")
    message(FATAL_ERROR "Metadata does not contain 'Name: test-pyproject-metadata'")
endif()

if(NOT content MATCHES "Version: 0.1.0")
    message(FATAL_ERROR "Metadata does not contain 'Version: 0.1.0'")
endif()

if(NOT content MATCHES "Summary: A minimal test for pyproject metadata")
    message(FATAL_ERROR "Metadata does not contain expected Summary")
endif()

message(STATUS "Metadata validation successful!")
