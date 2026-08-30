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
| Catch2 (v3+) | Acceptable | Preferred when a zero-install dependency model matters more than gmock: v3 is a compiled library — vendoring the amalgamated two-file release keeps installation trivial — while header-only is the v2 model, which trades per-TU compile time for zero build wiring |

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

Every new test file must be registered with the test runner so the suite discovers it automatically.

A test that exists but is not registered does not exist — nothing ever executes it, and it rots.

Scope of the 1:1 mandate: every production translation unit with **observable behavior** gets a mirrored suite. `main.cpp` glue, generated code, and vendored code are excluded — they carry no project-owned behavior to pin, and a test file for them would violate What NOT to Test, not honor it.

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

The name must read as a sentence describing the contract, so a red test communicates the bug without opening the file.

Deviation-style caveat on underscores in the `TEST` arguments: GoogleTest documents that underscores there can generate colliding fixture classes — `TEST(Time, Flies_Like_An_Arrow)` and `TEST(Time_Flies, Like_An_Arrow)` both expand to a class named `Time_Flies_Like_An_Arrow` — and may break across gTest versions. The grammar above stays; the mitigation is structural: keep the `<Suite>` argument underscore-free, so an underscore can never blur the suite boundary.

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
| Fast | Whole unit suite finishes in seconds; any test over ~100 ms belongs in the integration tier — the budget is declared on the default **ASan + UBSan** run, so the ~2x sanitizer cost is inside it (the plain build is roughly half the cost, which only helps) |
| Isolated | No ordering dependence, no shared mutable globals; every test runs alone via `--gtest_filter`, and the suite passes `--gtest_shuffle --gtest_repeat=2` (or the framework's equivalent shuffle mode) — passing alone verifies independence, only shuffling exposes order dependence |
| Repeatable | Same verdict on every machine and run: no wall-clock reads, sleeps, network, or unseeded randomness |
| Self-validating | Assertions decide pass/fail; a test requiring human inspection of output is not a test |
| Timely | Written with the change it protects, not scheduled "later" |

**Integration tier.** Anything over the 100 ms gate — process spawns, network or filesystem fixtures, end-to-end runs — goes to a separate integration suite: its own binary or tag, excluded from the fast default pass, so the everyday gate stays in seconds. Same FIRST rules apply; only the run schedule differs.

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

Unit tests run under sanitizers by default; a green test run without them proves less than it appears to. Memory bugs often manifest as *passing* tests that corrupt state for later ones.

| Sanitizer | What it catches | Hard constraints | Rough cost |
|-----------|-----------------|------------------|------------|
| ASan (+LSan) | Heap/stack/global buffer overflow, use-after-free, use-after-return, double free; LSan reports leaked allocations | Never shares a binary with TSan or MSan | ~2x |
| UBSan | Undefined behavior short of corruption: signed overflow, bad shifts, misaligned access, invalid enum values | Compiled with `-fno-sanitize-recover=all` so findings fail the run instead of printing and continuing | small |
| TSan | Data races, lock-order inversions, destruction-of-locked-mutex hazards | Never combined with ASan; reports only interleavings that actually execute | 5–15x |
| MSan | Reads of uninitialized memory | Clang-only; needs an instrumented libc++ and fully instrumented dependencies | ~3x |

Two postures follow from the table. The unit suite runs under **ASan + UBSan**, failing hard on the first finding — a sanitizer warning printed and ignored is a bug deferred to production. Threading changes additionally run under **TSan** in its own build, because TSan cannot combine with ASan.

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

Internal-linkage helpers meet the same wall from the other side: a function in an anonymous namespace (`SF.22`) is invisible outside its translation unit, so it is untestable by construction — and the white-box ban above rules out peeling it open. The reachable path is promotion: logic worth direct testing moves to an internal header or a named-namespace translation unit with its own suite; what stays anonymous is what the public suite already exercises transitively. The linkage side of this trade is the quality guide's [internal-linkage rules](./quality-guidelines.md).

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

- [ ] New/changed translation units with observable behavior have a mirrored `<name>.test.cpp` registered in the build (`main.cpp`, generated, and vendored code excluded)
- [ ] Names follow `Test_<Subject>_<Behavior>_<Expectation>` and read as sentences
- [ ] Suite passes under ASan + UBSan with `-fno-sanitize-recover=all`
- [ ] Every test passes alone under `--gtest_filter`, and the suite stays green under `--gtest_shuffle --gtest_repeat=2` (or the framework's equivalent shuffle mode)
- [ ] Time injected, randomness seeded, zero sleeps
- [ ] Assertions target observable public behavior; no private-member access
- [ ] Error paths and boundaries covered, not just the happy path
- [ ] No tests of trivial wrappers, third-party internals, or generated code

---

**Language**: All documentation should be written in **English**.

> Aligned with the [ISO C++ Core Guidelines](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines) © Standard C++ Foundation and its contributors. Rule IDs cited for cross-reference; original internal digest (internal business use).
