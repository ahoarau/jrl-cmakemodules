// Loads a module the way python does: with dlopen(), and with no help from the
// environment. The module must therefore find its own shared library through
// its RPATH alone, which is what this test is about.

#include <dlfcn.h>

#include <cstdio>

int main(int argc, char** argv) {
  if (argc != 2) {
    std::fprintf(stderr, "usage: %s <module>\n", argv[0]);
    return 2;
  }

  void* handle = dlopen(argv[1], RTLD_NOW | RTLD_LOCAL);
  if (handle == nullptr) {
    std::fprintf(stderr, "dlopen('%s') failed: %s\n", argv[1], dlerror());
    return 1;
  }

  using answer_fn = int (*)();
  answer_fn answer =
      reinterpret_cast<answer_fn>(dlsym(handle, "pml_module_answer"));
  if (answer == nullptr) {
    std::fprintf(stderr, "dlsym('pml_module_answer') failed: %s\n", dlerror());
    dlclose(handle);
    return 1;
  }

  const int value = answer();
  if (value != 42) {
    std::fprintf(stderr, "expected 42, got %d\n", value);
    dlclose(handle);
    return 1;
  }

  std::printf("loaded '%s', the module found its library\n", argv[1]);
  dlclose(handle);
  return 0;
}
