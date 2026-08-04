# Every case starts from a layout that mirrors: the libraries in <prefix>/lib,
# the module in <prefix>/lib/python3.12/site-packages/mypkg, so that "../../.."
# is the library dir in both trees. A case sets only what it changes, then calls
# compute_layout().
set(layout_prelude
    [[
    set(binary_dir /build)
    set(install_prefix /opt/prefix)
    set(site_packages lib/python3.12/site-packages)
    set(library_install_dir lib)
    set(library_build_dirs /build/lib)
    set(origin_token "$ORIGIN")
    set(package_dir mypkg)

    macro(compute_layout)
      _jrl_python_compute_module_layout(
        BINARY_DIR "${binary_dir}"
        INSTALL_PREFIX "${install_prefix}"
        SITE_PACKAGES_INSTALL_DIR "${site_packages}"
        LIBRARY_INSTALL_DIR "${library_install_dir}"
        LIBRARY_BUILD_DIRS "${library_build_dirs}"
        ORIGIN_TOKEN "${origin_token}"
        PACKAGE_DIR "${package_dir}"
        MIRRORED_VAR mirrored
        RPATH_VAR rpath
        SITE_PACKAGES_BUILD_DIR_VAR build_dir
        REASON_VAR reason
      )
    endmacro()
    ]]
)

function(layout_test_case)
    cmake_parse_arguments(PARSE_ARGV 0 arg "" "NAME;CODE" "PROPERTIES")
    jrl_test_case(
      NAME "_jrl_python_compute_module_layout: ${arg_NAME}"
      CODE "${layout_prelude}${arg_CODE}"
      PROPERTIES ${arg_PROPERTIES}
    )
endfunction()

# ---------------------------------------------------------------------------
# Layouts that can be mirrored
# ---------------------------------------------------------------------------

layout_test_case(
  NAME "the standard layout is mirrored"
  CODE [[
    compute_layout()

    _jrl_check(mirrored)
    _jrl_check("${rpath}" STREQUAL "$ORIGIN/../../..")
    _jrl_check("${build_dir}" STREQUAL "/build/lib/python3.12/site-packages")
    _jrl_check("${reason}" MATCHES "mirrors the install layout")
  ]]
)

layout_test_case(
  NAME "macOS uses loader_path"
  CODE [[
    set(origin_token "@loader_path")
    compute_layout()

    _jrl_check(mirrored)
    _jrl_check("${rpath}" STREQUAL "@loader_path/../../..")
  ]]
)

layout_test_case(
  NAME "without a package the module is one level up"
  CODE [[
    set(package_dir "")
    compute_layout()

    _jrl_check(mirrored)
    _jrl_check("${rpath}" STREQUAL "$ORIGIN/../..")
  ]]
)

layout_test_case(
  NAME "a nested package adds one level"
  CODE [[
    set(package_dir foo/bar)
    compute_layout()

    _jrl_check(mirrored)
    _jrl_check("${rpath}" STREQUAL "$ORIGIN/../../../..")
    # The build dir stays the site-packages root, the module goes below it.
    _jrl_check("${build_dir}" STREQUAL "/build/lib/python3.12/site-packages")
  ]]
)

layout_test_case(
  NAME "lib64 is mirrored too"
  CODE [[
    set(site_packages lib64/python3.12/site-packages)
    set(library_install_dir lib64)
    set(library_build_dirs /build/lib64)
    compute_layout()

    _jrl_check(mirrored)
    _jrl_check("${rpath}" STREQUAL "$ORIGIN/../../..")
    _jrl_check("${build_dir}" STREQUAL "/build/lib64/python3.12/site-packages")
  ]]
)

layout_test_case(
  NAME "an absolute site-packages inside the prefix is mirrored"
  CODE [[
    # What a project passing an absolute <PROJECT>_PYTHON_INSTALL_DIR gets.
    set(site_packages /opt/prefix/lib/python3.12/site-packages)
    compute_layout()

    _jrl_check(mirrored)
    _jrl_check("${rpath}" STREQUAL "$ORIGIN/../../..")
    _jrl_check("${build_dir}" STREQUAL "/build/lib/python3.12/site-packages")
  ]]
)

layout_test_case(
  NAME "an absolute library install dir inside the prefix is mirrored"
  CODE [[
    set(install_prefix /wheel)
    set(site_packages /wheel/lib/python3.12/site-packages)
    set(library_install_dir /wheel/lib)
    compute_layout()

    _jrl_check(mirrored)
    _jrl_check("${rpath}" STREQUAL "$ORIGIN/../../..")
  ]]
)

layout_test_case(
  NAME "a module sitting in the library dir gets a bare token"
  CODE [[
    set(site_packages lib)
    set(package_dir "")
    compute_layout()

    _jrl_check(mirrored)
    _jrl_check("${rpath}" STREQUAL "$ORIGIN")
  ]]
)

layout_test_case(
  NAME "untidy paths give the same answer"
  CODE [[
    set(binary_dir /build/)
    set(install_prefix /opt/prefix/)
    set(site_packages "lib//python3.12/./site-packages/")
    set(library_install_dir "lib/")
    set(library_build_dirs "/build/lib/")
    set(package_dir "mypkg/")
    compute_layout()

    _jrl_check(mirrored)
    _jrl_check("${rpath}" STREQUAL "$ORIGIN/../../..")
    _jrl_check("${build_dir}" STREQUAL "/build/lib/python3.12/site-packages")
  ]]
)

# ---------------------------------------------------------------------------
# Layouts that cannot be mirrored: the module goes to <build>/lib/site-packages,
# gets no RPATH of ours, and the reason says why
# ---------------------------------------------------------------------------

layout_test_case(
  NAME "no loader-relative token means no mirroring"
  CODE [[
    # Windows: no RPATH at all.
    set(origin_token "")
    compute_layout()

    _jrl_check(NOT mirrored)
    if(NOT rpath STREQUAL "")
      message(FATAL_ERROR "Expected no RPATH, got '${rpath}'")
    endif()
    _jrl_check("${build_dir}" STREQUAL "/build/lib/site-packages")
    _jrl_check("${reason}" MATCHES "no loader-relative RPATH")
  ]]
)

layout_test_case(
  NAME "Debian multiarch is not mirrored"
  CODE [[
    # The library install dir does not match the library output dir, so the
    # module would not reach the libraries the same way in both trees.
    set(install_prefix /usr)
    set(site_packages lib/python3/dist-packages)
    set(library_install_dir lib/x86_64-linux-gnu)
    compute_layout()

    _jrl_check(NOT mirrored)
    if(NOT rpath STREQUAL "")
      message(FATAL_ERROR "Expected no RPATH, got '${rpath}'")
    endif()
    _jrl_check("${build_dir}" STREQUAL "/build/lib/site-packages")
    _jrl_check("${reason}" MATCHES "would reach the library dir through")
  ]]
)

layout_test_case(
  NAME "per-configuration library dirs are not mirrored"
  CODE [[
    # Libraries in lib/Debug and lib/Release: no single relative RPATH is right.
    set(library_build_dirs "/build/lib/Debug;/build/lib/Release")
    compute_layout()

    _jrl_check(NOT mirrored)
    _jrl_check("${build_dir}" STREQUAL "/build/lib/site-packages")
    _jrl_check("${reason}" MATCHES "different directory in each configuration")
  ]]
)

layout_test_case(
  NAME "a generator expression is not mirrored"
  CODE [[
    set(library_build_dirs "/build/lib/$<CONFIG>")
    compute_layout()

    _jrl_check(NOT mirrored)
    _jrl_check("${reason}" MATCHES "generator expression")
  ]]
)

layout_test_case(
  NAME "a relative library output dir is not mirrored"
  CODE [[
    set(library_build_dirs lib)
    compute_layout()

    _jrl_check(NOT mirrored)
    _jrl_check("${reason}" MATCHES "is not absolute")
  ]]
)

layout_test_case(
  NAME "no library output dir is not mirrored"
  CODE [[
    set(library_build_dirs "")
    compute_layout()

    _jrl_check(NOT mirrored)
    _jrl_check("${build_dir}" STREQUAL "/build/lib/site-packages")
    _jrl_check("${reason}" MATCHES "no library output directory is set")
  ]]
)

layout_test_case(
  NAME "no library install dir is not mirrored"
  CODE [[
    # What a project that never included GNUInstallDirs gets.
    set(library_install_dir "")
    compute_layout()

    _jrl_check(NOT mirrored)
    _jrl_check("${reason}" MATCHES "no library install directory is set")
  ]]
)

layout_test_case(
  NAME "a site-packages outside the prefix is not mirrored"
  CODE [[
    set(site_packages /usr/lib/python3.12/site-packages)
    compute_layout()

    _jrl_check(NOT mirrored)
    _jrl_check("${reason}" MATCHES "site-packages install dir")
    _jrl_check("${reason}" MATCHES "outside the install prefix")
  ]]
)

layout_test_case(
  NAME "a library install dir outside the prefix is not mirrored"
  CODE [[
    set(library_install_dir /usr/lib)
    compute_layout()

    _jrl_check(NOT mirrored)
    _jrl_check("${reason}" MATCHES "library install dir")
    _jrl_check("${reason}" MATCHES "outside the install prefix")
  ]]
)

layout_test_case(
  NAME "libraries outside the build tree are not mirrored"
  CODE [[
    set(library_build_dirs /somewhere/else/lib)
    compute_layout()

    _jrl_check(NOT mirrored)
    _jrl_check("${reason}" MATCHES "would reach the library dir through")
  ]]
)

# ---------------------------------------------------------------------------
# Caller mistakes
# ---------------------------------------------------------------------------

layout_test_case(
  NAME "an absolute PACKAGE_DIR is rejected"
  CODE [[
    set(package_dir /mypkg)
    compute_layout()
  ]]
  PROPERTIES PASS_REGULAR_EXPRESSION "PACKAGE_DIR must be relative to site-packages"
)

layout_test_case(
  NAME "a PACKAGE_DIR escaping site-packages is rejected"
  CODE [[
    set(package_dir ../mypkg)
    compute_layout()
  ]]
  PROPERTIES PASS_REGULAR_EXPRESSION "PACKAGE_DIR must not contain"
)

jrl_test_case(
  NAME "_jrl_python_compute_module_layout: an unknown argument is rejected"
  CODE [[
    _jrl_python_compute_module_layout(
      BINARY_DIR /build
      INSTALL_PREFIX /opt/prefix
      SITE_PACKAGES_INSTALL_DIR lib/python3.12/site-packages
      NOT_AN_ARGUMENT whatever
    )
  ]]
  PROPERTIES PASS_REGULAR_EXPRESSION "Unrecognized arguments: NOT_AN_ARGUMENT whatever"
)

jrl_test_case(
  NAME "_jrl_python_compute_module_layout: a missing required argument is reported"
  CODE [[
    _jrl_python_compute_module_layout(
      INSTALL_PREFIX /opt/prefix
      SITE_PACKAGES_INSTALL_DIR lib/python3.12/site-packages
    )
  ]]
  PROPERTIES PASS_REGULAR_EXPRESSION "Variable 'arg_BINARY_DIR' is not defined"
)

# ---------------------------------------------------------------------------
# jrl_target_set_python_module_layout: the public wrapper needs a real target,
# so only what script mode can check is checked here. The behaviour on a target
# is covered by the python_module_layout test.
# ---------------------------------------------------------------------------

jrl_test_case(
  NAME "jrl_target_set_python_module_layout: an unknown target is reported"
  CODE [[
    jrl_target_set_python_module_layout(no_such_target PACKAGE_DIR mypkg)
  ]]
  PROPERTIES PASS_REGULAR_EXPRESSION "Target 'no_such_target' does not exist"
)

jrl_test_case(
  NAME "jrl_target_set_python_module_layout: an unknown argument is rejected"
  CODE [[
    jrl_target_set_python_module_layout(no_such_target PACKAGE whatever)
  ]]
  PROPERTIES PASS_REGULAR_EXPRESSION "Unrecognized arguments: PACKAGE whatever"
)
