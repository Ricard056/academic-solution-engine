# Golden Expected Reference — Symbolic Contract (Phase 1.1) — v3.2

> **Status**: Phase 1.1 acceptance reference (symbolic-only success contract).
> **Purpose**: Defines expected RENDER-MODEL values for
> `48_test_data_symbolic_v3_2.json`, so the symbolic-only contract is testable.
> **Source data**: 48_test_data_symbolic_v3_2.json.
> **Note**: Values describe the render model produced by
> build_render_model(extended_json, defaults), i.e. AFTER adapter resolution.
> The original Phase 1 acceptance (47_golden_expected_v3_2.md over 46) remains
> frozen and must continue to pass unchanged.

---

## Conventions

- 48's display block sets `show_input`, `show_symbolic`, `show_numeric`,
  `show_quantity` all true and `decimal_places` 4 at the default level — so
  every `show_numeric: false` below is RESOLVED by the adapter's
  Numeric-Availability Resolution (85), never authored.
- Units follow the adapter Unit Derivation Rule (85).
- "S1"/"S2" are explanatory planning labels only; input IDs are numeric.
- The ROUND_HALF_UP Rounding Rule Guard is owned by 47 and is not repeated here.

---

## Ex 1 — S1: standard symbolic success (parameters in the bounds)

Input: `id=1`, `function="1"`, y from 0 to `a`, x from 0 to `b`, no explicit
quantity.

Expected render item:
- `kind`: `"standard"`
- `exercise_label`: `"1"`
- `quantity_label`: `"A"`  (inferred: 2 integrals + function "1")
- `units`: `"u^2"`
- `solution_latex`: `"a b"`
- `numeric_value` (source, Extended JSON): `null`
- `show_numeric`: **false**  (RESOLVED off despite config true — the
  Numeric-Availability guard)
- `decimal_string`: `""`  (populated for contract closure; never rendered)
- `show_input`: true, `show_symbolic`: true, `show_quantity`: true

Purpose: proves `numeric_value: null` is a SUCCESS, quantity inference still
fires on a symbolic result, and the adapter — not the author — turned the
numeric line off.

---

## Ex 2 — standard symbolic success (parameter in the function, 1D)

Input: `id=2`, `function="k*x^2"`, x from 0 to 1.

Expected render item:
- `kind`: `"standard"`
- `exercise_label`: `"2"`
- `quantity_label`: `"R"`  (1D never infers A/V)
- `units`: `"u"`
- `solution_latex`: `"\\frac{k}{3}"`
- `numeric_value` (source): `null`
- `show_numeric`: **false**  (resolved), `decimal_string`: `""`
- `show_input`: true, `show_symbolic`: true, `show_quantity`: true

Purpose: symbolic success via a function parameter; exercises the 1D path and
caret cleaning (`k*x^2` -> `k*x**2`) on a symbolic integrand.

---

## Ex 3 — S2: component group with a symbolic member (INTENDED ERROR)

Input: `id=3`, two components, both `quantity="A"`, both `function="1"`:
- Component 1 (numeric): y from 0 to x, x from 0 to 1  -> 1/2
- Component 2 (symbolic): y from 0 to `a`, x from 1 to 2 -> `a`

Expected render item:
- `kind`: `"error"`
- `exercise_label`: `"3"`
- `message`: `"ERROR: no se pudo procesar este ejercicio."`

Reason: component sums are numeric-only in Phase 1 (75/90). Aggregation MUST
refuse the group (no `results.component`); the adapter MUST collapse it to ONE
generic error item. **This passing is a success, not a bug** — the same
acceptance semantics as 47's Ex 9.

---

## Ex 4 / Ex 5 — divergence guards (must REMAIN errors)

- Ex 4: `function="x"`, x from 0 to `inf` — divergent improper integral.
- Ex 5: `function="1/x"`, x from 0 to 1 — divergent at the lower bound.

Expected: each renders as `kind:"error"` with the generic Spanish marker.

Purpose: the symbolic contract must not weaken the finite guard —
`numeric_value` is never Infinity/NaN, and infinite/indeterminate results are
NOT symbolic successes (90, symbolic-success conditions).

---

## Acceptance Rule (Phase 1.1)

A Phase 1.1 implementation is acceptance-correct when:
1. Ex 1 and Ex 2 match the values above field-for-field (for the fields
   listed), including the RESOLVED `show_numeric: false` and
   `decimal_string: ""`.
2. Ex 3 renders as ONE `kind:"error"` item with the generic marker.
3. Ex 4 and Ex 5 render as `kind:"error"` items.
4. The full 48 run completes without halting.
5. The full Phase 1 golden set (47_golden_expected_v3_2.md over
   46_test_data_integral_edge_cases_v3_2.json) still passes UNCHANGED.
