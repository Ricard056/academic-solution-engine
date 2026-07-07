# ID System Specification — v3.2

> **v3.2 changes**: `component_operation` closed — Phase 1 accepts only an absent
> value or `"sum"`; any other value makes the whole component group an ERROR (P2);
> component-quantity uniformity hardened to a group-ERROR rule (P3). References
> updated to _v3_2.
> **Phase 1.1 amendment**: component members must produce numeric results (see
> Component Rules).

## Core ID Fields

Every exercise uses a flexible identification system:

```json
{
  "id": 7,                    // Exercise number (NUMBER, REQUIRED)
  "id_letter": "a",          // Sub-exercise letter (string, OPTIONAL)
  "id_component": 1,         // Parts that combine (NUMBER, OPTIONAL)
  "id_output": 1,            // Independent results (NUMBER, OPTIONAL)
  "type": "integral"         // Solver type (string, REQUIRED)
}
```

## Field Types & Rules

### Critical Data Type Requirements
- `id`: **MUST be NUMBER** (not string) for proper sorting
- `id_component`: **NUMBER** when used
- `id_output`: **NUMBER** when used
- `id_letter`: **string** when used

> **Important**: Using `"id": "1"` (string) instead of `"id": 1` (number) will
> break sorting. Always use NUMBER type. A non-numeric `id` is an exercise-level
> ERROR; a missing `id` is a document-level hard stop (see 90_phase1_scope_v3_2.md).

### When to Use Each Field

| Field | Use When | Example |
|-------|----------|---------|
| `id` | Always (every exercise) | Exercise 1, 2, 3... |
| `id_letter` | Exercise has sub-parts | 1a, 1b, 1c... |
| `id_component` | Parts mathematically combine | Component 1 + Component 2 = Total Area |
| `id_output` | Multiple independent results | ∂z/∂x and ∂z/∂y separately |

---

## Component System (id_component)

### Purpose
For exercises broken into parts that mathematically combine for a final answer.

### How Components Combine
Each solver defines a default operation:

| Solver | Default Operation | Use Case |
|--------|------------------|----------|
| integral | sum | Areas/volumes add together |

> **Phase 1 accepts only an absent `component_operation` or `component_operation: "sum"`.**
> Any other value makes the whole component group a `kind:"error"` render item. The
> field is reserved for future operations (see 08_deferred_features_v3_2.md); it is
> not honored in Phase 1.

### Component Rules
- All components of the same exercise must share the same `id` and `id_letter`
- Components must be sequential (1, 2, 3... no gaps). A gap makes the whole group
  an ERROR item (see 90_phase1_scope_v3_2.md).
- All components in the same component group must resolve to the same
  `quantity_label`. If they do not, the whole group renders as one `kind:"error"`
  item.
- All members must produce numeric results; a symbolic-only member
  (`numeric_value: null`, see 75_json_output_spec_v3_2.md) makes the whole group
  a group-level ERROR (see 90_phase1_scope_v3_2.md). Component sums are
  numeric-only in Phase 1.

### Example: Multi-Region Integral
```json
[
  {"id": 3, "id_letter": "a", "id_component": 1, "type": "integral", "quantity": "A",
   "function": "x^2", "integrals": [
     {"var": "y", "lower": "0", "upper": "x"},
     {"var": "x", "lower": "0", "upper": "1"}
   ]},
  {"id": 3, "id_letter": "a", "id_component": 2, "type": "integral", "quantity": "A",
   "function": "x^2", "integrals": [
     {"var": "y", "lower": "x", "upper": "2-x"},
     {"var": "x", "lower": "1", "upper": "2"}
   ]}
]
```

**PDF Output**:

3a) Component 1: A = 1/4
Component 2: A = 7/12
Total Area = 1/4 + 7/12 = 5/6

> **Component results schema**: See 75_json_output_spec_v3_2.md for the full
> `component` object structure in extended JSON (written by the Component
> Aggregation stage), and 85_render_adapter_and_jinja2_spec_v3_2.md for the
> component_group render item.

---

## Output System (id_output)

### Purpose
For exercises requiring multiple INDEPENDENT calculations displayed separately.
Unlike components, outputs do NOT combine — each is a standalone result.

### Example: Multiple Derivatives
```json
[
  {"id": 2, "id_letter": "a", "id_output": 1, "type": "derivative",
   "function": "x^2 * y", "variable": "x"},
  {"id": 2, "id_letter": "a", "id_output": 2, "type": "derivative",
   "function": "x^2 * y", "variable": "y"}
]
```

**PDF Output**:

2a) ∂z/∂x = 2xy
∂z/∂y = x²

### Output Rules
- Outputs must be sequential (1, 2, 3... no gaps). A gap makes the whole group an
  ERROR item (see 90_phase1_scope_v3_2.md).
- Each output is solved independently
- No combination operation — results displayed side by side

---

## Sorting Order

Exercises sort by:
1. `id` (numeric) — requires NUMBER type
2. `id_letter` (alphabetic)
3. `id_component` or `id_output` (numeric)

---

## Decision Guide

### Should I use id_component?
✅ Use if: Parts combine mathematically (C1 + C2 = Total)
❌ Don't if: Results are independent

### Should I use id_output?
✅ Use if: Multiple independent results needed
❌ Don't if: Results combine into one answer

### Should I use id_letter?
✅ Use if: Exercise has logical sub-parts
❌ Don't if: Each is truly a separate exercise

> An exercise must not carry BOTH `id_component` and `id_output`, and a single
> `(id, id_letter)` group must not mix standard, component, and output modes. Either
> case makes the whole group an ERROR (see 90_phase1_scope_v3_2.md).

---

## Common Patterns

### Pattern 1: Simple Exercise
```json
{"id": 1, "type": "integral", "function": "x^2", "integrals": []}
```

### Pattern 2: Sub-parts
```json
{"id": 1, "id_letter": "a", "type": "integral"}
{"id": 1, "id_letter": "b", "type": "integral"}
```

### Pattern 3: Multi-component (combine)
```json
{"id": 1, "id_component": 1, "type": "integral"}
{"id": 1, "id_component": 2, "type": "integral"}
```

### Pattern 4: Multi-output (independent)
```json
{"id": 1, "id_output": 1, "type": "derivative", "variable": "x"}
{"id": 1, "id_output": 2, "type": "derivative", "variable": "y"}
```

### Pattern 5: Complex
```json
{
  "id": 5,
  "id_letter": "c",
  "id_component": 2,
  "type": "integral"
}
```

---

## Render-Only Labels

The ID fields above are structural data. They are used for sorting, grouping, and
deciding whether values combine or remain independent.

A rendered label such as `"1.a"` or `"3.b — Resultado 2"` is NOT an input ID
field. It should be created by the render adapter as `exercise_label`,
`component_label`, or `output_label`.

Rules:
- `id` remains numeric in input and extended JSON.
- `id_letter` remains the only structural string identifier.
- `exercise_label` is display-only and may be a string because it is not used for sorting.
- Templates should use render-only labels; solvers should use structural IDs.
