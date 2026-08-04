// The C++ shared library the module has to find at load time, through its own
// RPATH, in the build tree as well as in the install tree.

#include "pml/answer.hpp"

namespace pml {

Answer::Answer(std::string_view question) : question_{question} {}

std::string Answer::question() const { return question_; }

int Answer::value() const noexcept { return 42; }

}  // namespace pml
