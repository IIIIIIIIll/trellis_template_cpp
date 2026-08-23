# Testing Conventions

> Testing conventions for C++ code: framework choice, file layout, naming, sanitizer pairing, and what deserves a test at all.

---

## Overview

Tests exist to pin **observable behavior**. A test suite that is slow, order-dependent, or coupled to private internals gets deleted within a year; these rules keep the suite one people run voluntarily.

---

## Framework Stance

| Framework | Status | Notes |
|-----------|--------|-------|
| GoogleTest | Default | Mature, universally known; death tests, value/type-parameterized tests, `gtest_discover_tests` |
| Catch2 (v3+) | Acceptable | Preferred when a header-only / zero-install dependency model matters more than gmock |

One framework per repository — never mix. Choose Catch2 only deliberately and document why in the repo README.

---

## File Layout

Test files mirror the source tree, named `<name>.test.cpp`, one test binary per production translation unit:

```
src/
  net/http/parser.cpp
  net/http/router.cpp
tests/
  net/http/parser.test.cpp
  net/http/router.test.cpp
  test_util.h            // shared fixtures/helpers, no tests of its own
```

Every new test file must be registered in the build and discovered by the runner:

```cmake
add_executable(parser.test net/http/parser.test.cpp)
target_link_libraries(parser.test PRIVATE mylib GTest::gtest_main)
include(GoogleTest)
gtest_discover_tests(parser.test)
```

A test that exists but is not registered does not exist — it will not run in CI and it will rot.

```cpp
// Wrong: unregistered "temporary" test living in src/, still there two years later
// src/net/http/manual_check.cpp
int main() { assert(parse("") == nullopt); }

// Right: registered suite next to its siblings
// tests/net/http/parser.test.cpp
TEST(HttpParser, Test_Parse_EmptyInput_ReturnsError) { ... }
```

---

## Naming

Format: `TEST(<Suite>, Test_<Subject>_<Behavior>_<Expectation>)`.

- `<Suite>`: component under test (`HttpParser`, `RingBuffer`).
- `<Subject>`: function or feature (`Parse`, `Push`).
- `<Behavior>`: input or circumstance (`TruncatedHeader`, `AtCapacity`).
- `<Expectation>`: outcome (`ReturnsError`, `DropsOldest`).

The name must read as a sentence describing the contract, so a CI failure communicates the bug without opening the file.

```cpp
// Good
TEST(HttpParser, Test_Parse_TruncatedHeader_ReturnsTruncatedError);
TEST(RingBuffer, Test_Push_AtCapacity_DropsOldest);

// Bad: tells you nothing when red
TEST(HttpParser, Test1);
TEST(HttpParser, Works);
TEST(HttpParser, HandlesErrors);        // which errors? from what?
```

---

## FIRST Principles, Adapted

| Principle | Meaning here |
|-----------|--------------|
| Fast | Whole unit suite finishes in seconds; any test over ~100 ms belongs in an integration tier |
| Isolated | No ordering dependence, no shared mutable globals; every test runs alone via `--gtest_filter` |
| Repeatable | Same verdict on every machine and run: no wall-clock reads, sleeps, network, or unseeded randomness |
| Self-validating | Assertions decide pass/fail; a test requiring human inspection of output is not a test |
| Timely | Written with the change it protects, not scheduled "later" |

Determinism mechanics:

- Inject time (`Clock` interface) instead of reading system time.
- Seed RNG per test with a fixed value; reserve `std::random_device` for fuzz harnesses only.
- Never `sleep()` to wait for anything; wait on the synchronization primitive itself or fake the clock.

```cpp
// Wrong: flaky by construction
TEST(Cache, Test_Expiry_EntriesVanish) {
    put("k", "v", std::chrono::seconds(1));
    std::this_thread::sleep_for(std::chrono::milliseconds(1100));   // timing race
    EXPECT_TRUE(find("k").empty());
}

// Right: time is controlled by the test
TEST_F(CacheTest, Test_Expiry_AfterTtl_EntryNotFindable) {
    cache_->put("k", "v", ttl_);
    clock_.advance(ttl_ + std::chrono::seconds(1));
    EXPECT_FALSE(cache_->find("k").has_value());
}
```

---

## Sanitizer Pairing

Unit tests are run under sanitizers in CI; a green test run without them proves less than it appears to. Memory bugs often manifest as *passing* tests that corrupt state for later ones.

- **ASan + UBSan** on every unit-suite CI job, failing hard instead of limping on.
- **TSan** in a separate job (ASan and TSan cannot combine).
- Leak detection ships with ASan (LSan).

```bash
cmake -B build-san -DCMAKE_BUILD_TYPE=Debug \
      -DCMAKE_CXX_FLAGS="-fsanitize=address,undefined -fno-sanitize-recover=all -g"
cmake --build build-san -j
ctest --test-dir build-san --output-on-failure
```

`-fno-sanitize-recover=all` turns UB into immediate hard failures — a sanitizer warning printed and ignored is a bug deferred to production.

---

## What to Test

Test the public contract through the public API:

- **Observable behavior**: return values, emitted events, state transitions visible to callers.
- **Boundary conditions**: empty input, single element, capacity exactly reached, maximum sizes, malformed encodings.
- **Error paths**: every documented error code/status thrown or returned by the unit is exercised at least once. Untested error paths are theoretical code.
- **Regressions**: every fixed bug ships with a test that failed before the fix.

```cpp
// Good: contract-level assertions
EXPECT_EQ(router.route("/users/42").handler(), &handle_user);
EXPECT_EQ(parser.parse("GET /\r\n").error(), ParseErr::kIncomplete);

// Bad: mirrors implementation steps; breaks on any refactor that preserves behavior
EXPECT_CALL(mock_internal_scanner, scan_token_times(3));
EXPECT_EQ(parser.state_, State::kHeaderDone);     // private member poking
```

White-box access to privates — `friend class ...Test`, `#define private public`, testing free functions that exist only to serve internals — is forbidden. If a private piece is complex enough to need direct tests, it wants to be extracted behind its own interface and tested through it.

---

## Test Utilities and Fixtures

- Prefer **fixtures** (`::testing::Test` subclasses; fresh instance per test) over global/shared state. Anything static-and-mutable in test code is a defect waiting for `-j` parallelism.
- Shared helpers live in `tests/test_util.h` / `test_fixtures.h`; duplicated setup across suites is a refactor signal, not a style choice.
- Randomness: seeded generators created inside the fixture; log the seed so failures replay.
- No cross-test data files with hidden coupling; each test constructs the inputs it needs.

```cpp
// Right: fresh state per test, deterministic seed
class RingBufferTest : public ::testing::Test {
protected:
    void SetUp() override { rng_.seed(42); }
    RingBuffer make_filled(size_t n) {
        RingBuffer b{kCapacity};
        for (size_t i = 0; i < n; ++i) b.push(rng_());
        return b;
    }
    std::mt19937 rng_{42};

private:
    static constexpr size_t kCapacity = 8;
};

// Wrong: global mutated by every test; result depends on execution order
static RingBuffer g_buffer{8};
TEST(RingBuffer, A) { g_buffer.push(1); }
TEST(RingBuffer, B) { EXPECT_EQ(g_buffer.size(), 1); }   // passes alone, fails shuffled
```

---

## What NOT to Test

Skip these; they cost review time and rot without catching defects:

- **Trivial getters/setters** and one-line forwarding wrappers — exercised transitively by every behavioral test.
- **Third-party library behavior** — do not re-test whether the vendor's sort sorts. Test *your* seam: the adapter's mapping between your types and theirs.
- **Generated and vendored code** — owned upstream.
- Coverage percentage as a goal: chasing a number produces assertion-free tests, which are worse than none.

```cpp
// Bad: tests the compiler, not the design
TEST(Name, Test_Name_GetterReturnsName) {
    User u{"ada"};
    EXPECT_EQ(u.name(), "ada");
}

// Good: test the adapter's actual logic — how vendor errors map to ours
TEST(LibAdapter, Test_Open_MissingFile_MapsToNotFound) {
    EXPECT_EQ(adapter.open("/no/such/file").error(), Errc::kNotFound);
}
```

---

## Quality Check

Before merging test code, confirm:

- [ ] New/changed translation units have a mirrored `<name>.test.cpp` registered in the build
- [ ] Names follow `Test_<Subject>_<Behavior>_<Expectation>` and read as sentences
- [ ] Suite passes under ASan + UBSan with `-fno-sanitize-recover=all`
- [ ] Every test passes alone under `--gtest_filter` (no ordering or shared-state dependence)
- [ ] Time injected, randomness seeded, zero sleeps
- [ ] Assertions target observable public behavior; no private-member access
- [ ] Error paths and boundaries covered, not just the happy path
- [ ] No tests of trivial wrappers, third-party internals, or generated code

<!-- registry-e2e-marker -->
