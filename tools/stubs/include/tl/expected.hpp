// tools/stubs/include/tl/expected.hpp — minimal compile stand-in for the real
// tl::expected single header (github.com/TartanLlama/expected). It provides
// just the surface the guideline examples use — construction, make_unexpected,
// and the expected-style inspection shape — so examples can keep naming the
// real-world API without pulling the vendored dependency into the gate.

#ifndef TOOLS_STUBS_TL_EXPECTED_HPP
#define TOOLS_STUBS_TL_EXPECTED_HPP

#include <new>
#include <utility>
#include <variant>

namespace tl {

template <typename E>
class unexpected {
public:
    explicit unexpected(E e) : err_(std::move(e)) {}
    const E& value() const& noexcept { return err_; }

private:
    E err_;
};

template <typename E>
unexpected<E> make_unexpected(E&& e) {
    return unexpected<E>(std::forward<E>(e));
}

template <typename T, typename E>
class expected {
public:
    expected(T v) : store_(std::move(v)) {}
    expected(unexpected<E> u) : store_(std::move(u.value())) {}

    bool has_value() const noexcept { return store_.index() == 0; }
    explicit operator bool() const noexcept { return has_value(); }
    T& value() & { return std::get<0>(store_); }
    const T& value() const& { return std::get<0>(store_); }
    E& error() & { return std::get<1>(store_); }
    const E& error() const& { return std::get<1>(store_); }
    T& operator*() { return value(); }
    const T& operator*() const { return value(); }

private:
    std::variant<T, E> store_;
};

}  // namespace tl

#endif  // TOOLS_STUBS_TL_EXPECTED_HPP
