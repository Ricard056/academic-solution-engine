# CLAUDE.md

Navigation map for `academic-solution-engine`, a long-term academic math solution
generator. Current v3.2 scope: ITSON Calculus 3 *solucionario* generation. This is a MAP,
**not** a spec. The authoritative rules live in `bible/*_v3_2.md`. When this file
and a bible file disagree, the bible wins. Read the relevant bible file before
implementing any stage. Do not paraphrase a rule from memory — open the file.

## What this is
This is a CLI tool: structured JSON calculus exercises → SymPy-solved results →
Jinja2/LaTeX → PDF solution manuals. Single user, Spanish (es-MX) output. Phase 1
solves integrals (frozen); Phase 1.1 added symbolic-only integral results; Phase
2A adds a 2-variable Cartesian gradient solver (spec in `bible/91`). See
`bible/99_project_overview_v3_2.md`.

## Pipeline (Phase 1)
Input JSON → Validate → Expression Cleaner → Integral Solver (per-exercise) →
Component Aggregation (cross-exercise) → Extended JSON → Render Adapter →
Jinja2/LaTeX → PDF

Phase 2A adds a gradient path by `type` dispatch: the Gradient Solver replaces the
Integral Solver per exercise, Component Aggregation is skipped (integral-only), and
the Render Adapter emits a `"gradient"` item rendered by a gradient template chosen
via a `render/latex.py` router. Documents are single-solver in 2A. (91)

## Where to look
| Need | Bible file |
|---|---|
| Scope: what is IN/OUT of Phase 1 | `90_phase1_scope_v3_2.md` |
| Scope: what is IN/OUT of Phase 2A (gradient) | `91_phase2a_gradient_scope_v3_2.md` |
| Vision & key design decisions | `99_project_overview_v3_2.md` |
| Input JSON structure & syntax | `80_json_input_spec_v3_2.md` |
| Extended JSON (output) schema | `75_json_output_spec_v3_2.md` |
| Display merge & auto-inference | `70_display_system_v3_2.md` |
| ID system (component/output grouping) | `65_id_system_v3_2.md` |
| Expression cleaner rules | `60_expression_cleaner_v3_2.md` |
| File-handling safety | `55_file_handling_v3_2.md` |
| Hardcoded display defaults | `50_config_defaults_global_v3_2.json` |
| Render Adapter + Jinja2 contract | `85_render_adapter_and_jinja2_spec_v3_2.md` |
| Golden acceptance values | `47_golden_expected_v3_2.md` |
| Symbolic-contract acceptance (Phase 1.1) | `48_test_data_symbolic_v3_2.json` / `49_golden_expected_symbolic_v3_2.md` |
| Gradient-contract acceptance (Phase 2A) | `51_test_data_gradient_v3_2.json` / `52_golden_expected_gradient_v3_2.md` |
| Test data (real T21 / edge cases) | `45_*.json` / `46_*.json` |
| Deferred — DO NOT BUILD | `08_*` ; `09_*_v3_2.md` (derivative only; 09 gradient superseded by Phase 2A) |

## Most dangerous rules (violating any breaks the contract)
1. **Input files are read-only.** Never move/rename/modify `inputs/`. Write only
   to `outputs/`; outputs are overwritable derivatives. (55)
2. **`coordinate_system` is passive.** Label/metadata only — never injects a
   Jacobian, never drives quantity or unit inference. The author writes any
   Jacobian into `function`. (70, 80)
3. **The solver never formats.** It emits LaTeX strings + a raw unrounded
   `numeric_value` float, or `null` for symbolic-only successes — no rounding,
   no units. Enforced by `tests/test_architecture.py` (solvers must not import
   `render`/formatting). (75, 90)
4. **Component aggregation is a post-solve stage.** It runs after the solver,
   before Extended JSON, summing components per `(id, id_letter)`. Solvers stay
   per-exercise; the adapter never computes totals. (90, 75)
5. **Extended JSON is pure data.** No formatted decimals, no units — so re-runs
   with new display settings reformat correctly. (75)
6. **Render Adapter owns display.** Merge, decimals, units, grouping, labels all
   live in `build_render_model(extended_json, defaults)`. Decimals MUST use
   `decimal.Decimal` + `ROUND_HALF_UP`; never `round()` or `f"{v:.nf}"`. (85, 70)
7. **Jinja2 = StrictUndefined, zero logic.** Templates only render already-resolved
   fields — no math, merge, group, sort, infer, or format. Closed render
   contract: every declared field must be populated by the adapter. (85)
8. **Solvers: integrals (Phase 1) + 2-var Cartesian gradient (Phase 2A).** One
   generic recursive integrator handles 1D/2D/3D — do NOT add a separate
   single-integral solver. The gradient solver is spec'd in Phase 2A; build it per
   `91` without modifying the integral solver or the integral template
   (99 #4/#5) — gradient gets its own template + a `render/latex.py` router. (90, 91)
9. **Do not implement deferred features.** No `show_steps`/`show_all`/
   interpretations, no `component_operation` other than `"sum"`, no derivative
   solver, no 3D/polar gradients, no degree input/display, no `angle_unit` or
   `variables` field, no mixed-solver documents. (08, 09, 91)

## Acceptance
A correct first run matches `47_golden_expected_v3_2.md` for Ex 1, 7, 5, 6, 9 of
`46` (Ex 9 `function:"2x"` is an INTENDED error — implicit multiplication is
rejected) and passes the ROUND_HALF_UP rounding guard. (47, 90)
Phase 1.1 (symbolic-only contract): once implemented, `49_*.md` over `48_*.json`
must also pass, with 46/47 remaining frozen. (48, 49)
Phase 2A (gradient contract): once implemented, `52_*.md` over `51_*.json` must
also pass, with 46/47 and 48/49 remaining frozen. (51, 52, 91)

## Project layout
- `src/solucionario/` — pipeline stages (`validation`, `cleaner`, `display`,
  `ids`, `solvers/`, `aggregation`, `extended_json`, `render/`, `fileio`).
- `templates/` — `base.tex.j2`, `solucionario_integrales.tex.j2` (loader root; no subdir).
  Phase 2A adds `solucionario_gradientes.tex.j2` (created in the gradient
  implementation milestone; `solvers/gradient.py` likewise). (91)
- `config/display_defaults/default.json` — runtime copy of `bible/50`, kept
  identical by `tests/test_config_matches_bible.py`.
- `inputs/` (read-only, gitignored) · `outputs/` (generated, gitignored) · `tests/`.
- `_local/` — private scratch (inputs/outputs/notes); NEVER committed.

## Running
`src/` layout: run `pip install -e .` once before `python -m solucionario ...`,
or imports will fail.