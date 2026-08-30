#ifndef TOOLS_STUBS_STUBS_HPP
#define TOOLS_STUBS_STUBS_HPP

// tools/stubs/stubs.hpp — compile-stub prelude for tools/check_snippets.py.
//
// The snippet harness prepends this header (plus a #line directive) to every
// fenced ```cpp example before running g++ -std=c++17 -Wall -Wextra
// -fsyntax-only, so guideline examples can name the invented types each guide
// uses (Window, Poller, FileDesc, Task/Model, ...) without carrying their
// definitions inline.
//
// Scaffold state: per-doc stub declarations land in Phase 4 of task
// 08-30-cpp-rules-machine-format. Until then every snippet compiles against
// this empty prelude and missing declarations surface as ordinary
// diagnostics — expected while the docs are unmarked.

#endif  // TOOLS_STUBS_STUBS_HPP
