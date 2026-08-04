# ---------------------------------------------------------------------------
# _jrl_join_path
# ---------------------------------------------------------------------------

jrl_test_case(
  NAME "_jrl_join_path: joins components with a single slash"
  CODE [[
    _jrl_join_path(
      PATH_VAR result
      COMPONENTS "/opt/prefix" "lib/python3.12/site-packages" "mypkg"
    )
    _jrl_check("${result}" STREQUAL "/opt/prefix/lib/python3.12/site-packages/mypkg")
  ]]
)

jrl_test_case(
  NAME "_jrl_join_path: skips empty components"
  CODE [[
    _jrl_join_path(PATH_VAR result COMPONENTS "/opt/prefix" "" "mypkg" "")
    _jrl_check("${result}" STREQUAL "/opt/prefix/mypkg")
  ]]
)

jrl_test_case(
  NAME "_jrl_join_path: no component gives an empty result"
  CODE [[
    _jrl_join_path(PATH_VAR result)
    if(NOT result STREQUAL "")
      message(FATAL_ERROR "Expected an empty path, got '${result}'")
    endif()
  ]]
)

jrl_test_case(
  NAME "_jrl_join_path: normalizes the joined path"
  CODE [[
    _jrl_join_path(PATH_VAR result COMPONENTS "/build/" "lib//python3.12/./site-packages")
    _jrl_check("${result}" STREQUAL "/build/lib/python3.12/site-packages")

    _jrl_join_path(PATH_VAR result COMPONENTS "/opt/prefix/lib/../lib64")
    _jrl_check("${result}" STREQUAL "/opt/prefix/lib64")

    _jrl_join_path(PATH_VAR result COMPONENTS "/build/lib/site-packages/")
    _jrl_check("${result}" STREQUAL "/build/lib/site-packages")
  ]]
)

jrl_test_case(
  NAME "_jrl_join_path: an absolute component replaces what came before it"
  CODE [[
    # cmake_path(APPEND) semantics: joining an absolute component is a reset,
    # not a concatenation.
    _jrl_join_path(PATH_VAR result COMPONENTS "/opt/prefix" "/elsewhere/lib")
    _jrl_check("${result}" STREQUAL "/elsewhere/lib")
  ]]
)

jrl_test_case(
  NAME "_jrl_join_path: keeps relative paths relative"
  CODE [[
    _jrl_join_path(PATH_VAR result COMPONENTS "lib" "python3.12/site-packages")
    _jrl_check("${result}" STREQUAL "lib/python3.12/site-packages")
  ]]
)

jrl_test_case(
  NAME "_jrl_join_path: a missing output variable is reported"
  CODE [[
    _jrl_join_path(COMPONENTS "/opt/prefix" "lib")
  ]]
  PROPERTIES PASS_REGULAR_EXPRESSION "Variable 'arg_PATH_VAR' is not defined"
)

jrl_test_case(
  NAME "_jrl_join_path: an unknown argument is rejected"
  CODE [[
    _jrl_join_path(PATH_VAR result NOT_AN_ARGUMENT whatever)
  ]]
  PROPERTIES PASS_REGULAR_EXPRESSION "Unrecognized arguments: NOT_AN_ARGUMENT whatever"
)

# ---------------------------------------------------------------------------
# _jrl_path_relative_to_prefix
# ---------------------------------------------------------------------------

jrl_test_case(
  NAME "_jrl_path_relative_to_prefix: a relative path is already relative to the prefix"
  CODE [[
    _jrl_path_relative_to_prefix(
      PATH "lib/python3.12/site-packages"
      PREFIX "/opt/prefix"
      RELATIVE_PATH_VAR result
    )
    _jrl_check("${result}" STREQUAL "lib/python3.12/site-packages")

    # ... and only normalized.
    _jrl_path_relative_to_prefix(
      PATH "lib//python3.12/./site-packages/"
      PREFIX "/opt/prefix"
      RELATIVE_PATH_VAR result
    )
    _jrl_check("${result}" STREQUAL "lib/python3.12/site-packages")
  ]]
)

jrl_test_case(
  NAME "_jrl_path_relative_to_prefix: an absolute path inside the prefix is made relative"
  CODE [[
    _jrl_path_relative_to_prefix(
      PATH "/opt/prefix/lib/python3.12/site-packages"
      PREFIX "/opt/prefix"
      RELATIVE_PATH_VAR result
    )
    _jrl_check("${result}" STREQUAL "lib/python3.12/site-packages")
  ]]
)

jrl_test_case(
  NAME "_jrl_path_relative_to_prefix: an absolute path outside the prefix has no relative form"
  CODE [[
    _jrl_path_relative_to_prefix(
      PATH "/usr/lib/python3.12/site-packages"
      PREFIX "/opt/prefix"
      RELATIVE_PATH_VAR result
    )
    _jrl_check("${result}" STREQUAL "NOTFOUND")
  ]]
)

jrl_test_case(
  NAME "_jrl_path_relative_to_prefix: a prefix is not a mere string prefix"
  CODE [[
    # /opt/prefixed starts with /opt/prefix as a string, but is not inside it.
    _jrl_path_relative_to_prefix(
      PATH "/opt/prefixed/lib"
      PREFIX "/opt/prefix"
      RELATIVE_PATH_VAR result
    )
    _jrl_check("${result}" STREQUAL "NOTFOUND")
  ]]
)

jrl_test_case(
  NAME "_jrl_path_relative_to_prefix: the prefix itself is the empty relative path"
  CODE [[
    _jrl_path_relative_to_prefix(
      PATH "/opt/prefix"
      PREFIX "/opt/prefix"
      RELATIVE_PATH_VAR result
    )
    if(NOT result STREQUAL "")
      message(FATAL_ERROR "Expected an empty path, got '${result}'")
    endif()
  ]]
)

jrl_test_case(
  NAME "_jrl_path_relative_to_prefix: an empty path stays empty"
  CODE [[
    _jrl_path_relative_to_prefix(PATH "" PREFIX "/opt/prefix" RELATIVE_PATH_VAR result)
    if(NOT result STREQUAL "")
      message(FATAL_ERROR "Expected an empty path, got '${result}'")
    endif()
  ]]
)

jrl_test_case(
  NAME "_jrl_path_relative_to_prefix: an absolute path has no relative form without a prefix"
  CODE [[
    _jrl_path_relative_to_prefix(PATH "/opt/prefix/lib" PREFIX "" RELATIVE_PATH_VAR result)
    _jrl_check("${result}" STREQUAL "NOTFOUND")
  ]]
)

jrl_test_case(
  NAME "_jrl_path_relative_to_prefix: a missing output variable is reported"
  CODE [[
    _jrl_path_relative_to_prefix(PATH "/opt/prefix/lib" PREFIX "/opt/prefix")
  ]]
  PROPERTIES PASS_REGULAR_EXPRESSION "Variable 'arg_RELATIVE_PATH_VAR' is not defined"
)

jrl_test_case(
  NAME "_jrl_path_relative_to_prefix: an unknown argument is rejected"
  CODE [[
    _jrl_path_relative_to_prefix(
      PATH "/opt/prefix/lib"
      RELATIVE_PATH_VAR result
      NOT_AN_ARGUMENT whatever
    )
  ]]
  PROPERTIES PASS_REGULAR_EXPRESSION "Unrecognized arguments: NOT_AN_ARGUMENT whatever"
)
