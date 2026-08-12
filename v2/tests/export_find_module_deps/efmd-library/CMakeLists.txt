cmake_minimum_required(VERSION 3.22)
project(efmd-library VERSION 1.0.0)

find_package(jrl-cmakemodules REQUIRED)
jrl_configure_defaults()

# A jrl find module that needs another one. FindMPFR.cmake registers FindGMP.cmake itself,
# so nothing extra is needed here.
jrl_find_package(MPFR REQUIRED EXPECTED_TARGETS MPFR::MPFR)

# A find module owned by this project rather than by jrl-cmakemodules. It cannot register
# anything itself, so the project declares what has to travel with it.
set(CMAKE_MODULE_PATH "${CMAKE_CURRENT_SOURCE_DIR}/cmake")
jrl_find_package(EfmdOuter REQUIRED EXPECTED_TARGETS EfmdOuter::EfmdOuter)
jrl_export_find_module(EfmdInner)

add_library(efmd-library INTERFACE)
target_link_libraries(efmd-library INTERFACE MPFR::MPFR EfmdOuter::EfmdOuter)

jrl_add_export_component(NAME AllComponents TARGETS efmd-library)
jrl_export_package()
