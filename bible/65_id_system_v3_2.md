# ID System Specification — v3.2

> **v3.2 changes**: `component_operation` closed — Phase 1 accepts only an absent
> value or `"sum"`; any other value makes the whole component group an ERROR (P2);
> component-quantity uniformity hardened to a group-ERROR rule (P3). References
> updated to _v3_2.
> **Phase 1.1 amendment**: component members must produce numeric results (see
> Component Rules).
> **Phase 2A amendment**: gradient exercises are standard-items-only; a gradient
> member carrying `id_component` or `id_output` is a group-level ERROR (see
> "Gradient (Phase 2A)" below and `91_phase2a_gradient_scope_v3_2.md`). Aggregation
> stays integral-only. Integral grouping rules are unchanged.
> **Phase 2B-M amendment**: this file is now the single authoritative owner of the
> multi-solver group contract — recognized solver identity, the D2 rule and its
> precedence and cardinality matrix, the supported-mode table, and the canonical
> ordering guarantees (see "Multi-Solver Groups (Phase 2B-M)" below). Milestone
> scope lives in `92_phase2bm_multisolver_scope_v3_2.md`. Integral and gradient
> grouping rules themselves are unchanged.

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

## Gradient (Phase 2A)

Gradient exercises support **standard items only**. Each `(id, id_letter)` is a
single standard gradient item; the six gradient outputs are facets of that one
item, not separate results — so neither combining (`id_component`) nor
independent-outputs (`id_output`) applies.

- A gradient member carrying `id_component` **or** `id_output` makes the whole
  `(id, id_letter)` group a **group-level ERROR** (one `kind:"error"` render item).
  This is a **Phase 2A restriction, not permanent** — there is no current gradient
  use case for either field.
- **Aggregation remains integral-only.** The Component Aggregation stage never runs
  for gradient (gradient has no `id_component`).
- `id`/`id_letter` labeling (`1.a`, `1.b`, `1.c`) works exactly as for integrals.

The `id_output` example above uses `type:"derivative"` (still deferred) purely to
illustrate the independent-outputs concept; it is not a gradient pattern.

> **Phase 2B-M note**: the group-error rule above is the `gradient → {standard}`
> row of the single authoritative supported-mode table in the **following
> "Multi-Solver Groups (Phase 2B-M)" section below**.

---

## Multi-Solver Groups (Phase 2B-M)

> Milestone scope: `92_phase2bm_multisolver_scope_v3_2.md`. This section is the
> **single authoritative owner** of the rules below; 92 and 80 summarize and
> point here — they never carry a second copy.

### Recognized solver identity

- A **raw authored `type` token** is any JSON value in the `type` field. A
  **recognized solver identity** is a **string** value belonging to the closed
  active solver set (Phase 2B-M: `integral`, `gradient`).
- Missing, `null`, non-string, and unknown-string tokens have **no** recognized
  identity. They remain exercise-level authored validation failures — never a
  document-level stop.
- Two equal unknown tokens never form a recognized identity ("a raw unknown
  token does not become a valid solver merely because two members share it").
- Identity comparison uses **equality scans only** — authored values may be
  unhashable (e.g. `[]`, `{}`), so no set/hash operation is ever applied to them.

### D2 — one recognized solver identity per group

Every member of one `(id, id_letter)` group must share one recognized solver
identity. A group may never contain two different recognized identities — in
**any** structural mode (standard, component, or output).

### Precedence (evaluated per group, in order)

1. Exercise validation classifies each member (authored-input failures).
2. Structural-mode coherence is evaluated for the full group.
3. D2 is evaluated over recognized solver identities.
4. Solver structural capability is evaluated (supported-mode table below).
5. Mode-specific sequence, duplicate, operation, quantity, and solved-member
   rules are evaluated.
6. The render adapter applies the resulting group-versus-member error
   cardinality.

### Cardinality matrix (authoritative)

| Group composition | D2 | Standard mode | Component/output mode |
|---|---|---|---|
| Integral + Gradient recognized identities | violated | one group error | one group error |
| One recognized + one unknown string | not violated | valid item + one exercise error | one group error |
| One recognized + missing `type` | not violated | valid item + one exercise error | one group error |
| One recognized + `null` | not violated | valid item + one exercise error | one group error |
| One recognized + number/array/object | not violated | valid item + one exercise error | one group error |
| Only one unknown string | n/a | one exercise error | one group error if structurally grouped |
| Two equal unknown strings | n/a | two exercise errors | one group error |
| Two different unknown strings | n/a | two exercise errors | one group error |
| Only missing/null/non-string values | n/a | one exercise error per member | one group error |
| ≥3 members incl. Integral and Gradient, with or without malformed members | violated | one group error | one group error |
| ≥3 members, one recognized solver + malformed members | not violated | recognized members render + individual malformed-member errors | one group error |
| Any composition also mixing standard/component/output modes | structural violation | one group error | one group error |

Additionally: a member of a solver used in a structural mode outside that
solver's supported set (table below) makes the whole group **one group error**.

The same visible one-group-error card may have several internal causes.
Detailed diagnostics stay internal; only the generic render marker appears
(bible 85).

### Supported-mode table (single authoritative copy)

| Solver | Supported structural modes |
|---|---|
| `integral` | standard, component, output |
| `gradient` | standard |

This table is owned by the validation layer and is the capability registry a
future solver must extend **explicitly** with its own row. Component
Aggregation remains Integral-only; component mathematics never moves into the
adapter or Jinja (90/92).

### Ordering guarantees (Phase 2B-M contractual)

- Canonical ordering is unchanged: `(id, id_letter)` groups by defensive
  numeric `id` rank then `id_letter`; members by `id_component` / `id_output`.
- **Stable authored relative order is contractual for members with identical
  complete structural keys.**
- A collapsed group error occupies exactly **one** structural output position
  for its group.
- Solver identity never participates in any sorting or grouping key.
- No solver partitioning occurs before or after canonical structural ordering.

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
