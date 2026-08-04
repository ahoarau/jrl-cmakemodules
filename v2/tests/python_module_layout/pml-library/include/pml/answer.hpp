#pragma once

#include <string>
#include <string_view>

namespace pml {

/// The C++ API a python module would bind. Defined in the shared library, so a
/// module using it has to find that library at load time.
class Answer {
 public:
  explicit Answer(std::string_view question);

  [[nodiscard]] std::string question() const;
  [[nodiscard]] int value() const noexcept;

 private:
  std::string question_;
};

}  // namespace pml
