# Stand-in for a find module the project does not own, e.g. vendored from upstream.
include(FindPackageHandleStandardArgs)
set(EfmdInner_VERSION 1.0.0)
find_package_handle_standard_args(
    EfmdInner
    REQUIRED_VARS EfmdInner_VERSION
    VERSION_VAR EfmdInner_VERSION
)

if(EfmdInner_FOUND AND NOT TARGET EfmdInner::EfmdInner)
    add_library(EfmdInner::EfmdInner INTERFACE IMPORTED)
endif()
