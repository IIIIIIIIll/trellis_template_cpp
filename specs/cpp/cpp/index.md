# C++ Development Guidelines

> Best practices for native C++ development in this project.

---

## Overview

This directory contains the guidelines for C++ development. They are opinionated defaults targeting a C++17 baseline built through CMake presets, with C++20/23 differences noted where they change a recommendation. Treat them as the starting point to adapt: record what your project actually enforces, not aspirations nobody checks.

---

## Guidelines Index

| Guide | Description |
|-------|-------------|
| [Build and Toolchain](./build-and-toolchain.md) | CMake presets as the only entry point, compiler warning policy, clang-format and clang-tidy curation, sanitizer matrix, CI build matrix, dependency management |
| [Memory and Ownership](./memory-and-ownership.md) | RAII invariant, ownership ladder, pass-by conventions, iterator invalidation and other lifetime pitfalls |
| [Error Handling](./error-handling.md) | Exceptions versus `expected`/error-code policy, failure contracts across API boundaries |
| [Quality Guidelines](./quality-guidelines.md) | Naming, header hygiene, ODR and ABI pitfalls |
| [Testing Conventions](./testing-conventions.md) | Test framework and layout, test naming, what deserves a test |

---

## Adapting These Guidelines

These documents ship with concrete defaults so a new repository starts consistent instead of empty:

1. Keep the **structure** (sections, tables, wrong-vs-right examples) and replace specifics that conflict with your project's reality
2. Document **actual** conventions, not ideals; a rule nobody enforces is worse than no rule
3. Add **common mistakes** your team has made, pairing each pitfall with the tool that catches it
4. When a rule stops being enforced by CI or review, either restore enforcement or delete the rule

---

## Pre-Development Checklist

Before writing code, route the task through the relevant guide:

| Task involves | Read first |
|---------------|------------|
| New targets, flags, presets, third-party dependencies | [Build and Toolchain](./build-and-toolchain.md) |
| Raw pointers, resource handles, container lifetime questions | [Memory and Ownership](./memory-and-ownership.md) |
| Reporting failures, designing error paths across APIs | [Error Handling](./error-handling.md) |
| New headers or files, public API surface, naming decisions | [Quality Guidelines](./quality-guidelines.md) |
| Writing, changing, or removing tests | [Testing Conventions](./testing-conventions.md) |

A change touching several rows above should skim every listed guide before starting — the expensive C++ mistakes are cross-cutting.

---

## Quality Check

Run the full gate before declaring any change complete. Preset names assume the standard family defined in the Build and Toolchain guide (`default`, `release`, `asan`, `tsan`):

```bash
# Configure + build + test, warnings as errors
cmake --preset default && cmake --build --preset default
ctest --preset default --output-on-failure

# Static analysis on changed sources
clang-tidy -p build/default path/to/changed.cpp
```

When the change touches allocation, container mutation, concurrency, or lifetime-sensitive code, repeat under sanitizers:

```bash
cmake --preset asan && cmake --build --preset asan
ctest --preset asan --output-on-failure
```

Concurrency changes additionally run the `tsan` preset.

---

**Language**: All documentation should be written in **English**.
