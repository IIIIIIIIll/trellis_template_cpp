# Performance

> Performance practice for C++ in this project: measurement before change, allocation and move discipline by default, and data layouts that respect how caches actually behave.

---

## Overview

Performance work follows one order: measure, change the algorithm or the layout, measure again. Micro-edits justified only by intuition are rejected in review even when harmless — an unmeasured optimization costs future readers comprehension and reviewers time. Baseline is C++17. Numbers you intend to quote come from optimized (`Release`) builds; sanitizer builds answer correctness questions — never as stopwatches.

---

## Measure First

No optimization lands without evidence (`Per.1`) and none begins before the current cost is known (`Per.2`). Claims without numbers are opinions (`Per.6`). Design so optimization stays possible later (`Per.7`): clean interfaces, replaceable data structures.

| Question | Answered by |
|----------|-------------|
| Is this path actually hot? | Profiler flame graph on a representative workload |
| What dominates it — allocation, cache misses, syscalls, locks? | Profiler counters, allocator statistics |
| Did the change help? | Before/after numbers: same machine, same input, optimized (`Release`) build |
| Does the win survive other inputs? | Benchmark spread over realistic sizes |

Rules:

1. Numbers quoted in reviews state machine, input, build configuration, and repetition count.
2. Sanitizer builds answer correctness questions; their slowdowns make them useless for timing.
3. The benchmark that justified a change stays in the tree so the next person can re-verify it.
4. Effort concentrates on code the profiler indicts, not code that merely looks slow (`Per.3`): a 50% win on a component eating 4% of runtime moves the whole program less than a 5% win on one eating 40%. Optimizing anywhere else is churn paid in readability for an unmeasurable return.
5. Keeping context switches off the critical path is threading work (`Per.30`) — lock hold times, shared-state minimization, and wakeup discipline live in [Concurrency](./concurrency.md); the measurement gate here still decides whether the path is critical at all.

```cpp
// Minimal harness: steady_clock, warm cache, results observed so nothing is optimized away
using Clock = std::chrono::steady_clock;

Clock::duration bench(std::span<const Input> cases) {
    std::uint64_t sink = 0;
    const auto start = Clock::now();
    for (const Input& in : cases) {
        sink ^= run_case(in).checksum();     // consume output; dead work gets deleted
    }
    const auto elapsed = Clock::now() - start;
    if (sink == 0xDEADBEEF) { std::puts(""); }   // keep the accumulator live
    return elapsed;
}
```

---

## Allocation Hygiene

Allocation dominates more profiles than any other micro-effect. The target is the count of allocations and deallocations, not merely their unit cost (`Per.14`): `reserve()`, in-place construction, and buffers reused across iterations attack the count itself. Defaults:

1. `reserve()` before growth loops — vectors, string builders, hash maps heading for a known size.
2. `emplace_back(...)` over `push_back(T{...})`: construct in place instead of materializing a temporary to move.
3. Steady-state buffers are reused across iterations, not rebuilt per call; hoist them to a scope outliving the loop.
4. Building text appends into one reserved buffer; chained `+` in a loop is forbidden.

```cpp
// Wrong: O(log n) reallocations, each copying everything accumulated so far
std::string report;
for (const Entry& e : entries) {
    report += format(e) + "\n";
}

// Right: one allocation, sized up front
std::string report;
report.reserve(entries.size() * kAvgLineLen);
for (const Entry& e : entries) {
    report.append(format(e));
    report.push_back('\n');
}
```

Where a profile shows allocator pressure that `reserve()` cannot fix, arenas and object pools are the escalation path — under the ownership and ASan-annotation rules in [Memory and Ownership](./memory-and-ownership.md). An arena introduced without a profile is complexity debt, not performance work (`Per.2`).

Nothing allocates on the critical branch (`Per.15`): sizes are known and buffers staged before the hot region begins. An allocation surfacing mid-hot-path fails review even when today's profile forgives its cost.

Caught by: heap profilers (allocation counts and byte totals); allocator statistics from sanitizer builds during correctness runs.

---

## Move Semantics Economics

Moves exist so expensive values can change hands without copying. The economics only pay when the type cooperates: move construction must be `noexcept`, or containers copy instead (see [Error Handling](./error-handling.md)). Three rules:

1. Sink parameters take by value and `std::move` into storage once, at the last moment — the pass-by table in [Memory and Ownership](./memory-and-ownership.md).
2. `std::move` appears exactly where the source's value is finished, typically at a return or hand-off (`ES.56`). Moving earlier leaves the rest of the function reading a husk.
3. A moved-from object is destructible and assignable; everything else about its state is unspecified. Never read one expecting its old value.

```cpp
// Wrong: moving a const source silently falls back to a copy
void store(const std::string& name) {
    const std::string local = canonical(name);
    records_.push_back(std::move(local));   // still copies: local is const
}

// Right: non-const source, finished being used
void store(const std::string& name) {
    std::string local = canonical(name);
    records_.push_back(std::move(local));   // transfers ownership of the buffer
}
```

Return values need no help: `return local;` already moves or elides, and writing `return std::move(local);` pessimizes by suppressing elision.

---

## Cheap-by-Default Boundaries

Signatures decide whether callers pay for copies. Read-only text arrives as `std::string_view`; read-only sequences arrive as `std::span<const T>` (pointer-plus-size until C++20), so literals, substrings, and slices cross the boundary without allocating. The signature policy itself is owned by [Functions and Interfaces](./functions-and-interfaces.md) — View Inputs Borrow, Never Store; what stays here is the cost rationale.

```cpp
// Wrong: every caller holding a literal or a slice pays for a std::string
Host parse_host(const std::string& url);

// Right: no copy to call it, no copy inside it
Host parse_host(std::string_view url);
```

Two obligations come with views:

1. Inside the callee, slicing is free — `remove_prefix` and `substr` on views allocate nothing. Reach for them before any `.str()` or `std::string` round trip.
2. Views borrow. The moment a value must outlive the call — stored, shipped across threads, put into a container — convert once to an owning type at the storage boundary. Lifetime rules live in [Memory and Ownership](./memory-and-ownership.md).

Redundant temporaries are the same sin inside bodies: each `format(a) + ", " + format(b)` materializes intermediates, while an append chain into one buffer does not.

The static type system is doing performance work too (`Per.10`): `void*` erasures, weak types, and byte-level manipulation strip exactly the information the optimizer needs — strongly typed simple code compiles better than clever low-level code.

---

## Shift Work to Compile Time

Anything computable at compile time should be (`Per.11`): lookup tables, polynomial coefficients, dispatch matrices. A runtime-built table costs an initialization pass on every cold start plus first-touch latency; a `constexpr` table costs binary size once.

```cpp
// Wrong: global with init-order questions, built lazily on first use
const std::array<double, 256>& gain_table() {
    static const auto table = build_gain_table();
    return table;
}

// Right: the compiler builds it; immutable forever, zero startup cost
inline constexpr std::array<double, 256> kGainTable = build_gain_table();
```

Limits: tricks that balloon build minutes or binary size tax everyone on every build. Reserve them for genuinely constant data; metaprogramming for fun fails the same measurement rule as runtime micro-optimization.

---

## Cache Layout Awareness

Data layout decides whether the memory subsystem feeds the CPU or starves it:

1. Compact structures win (`Per.16`): fewer bytes means more objects per cache line. Order members largest-first to close padding holes, or cluster the hottest members together (`Per.17`).
2. Space is time (`Per.18`): shaving a flag-swollen struct from 64 to 56 bytes cuts scan traffic by an eighth before anything else improves.
3. Predictable access wins (`Per.19`): linear walks over contiguous memory beat pointer-chasing through node containers, and small sorted-array lookups often beat hash maps at low cardinality — measure, then choose.
4. Hot data keeps one canonical access path (`Per.12`): redundant aliases — several names reaching the same storage — cost reader clarity and inhibit optimization.

```cpp
// Wrong: flags interleaved between doubles widen the struct with padding
struct Particle {
    bool active;
    double x, y, z;
    bool tagged;
    std::uint32_t material;
    double vx, vy, vz;
};

// Right: doubles clustered, small fields gathered at the tail
struct Particle {
    double x, y, z;
    double vx, vy, vz;
    std::uint32_t material;
    bool active;
    bool tagged;
};
static_assert(sizeof(Particle) == 56);   // layout regressions break the build
```

When profiles show scan-heavy numeric loops starving on strided access, restructure hot data from array-of-structs to struct-of-arrays: one contiguous array per field lets each pass stream exactly the fields it touches. That is an invasive change — hide it behind the interface of the module owning the data, and do it only with profile evidence.

---

## The Anti-Rule: No Data, No Micro-Optimization

Readability is the default currency. Manual strength reduction, hand-unrolled loops, cached `end()` iterators, home-grown string implementations — none land without profiler evidence that this exact spot matters and a benchmark delta proving the variant helps (`Per.1`). Code optimized without data is a tax every future reader pays for a speedup nobody measured. Low-level code is not automatically faster (`Per.5`) — hand-rolled variants routinely defeat optimizers that do marvels with clear high-level code — so simplicity is the default speed strategy, and going lower requires the measured delta.

---

## Quality Check

Gates before merging optimization work: the unit suite green, plus before/after benchmark numbers for any touched hot path produced by an optimized (`Release`) build.

Review checklist:

- [ ] Optimization claims carry before/after numbers: machine, input, optimized (`Release`) build, repetitions
- [ ] Growth loops `reserve()` up front; hot-path buffers reused across iterations
- [ ] Sinks take by value and move; no `std::move` on `const` sources or on returned values
- [ ] Read-only boundaries take `string_view`/`span`; stored data re-owned exactly once
- [ ] Constant tables are `constexpr`; no lazy runtime construction of fixed data
- [ ] Hot struct layouts audited for padding; sizes pinned by `static_assert` where layout matters
- [ ] No micro-optimization without an attached profile and a measured delta

---

**Language**: All documentation should be written in **English**.

> Aligned with the [ISO C++ Core Guidelines](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines) © Standard C++ Foundation and its contributors. Rule IDs cited for cross-reference; original internal digest (internal business use).
