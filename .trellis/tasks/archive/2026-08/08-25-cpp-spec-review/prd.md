# Point-by-point Review of C++ Spec Guidelines

## Goal

Review every guideline document this registry ships (`specs/cpp/cpp/*.md`, 12
guides + `index.md`) one document at a time, discussing each rule/claim with
the developer, then applying agreed fixes.

## Scope

- All files under `specs/cpp/cpp/**` plus their overview `specs/cpp/README.md`
- First deliverable (developer decision, 2026-08-25): remove all
  build-system/CI/dependency-management content — delete
  `build-and-toolchain.md`, strip CMake/preset/CI/vcpkg mentions repo-wide.
  Sanitizer/clang-tidy/warning names stay where they pair pitfalls with
  detectors; only build-system mechanics go.
- Review order after the sweep: memory-and-ownership → error-handling →
  quality-guidelines → testing → functions → classes → templates →
  concurrency → expressions → performance → core-guidelines-alignment →
  index.md.

## Review dimensions

1. **Technical correctness** — C++17 baseline facts; C++20/23 notes only where
   they change a recommendation; no wrong API/UB/tooling claims.
2. **Authoring-guide compliance** (`.trellis/spec/registry/guideline-authoring.md`)
   — document skeleton, Wrong/Right pairs for codifiable rules, Core Guidelines
   IDs cited as anchors not copies, fixed stance vocabulary (*Adopt* / *Adapt* /
   *Covered elsewhere*).
3. **Enforceability** — every pitfall paired with its detector (clang-tidy
   check, sanitizer, CI gate); unenforced rules flagged for enforcement-or-delete.
4. **Cross-doc consistency** — one home per rule; links resolve; section table
   in `core-guidelines-alignment.md` routes correctly.

## Process

Per document: read fully → extract its claims/rules as numbered points →
present verdicts with evidence → developer decides per finding → fixes applied
in-task (same session when small) → findings persisted to
`research/findings.md`.

## Acceptance criteria
- [ ] Build/CI/CMake/vcpkg content removed; no residue in `specs/cpp/**`,
      top-level README, or `index.json`; counts corrected to 12 docs.
- [ ] Agreed fixes applied; structural checks from
      `.trellis/spec/registry/index.md` (manifest paths + relative links) pass.
- [ ] File-set invariant intact: `specs/cpp/README.md`,
      `specs/cpp/cpp/index.md`, file tree, and `index.json` agree.
