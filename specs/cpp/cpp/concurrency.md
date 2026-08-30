# Concurrency

> Threads, locks, atomics, and message passing for C++ in this project: shared mutable state is always deliberate, synchronization is RAII-based, and threading changes are gated through a ThreadSanitizer build.

---

## Overview

Two facts shape every rule here. First, a data race is undefined behavior, not a slowdown (`CP.2`): racing code has no meaningful specification at all, so "it seems to work" is not evidence. Second, any function may eventually run on more than one thread, whether or not its author planned for it (`CP.1`) — libraries cannot know their callers' threading model.

Default strength: hard.

Caught by: review — no automated detector.

Therefore the design order of preference is:

- **CONC-1.** **Do not share** mutable state across threads at all (`CP.3`).
- **CONC-2.** **Share immutable** data freely — immutability needs no synchronization.
- **CONC-3.** **Communicate instead of sharing**: move ownership through channels, queues, futures.
- **CONC-4.** Where sharing survives, guard every access with a mutex co-designed with its data (`CP.50`).
- **CONC-5.** Atomics for narrow, single-variable cases only.

Baseline: C++17 (`std::thread` plus explicit join discipline). C++20's `std::jthread`, `std::stop_token`, and counting semaphores are preferred where the toolchain provides them; differences are noted inline.

Coroutines are C++20-only; on the C++17 baseline the coroutine section below does not apply.

---

## Shared Mutable State Is a Design Decision

**CONC-6 (hard).** Mutable data reachable from two threads without a synchronization mechanism is a defect regardless of observed behavior. Every shared object gets one row in this ladder, chosen deliberately:

Caught by: TSan reports the race when both accesses actually execute under a ThreadSanitizer build — see the gate below. Nothing catches a race whose interleaving the test run happens never to trigger, which is why the design rule comes first.

| Rank | Mechanism | Cost | Use when |
|------|-----------|------|----------|
| 1 | Thread-local or per-task copies | None | State nobody else needs |
| 2 | Immutability (`const`, built once, frozen) | None | Configuration, lookup tables, snapshots |
| 3 | Message passing (queues, futures) | Copy/move cost, one indirection | Pipelines, work distribution |
| 4 | Mutex-guarded shared state | Contention, deadlock risk | Genuinely shared hot state |
| 5 | Atomics | Subtle memory-model reasoning | Single flags, counters, lock-free structures |

Wrong:

```cpp
// A cache reachable from worker threads, synchronized by nobody — corrupted nodes in production.
class SessionCache {
public:
    Session& get(int id);
private:
    std::unordered_map<int, Session> sessions_;
};
```

Right:

```cpp
// The mutex is part of the type's contract: all access goes through it.
class SessionCache {
public:
    std::shared_ptr<const Session> get(int id) {
        std::lock_guard lock(mutex_);          // C++17: lock_guard<std::mutex>
        return lookup_locked(id);              // returns an immutable snapshot
    }
private:
    std::shared_ptr<const Session> lookup_locked(int id);
    mutable std::mutex mutex_;
    std::unordered_map<int, Session> sessions_;
};
```

Notes:

- **CONC-7 (default).** Prefer making objects immutable over making them synchronized: `const`-first APIs keep the concurrency story out of most types entirely (constants-and-immutability defaults: immutable by default, `const` members by default, `const&` parameters by default — `Con.1`, `Con.2`, `Con.3`; recompute-at-compile-time where possible, `Con.5`).
- **CONC-8 (default).** Refactoring to remove sharing beats refactoring to protect it. Before adding a second mutex to a class, ask which design produced two writers.
- Returning shared *immutable* snapshots (`shared_ptr<const T>`) lets readers work without locks after the hand-off point.
- **CONC-9 (hard).** Ownership crossing unrelated thread lifetimes goes through `shared_ptr` (`CP.32`) — the only safe deletion story; static objects, never-freed objects, and owner-outlives-sharer arrangements are exempt. Ladder-first: prefer the immutable snapshots above so readers need no locks, and justify sharing per [Memory and Ownership](./memory-and-ownership.md).

---

## Threads: `jthread` and Join Discipline

Default strength: hard.

**CONC-10.** A running thread is a resource like a file descriptor: someone must own it and wait for its completion exactly once.

Caught by: review for `detach()` and unjoined `std::thread`; TSan flags races caused by threads outliving their data.

| Tool | Status | Notes |
|------|--------|-------|
| `std::jthread` (C++20) | Preferred owner | Joins in its destructor; cooperative cancellation via `stop_token` |
| `std::thread` | Allowed with care | Must be joined (or moved into a pool/jthread wrapper) before every scope exit |
| `detach()` | Forbidden in application code | Detached threads outlive every guard, logger, and config object they touch |
| **CONC-11** Raw handles from third-party runtimes | Quarantined | Wrap immediately in an owning RAII adapter |

**CONC-12.** The guideline phrasing that joins should behave like destructors — automatic, unconditional, exception-safe (`CP.23`) — and the preference for a joining thread abstraction over bare `std::thread` (`CP.25`) land on `std::jthread` in C++20 code.

**CONC-13.** Never detach (`CP.26`).

**CONC-14.** Think of a thread as a global container (`CP.24`): anything reachable from it must provably outlive every possible use, and a thread that might detach is assumed to outlive its constructing scope — including racing static-object teardown at program exit. The detach ban and joining owners subsume most of the risk, yet the framing stays load-bearing for third-party runtimes, which the table above quarantines behind owning RAII adapters.

Wrong:

```cpp
void handle_request(Request req) {
    std::thread responder([req] { send_reply(req); });
    // If send_reply throws or handle_request returns early: std::terminate.
    responder.detach();   // and now it may run forever past shutdown
}
```

Right:

```cpp
#include <thread>

void poll_device(std::stop_token stop, Device& dev) {
    while (!stop.stop_requested()) {
        dev.sample();
        std::this_thread::sleep_for(std::chrono::milliseconds(10));
    }
}

void start_polling(Device& dev) {
    std::jthread worker(poll_device, std::ref(dev));   // joins itself at scope exit;
    request_shutdown(worker.get_stop_token());         // cancellation is cooperative
}
```

**CONC-15.** On C++17, wrap `std::thread` in a small joining-thread class whose destructor calls `join()` unless already joined; do not sprinkle `join()` calls through control flow — the early-return branch is how terminates happen.

**CONC-16.** Waiting for a thread's result means `join()` (or a future), not polling a flag.

---

## Locks

**CONC-17 (hard).** Locking is RAII-only. Plain `lock()`/`unlock()` pairs are forbidden (`CP.20`) — the early return, the throw, and the second maintainer all defeat them.

Caught by: TSan for the resulting races; deadlock detection tools and code review for lock-order issues. clang-tidy's concurrency checks catch some unnamed-guard cases; the rest are review items.

| Situation | Tool |
|-----------|------|
| Guard a scope, one mutex | `std::lock_guard` (or CTAD `std::scoped_lock` on C++17) |
| Acquire several mutexes without deadlock | `std::scoped_lock` / `std::lock` (`CP.21`) |
| Need condition variables, timed ops, deferred locking | `std::unique_lock` |
| Read-mostly shared structures | `std::shared_mutex` with `shared_lock`, measured first |
| Anything else (manual pairs, double-checked patterns) | No |

Rules:

- **CONC-18 (hard).** Define each mutex next to the data it guards, with names that pair visibly (`state_` / `stateMutex_`) (`CP.50`). A mutex guarding three distant fields is a distributed invariant waiting to break.
- **CONC-19 (hard).** Name every guard (`CP.44`). The brace spelling compiles, runs, and protects nothing — an unnamed temporary that destroys the lock at the end of the statement. The paren spelling of the same line is not the safer alternative: it is a most-vexing-parse declaration of a default-initialized guard, and `std::lock_guard` has no default constructor, so it fails to compile. The silent sibling is the paren spelling of `unique_lock`, which *is* default-constructible:
   ```cpp
   std::lock_guard<std::mutex>{queueMutex_};         // WRONG: unnamed temporary, destroyed at end of statement
   std::unique_lock<std::mutex>(m1);                 // WRONG: vexing parse — default-constructed local named `m1`, never locks
   std::lock_guard<std::mutex> guard(queueMutex_);   // RIGHT: named, lives to scope end
   ```
- **CONC-20 (default).** Hold locks for the shortest region that keeps the invariant (`CP.43`): copy what you need out under the lock, then work on the copy. I/O, allocation-heavy formatting, and logging stay outside critical sections.
- **CONC-21 (hard).** Never call unknown code while holding a lock (`CP.22`) — callbacks, virtual functions on overridable interfaces, `std::function` parameters, anything that can re-enter. The callee that takes another lock (or the same one) deadlocks; the callee that runs long serializes the whole system. Copy inputs out, release, then invoke.
- **CONC-22 (hard).** Wait on a condition variable only inside a predicate loop (`CP.42`); spurious wakeups are guaranteed, not theoretical. Prefer waits with timeouts so a lost wakeup degrades instead of hanging forever.

Wrong:

```cpp
void broadcast(const Event& ev, const std::vector<Listener*>& listeners) {
    std::lock_guard<std::mutex> guard(listenersMutex_);
    for (Listener* l : listeners) {
        l->on_event(ev);      // unknown code under our lock:
                              // on_event() taking statsMutex_ here = deadlock roulette
    }
}
```

Right:

```cpp
void broadcast(const Event& ev, const std::vector<Listener*>& listeners) {
    std::vector<Listener*> snapshot;
    {
        std::lock_guard<std::mutex> guard(listenersMutex_);
        snapshot = listeners;              // copy under the lock
    }                                       // released before callbacks
    for (Listener* l : snapshot) {
        l->on_event(ev);
    }
}
```

---

## Coroutines and Suspension Points

A coroutine is a threading change like any other and answers to the TSan gate below. Three rules keep suspensions from shredding memory:

Default strength: hard.

Caught by: review — no automated detector for the constructs themselves; TSan catches the resulting races when the path executes under the gate.

- **CONC-23.** Never write a capturing lambda that is a coroutine (`CP.51`): the captures die with the closure scope while resumption after the first suspension reads them — use-after-free even for `shared_ptr` and copyable captures. Take values as parameters, or write a plain coroutine function.
- **CONC-24.** Never hold a lock across a suspension point (`CP.52`): resumption may want the held lock (self-deadlock), may land on a different thread (undefined behavior), and if the coroutine is destroyed while suspended, the frame's guard destructor runs on whichever thread does the destroying — cross-thread unlock again — all while the held lock serializes everyone else for the suspension's duration. Scope the guard, release, then suspend; the shortest-critical-region rule gains a coroutine clause.
- **CONC-25.** Coroutine parameters pass by value (`CP.53`): reference parameters dangle from the first suspension onward, and some coroutine shapes suspend before their first line runs. The copy lives in the coroutine frame; output parameters are forbidden outright, matching the return-don't-out discipline.

---

## Atomics: Flags and Counters Only

Default strength: hard.

Atomics provide lock-free reads/writes of single variables. They are the tool for progress flags, counters, sequence numbers, and published pointers. They are not a general synchronization mechanism: an atomic variable does not make neighboring non-atomic data safe, does not compose into multi-variable invariants, and its memory-ordering rules are easy to get subtly wrong.

Caught by: TSan for the racy cases; review for `volatile` used near threading and for any new `memory_order_` spelling beyond relaxed-with-comment.

**CONC-26.** `volatile` is not synchronization (`CP.8`). It disables compiler caching around hardware-special accesses; it inserts no fences, orders nothing, and races on `volatile` remain undefined behavior. Its legitimate job is narrow (`CP.200`): memory shared with non-C++ code or hardware — clock registers, device mappings — almost never a local or data member; a flagged `volatile T` nearly always wanted `std::atomic<T>`.

Wrong:

```cpp
volatile bool ready = false;            // volatile ≠ atomic; race is UB
int shared_counter = 0;                 // guarded by... hope
while (!ready) {}                       // spin the CPU at 100%
```

Right:

```cpp
#include <atomic>

std::atomic<bool> ready{false};
std::atomic<uint64_t> packets_dropped{0};
// Sequential consistency stays the default until a measured problem says otherwise.
ready.store(true);

if (ready.load()) { /* proceed */ }

packets_dropped.fetch_add(1, std::memory_order_relaxed);   // statistics need no ordering
```

Rules:

- **CONC-27.** Default to sequential-consistency ordering. Relax/acquire/release require a comment naming the exact protocol they implement and why it suffices.
- **CONC-28.** Two variables whose relationship matters (a buffer pointer plus its length, a state plus a payload) need a mutex, a sequenced publication protocol, or a single larger atomic — never two independent atomic members.
- **CONC-29.** `shared_ptr`'s atomic refcounts are not atomic pointer access: concurrent reads and writes of a shared `shared_ptr` member race even when every pointee is immutable. On the C++17 baseline the spellings are `std::atomic_load(&ptr_)` / `std::atomic_store(&ptr_, value)` — deprecated in C++20 in favor of `std::atomic<std::shared_ptr<T>>` — or a plain mutex; the better default remains the immutable-snapshot hand-off (`shared_ptr<const T>`) from the design section above, which leaves readers nothing to synchronize.
- **CONC-30.** Do not write lock-free data structures by hand (`CP.100`). The standard containers, well-tested concurrent libraries, or a plain mutex cover nearly everything; a homemade queue is a research project with a bug quota. Beyond atomics and a handful of standard patterns, lock-free programming is expert-only (`CP.102`): a proposal arrives citing the literature (Williams, Herlihy & Shavit, Boehm) and survives design review, or it stays a mutex. Beware classic hazards such as A-B-A reuse of addresses if you ever must (`CP.101` territory).
- **CONC-31.** Lazy initialization is solved by magic statics (`static local` initialization is thread-safe since C++11) or `std::call_once`. Hand-rolled double-checked locking is forbidden (`CP.110`, `CP.111`).

---

## Message Passing and Task-Based Flow

Caught by: review — no automated detector.

Wherever the design allows, replace shared state with data flowing between owners: a work item moves down a queue, a future carries a result back, nobody needs a lock because nobody shares (`CP.31`).

**CONC-32 (hard).** Think in tasks, not threads (`CP.4`): name *what* runs concurrently, and let infrastructure decide *where*. Ad-hoc `thread-per-request` scales poorly and hides its cost structure; a bounded pool makes both visible.

```cpp
// Producer/consumer through a bounded blocking queue: ownership moves, no locks leak.
void ingest(ThreadSafeQueue<Job>& jobs, std::stop_token stop) {
    while (!stop.stop_requested()) {
        auto job = jobs.pop();           // blocks; Job moved, not shared
        process(job);
    }
}
```

Futures carry one-shot results (`CP.60`): a concurrent task returns its value through a future, preserving ordinary call semantics — value or exception, no explicit locking:

```cpp
auto result = std::async(std::launch::async, compress_chunk, chunk);
// ... overlap other work ...
auto compressed = result.get();          // exactly once, transfers ownership
```

Pitfalls:

- **CONC-33 (hard).** The launch policy is spelled on every call: without `std::launch::async`, `std::async` may run the task deferred — inline at `.get()`, or not at all if the future is dropped — while an async launch blocks in the future's destructor. Omitting the policy is forbidden.
- **CONC-34 (hard).** `std::async` returned-future destruction blocks until completion; dropping the future to "fire and forget" turns an async call into a synchronous surprise (`CP.61`). Fire-and-forget work goes to the project's job queue, not `std::async`.
- **CONC-35 (default).** `promise`/`future` pairs are single-use; a broken promise (destroyed without setting) surfaces as an exception on the waiting side — handle it where the `.get()` lives.
- **CONC-36 (hard).** Channels and queues must have a bound and an overflow policy. Unbounded growth converts a producer/consumer bug into an OOM incident hours later.

---

## Thread Pools and Shutdown

Caught by: review — no automated detector.

Thread creation and destruction cost real time (`CP.41`): a thread-per-message dispatcher is the anti-pattern, ad-hoc spawning hiding its cost structure until latency budgets vanish. Pre-created workers fed by a queue keep both visible.

Default infrastructure for background work is one process-wide pool with:

- **CONC-37 (hard).** **Bounded queue depth** with an explicit policy on overflow (block, reject, or shed — documented per entry point).
- **CONC-38 (default).** **Pool size** derived from workload class: CPU-bound ≈ hardware cores; I/O-bound sized against measured latency targets, not folklore.
- **CONC-39 (hard).** **Cooperative cancellation**: jobs accept `std::stop_token` (C++20) or check an atomic shutdown flag between units, so drain time is bounded.
- **CONC-40 (hard).** **Ordered shutdown**: stop accepting, drain or cancel queued work, join workers — in that order, exercised by a test, because shutdown races are the ones nobody debugs calmly.

**CONC-41 (hard).** Library code never spawns unbounded threads per call and never assumes a pool exists around it; accept an executor/pool reference where scheduling matters. Application wiring decides pools.

---

## The TSan Gate

**CONC-42 (hard).** Any change touching threads, atomics, locks, or signal handlers runs a ThreadSanitizer build (`-fsanitize=thread`) of the full test suite before merge:

Caught by: review — no automated detector.

Operating notes:

- **CONC-43 (hard).** TSan detects data races, lock-order inversions, and destruction-of-locked-mutex hazards *when executed*. Tests must genuinely exercise the concurrent paths; a test that never overlaps two threads validates nothing here.
- **CONC-44 (hard).** TSan and ASan never share one binary — the separate builds exist precisely for that reason.
- Expect real overhead (roughly 5–15x CPU, 5–10x memory in practice): schedule the full suite accordingly rather than skipping it.
- **CONC-45 (hard).** A flaky sanitizer finding is still a finding. Fix it, or reduce it to a tracked issue the same day; quieting the tool is forbidden.

**CONC-46 (hard).** Signal handlers sit inside this gate too. Deviation from `CP.201`: the upstream entry is itself a question mark; its usable content is that very little is async-signal-safe and the best handler communicates "not at all". Local posture: handlers store only to lock-free atomic flags consumed outside the handler — polled or drained via self-pipe — and any signal-handler change runs a ThreadSanitizer build explicitly.

---

## Quality Check

Before merging concurrency code, confirm the suite is green under a ThreadSanitizer build:

- [ ] New shared mutable state justified against the isolation ladder; message passing or immutability considered first
- [ ] Every mutex defined adjacent to its data; all access routes go through it
- [ ] All guards RAII-based and named; no manual `lock()`/`unlock()`
- [ ] Multi-lock acquisition uses `std::scoped_lock`; global lock ordering documented where multiple mutexes meet
- [ ] No unknown/callback/virtual-overridable code invoked under a held lock
- [ ] Condition-variable waits sit in predicate loops with timeouts
- [ ] Threads owned by `std::jthread` (or a joining wrapper on C++17); zero `detach()` calls
- [ ] Atomics limited to single-variable flags/counters; ordering relaxations commented; no `volatile` used for synchronization
- [ ] Queues bounded with a stated overflow policy; shutdown path drains and joins deterministically
- [ ] Concurrent paths actually exercised under a ThreadSanitizer build, findings resolved or tracked

---

**Language**: All documentation should be written in **English**.

> Aligned with the [ISO C++ Core Guidelines](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines) © Standard C++ Foundation and its contributors. Rule IDs cited for cross-reference; original internal digest (internal business use).
