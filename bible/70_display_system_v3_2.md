# Display System Specification — v3.2

> **This file is the single source of truth for display behavior.**
> It covers: hierarchy, merge strategy, auto-inference, and all display field definitions.
> For actual default values, see 50_config_defaults_global_v3_2.json.
> **v3.2 changes**: `coordinate_system` no longer drives quantity/unit inference,
> with explicit-quantity-for-Jacobian note (P5); `quantity_label`/`units_override`
> flagged as part of the Phase 1 contract (P6); `file_naming_mode` clarified as a
> processing default whose source of truth is metadata, not merged into render
> config (P10). v3.1 baseline: `decimal_places`/`default_units` consumed by the
> adapter; `show_interpretations`, `show_id_component_process`,
> `show_id_component_accumulative` removed from Phase 1; component fields wired.
> **Phase 1.1 amendment**: nothing-to-show clarification for symbolic-only
> results (see Implementation Notes).

---

## Three-Level Display Hierarchy

display_default (base) → display_[solver] (solver-specific) → display_override (exercise-specific)

**Priority Rule**: Higher levels COMPLETELY override lower levels for any field
they specify. All display fields at ALL levels are OPTIONAL.

### Level 1: display_default (Base Configuration)
Global defaults for the entire assignment. Specified in the input JSON at the top level.

### Level 2: display_[solver] (Solver-Specific)
Override defaults for a specific solver type. For Phase 1, this is
`display_integral`. Specified in the input JSON at the top level.

### Level 3: display_override (Exercise-Specific)
Final override for individual exercises. Specified inside the exercise object.

---

## Merge Strategy

### Hardcoded Template System

The project includes hardcoded display defaults in
`config/display_defaults/default.json` (see 50_config_defaults_global_v3_2.json
for the actual values). This template provides fallback values for ALL display
settings.

**Merge behavior**:
```python
# Step 1: Start with hardcoded template
final = load("config/display_defaults/default.json")

# Step 2: Merge input JSON display_default (if present)
if 'display_default' in input_json:
    final.update(input_json['display_default'])

# Step 3: Merge solver-specific (if present)
solver_key = f'display_{exercise_type}'  # e.g., "display_integral"
if solver_key in input_json:
    final.update(input_json[solver_key])

# Step 4: Merge exercise-specific (if present)
if 'display_override' in exercise:
    final.update(exercise['display_override'])
```

> `file_naming_mode` is a processing default, not a display field. Its source of
> truth is `metadata.file_naming_mode` (default `"production"`); the value in 50 is
> the fallback only and is NOT merged into the per-exercise render config.

**What this means**: You only specify fields you want to change. All unspecified
fields inherit from the previous level. This merge is performed by the Render
Adapter, not by the solver or the template.

### Resolution Example

```json
// Given:
// Hardcoded template: { "show_input": true, "decimal_places": 4, "show_symbolic": true }
// Input JSON:
// "display_default": { "show_input": false, "decimal_places": 6 }
// "display_integral": { "decimal_places": 8 }
// Exercise:
// { "display_override": { "show_input": true } }

// Result for this integral exercise:
{
  "show_input": true,       // display_override wins
  "decimal_places": 8,      // display_integral wins
  "show_symbolic": true     // hardcoded template (nothing overrode it)
}
```

---

## Display Fields — Complete Reference

> **Note:** `decimal_places` and `default_units` are *consumed by the adapter* to
> produce `decimal_string` and `units` in the render model. The solver and
> Extended JSON store only raw `numeric_value` and symbolic LaTeX. See
> 75_json_output_spec_v3_2.md and 85_render_adapter_and_jinja2_spec_v3_2.md.

### Global Fields (apply to any exercise, any solver)

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `show_input` | bool | true | Show the problem setup (problem_latex). Phase 1: standard items only |
| `show_symbolic` | bool | true | Show exact symbolic answer (e.g., π/2) |
| `show_numeric` | bool | true | Show decimal answer (e.g., 1.5708) |
| `show_quantity` | bool | true | Show quantity label prefix on exercise result (e.g., "A =", "V =", "R =", "M =") |
| `decimal_places` | int | 4 | Number of decimal places (consumed by adapter) |
| `default_units` | string | "u" | Default unit string used by adapter unit derivation |
| `language` | string | "es-MX" | Output language for PDF text |

> **`language` is reserved and inert in Phase 1.** Output is es-MX through
> hardcoded template strings; `language` is not surfaced in the render model.

> **Clarification on `show_quantity`**: This controls whether the quantity label
> (A, V, R, or explicit custom label) appears as a prefix on the exercise result
> line. Example: when true, result shows "A = 2/3" or "R = 2/3"; when false,
> result shows just "2/3".

### Component Display Fields (only apply when `id_component` exists)

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `show_component_quantity` | bool | true | Show quantity label (A, V, R, custom) on each individual component line |
| `show_component_symbolic` | bool | true | In the Total line, show the symbolic combination `operation_latex` (e.g., "¼ + 7/12") before the combined symbolic result |
| `show_component_operation` | bool | true | In the Total line, show the decimal combination `operation_decimal_string` (e.g., "0.25 + 0.583") |
| `show_component_total` | bool | true | Show the Total line at all |

> **Clarification on `show_component_quantity`**: same concept as `show_quantity`
> but specifically for individual component lines. When true, each component line
> shows "V = 1/4"; when false, just "1/4".

> **Component-line symbolic policy**: Per-component lines ALWAYS show their
> `solution_latex`; the global `show_symbolic` flag does not gate them. The
> combined `total_latex` always renders when `show_component_total` is true and is
> not gated by `show_symbolic`. `show_component_symbolic` and
> `show_component_operation` control only the Total line's combination display.
> See 85.

### Exercise-Level Override-Only Fields (Phase 1 contract)

These live only inside `display_override`. They are display overrides, not solver
fields, and are never produced by the solver. See also 90_phase1_scope_v3_2.md.

| Field | Type | Description |
|-------|------|-------------|
| `quantity_label` | string | Overrides the resolved quantity label for this exercise/group |
| `units_override` | string | Overrides adapter unit derivation; used verbatim (template wraps it in `\mathrm{...}`) |

### Solver-Specific Fields (Phase 1: none exclusive to integrals)

The integral solver uses only global and component fields. Solver-specific fields
are used by other solvers (see 09_deferred_solvers_v3_2.md).

Note: `display_integral` can still be used in input JSON to override any global
field specifically for integral exercises. It just doesn't introduce new fields
unique to integrals.

---

## Auto-Inference Rules

These fields are **OPTIONAL** in input JSON. If missing, the solver infers them
from the exercise structure.

### quantity (Integral Solver)

Explicit `quantity` always wins over auto-inference.

If `quantity` is missing, infer it using this rule:

| Condition | Inferred Value | Meaning |
|-----------|---------------|---------|
| 2 integrals and cleaned `function == "1"` | `"A"` | Area |
| 3 integrals and cleaned `function == "1"` | `"V"` | Volume |
| Anything else | `"R"` | Generic result |

**Valid explicit values**: any short display label string. Recommended labels:
`"A"` (area), `"V"` (volume), `"R"` (generic result), `"M"` (mass), `"Q"` or
`"C"` (charge/context-dependent), `"T"` only if the author intentionally wants
Total/Other.

Use explicit `quantity` when the default inference is wrong. Example: a triple
integral with density should usually use `"M"`, not auto-inferred `"V"`.

### coordinate_system (Integral Solver)

| Variables Present | Inferred System |
|-------------------|----------------|
| x, y (or x, y, z) | `"cartesian"` |
| r, theta | `"polar"` |
| r, theta, z | `"cylindrical"` |
| rho, phi, theta | `"spherical"` |

Use explicit value when variable names don't match conventions or you need to
force a specific system.

**Phase 1 note:** This field is computationally passive — it is a label for
metadata and display only. It does NOT modify the integrand, does NOT inject a
Jacobian, and does NOT drive quantity or unit inference (quantity depends only on
integral count and cleaned `function == "1"`; units depend only on the resolved
`quantity_label` and `default_units`/`units_override`). If the integral requires a
Jacobian, the author must write it explicitly in `function`. If a Jacobian is
written into `function` (so `function != "1"`), the `function == "1"` area/volume
heuristic cannot fire; set `quantity` explicitly (`"A"` or `"V"`) when area/volume
labels and units are wanted. See 80_json_input_spec_v3_2.md.

### Examples
```json
{
  "id": 1,
  "type": "integral",
  "function": "x^2 + y^2",
  "integrals": [
    {"var": "y", "lower": "0", "upper": "1"},
    {"var": "x", "lower": "0", "upper": "1"}
  ]
}
```

```json
{
  "id": 2,
  "type": "integral",
  "quantity": "T",
  "function": "x^2",
  "integrals": [
    {"var": "z", "lower": "0", "upper": "1"},
    {"var": "y", "lower": "0", "upper": "1"},
    {"var": "x", "lower": "0", "upper": "1"}
  ]
}
```

**Philosophy**: Type less for common cases, override when needed.

---

## Real-World Display Scenarios

### Scenario: Testing (show everything)
```json
"display_default": {
  "show_input": true,
  "show_symbolic": true,
  "show_numeric": true,
  "decimal_places": 8
}
```

### Scenario: Student Assignment
```json
"display_default": {
  "show_input": true,
  "show_symbolic": true,
  "show_numeric": true,
  "decimal_places": 4
},
"display_integral": {
  "show_input": false
}
```

### Scenario: Coordinator — Minimal
```json
"display_default": {
  "show_input": false,
  "show_symbolic": false,
  "show_numeric": true,
  "decimal_places": 2
}
```

### Scenario: Component Display
```json
"display_default": {
  "show_component_quantity": true,
  "show_component_symbolic": true,
  "show_component_operation": false,
  "show_component_total": true
}
```

---

## Display Override — Advanced Options

### Exercise-Level Override
```json
{
  "id": 5,
  "id_letter": "c",
  "type": "integral",
  "display_override": {
    "show_input": true,
    "decimal_places": 2
  }
}
```

### Custom Labels (Advanced)
```json
{
  "id": 5,
  "id_letter": "d",
  "type": "integral",
  "display_override": {
    "quantity_label": "M",
    "units_override": "kg"
  }
}
```

These two fields are part of the Phase 1 contract (see 90_phase1_scope_v3_2.md,
"Exercise-level override-only fields"). They live only in `display_override`.

- `quantity_label`: overrides the resolved quantity label for this exercise.
- `units_override`: overrides adapter unit derivation; used verbatim.

---

## Implementation Notes

- All display fields are OPTIONAL at every level
- Unspecified fields inherit from the level below
- The system gracefully handles missing display objects entirely
- Default fallbacks exist in the hardcoded template (50_config_defaults_global_v3_2.json)
- Display merging is performed by the Render Adapter; the resolved values are
  baked into the render model so the template never merges anything
- Consider warning if `show_symbolic: false` AND `show_numeric: false` (nothing
  to show). Phase 1 does not surface this as a structured warning (see
  90_phase1_scope_v3_2.md, deferred `warnings` channel). A symbolic-only result
  (`numeric_value: null`, see 75) with `show_symbolic: false` reaches this same
  nothing-to-show outcome — its `show_numeric` resolves to false (85,
  Numeric-Availability Resolution) — and renders an empty result body; warnings
  remain deferred
