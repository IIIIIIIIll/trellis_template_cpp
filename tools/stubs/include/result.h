// tools/stubs/include/result.h — compile stand-in for the guideline example's
// result.h: the single point where tl::expected becomes the project's Result
// alias and error construction funnels through make_error. Snippet fences that
// use Result/#include "result.h" resolve to this header via -isystem.

#ifndef TOOLS_STUBS_RESULT_H
#define TOOLS_STUBS_RESULT_H

#include "tl/expected.hpp"

template <typename T, typename E>
using Result = tl::expected<T, E>;

template <typename E>
auto make_error(E&& e) {
    return tl::make_unexpected(std::forward<E>(e));
}

#endif  // TOOLS_STUBS_RESULT_H
