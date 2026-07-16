# JSON Input Structure Specification — v3.2

> **v3.2 changes**: validation checklist points to the full three-tier matrix in 90
> (P3); Jacobian-defeats-`function=="1"` note added to the cylindrical example (P5);
> references updated to _v3_2. v3.1 baseline: `coordinate_system` computationally
> passive (author supplies Jacobian); canonical `assignment.type` vocabulary;
> `show_interpretations`/`interpretation` removed from Phase 1.
> **Phase 2A amendment**: adds the `type: "gradient"` input contract (2-variable,
> Cartesian, radians only; string point/vector coordinates; four direction modes
> plus point-only). See "Gradient Solver — Exercise Examples" below and
> `91_phase2a_gradient_scope_v3_2.md`. The integral contract is unchanged.
> **Phase 2B-M amendment**: documents may now mix recognized solver types — the
> single-solver-document prohibition is superseded (annotated below). Adds the
> "Multi-Solver Documents (Phase 2B-M)" section and layered validation authority
> pointers. The integral and gradient field contracts are unchanged. See
> `92_phase2bm_multisolver_scope_v3_2.md`.

## Field Optionality Rules

**REQUIRED fields** (everything else is OPTIONAL):
- `metadata.course` (string)
- `metadata.assignment.type` (string)
- `metadata.assignment.number` (number)
- `exercises[].id` (NUMBER — not string)
- `exercises[].type` (string)

> **Core Rule**: Only `id` (NUMBER) and `type` are required per exercise. All
> other fields are optional and have sensible defaults or are auto-inferred.

---

## JSON Input Structure

### Minimal Valid JSON
```json
{
  "metadata": {
    "course": "Calculus 3",
    "assignment": {
      "type": "hw",
      "number": 1
    }
  },
  "exercises": [
    {
      "id": 1,
      "type": "integral",
      "function": "x^2 + y^2",
      "integrals": [
        {"var": "y", "lower": "0", "upper": "1"},
        {"var": "x", "lower": "0", "upper": "1"}
      ]
    }
  ]
}
```

### Complete JSON with All Features
```json
{
  "metadata": {
    "institution": "itson",
    "course_code": "c3",
    "course": "Calculus 3",
    "assignment": {
      "type": "hw",
      "number": 18,
      "year": 2025,
      "month": 6,
      "day": 15,
      "iteration": 7
    },
    "file_naming_mode": "production"
  },

  "display_default": {
    "show_input": false,
    "decimal_places": 6
  },

  "display_integral": {
    "show_input": false,
    "decimal_places": 6
  },

  "exercises": [
    // See exercise examples below
  ]
}
```

> **Display fields**: Only specify fields you want to override. All others inherit
> from defaults. See 70_display_system_v3_2.md for full merge behavior and
> auto-inference rules.

---

## Integral Solver — Exercise Examples

### Solver-Specific Required Fields
- `function` (string) — the integrand expression
- `integrals` (array) — integration bounds, ordered innermost to outermost

### Solver-Specific Optional Fields
- `quantity` — auto-inferred if missing (see 70_display_system_v3_2.md)
- `coordinate_system` — auto-inferred if missing (see 70_display_system_v3_2.md).
  **Phase 1 semantics: computationally passive.** It does NOT alter the integrand
  and does NOT inject a Jacobian. If the integral requires a Jacobian (e.g. `r`
  for polar/cylindrical, `rho^2 * sin(phi)` for spherical), the author must write
  it explicitly in `function`. Example: a cylindrical volume integral uses
  `"function": "r"`, not `"function": "1"`.

### Simple Integral (Auto-Inference)
```json
{
  "id": 1,
  "type": "integral",
  "function": "x^2 + y^2",
  "integrals": [
    {"var": "y", "lower": "0", "upper": "1"},
    {"var": "x", "lower": "0", "upper": "1"}
  ]
  // quantity auto-inferred as "R" because function is not exactly "1"
  // (it would be "A" only if function == "1" for a double integral)
  // coordinate_system auto-inferred as "cartesian" (x,y variables)
}
```

### Simple Integral (Explicit)
```json
{
  "id": 1,
  "type": "integral",
  "quantity": "A",
  "function": "x^2 + y^2",
  "integrals": [
    {"var": "y", "lower": "0", "upper": "1"},
    {"var": "x", "lower": "0", "upper": "1"}
  ]
}
```

### Integral with Components
```json
[
  {
    "id": 3,
    "id_letter": "a",
    "id_component": 1,
    "type": "integral",
    "quantity": "A",
    "function": "x^2",
    "integrals": [
      {"var": "y", "lower": "0", "upper": "x"},
      {"var": "x", "lower": "0", "upper": "1"}
    ]
  },
  {
    "id": 3,
    "id_letter": "a",
    "id_component": 2,
    "type": "integral",
    "quantity": "A",
    "function": "x^2",
    "integrals": [
      {"var": "y", "lower": "x", "upper": "2-x"},
      {"var": "x", "lower": "1", "upper": "2"}
    ]
  }
]
// Result: Total A = C1 + C2
```

> **Component system details**: See 65_id_system_v3_2.md for when to use
> id_component and combination rules.

### Cylindrical Coordinates
```json
{
  "id": 2,
  "type": "integral",
  "quantity": "V",
  "function": "r",
  "coordinate_system": "cylindrical",
  "integrals": [
    {"var": "z", "lower": "0", "upper": "4 - r*sin(theta)"},
    {"var": "r", "lower": "0", "upper": "4"},
    {"var": "theta", "lower": "0", "upper": "pi/2"}
  ]
}
// Note: the Jacobian factor `r` is written explicitly into `function`.
// coordinate_system is a label only and does not add it automatically.
```

> Because the Jacobian `r` makes `function != "1"`, this exercise sets `quantity:"V"`
> explicitly. Without it, auto-inference yields `R` (generic) with bare `u`.

### With Display Override
```json
{
  "id": 5,
  "id_letter": "d",
  "type": "integral",
  "function": "cos(x / y)",
  "integrals": [
    {"var": "z", "lower": "0", "upper": "y"},
    {"var": "x", "lower": "0", "upper": "y**2"},
    {"var": "y", "lower": "0", "upper": "pi/2"}
  ],
  "display_override": {
    "show_input": true,
    "show_symbolic": true,
    "show_numeric": true,
    "decimal_places": 2
  }
}
```

> **Derivative solver example**: still deferred — see 09_deferred_solvers_v3_2.md.
> The **gradient** input contract is now active in Phase 2A and specified below;
> 09's gradient section is superseded.

---

## Gradient Solver — Exercise Examples (Phase 2A)

> Full scope, restrictions, and validation matrix: `91_phase2a_gradient_scope_v3_2.md`.
> Phase 2A is **2-variable `f(x, y)` only**, **Cartesian only**, **radians only**.

### Solver-Specific Required Fields
- `function` (string) — the scalar field `f(x, y)`.
- An **evaluation point**, provided in exactly one of two ways:
  - `point` — a 2-element array of strings, e.g. `["1", "3"]`; or
  - `initial_point` **and** `final_point` — the two-points mode; the evaluation
    point is `initial_point`.

### Solver-Specific Optional Fields (direction source — at most one)
- `vector` — a 2-element array of strings; the solver normalizes it.
- `angle` — a **radians** math string, e.g. `"pi/4"`; `û = ⟨cos θ, sin θ⟩`.
- `direction_source: "max_ascent"` — the direction is `∇f(P)` itself, so
  `û ∥ ∇f(P)` and `D_u f == |∇f(P)|`.
- If none is supplied, the exercise is a **point-only** gradient: `∇f`, `∇f(P)`,
  `|∇f(P)|`, and `theta_max` are produced; `û` and `D_u f` are absent.

### Coordinates are strings
Every point/vector entry is a **sympy-parseable string** (`"0"`, `"sqrt(pi)"`,
`"pi/4"`), mirroring integral bounds. They are cleaned like any math field
(see 60_expression_cleaner_v3_2.md). Do **not** write raw JSON numbers for
coordinates.

### Not in Phase 2A
- **No `angle_unit`.** `angle` is always radians in 2A; degree input/display is 2B.
- **No `variables` field.** Variable order is fixed `(x, y)` in 2A.
- **No `coordinate_system`, `quantity`, or units** for gradient — gradient output
  is unitless in 2A.
- A gradient exercise must **not** carry `id_component` or `id_output` (2A: makes
  the whole `(id, id_letter)` group a `kind:"error"` — see 65/91).

### Invalid gradient inputs (exercise-level ERROR — full matrix in 91)
- `point` supplied together with `initial_point`/`final_point`, or an incomplete
  two-points pair (one of `initial_point`/`final_point` without the other).
- More than one direction source: a complete `initial_point`+`final_point` pair,
  `vector`, `angle`, or `direction_source: "max_ascent"` — any combination of two
  or more.
- A point/vector entry or `angle` that is not a string (raw JSON numbers are
  rejected — coordinates are strings).
- A `point`/`initial_point`/`final_point`/`vector` array whose length is not
  exactly 2 (Phase 2A is 2-variable).
- A zero-length direction (`final_point == initial_point`, `vector` parses to
  `⟨0, 0⟩` — e.g. `["0","0"]`, `["0.0","0"]`, `["sin(0)","0"]` — or `max_ascent`
  when `∇f(P) = ⟨0, 0⟩`).

A document mixing `type: "gradient"` with any other exercise type is a
**document-level hard stop** in 2A (single-solver documents only — see 91).

> **SUPERSEDED (Phase 2B-M):** the sentence above is retained as Phase 2A
> history only. Mixed-solver documents are now supported — see
> `92_phase2bm_multisolver_scope_v3_2.md` and "Multi-Solver Documents
> (Phase 2B-M)" below. There is no document-level type-mixing hard stop.

### Mode 1 — Two points (`initial_point` → `final_point`)
```json
{
  "id": 1,
  "id_letter": "a",
  "type": "gradient",
  "function": "y**2 * exp(x*y)",
  "initial_point": ["0", "2"],
  "final_point": ["5", "7"]
}
```

### Mode 2 — Point + vector
```json
{
  "id": 1,
  "id_letter": "b",
  "type": "gradient",
  "function": "x**2 * cos(x*y)",
  "point": ["sqrt(pi)", "sqrt(pi)"],
  "vector": ["4", "1"]
}
```

### Mode 3 — Point + angle (radians)
```json
{
  "id": 1,
  "id_letter": "c",
  "type": "gradient",
  "function": "100 * exp(-x**2 - y**2)",
  "point": ["1", "3"],
  "angle": "pi/4"
}
```

### Mode 4 — Steepest ascent (`max_ascent`)
```json
{
  "id": 3,
  "id_letter": "a",
  "type": "gradient",
  "function": "100 * exp(-x**2 - y**2)",
  "point": ["1", "3"],
  "direction_source": "max_ascent"
}
```

### Mode 5 — Point only (no direction)
```json
{
  "id": 3,
  "id_letter": "b",
  "type": "gradient",
  "function": "100 * exp(-x**2 - y**2)",
  "point": ["1", "3"]
}
```

### Display for gradient
Gradient visibility is controlled by a **top-level** `display_gradient` block
(parallel to `display_integral`) plus per-exercise `display_override`. See
70_display_system_v3_2.md.

```json
{
  "display_gradient": {
    "show_gradient": true,
    "show_gradient_evaluated": true,
    "show_magnitude": true,
    "show_unit_vector": true,
    "show_directional_derivative": true,
    "show_theta_max": true,
    "decimal_places": 4
  }
}
```

---

## Multi-Solver Documents (Phase 2B-M)

> Milestone scope: `92_phase2bm_multisolver_scope_v3_2.md`. Group rules:
> `65_id_system_v3_2.md` (authoritative — this section only summarizes).

- **Documents may freely interleave exercises of recognized solver types**
  (Phase 2B-M: `integral` and `gradient`) under one valid document envelope.
  Document-tier validation keeps only the envelope rules: required metadata
  fields, a non-empty `exercises` array, and a present `id` per exercise.
  There is no document-level type-mixing hard stop.
- **Per-exercise validation is unchanged and solver-specific**: each exercise
  is validated by its own solver's static matrix (90 for integral, 91 for
  gradient).
- **D2**: one `(id, id_letter)` group may not contain two different recognized
  solver identities, in any structural mode. The recognized-identity
  definition, precedence, and the complete cardinality matrix live in 65.
- **Malformed `type` values** (missing, `null`, non-string, unknown string)
  are always exercise-level authored errors, never a document stop. A document
  whose every exercise is malformed still processes to an all-error document
  (see 92).
- **Simultaneous `display_integral` and `display_gradient`** blocks are both
  honored in one document: each exercise resolves display through
  `display_{its own type}` (70); the blocks never interfere with each other.
- **Authored input can never select or influence presentation routing**: no
  input field participates in the choice of document shell, item fragments, or
  renderer registry. The render model is built exclusively by the Render
  Adapter (85).
- **All-error documents**: behavior (summary semantics, TeX/PDF attempts, CLI
  exit) is owned by 92.

---

## Expression Syntax Rules

### Supported Mathematical Expressions
```python
# These are all valid and equivalent:
"x^2 + y^2"      # Caret notation (auto-converted)
"x**2 + y**2"    # Python notation (preferred internally)

# Supported functions:
"sin(x)", "cos(x)", "tan(x)"
"exp(x)", "log(x)", "ln(x)"
"sqrt(x)", "abs(x)"
"pi"             # Constant
"exp(1)"         # Euler's number; standalone "e" is not supported
```

### Auto-conversions Applied
See 60_expression_cleaner_v3_2.md for complete transformation rules.

- `^` → `**` (exponentiation)
- `ln` → `log` (natural logarithm)
- `sin^2(x)` → `sin(x)**2` (trig powers)
- `sin^-1(x)` → `asin(x)` (inverse trig)

> **Implicit multiplication is NOT supported.** `2x` will not be converted to
> `2*x`. Write explicit `*`. An expression relying on implicit multiplication
> becomes an ERROR exercise (see 60).

---

## File Naming Convention

Files are named based on metadata and `file_naming_mode`.

`assignment.type` is a canonical short token used verbatim in filenames and
mapped to a Spanish display label by the adapter (see
85_render_adapter_and_jinja2_spec_v3_2.md). Canonical Phase 1 tokens:
`hw`, `exam`, `quiz`, `test`, `project`. The filename `<type>` slot is this
token; the document label is the mapped word (`hw → Tarea`).

### Production Mode (default — no timestamp)

```
<institution>_<course_code>_<type>_<number>.json
<institution>_<course_code>_<type>_<number>_extended.json
Examples:
itson_c3_hw_16.json
itson_c3_hw_16_extended.json
```

> If `institution` or `course_code` are absent, the corresponding slot is omitted
> and remaining slots are joined with single underscores. `type` and `number` are
> always present (required fields).

### Testing Mode (with timestamp)

```
<institution>_<course_code>_<type>_<number>_YYYYMMDD_HHMMSS.json
Examples:
itson_c3_hw_16_20260121_161159.json
itson_c3_hw_16_20260121_161159_extended.json
```

### Generated LaTeX/PDF
Same base name as JSON files:

```
itson_c3_hw_16.tex / itson_c3_hw_16.pdf
itson_c3_hw_16_20260121_161159.tex  ← If testing mode
```

### Controlled by Metadata
```json
{
  "metadata": {
    "institution": "itson",
    "course_code": "c3",
    "assignment": {
      "type": "hw",
      "number": 16
    },
    "file_naming_mode": "production"
  }
}
```

`file_naming_mode` defaults to `"production"` if not specified. Its source of truth
is `metadata.file_naming_mode`; the value in 50_config_defaults_global_v3_2.json is
a fallback only and is not merged into per-exercise display config (see
70_display_system_v3_2.md, 55_file_handling_v3_2.md).

---

## Validation Checklist

### Required Fields (everything else is OPTIONAL)
- [ ] `metadata.course`
- [ ] `metadata.assignment.type`
- [ ] `metadata.assignment.number`
- [ ] Each exercise: `id` (NUMBER) and `type`

Missing required top-level fields, or any exercise missing `id`, → document-level
hard stop (see 90_phase1_scope_v3_2.md). A non-numeric `id`, missing/unknown
`type`, missing/malformed solver fields → exercise-level ERROR. Group-structure
problems (sequence gaps, duplicate or mixed IDs, both `id_component`+`id_output`,
conflicting component quantities, invalid `component_operation`) → group-level
ERROR. Layered validation authority (Phase 2B-M): `90_phase1_scope_v3_2.md`
remains the Phase 1 **Integral** validation contract (frozen);
`91_phase2a_gradient_scope_v3_2.md` remains the **Gradient** exercise-validation
contract; `65_id_system_v3_2.md` owns **D2, supported modes, precedence, and
group/cardinality behavior**; `92_phase2bm_multisolver_scope_v3_2.md` owns the
**Phase 2B-M milestone and mixed-document behavior**. This checklist points to
those owners; it never duplicates their matrices.

### Integral Solver Required Fields
- `function` (string)
- `integrals` (array with var/lower/upper per integral)
- `quantity` and `coordinate_system` are auto-inferred if missing

### Type Requirements
- `id`: Must be NUMBER (not string) — breaks sorting if string
- `id_component`: NUMBER when used
- `id_output`: NUMBER when used
- `id_letter`: string when used

---

## Quick Reference — Most Common Patterns

```json
// ~90% of exercises (minimal):
{
  "id": 1,
  "id_letter": "a",
  "type": "integral",
  "function": "x^2 + y^2",
  "integrals": [/* ... */]
}

// With explicit override (~10%):
{
  "id": 1,
  "type": "integral",
  "quantity": "T",
  "coordinate_system": "polar",
  "function": "r^2",
  "integrals": [/* ... */]
}

// With display override (~5%):
{
  "id": 1,
  "type": "integral",
  "function": "x^2",
  "integrals": [/* ... */],
  "display_override": {
    "show_input": false,
    "quantity_label": "M"
  }
}
```

---

## Quantity Label Policy

`quantity` is optional. If provided, it overrides auto-inference.

Recommended labels:
- `A` = area
- `V` = volume
- `R` = generic result
- `M` = mass
- `Q` = charge or context-specific quantity
- `T` = only when the author intentionally wants Total/Other

Auto-inference for integrals:
- double integral with `function == "1"` → `A`
- triple integral with `function == "1"` → `V`
- anything else → `R`

Examples:

```json
{
  "id": 4,
  "type": "integral",
  "quantity": "M",
  "function": "2*x*y",
  "integrals": [
    {"var": "z", "lower": "0", "upper": "1"},
    {"var": "y", "lower": "0", "upper": "1"},
    {"var": "x", "lower": "0", "upper": "1"}
  ],
  "display_override": {
    "units_override": "kg"
  }
}
```

---

## Standalone `e` Policy

Standalone `e` is not supported as a constant.

Use:
- `exp(1)` for Euler's number
- `exp(x)` for e raised to x
- `exp(3*x)` for e raised to 3x

Do not use:
- `e`
- `e^x`
- `e**x`
