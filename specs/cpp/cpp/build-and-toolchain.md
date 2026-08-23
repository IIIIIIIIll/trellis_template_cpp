# Build and Toolchain

> How this project configures, compiles, analyzes, sanitizes, and depends on third-party code.

---

## Overview

All builds flow through CMake presets — never ad-hoc flag invocations. Warnings are uniform and fatal in CI. Formatting is mechanical, static analysis runs on changed code, and sanitizers are a routine gate rather than a debugging afterthought. Dependency policy differs between applications and libraries; both stances are stated here instead of left to per-developer taste.

Baseline: **C++17** on GCC 12+ / Clang 15+ / MSVC 2022-class compilers. C++20/23 differences are noted inline where they change a recommendation.

---

## CMake Presets Are the Only Entry Point

Every configure, build, and test invocation goes through a named preset in `CMakePresets.json`. Ad-hoc `-D` flag soup is forbidden because it forks the set of builds the team can reproduce.

Wrong:

```bash
# Undocumented, unreviewable, unreproducible
cmake -B build -DCMAKE_BUILD_TYPE=RelWithDebInfo \
      -DCMAKE_CXX_FLAGS="-O3 -march=native" \
      -DBUILD_SHARED_LIBS=ON -DUSE_SYSTEM_ZLIB=OFF
cmake --build build -j
```

Right:

```bash
cmake --preset default
cmake --build --preset default
ctest --preset default
```

Rules:

1. `CMakePresets.json` (schema version 3+) is committed and reviewed like source code.
2. The committed preset family is small and named by intent:
   - `default` — Debug, full warning set with `-Werror`
   - `release` — optimized, `NDEBUG`
   - `asan` — Debug plus ASan + UBSan + LeakSanitizer
   - `tsan` — Debug plus ThreadSanitizer
3. Developer-specific conveniences go in `CMakeUserPresets.json` (gitignored), which may extend but never redefine the committed presets.
4. Behavior switches (`USE_*` feature toggles) live as `option()` declarations with documented defaults or as explicit presets — not as README command-line incantations.
5. CI invokes exactly the preset names developers use locally, so environment drift shows up in review instead of in "works on my machine" debates.

C++20 note: do not flip `-std=c++20` globally because one dependency wants it. Add a dedicated preset (for example `cxx20`) once the whole codebase migrates; mixed-standard targets inside one binary invite ODR trouble (see Quality Guidelines).

---

## Compiler Warning Policy

All targets compile with `-Wall -Wextra -Wpedantic` (MSVC: `/W4 /permissive-`), and `-Werror` is on in every preset. A warning must be resolved the moment it appears: fix it, or suppress it at the exact site with a comment explaining why the failure mode cannot occur there.

Beyond the base set, adopt deliberately:

| Flag | Verdict | Rationale |
|------|---------|-----------|
| `-Wshadow` | Enable everywhere | Cheap catch of shadowing bugs |
| `-Wundef`, `-Wnon-virtual-dtor` | Enable everywhere | Near-zero noise, real defects |
| `-Wconversion` | Enable per-target, new code first | High value, noisy over legacy numeric code |
| `-fno-omit-frame-pointer` | Sanitizer and profiling presets | Readable stacks |
| `-Wold-style-cast` | Skip globally | Already covered by a clang-tidy check |

Wrong:

```cpp
#pragma GCC diagnostic ignored "-Wconversion"   // blanket suppression
int n = compute_long_value();                   // silent narrowing
```

Right:

```cpp
int n = static_cast<int>(compute_long_value()); // deliberate narrowing, visible
// Or, when truly unavoidable, a scoped pragma push/pop AT the site,
// with a comment stating why this exact line cannot hit the failure mode.
```

Toolchain upgrades that surface new warnings are fixed or site-suppressed with justification; downgrading `-Werror` is not an option.

---

## Formatting and Static Analysis

`.clang-format` is committed, and formatting is enforced mechanically (a CI step running `clang-format --dry-run -Werror` over tracked sources). Never hand-align code; never debate style in review.

`.clang-tidy` enables a curated set. Worth enabling (low noise, high yield):

| Checks | Why |
|--------|-----|
| `bugprone-*` | Real defect patterns: use-after-move, dangling references, suspicious casts |
| `performance-*` | Unnecessary copies, pass-by-value misses, inefficient calls |
| `modernize-*` | Mechanical language hygiene (`use-override`, `use-nullptr`, `use-emplace`) |
| Selected `misc-*` (`misc-unused-*`) | Dead declarations and parameters |

Noise to leave off by default:

| Checks | Why off |
|--------|---------|
| `cppcoreguidelines-*` wholesale | Hundreds of hits; enable individual high-value ones (`cppcoreguidelines-slicing`, `-init-variables`) |
| `readability-identifier-naming` without a committed config | Churn generator unless the naming table ships with the repo |
| `fuchsia-*`, `llvm-*`, other house styles | Someone else's conventions |
| Most `clang-analyzer-*` | Overlaps compiler warnings; keep only `clang-analyzer-core.*` |

CI runs clang-tidy on changed lines (via `clang-tidy-diff.py` against the merge base), so adoption never demands fixing the whole repository at once. Findings are fixed or silenced with an inline comment explaining why; a bare `// NOLINT` without justification is rejected in review.

---

## Sanitizer Matrix

| Sanitizer | Catches | Requirements | Runtime cost | When to run |
|-----------|---------|--------------|--------------|-------------|
| ASan (+LSan) | Heap/stack/global buffer overflows, use-after-free, double-free, leaks | `-fsanitize=address`, debug info, frame pointers | ~2x CPU, ~2-3x memory | Default gate for any test run touching allocation |
| UBSan | Signed overflow, bad shifts, misalignment, null derefs, invalid vptrs | `-fsanitize=undefined -fno-sanitize-recover=all` | Small; combines with ASan | Paired with ASan in the `asan` preset |
| TSan | Data races, lock-order issues | `-fsanitize=thread`; never combined with ASan | 5-15x CPU, 5-10x memory | Any change touching threads, atomics, or locks |
| MSan | Reads of uninitialized memory | Clang-only; needs instrumented libc++ | ~3x | Niche: parsers of untrusted input; adopt deliberately |

Rules:

1. Debug info (`-g`) is mandatory in sanitizer presets; symbols-free sanitized binaries waste the entire run. `-O1` keeps traces readable while preserving most undefined behavior.
2. ASan and TSan never share one binary — separate presets exist precisely for this.
3. `-fno-sanitize-recover=all` makes findings fail the run instead of printing and continuing.
4. A flaky sanitizer finding is still a finding: fix it or reduce it to a tracked issue the same day. Disabling leak detection via options to quiet tests is forbidden.

---

## CI Build Matrix

Four dimensions exist: compiler x standard x build type x sanitizer. The full cartesian product explodes, so pick axes deliberately and expand only after a bug escapes the net.

Sane minimal default:

| Job | Compiler | Standard | Build type | Sanitizer |
|-----|----------|----------|------------|-----------|
| `default` | GCC 12+ | 17 | Debug | none |
| `release` | GCC 12+ | 17 | Release | none |
| `asan` | Clang 15+ | 17 | Debug | ASan + UBSan + LSan |
| msvc (only if Windows is supported) | MSVC 2022 | 17 | Debug | none |
| `tsan` nightly | Clang 15+ | 17 | Debug | TSan |

Guidance:

1. Two compilers minimum: GCC and Clang disagree productively about templates and UB. MSVC joins only when Windows is a support target.
2. One sanitizer job belongs in the mandatory set (ASan + UBSan); TSan runs scheduled or whenever threading code changes.
3. A Release job matters beyond speed flags: optimization changes UB outcomes and `NDEBUG` removes asserts.
4. Matrix entries enumerate preset names — never raw cmake invocations:

```yaml
strategy:
  matrix:
    preset: [default, release, asan]   # preset names ARE the matrix
steps:
  - run: cmake --preset ${{ matrix.preset }}
  - run: cmake --build --preset ${{ matrix.preset }}
  - run: ctest --preset ${{ matrix.preset }} --output-on-failure
```

---

## Dependency Management

The stance splits by artifact type, and it is opinionated on purpose:

- **Applications** (you ship/deploy the binary): **vcpkg manifest mode**. A `vcpkg.json` beside the root `CMakeLists.txt` declares direct dependencies with version constraints; the manifest baseline pins transitives; presets carry the toolchain file. Fresh machines and CI images build identically with zero global state.
- **Libraries** (others consume your package): **system packages** via honest `find_package(<Pkg> REQUIRED ...)` calls. Consumers want to reuse their existing dependency graph; forcing a private copy invites ODR clashes and diamond-version conflicts.
- **FetchContent**: only for tiny, stable, header-only dependencies pinned to an exact tag, when neither vcpkg nor a system package fits. Never track a moving branch.

Wrong:

```cmake
include(FetchContent)
FetchContent_Declare(json
    GIT_REPOSITORY https://github.com/example/json.git
    GIT_TAG main)                       # moving target, unpinned
FetchContent_MakeAvailable(json)

add_subdirectory(vendor/fmt)            # hand-vendored copy drifting silently
```

Right (application):

```json
{
  "name": "myapp",
  "version": "0.1.0",
  "dependencies": [
    { "name": "fmt", "version>=": "10.1.0" },
    "nlohmann-json"
  ]
}
```

```cmake
find_package(fmt CONFIG REQUIRED)
target_link_libraries(myapp PRIVATE fmt::fmt)
```

Rules:

1. Direct dependencies are declared explicitly; transitive resolution belongs to the package manager, not to `target_link_libraries` folklore.
2. Pin everything: manifest baseline for vcpkg, version constraints in `find_package(...)` where supported.
3. Vendored copies require a written upgrade story; a vendored directory without one is vetoed in review.

---

## Quality Check

```bash
cmake --preset default && cmake --build --preset default   # clean under -Werror
ctest --preset default --output-on-failure
cmake --preset asan && cmake --build --preset asan
ctest --preset asan --output-on-failure
clang-format --dry-run -Werror <changed sources>
clang-tidy -p build/default <changed sources>
```

Checklist:

- [ ] No ad-hoc `cmake -D` flags introduced outside presets
- [ ] Build clean under the full warning set with `-Werror`
- [ ] clang-format and clang-tidy clean on changed sources
- [ ] Threading changes exercised under the `tsan` preset
- [ ] New dependencies entered through manifest/system packages and pinned
