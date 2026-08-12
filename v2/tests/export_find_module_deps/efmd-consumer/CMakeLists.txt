cmake_minimum_required(VERSION 3.22)
project(efmd-consumer)

# No jrl-cmakemodules and no find-modules directory: everything needed to resolve MPFR and
# EfmdOuter must come from the installed efmd-library package itself.
find_package(efmd-library 1.0.0 REQUIRED)

foreach(
    target
    IN
    ITEMS efmd-library::efmd-library MPFR::MPFR GMP::GMP EfmdOuter::EfmdOuter EfmdInner::EfmdInner
)
    if(NOT TARGET ${target})
        message(FATAL_ERROR "${target} was not imported transitively")
    endif()
endforeach()
