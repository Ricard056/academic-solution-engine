# Phase 1 Scope Lock — v3.2

> **Purpose**: Defines exactly what is IN and OUT of Phase 1.
> **Rule**: If something is not listed under "IN SCOPE", it does not exist for Phase 1.
> **v3.2 changes**: named Component Aggregation stage (P1); `component_operation`
> closed to absent/`"sum"` (P2); full structural validation matrix (P3); coordinate
> systems no longer claim to drive quantity/unit inference (P5); `quantity_label`
> and `units_override` added to the final display-field contract (P6). v3.1
> baseline: formatting ownership, coordinate passivity, display-field pruning,
> tiered validation, golden reference, type vocabulary.
> **Phase 1.1 amendment**: symbolic-only success contract — `numeric_value: null`
> (solver guard, aggregation refusal, group collapse; acceptance in 48/49).

---

## IN SCOPE — Phase 1

### Solver
- **Integral solver only**
- Primary target: double and triple integrals used in Calculus 3 assignments
- Implementation may support 1D, 2D, and 3D integrals through the same generic recursive integration function
- Do NOT create a separate single-integral solver
- Cartesian, polar, cylindrical, spherical coordinate systems are **labels only**
  in Phase 1. They are stored/inferred for metadata and display; they do **not**
  affect computation, quantity inference, or unit derivation. Quantity inference
  depends only on integral count and cleaned `function == "1"`; units depend only
  on the resolved `quantity_label` and `default_units`/`units_override`. The
  Jacobian, when needed, is supplied by the author inside `function`, and the
  solver integrates exactly what is written. **Because a Jacobian makes
  `function != "1"`, coordinate-transformed area/volume integrals must set
  `quantity` explicitly (`"A"`/`"V"`) to get area/volume labels and units;**
  otherwise they auto-infer `R` with bare `u`.
- Auto-inference of `quantity` and `coordinate_system`

**Symbolic-only successes (Phase 1.1).** An integral whose exact result contains
free symbolic parameters is a SUCCESS with `numeric_value: null`, not an error.
ALL of the following must hold:
1. integration succeeded (no exception);
2. the result has free symbols;
3. the result contains no `oo`, `-oo`, `zoo`, or `nan`;
4. the result is not (and does not contain) an unevaluated `Integral`;
5. `numeric_value` is `null`;
6. `solution_latex` is the exact symbolic result.
Results failing any of these remain errors. Intentional asymmetry: the numeric
path may still evaluate a symbol-free unevaluated `Integral` numerically; the
symbolic path never accepts one.

### Formatting Ownership (v3.1)
- Solver = LaTeX strings (`problem_latex`, `solution_latex`) + raw float
  (`numeric_value`) — or `null` for symbolic-only successes — + component math.
  No rounding, no units.
- Render Adapter = all formatted decimals (`decimal_string`,
  `total_decimal_string`, `operation_decimal_string`) and `units`.
- Template = render only; StrictUndefined in dev/test.
- Extended JSON carries NO formatted decimals and NO units.

### Quantity Auto-Inference
Explicit `quantity` always wins.

If `quantity` is missing:
- 2 integrals and cleaned `function == "1"` → `A`
- 3 integrals and cleaned `function == "1"` → `V`
- anything else → `R`

Recommended explicit labels:
- `A` = area
- `V` = volume
- `R` = generic result
- `M` = mass
- `Q` = charge/context-specific quantity
- `T` = only if the author intentionally wants Total/Other

### ID System (all fields)
- `id` (NUMBER, required)
- `id_letter` (string, optional)
- `id_component` (NUMBER, optional) — parts that combine via sum operation
- `id_output` (NUMBER, optional) — independent results displayed separately

`exercise_label` is render-only and is created by the render adapter. It is not
an input ID field.

### Display Settings (Phase 1 fields — final)

**Global fields** (apply to any exercise):
- `show_input` — Show the integral setup (`problem_latex`)
- `show_symbolic` — Show exact symbolic answer (e.g., π/2)
- `show_numeric` — Show decimal answer (e.g., 1.5708)
- `show_quantity` — Show quantity label prefix (e.g., `A =`, `V =`, `R =`, `M =`)
- `decimal_places` — Number of decimal places (consumed by the adapter)
- `default_units` — Default unit string (consumed by the adapter)
- `language` — Output language (`es-MX`)

**Component-specific fields** (only when `id_component` exists):
- `show_component_quantity` — Show quantity label on each component line
- `show_component_symbolic` — Show the symbolic combination (`operation_latex`) in the Total line
- `show_component_operation` — Show the decimal combination (`operation_decimal_string`) in the Total line
- `show_component_total` — Show the Total line at all

**Exercise-level override-only fields** (valid only inside `display_override`; not
solver fields, never produced by the solver):
- `quantity_label` — overrides the resolved quantity label for this exercise/group
- `units_override` — overrides adapter unit derivation; used verbatim (still wrapped
  by the template in `\mathrm{...}`)

**Removed from Phase 1** (now in 08_deferred_features_v3_2.md):
- `show_interpretations` (no `interpretation` field schema — deferred)
- `show_id_component_process` (depends on deferred `show_steps`)
- `show_id_component_accumulative` (duplicate of `show_component_total`)
- `show_steps`, `show_all`

### Display Hierarchy (3 levels)

hardcoded defaults → display_default → display_integral → display_override

Full merge chain with hardcoded defaults template. See
`70_display_system_v3_2.md`.

### Expression Cleaner
Safe transformations: `^` → `**`, `ln` → `log`, trig powers, inverse trig,
infinity. See `60_expression_cleaner_v3_2.md`.

Standalone `e` is NOT supported. Use `exp(1)` or `exp(x)`.

### File Handling
- Input files read-only
- Output generation (extended JSON, TEX, PDF)
- Production and testing naming modes
See `55_file_handling_v3_2.md`.

### Validation and Error Handling (Minimal, Three-Tier)

**Document-level (hard stop).** Abort before solving; produce no output; leave the
input untouched (see 55) if any of:
- a required top-level field is missing (`metadata.course`,
  `metadata.assignment.type`, `metadata.assignment.number`)
- `exercises` is absent or empty
- the input is not a valid JSON object
- any exercise is missing `id` (no stable label/sort key can be produced)

**Exercise-level (continue; render that one exercise as `kind:"error"`).** Triggers:
- `id` is present but not a NUMBER
- `type` is missing
- `type` is present but unknown/unsupported in Phase 1 (only `"integral"` exists)
- a required solver field is missing (`function` or `integrals`)
- `integrals` is present but not an array, or any bound object is missing `var`,
  `lower`, or `upper`
- the expression cleaner or solver cannot process an expression (see 60)

**Group-level (continue; render the WHOLE `(id, id_letter)` group as one
`kind:"error"`).** Triggers:
- an `id_component` or `id_output` sequence gap (e.g. `id_component` 1, 3)
- duplicate `id_component` or duplicate `id_output` within the group
- an exercise carries BOTH `id_component` and `id_output`
- the group mixes modes (standard + component, standard + output, or component +
  output) under the same `(id, id_letter)`
- members of a component group resolve to different `quantity_label` values
- `component_operation` is present with any value other than `"sum"`

If any member of a component or output group fails at the exercise level (cleaner
or solver error), the entire `(id, id_letter)` group renders as a single
`kind:"error"` item. Likewise, a component group containing a symbolic-only
member (`results.numeric_value: null`) renders as a single `kind:"error"` item —
the adapter MUST apply this collapse (component sums are numeric-only in
Phase 1).

Error items show a generic Spanish ERROR marker. No detailed classification, no
debug logging in Phase 1.

### Render Adapter and Templates
- Required bible file: `85_render_adapter_and_jinja2_spec_v3_2.md`
- Required render adapter function: `build_render_model(extended_json, defaults) -> render_model`
- Jinja2 must remain simple and must not perform solver/display/grouping/formatting logic
- Templates rendered with StrictUndefined in dev/test
- Required templates:
  - `templates/base.tex.j2`
  - `templates/solucionario_integrales.tex.j2`

### Test Data and Golden Reference
- `45_test_data_T21_v3_2.json`: 17 integral entries with `id_letter` and `display_override` examples
- `46_test_data_integral_edge_cases_v3_2.json`: supplementary Phase 1 tests for:
  - `id_component`
  - `id_output`
  - quantity override
  - display override
  - cleaner behavior
  - generic 1D integration through the same integral solver
- `47_golden_expected_v3_2.md`: expected render-model values for acceptance

---

## Golden Reference (Phase 1 Acceptance)

See `47_golden_expected_v3_2.md`. A correct first run must match the expected
render-model values for exercises 1, 7, 5, 6, and 9 of
`46_test_data_integral_edge_cases_v3_2.json`. Notably, exercise 9 (`function:"2x"`)
is an **intended ERROR** because implicit multiplication is a rejected
transformation (see 60); its ERROR status is a pass, not a bug.

---

## OUT OF SCOPE — Deferred

### Deferred Solvers
- Gradient solver (see `09_deferred_solvers_v3_2.md`)
- Derivative solver (see `09_deferred_solvers_v3_2.md`)
- Vector solver (future)

### Deferred Display Fields
- `show_interpretations` and the `interpretation` field schema
- `show_id_component_process`
- `show_id_component_accumulative`
- `show_steps`
- `show_all`
- `display_gradient`, `display_derivative` (all solver-specific fields)
- Per-solver default config files (e.g., `50_config_defaults_integral.json`)

### Deferred Features
- Performance optimization
- Complex Jinja2 templates
- Validation for edge cases beyond Phase 1 tests
- Debug logging system
- Frontend
- Web API
- `warnings` channel in processing summary / render model
- `component_operation` values other than `"sum"`

---

## Phase 1 Pipeline

```
Input JSON
→ Validate
→ Expression Cleaner
→ Integral Solver           (per-exercise, independent)
→ Component Aggregation     (cross-exercise; sum within each id+id_letter group)
→ Extended JSON
→ Render Adapter
→ Jinja2/LaTeX
→ PDF
```

### Component Aggregation Stage (post-solve, pre-Extended-JSON)

A dedicated aggregation stage runs after the solver and before Extended JSON is
finalized. It is NOT a solver and does not violate solver independence (99 #5):
solvers stay per-exercise; aggregation is a separate stage. It:

1. Groups solved exercises that carry `id_component` by `(id, id_letter)`.
2. Computes `total_value` (sum of component `numeric_value`), `total_latex`,
   `operation` (`"sum"`), and `operation_latex` from the sibling components.
3. Writes the IDENTICAL `results.component` object onto every member of the group.

The stage MUST refuse to aggregate a component group containing any member
whose `results.numeric_value` is `null` (symbolic-only success); the group
receives no `results.component`. Component sums are numeric-only in Phase 1.

The Render Adapter NEVER computes component mathematics or symbolic combinations.
It only groups already-computed results into `component_group` render items,
validates render-level group structure, formats decimals, and derives units.

Each solver step is independent. If the integral solver works for one valid integral
exercise, it should work for all valid integral exercises of the same structure.

---

## Phase 1 Success Definition

1. Process `45_test_data_T21_v3_2.json` → correct PDF with display settings respected
2. Process `46_test_data_integral_edge_cases_v3_2.json` → correct PDF showing components, outputs, overrides, and error handling
3. Render-model output matches `47_golden_expected_v3_2.md` for the named exercises
4. Process at least 3 more real assignments → PDFs match or exceed Iteration 2 quality
5. `id_component` exercises combine correctly in PDF
6. `id_output` exercises display independently in PDF
7. `display_override` works per exercise (including `decimal_places` overrides reaching the formatted output)
8. Errors produce generic ERROR marker and do not stop processing

---

## Coding Approach

- **Coder**: Claude Sonnet / Claude Code in separate chat
- **Bible files**: All Phase 1 v3.2 files sent as context
- **Instruction**: Follow bible_files strictly; do not invent deferred features
- **Language**: Python with SymPy, Jinja2, LaTeX
- **Environment**: VS Code with Git
