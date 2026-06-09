# JSON Input Structure Specification — v3.2

> **v3.2 changes**: validation checklist points to the full three-tier matrix in 90
> (P3); Jacobian-defeats-`function=="1"` note added to the cylindrical example (P5);
> references updated to _v3_2. v3.1 baseline: `coordinate_system` computationally
> passive (author supplies Jacobian); canonical `assignment.type` vocabulary;
> `show_interpretations`/`interpretation` removed from Phase 1.

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

> **Other solver examples** (gradient, derivative): See 09_deferred_solvers_v3_2.md

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
ERROR. See the full validation matrix in 90_phase1_scope_v3_2.md.

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
