# Phase 2B-M Scope Lock — Multi-Solver Documents — v3.2

> **Purpose**: Defines exactly what is IN and OUT of **Phase 2B-M** (multi-solver
> documents / mixed PDF). Parallel to `90_phase1_scope_v3_2.md` (Phase 1, frozen)
> and `91_phase2a_gradient_scope_v3_2.md` (Phase 2A). If something is not listed
> under "IN SCOPE", it does not exist for Phase 2B-M.
> **Relationship to earlier phases**: Phase 2B-M is purely additive to solver
> mathematics. It changes no solver, no result schema, and no frozen acceptance.
> Bible 90 remains the frozen Phase 1 Integral scope and validation authority.
> Bible 91 remains the Phase 2A authority except for exactly three clauses
> (single-solver rendering restriction, document-level mixed-type hard stop,
> mixed-document deferral), each annotated as superseded in 91 itself.

---

## Objective

One assignment document may contain exercises of different **recognized solver
types** (Phase 2B-M: `integral` and `gradient`), freely interleaved, rendered
into one PDF in the existing canonical structural order.

---

## IN SCOPE — Phase 2B-M production changes

- **Remove the document-tier mixed-type hard stop** (the Phase 2A single-solver
  restriction in document validation).
- **Group-tier D2 and supported-mode validation** (authoritative rules in 65).
- **Neutral document shell + five closed item fragments** replacing the two
  full-document templates as the single universal production rendering path
  (contract in 85).
- **Renderer preflight, closed `item.kind → fragment` registry, and exact
  adapter-emittable/registry coverage** with a mandatory architecture test (85).
- **Adapter**: stamps the neutral shell identifier (internal metadata) and
  registers item builders through a closed, bounded per-type mapping.
- **Internal-render-failure taxonomy** with clean nonzero CLI handling (85 and
  "Error trust boundaries" below).
- **Group-level display resolution**: the existing implicit Integral default is
  made explicit at the call site (behavior unchanged; component/output groups
  remain Integral-only).
- **Obsolete single-solver test locks** replaced or inverted with traceability.
- **New acceptance artifacts**: `53_test_data_mixed_v3_2.json` and
  `54_golden_expected_mixed_v3_2.md`.

---

## OUT OF SCOPE — exclusions (do not build)

- Pipeline dictionary-dispatch refactor (optional cleanup; deferred).
- Renaming `document.template` (name retained).
- `display_gradient` canonicalization in Extended JSON assembly (deferred).
- Document variants (exam/class-work shells).
- Any plugin framework.
- Derivative or any other new solver; graph support.
- Changes to existing solver mathematics.
- Non-Integral aggregation; new `component_operation` values.
- New result schemas; new display features; per-solver config files.
- General filesystem atomic-write infrastructure (temp-file + rename).

---

## D1 — Canonical interleaving

Solver types interleave freely in the **existing canonical structural order**:

- `(id, id_letter)` groups ordered by the defensive numeric `id` rank, then
  `id_letter`; members ordered by `id_component` / `id_output` (65).
- **Stable authored relative order** is preserved for identical complete
  structural keys.
- The Render Adapter emits items in that group order; a collapsed group error
  occupies exactly one output position for its group.
- Solver identity never appears in any grouping or sorting key.
- No solver partitioning occurs before or after canonical ordering — the PDF is
  never reorganized into solver sections.

Operational detail and guarantees: 65 ("Multi-Solver Groups").

---

## D2 — One recognized solver identity per group (summary)

- A **raw authored `type` token** is any JSON value in `type`. A **recognized
  solver identity** is a string belonging to the closed active solver set
  (Phase 2B-M: `integral`, `gradient`).
- One `(id, id_letter)` group may not contain two different recognized solver
  identities — in any structural mode.
- Missing, `null`, non-string, and unknown-string tokens have **no** recognized
  identity; they remain authored exercise-validation failures and never form a
  document-level stop.
- Evaluation precedence (six steps): exercise validation → structural-mode
  coherence → D2 uniformity → supported-mode capability → mode-specific
  structural/solved-member rules → adapter cardinality.

**The authoritative definitions, precedence, and the complete cardinality
matrix live in `65_id_system_v3_2.md`.** This file intentionally carries no
copy.

---

## Supported modes (milestone summary)

Phase 2B-M solvers and structural modes: **Integral — standard, component,
output. Gradient — standard only.** Component Aggregation remains
Integral-only; component mathematics stays outside the adapter and Jinja.

**The single authoritative supported-mode table is in `65_id_system_v3_2.md`.**
A future solver must add its row there explicitly.

---

## Rendering architecture (Alternative 3)

- One **neutral document shell** (extends `base.tex.j2`) with **no `item.kind`
  branching**.
- **Five closed presentation fragments**: `standard`, `component_group`,
  `output_group`, `gradient`, `error`.
- A **Python-controlled closed `item.kind → fragment` registry** with exact
  adapter-emittable/registry coverage, complete whole-list preflight, one Jinja
  Environment per render invocation, **mandatory StrictUndefined** (production
  included), and `autoescape=False`.
- **Render fully in memory before any filesystem write**; deterministic
  internal failures with per-item attribution.
- **One universal production rendering path.** The evaluated fallback
  (a shell with static includes and Python preflight — "Alternative 2") is
  documented history only and is not implemented in parallel.

The complete renderer contract is in 85 ("Document Shell and Item Fragments").

---

## Compatibility oracle (normative)

For existing pure Integral, pure symbolic-Integral, and pure Gradient
documents, Phase 2B-M preserves:

- Extended JSON content and schema; result schemas;
- render-item fields; item and member order; labels; quantities; units;
- numeric and symbolic output; generic academic ERROR markers and cardinality;
- visible TeX content and logical order; successful TeX and PDF generation.

**Shell, fragment, and registry metadata is never persisted in Extended JSON.
The only narrowly approved assertion change for existing pure-document
expectations is the internal render-model `document.template` value — an
implementation-test assertion, never a golden Extended JSON field.**

Reviewed TeX differences consisting exclusively of whitespace/line breaks are
permitted. Whole-file TeX byte identity is a **temporary migration diagnostic
only**, not a product contract. PDF binary identity is not required.

---

## Extended JSON non-persistence

Extended JSON never contains shell metadata, fragment metadata, registry
metadata, routing metadata, or `rendered_items` — in any spelling. Bible 75 is
unchanged; it already excludes render-model fields from the canonical schema.

---

## Legacy-template lifecycle

`solucionario_integrales.tex.j2` and `solucionario_gradientes.tex.j2` remain
**temporary migration oracles only** during the implementation branch:

- after production cutover, invoking them is test/comparison-only;
- they are never alternate production paths;
- authored input can never select them (or anything else) as a rendering path;
- they are **deleted before Phase 2B-M closeout**, only after the deletion gate
  below passes.

---

## Error trust boundaries (three categories)

1. **Authored academic failures** — data outcomes: exercise-level error
   results, group-level structural collapse, generic Spanish ERROR render
   items. Processing continues; authored failures alone yield CLI exit 0.
2. **Internal rendering failures** — system defects (missing/malformed/unknown
   internal `item.kind`, adapter/registry drift, stale registry entry, missing
   fragment, invalid shell metadata, StrictUndefined contract failure; full
   taxonomy in 85). They are deterministic; they are **never** converted to
   academic ERROR items; they abort **before any output writing**; they create
   or overwrite **no** JSON/TeX/PDF output (pre-existing outputs remain
   untouched); the CLI reports a clean failure and exits nonzero.
3. **PDF-compilation failure** — occurs after JSON/TeX generation; returns
   nonzero; retains the generated derivatives per bible 55's existing policy.

---

## All-error authored documents

A valid document envelope whose authored exercises all fail:

- is **not** a document-level hard stop;
- keeps every authored exercise represented in Extended JSON;
- uses member-based `processing_summary` semantics: `total_exercises` counts
  authored exercise members; `successful = 0` in the all-error case; `errors`
  counts authored failed members, never render cards. A collapsed group whose
  members individually solved counts those members as successful — render
  cardinality and summary semantics are separate;
- renders error items under the 65 standard/group cardinality rules, in
  canonical structural order;
- generates TeX when internal rendering succeeds; attempts PDF compilation
  when TeX generation succeeds;
- returns CLI exit 0 when only authored academic errors occurred.

---

## Required acceptance

1. `54_golden_expected_mixed_v3_2.md` over `53_test_data_mixed_v3_2.json`
   passes (mixed golden).
2. The complete D2 cardinality matrix and supported-mode rules of 65 are
   covered by focused validation tests (including unhashable-token
   equality-scan safety).
3. Renderer tests cover preflight, registry closure, missing/malformed/unknown
   kinds, stale entries, missing fragments, invalid shell metadata,
   StrictUndefined (fragment and shell), fixed separators, no document context
   in fragments, and per-item failure attribution.
4. A mandatory architecture test proves exact adapter-emittable/registry
   coverage.
5. All-error CLI acceptance: exit 0, artifacts written, member-based summary.
6. Internal-render-failure CLI acceptance: nonzero exit, **no output writer
   invocation**, and **pre-seeded output files byte-unchanged**.
7. The frozen suites remain green unchanged: 47 over 46, 49 over 48, 52
   over 51.

## Pure-document universal-path TeX/PDF gate

Before legacy-template deletion (and recorded as closeout evidence),
representative **pure Integral**, **pure symbolic-Integral**, and **pure
Gradient** documents (46-, 48-, and 51-class) must each, through the universal
production path after cutover:

- render via the neutral shell;
- produce TeX successfully;
- compile to PDF successfully;
- pass visible-content and logical-order verification.

Mixed-document compilation is required separately and is **not** a substitute
for these three pure-document checks. Whole-file TeX byte identity and PDF
binary identity are not required.

## Mixed-document golden requirement

Bible 53/54 define the mixed acceptance contract: seven structural positions,
nine authored members, binding item-kind order
`standard, gradient, component_group, gradient, output_group, standard, error`,
member summary `9 / 8 / 1`, and canonical interleaving that cannot be produced
by any solver partitioning.

## Legacy-template deletion gate (all four, in order)

1. Corpus render equivalence over 45/46/48/51 through both paths, reviewed;
   only whitespace-class deltas accepted.
2. All permanent pure-document regression suites green on the universal path.
3. The mixed golden (54 over 53) green.
4. The pure-document universal-path TeX/PDF gate above passed and recorded.

Only then: delete both legacy templates, remove legacy names from the renderer
allowlist, and retire the temporary migration tests — together.

---

## Implementation sequencing constraints (specification level)

- Rendering substrate (shell, fragments, registry, preflight, migration
  comparisons) lands before the production cutover.
- D2 and supported-mode validation land **before** the document hard stop is
  removed.
- The hard-stop removal lands **in the same commit** as the inversion of its
  obsolete test locks.
- Mixed, all-error, and internal-failure acceptance land before the deletion
  gate; the deletion items land together.
- Prohibited intermediate states: an adapter stamping a shell the renderer
  rejects; the hard stop removed before group safety exists; legacy templates
  deleted before the gate; migration tests surviving the templates they
  compare.

---

## Completion and closeout criteria

- All gates above passed; full suite green; frozen acceptance unchanged.
- Implementation handoff + cumulative patch under `_local/` (never committed).
- External implementation audit returns an acceptable final decision.
- User-performed `--no-ff` merge; recorded post-merge suite results and the
  recorded pure-document compile evidence.
