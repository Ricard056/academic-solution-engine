# Extended JSON Output Specification — v3.2

> **This file is the canonical reference for all output schemas.**
> The extended JSON maintains input compatibility and can be reused as input.
> **v3.2 changes**: `results.component` is written by the Component Aggregation
> stage, not the solver and not the adapter (P1); `component_operation` honored
> only as absent/`"sum"`, anything else is a group ERROR (P2). v3.1 baseline:
> Extended JSON is PURE DATA — the solver stores only raw floats and LaTeX strings;
> formatted decimals (`decimal_string`, `total_decimal_string`,
> `operation_decimal_string`) and `units` are produced by the Render Adapter (see
> 85_render_adapter_and_jinja2_spec_v3_2.md).
> **Phase 1.1 amendment**: symbolic-only success contract — `numeric_value` may
> be `null` (see field description and Symbolic Result below).
> **Phase 2A amendment**: adds the gradient results schema — top-level
> `numeric_value: null` for every gradient success plus a `results.gradient`
> sub-object (the authoritative rendering source). See "Results Structure —
> Gradient Solver" below and `91_phase2a_gradient_scope_v3_2.md`. The integral
> results schema is unchanged.

---

## Extended JSON Structure (After Processing)

### Added by Algorithm
```json
{
  "schema_version": "1.0",
  "kind": "extended",

  "metadata": {
    "institution": "itson",
    "course_code": "c3",
    "course": "Calculus 3",
    "assignment": {
      "type": "hw",
      "number": 18
    },
    "file_naming_mode": "production",

    "processed": {
      "timestamp": "2025-06-15T10:30:45Z",
      "filename": "itson_c3_hw_18_extended.json",
      "filename_base": "itson_c3_hw_18",
      "naming_mode": "production",
      "algorithm_version": "3.2"
    },
    "processing_summary": {
      "total_exercises": 5,
      "successful": 5,
      "errors": 0,
      "processing_time_ms": 312
    }
  },

  "display_default": { },
  "display_integral": { },

  "exercises": [
    {
      "id": 1,
      "type": "integral",
      "function": "x^2 + y^2",

      "quantity": "A",
      "coordinate_system": "cartesian",

      "results": {
        "problem_latex": "\\int_{0}^{1} \\int_{0}^{1} x^2 + y^2 \\, dy \\, dx",
        "solution_latex": "\\frac{2}{3}",
        "numeric_value": 0.6666666667
      }
    }
  ]
}
```

> **Note on `processing_summary`**: Phase 1 tracks `total_exercises`, `successful`,
> `errors`, and `processing_time_ms`. There is no `warnings` channel in Phase 1
> (warnings are not surfaced to the render model).

---

## Results Structure — Integral Solver

### Standard Exercise Result
```json
"results": {
  "problem_latex": "\\int_{0}^{1} \\int_{0}^{1} f(x,y) \\, dy \\, dx",
  "solution_latex": "\\frac{2}{3}",
  "numeric_value": 0.6666666667
}
```

**Field descriptions**:
- `problem_latex`: LaTeX string showing the integral setup. Produced by the solver via `sympy.latex()`.
- `solution_latex`: LaTeX string of the exact symbolic result. Produced by the solver.
- `numeric_value`: Raw, unrounded float — or `null` when the exact result
  contains free symbolic parameters and therefore has no finite numeric value.
  `null` is a symbolic-only SUCCESS, not an error: `solution_latex` is the
  result. **The solver never rounds or formats.** `numeric_value` is never
  Infinity or NaN; divergent or indeterminate results remain errors.

**Not stored in Extended JSON** (these are render-model-only, produced by the
adapter from `numeric_value` + resolved display settings):
`decimal_string`, `units`. See 85_render_adapter_and_jinja2_spec_v3_2.md.

### Symbolic Result (success, no numeric value)

```json
"results": {
  "problem_latex": "\\int_{0}^{a} x \\, dx",
  "solution_latex": "\\frac{a^{2}}{2}",
  "numeric_value": null
}
```

A result with free symbolic parameters (here `a`) is a normal success. The
Render Adapter resolves its numeric display off (see
85_render_adapter_and_jinja2_spec_v3_2.md, Numeric-Availability Resolution);
no decimal string is ever produced for it.

### Component Result (when `id_component` exists)

Each component exercise includes both its individual result AND the combined
result. The `component` object is **identical** across all components of the same
exercise. It is written by the **Component Aggregation stage** (see
90_phase1_scope_v3_2.md, "Component Aggregation Stage"), which runs after the
per-exercise solver and before Extended JSON is finalized — not by the solver and
not by the Render Adapter. All fields are mathematical; none are formatted decimals.

```json
{
  "id": 3,
  "id_component": 1,
  "results": {
    "problem_latex": "\\int_{0}^{1} \\int_{0}^{x} x^2 \\, dy \\, dx",
    "solution_latex": "\\frac{1}{4}",
    "numeric_value": 0.25,

    "component": {
      "total_value": 0.833333,
      "total_latex": "\\frac{5}{6}",
      "operation": "sum",
      "operation_latex": "\\frac{1}{4} + \\frac{7}{12}"
    }
  }
}
```

```json
{
  "id": 3,
  "id_component": 2,
  "results": {
    "problem_latex": "\\int_{1}^{2} \\int_{x}^{2-x} x^2 \\, dy \\, dx",
    "solution_latex": "\\frac{7}{12}",
    "numeric_value": 0.583333,

    "component": {
      "total_value": 0.833333,
      "total_latex": "\\frac{5}{6}",
      "operation": "sum",
      "operation_latex": "\\frac{1}{4} + \\frac{7}{12}"
    }
  }
}
```

**Component field descriptions** (all produced by the Component Aggregation stage;
all mathematical):
- `total_value`: Combined raw float.
- `total_latex`: Combined symbolic result.
- `operation`: How components combine (Phase 1: always `"sum"`).
- `operation_latex`: Symbolic representation of the combination.

Decimal renderings of these (`total_decimal_string`, `operation_decimal_string`)
are produced by the adapter, not stored in Extended JSON. See 85.

Every member of a component group must have a numeric `numeric_value`. A
symbolic-only member (`numeric_value: null`) makes the whole `(id, id_letter)`
group a group-level ERROR (see 90_phase1_scope_v3_2.md); `total_value` is
always a float in Phase 1.

> **Note**: Phase 1 honors only `"sum"`. An absent `component_operation` defaults to
> `"sum"`; any explicit value other than `"sum"` makes the group an ERROR (see
> 65_id_system_v3_2.md). The field is reserved for future operations.

---

## Error Results Structure

If an exercise fails processing, results contain error information. The exercise
still appears in extended JSON — it is never omitted.

```json
{
  "id": 2,
  "type": "integral",
  "function": "invalid_expression",
  "results": {
    "status": "error",
    "problem_latex": "\\text{ERROR: Could not process exercise}",
    "solution_latex": "\\text{ERROR}",
    "error_message": "Cannot parse expression: invalid_expression"
  }
}
```

Group-level validation errors (component/output sequence gaps, duplicate/mixed IDs,
conflicting component quantity, invalid `component_operation`) are surfaced by the
**adapter** as a single `kind:"error"` render item for that group; they do not
require a per-exercise `results.status` field. Per-exercise solver/cleaner failures
use `results.status == "error"` as shown above. Both render identically.

Phase 1 error handling is minimal: a generic ERROR marker appears in the PDF. The
pipeline continues processing remaining exercises.

---

## Results Structure — Gradient Solver (Phase 2A)

> Scope/restrictions: `91_phase2a_gradient_scope_v3_2.md`. Like the integral
> solver, the gradient solver stores only raw floats and LaTeX strings — no
> formatted decimals, no units (adapter-owned, bible 85). Phase 2A is 2-variable,
> Cartesian, radians only.

A gradient result keeps the canonical `{problem_latex, solution_latex,
numeric_value}` skeleton **plus** a `results.gradient` sub-object holding every
output piece.

```json
"results": {
  "problem_latex": "\\nabla f(x, y)",
  "solution_latex": "\\left\\langle y^{3} e^{x y}, \\; y e^{x y} \\left(x y + 2\\right) \\right\\rangle",
  "numeric_value": null,

  "gradient": {
    "gradient_latex": "\\left\\langle y^{3} e^{x y}, \\; y e^{x y} \\left(x y + 2\\right) \\right\\rangle",
    "gradient_evaluated_latex": "\\left\\langle 8, \\; 4 \\right\\rangle",
    "gradient_evaluated_values": [8.0, 4.0],

    "magnitude_latex": "4 \\sqrt{5}",
    "magnitude_value": 8.94427190999916,

    "theta_max_latex": "\\operatorname{atan}{\\left(\\frac{1}{2} \\right)}",
    "theta_max_value": 0.4636476090008061,

    "unit_vector_latex": "\\left\\langle \\frac{\\sqrt{2}}{2}, \\; \\frac{\\sqrt{2}}{2} \\right\\rangle",
    "unit_vector_values": [0.7071067811865476, 0.7071067811865476],

    "directional_derivative_latex": "6 \\sqrt{2}",
    "directional_derivative_value": 8.485281374238571
  }
}
```

### Field rules
- **Top-level `numeric_value` is `null`** for every gradient SUCCESS. A gradient
  headline is vector-valued and has no single scalar; `null` here is a success,
  not an error. The gradient render path never uses this field.
- **`solution_latex` is a non-rendered mirror** of `gradient.gradient_latex`. It
  exists only for skeleton uniformity and JSON readability; **`results.gradient`
  is the authoritative source for all rendering** (bible 85).
- **`problem_latex`** is the gradient setup (e.g. `\nabla f(x, y)`).

### `results.gradient` pieces
| Key | Meaning | Value type |
|---|---|---|
| `gradient_latex` | symbolic `∇f(x, y)` | LaTeX string (always present) |
| `gradient_evaluated_latex` / `_values` | `∇f(P)` | LaTeX + component floats (or `null` if symbolic) |
| `magnitude_latex` / `magnitude_value` | `\|∇f(P)\|` | LaTeX + float (or `null` if symbolic) |
| `theta_max_latex` / `theta_max_value` | steepest-ascent angle, **radians** | LaTeX + float (or `null`) |
| `unit_vector_latex` / `_values` | `û` — **present only when a direction was supplied** | LaTeX + component floats (or `null`) |
| `directional_derivative_latex` / `_value` | `D_u f` — **present only when a direction was supplied** | LaTeX + float (or `null`) |

### Two kinds of absence (important)
- **Not applicable** — e.g. point-only exercise (no direction): the
  `unit_vector_*` and `directional_derivative_*` keys are **omitted** entirely.
- **Applicable but symbolic** — e.g. a symbolic point/parameter: the piece's
  `*_value`/`*_values` is **`null`**, and its `*_latex` is the exact symbolic
  form. This mirrors the Phase 1.1 numeric-availability contract, per piece.

Divergent/undefined results (any `oo`/`-oo`/`zoo`/`nan`, a domain error at the
point, or a zero-length direction) remain **errors** — never symbolic successes.

### Canonical vector delimiter
All vector LaTeX (symbolic and, in the render model, decimal) uses
`\left\langle … \right\rangle`. The solver emits it for `*_latex`; the adapter
emits it for decimal vectors (bible 85). No other delimiter is used.

### Purity
`results.gradient` contains only raw floats (nullable) and LaTeX strings. No
formatted decimal strings, no units — those are render-model-only (bible 85), so
re-runs with new `decimal_places` reformat correctly.

---

## Results Structure — Other Solvers

> **Deferred**: the **derivative** results structure is documented in
> 09_deferred_solvers_v3_2.md for future reference. (09's **gradient** section is
> superseded by the section above.)

---

## Processing Summary Interpretation

```json
"processing_summary": {
  "total_exercises": 20,
  "successful": 18,
  "errors": 2,
  "processing_time_ms": 1543
}
```

Exercises with errors still appear in the extended JSON with error results.

---

## File Naming in Extended JSON

The `processed.filename` and `processed.filename_base` reflect the naming mode:

```json
{
  "processed": {
    "filename": "itson_c3_hw_16_extended.json",
    "filename_base": "itson_c3_hw_16",
    "naming_mode": "production"
  }
}
```

```json
{
  "processed": {
    "filename": "itson_c3_hw_16_20260121_161159_extended.json",
    "filename_base": "itson_c3_hw_16_20260121_161159",
    "naming_mode": "testing"
  }
}
```

`filename_base` is used to generate matching TEX and PDF filenames.

---

## Reusability as Input

The extended JSON can be fed back as input for re-processing:

1. All original input fields are preserved.
2. Auto-inferred fields (`quantity`, `coordinate_system`) are now explicit.
3. The `results` section is ignored on re-input (solver regenerates).
4. Display settings remain intact.
5. Because Extended JSON carries no formatted decimals or units, re-running with
   different `decimal_places` or `default_units` produces correctly reformatted
   output — formatting is always recomputed by the adapter, never stale.
