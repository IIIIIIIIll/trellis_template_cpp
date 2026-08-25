# Review Findings

## 2026-08-25 · build-and-toolchain.md framing (DECIDED)

Developer decision: this registry ships a **language and code-writing guide**;
it must not mandate toolchains. All build-system/CI/dependency-management
content is removed:

- `specs/cpp/cpp/build-and-toolchain.md` deleted entirely.
- CMake/preset/CI/vcpkg/FetchContent mentions stripped repo-wide:
  guides' Quality Check blocks, index/README tables and trees,
  `index.json` description+tags, registry spec counts.
- **Boundary**: sanitizer / clang-tidy / compiler-warning *names* stay where
  they pair a pitfall with its detector ("Caught by:" lines) — that is code
  knowledge, not build policy, and the authoring contract requires detectors.
  Build-system mechanics (how to configure those tools into a build/CI) go.
- Vocabulary map for rewording: "`asan` preset" → "an ASan+UBSan build";
  "`tsan` preset" → "a ThreadSanitizer build"; "`release` preset" → "an
  optimized (`Release`) build"; cmake command blocks → prose gates without
  prescribed invocation.

## Resolution status (2026-08-25, post-sweep)

1. **Footer contract violated repo-wide** — RESOLVED by enforcement: the
   written authoring contract wins, Language line inserted into every shipped
   guide (FooterFix agent: 10 files; memory-and-ownership.md inline).
2. **Unnamed C-style-cast detector** — RESOLVED: sweep added
   `cppcoreguidelines-pro-type-cstyle-cast` (ES.49) to the enable-first table
   in `core-guidelines-alignment.md`; clang-tidy curation now canonically
   lives in `quality-guidelines.md` "Static Analysis Curation".
3. **Wildcard tidy opt-outs** — RESOLVED: named exceptions
   (`bugprone-easily-swappable-parameters`,
   `modernize-use-trailing-return-type`) listed there.
4. **Missing CMake minimum** — MOOT: all build-system content removed by
   developer decision.

## memory-and-ownership.md verdicts (2026-08-25)

- Verified correct: ownership-ladder citations (R.2-R.6, R.10, R.13, R.15,
  R.20-R.24, R.30-R.37), invalidation table, sink-by-value rules,
  dangling-view examples, arena ASan annotations, R.36 written deviation.
- Applied: oversized-local attribution softened (upstream anchor
  unverifiable offline); `-Wdangling-reference` false-positive hedge; CI
  phrasing neutralized by sweep.
- Deferred: `nothrow`-new-as-fallback vs error-handling policy — cross-check
  during error-handling.md review.

## quality-guidelines.md early observations (read during spot-check)

- NL.16 member order, NL.4/15/17/18/20 delegation deviations, SF.6/SF.8
  deviations all carry written rationale per authoring contract.
- Technically sound so far: std forward-declaration UB, inline constexpr
  linkage reasoning, static-init fiasco remedies, PIMPL ABI story,
  RTTI-across-modules stance. Full pass pending (L301-389 unread).

## error-handling.md verdicts (2026-08-25)

- Citation audit against upstream master (2026-06-14 snapshot, local catalog
  /tmp/all_rules.txt): all cited E-IDs exist; E.2/E.3/E.4/E.5/E.7/E.8/E.12/
  E.13/E.14/E.15/E.16/E.19/E.25/E.27/E.28/E.30/E.31 paraphrases accurate,
  including the four written deviations. Only E.26 was applied outside its
  no-exceptions premise — FIXED inline with a premise clause.
- Fixed: `make_error` snippet implied enum→error_code without the
  std::is_error_code_enum specialization; replaced with a wiring note.
- Verified correct: throw-by-value/catch-const-ref, bare `throw;` slicing
  warning, vector move_if_noexcept growth claim, noexcept table + snapshot()
  counter-example, conditional noexcept syntax, ABI-boundary translation
  policy incl. _GLIBCXX_USE_CXX11_ABI caveat, throw_with_nested pattern,
  log-once-at-handler discipline.
- Resolved deferred memory-doc question: `nothrow` new as fallback is
  consistent with this guide's can't-throw deviations (E.25/E.27) — no
  contradiction.
- Cosmetic backlog: five guides lacked `---` above footer → SepFix agent.

## testing-conventions.md verdicts (2026-08-25)

- Verified correct: framework table, per-TU test layout stance, naming
  grammar, FIRST adaptation (~100 ms tiering), clock/RNG injection examples,
  sanitizer reference table (now canonical home), white-box prohibition,
  fixture-over-globals example, what-NOT-to-test incl. coverage-as-goal ban.
- Fixed inline: dangling colon left by sweep at the registration paragraph.
- Known nuance, left alone deliberately: "use-after-return" in the ASan row
  assumes stack-use-after-return detection enabled (runtime opt-in on some
  toolchains); adding a hedge would risk stating unverified toolchain
  defaults.

## Final structural gate (2026-08-25, post SepFix) — ALL PASS

Manifest paths exist · relative links resolve · every shipped doc ends with
exactly one Language line + attribution · `specs/cpp/README.md` tree/table ==
disk == top-level README tree (12 docs; README self-listing expected).

## functions-and-interfaces.md verdicts (2026-08-25)

- Citation audit: every cited P./F./I./C.46/Con./Enum./SL.str ID exists
  upstream; paraphrases accurate incl. all five written deviations
  (F.23/F.25/I.5/I.6/I.7/I.8/I.10/I.12/I.26) — deviation contract honored.
- FIXED: `P.9` misattribution on the measurement-first sentence — upstream
  P.9 is "Don't waste time or space"; re-anchored to `Per.6` ("Don't make
  claims about performance without measurements") + grammar repair.
- FIXED: duplicated rule "no parallel view/non-view overloads" — normative
  text removed here; home remains Memory and Ownership Pass-by notes
  (checklist clause kept as review routing).
- FIXED: `[[nodiscard]]` example now contrasts un-annotated vs annotated
  declarations (was a single self-referencing pair); fence restored after an
  edit mishap.
- FIXED: `F.4` parenthetical moved onto its constexpr-function clause.
- Verified correct: guaranteed elision / NRVO claims, return-move-local,
  F.42-F.49 return family, lambda capture matrix incl. F.54 `[=]` trap,
  explicit-single-arg (C.46), const-documentation quartet (P.10/Con.1-4),
  I-series interface rules and options-struct adaptation of I.23.

## performance.md verdicts (2026-08-25)

- Citation audit against upstream bodies: Per.1/2/3/5/6/7/10/11/12/14/15/
  16/17/18/19/30 accurate; ES.56 verified verbatim ("Write std::move() only
  when you need to explicitly move an object to another scope").
- FIXED: `Per.4` was cited for benchmark persistence — upstream Per.4 is
  "complicated code is not necessarily faster"; ID dropped, practice kept.
- FIXED: `Per.13` ("eliminate redundant indirections") misapplied to
  redundant temporaries; ID dropped.
- Verified correct: allocation-count framing, const-source move fallback,
  string_view free slicing, constexpr-vs-lazy-static tradeoff, Particle
  layout arithmetic (72→56 bytes checked by hand), AoS-to-SoA gate.

## concurrency.md verdicts (2026-08-25)

- Citation audit: 33 anchors accurate (CP.1/2/3/4/8/20-26/31/32/41-44/
  50-53/60/61/100-102/110/111/200/201, Con.1-5); CP.24 "thread as global
  container" quoted exactly; CP.201 deviation text matches upstream's own
  "???" placeholder honestly.
- FIXED: `CP.9` misattributed twice — upstream is "use tools to validate
  concurrent code", not message-passing preference; IDs dropped at the
  design-ladder item and the task-flow section (CP.31 kept where it fits).
- FIXED: `CP.40` misattributed — upstream is "minimize context switching",
  unrelated to the refactor-away-sharing aphorism; ID dropped.
- Verified correct: lock_guard CTAD on C++17, unnamed-guard temporary trap,
  async-future destructor blocking (CP.61 body), magic statics vs DCL ban,
  coroutine capture/suspension/parameter trio, TSan gate prose.

## expressions-and-flow.md verdicts (2026-08-25)

- Citation audit: ~55 ES-family anchors checked against upstream titles;
  52 accurate (incl. ES.56 move-scope rule reused correctly from
  performance.md's perspective). Three misattributions FIXED:
  ES.28 (upstream: lambdas for complex initialization) was cited for
  predicate extraction; ES.70 (switch over if) for "delete cleverness";
  ES.74 (loop-variable in for-initializer) for smallest-scope where ES.5
  is the anchor.
- FIXED: Window constructor example contradicted its own comment (the
  initializer read Size parameters, not members); replaced with a genuine
  declaration-order hazard (area_ declared first, initialized first,
  reading width_/height_).
- Verified correct: narrowing-brace discipline, T{e} construction,
  unsigned-wrap loop hazard, one-pass expression rules, macro family bans,
  unnamed-guard silent race, range-for temporary binding.
