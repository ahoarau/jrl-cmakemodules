// Stand-in for a python extension module: a MODULE library linked against the
// C++ shared library it must find at load time, like a nanobind or
// Boost.Python module.

#include "pml/answer.hpp"

// dlsym() looks this entry point up by name, so it is the one symbol that needs
// C linkage. A real binding exports PyInit_<module> the same way, with plain
// C++ behind it.
extern "C" int pml_module_answer() {
  const pml::Answer answer{"the answer"};
  return answer.question().empty() ? 0 : answer.value();
}
