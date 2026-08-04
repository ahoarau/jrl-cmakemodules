cmake_minimum_required(VERSION 3.22)

project(pml-library VERSION 1.0.0 DESCRIPTION "A test project for jrl-cmakemodules" LANGUAGES CXX)

find_package(jrl-cmakemodules 1.2.0 CONFIG REQUIRED)
jrl_configure_defaults()

# The C++ shared library the module has to find at load time.
add_library(pml SHARED src/answer.cpp)
target_include_directories(pml PUBLIC $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>)
target_compile_features(pml PUBLIC cxx_std_17)
set_target_properties(
    pml
    PROPERTIES VERSION ${PROJECT_VERSION} SOVERSION 1 WINDOWS_EXPORT_ALL_SYMBOLS ON
)
install(TARGETS pml LIBRARY DESTINATION ${CMAKE_INSTALL_LIBDIR})

# Stand-in for a python extension module. Passing the site-packages dir
# explicitly keeps the test independent from the python interpreter of the
# machine running it.
add_library(pml_pywrap MODULE src/mymodule.cpp)
target_link_libraries(pml_pywrap PRIVATE pml)

jrl_target_set_python_module_layout(
    pml_pywrap
    PACKAGE_DIR pml
    SITE_PACKAGES_INSTALL_DIR lib/python3/site-packages
    SITE_PACKAGES_INSTALL_DIR_VAR python_install_dir
    SITE_PACKAGES_BUILD_DIR_VAR python_build_dir
)
install(TARGETS pml_pywrap LIBRARY DESTINATION ${python_install_dir}/pml)

# A project that already asked for an RPATH keeps it: ours is prepended.
set(CMAKE_INSTALL_RPATH "/opt/extra/lib")
add_library(pml_pywrap_kept_rpath MODULE src/mymodule.cpp)
target_link_libraries(pml_pywrap_kept_rpath PRIVATE pml)
jrl_target_set_python_module_layout(
    pml_pywrap_kept_rpath
    PACKAGE_DIR pml
    SITE_PACKAGES_INSTALL_DIR lib/python3/site-packages
)
unset(CMAKE_INSTALL_RPATH)

# A site-packages dir outside the install prefix cannot be mirrored: this
# module falls back to the plain build layout.
add_library(pml_pywrap_fallback MODULE src/mymodule.cpp)
target_link_libraries(pml_pywrap_fallback PRIVATE pml)
jrl_target_set_python_module_layout(
    pml_pywrap_fallback
    PACKAGE_DIR pml
    SITE_PACKAGES_INSTALL_DIR /outside/of/the/prefix/site-packages
    SITE_PACKAGES_BUILD_DIR_VAR fallback_build_dir
)

enable_testing()
add_subdirectory(tests)
