# Calls another find module, the way FindMPFR.cmake calls FindGMP.cmake. Deliberately naive:
# it does not prepend its own directory to CMAKE_MODULE_PATH, so it only works if the module
# it needs is reachable on CMAKE_MODULE_PATH.
find_package(EfmdInner QUIET)

include(FindPackageHandleStandardArgs)
set(EfmdOuter_VERSION 1.0.0)
find_package_handle_standard_args(
    EfmdOuter
    REQUIRED_VARS EfmdInner_FOUND
    VERSION_VAR EfmdOuter_VERSION
)

if(EfmdOuter_FOUND AND NOT TARGET EfmdOuter::EfmdOuter)
    add_library(EfmdOuter::EfmdOuter INTERFACE IMPORTED)
    set_target_properties(
        EfmdOuter::EfmdOuter
        PROPERTIES INTERFACE_LINK_LIBRARIES EfmdInner::EfmdInner
    )
endif()
