# export_find_module_deps

A find module that itself calls `find_package()` is useless to a consumer unless the module
it calls is exported too. `jrl_find_package()` ships the module it resolved, but cannot know
what that module calls internally.

`efmd-library` covers both ways of declaring the extra module:

- `FindMPFR.cmake` calls `find_package(GMP)` and registers `FindGMP.cmake` itself, via
  `jrl_export_find_module()`. A project using it needs no extra call.
- `FindEfmdOuter.cmake` belongs to the project rather than to jrl-cmakemodules, so it cannot
  register anything. The project calls `jrl_export_find_module(EfmdInner)` instead. This is
  the case for any find module you do not own, e.g. one vendored from upstream.

`efmd-consumer` then consumes the installed package with only that prefix on
`CMAKE_PREFIX_PATH`, and no access to jrl's `find-modules` directory or to the library's
source tree, which is the situation of a real downstream user.
