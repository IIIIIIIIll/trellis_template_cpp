// tools/stubs/per-doc/expressions-and-flow.hpp — names only this guide spells
// differently. `Result` is a concrete default-constructed-then-assigned value
// in EXPR-4/5, while the rest of the docs use the templated tl::expected alias
// from stubs/include/result.h; one global header cannot be both.

struct Result {
    Status status() const { return Status::Ok; }
};
inline Result evaluate(const Request&) { return {}; }
