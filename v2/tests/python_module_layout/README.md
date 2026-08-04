# python_module_layout

End-to-end test for `jrl_target_set_python_module_layout()`.

A `MODULE` library standing in for a python extension module is linked against a
C++17 shared library, then laid out and installed the way a real binding would
be. Only the entry point the loader looks up has C linkage, like the
`PyInit_<module>` of a real binding.

The test checks that:

* the module is built at the place the mirrored layout promises;
* it gets a loader-relative RPATH (`@loader_path`/`$ORIGIN`), used as is in the
  build tree;
* installing it does not rewrite that RPATH, so `install_name_tool` never runs
  and the macOS code signature stays valid;
* the module finds its shared library both in the build tree and once installed,
  **including after the install tree has been moved somewhere else**, which is
  what relocatable means.

No python interpreter is involved: the site-packages directory is passed
explicitly so that the expected paths are the same on every machine.
