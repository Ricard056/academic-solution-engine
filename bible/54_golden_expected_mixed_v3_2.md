# Golden Expected Reference — Mixed Contract (Phase 2B-M) — v3.2

> **Status**: Phase 2B-M acceptance reference (multi-solver documents).
> **Purpose**: Defines expected RENDER-MODEL values for
> `53_test_data_mixed_v3_2.json`, so the mixed-document contract is testable.
> **Source data**: 53_test_data_mixed_v3_2.json.
> **Note**: Values describe the render model produced by
> `build_render_model(extended_json, defaults)` — i.e. AFTER adapter resolution.
> The Phase 1 golden (47 over 46), the Phase 1.1 symbolic golden (49 over 48),
> and the Phase 2A gradient golden (52 over 51) remain **frozen** and must
> continue to pass unchanged.

---

## Conventions

- Every position reuses an exact frozen case (see 53's notes); only the local
  document id differs from the source. Expected values below therefore restate
  already-frozen contracts (47/49/52) in this document's display context.
- 53 sets `display_default {show_input: true, decimal_places: 4}`,
  `display_integral {show_input: false}`, and all six `show_gradient_*` flags
  true — both solver display blocks are present simultaneously and each
  exercise resolves through `display_{its own type}` only.
- **Binding vs illustrative**: decimal strings and boolean flags below are
  **byte-exact**. LaTeX `*_latex` fields are pinned as MATHEMATICAL content in
  shorthand; the byte-exact SymPy strings are captured when the golden test is
  written (the 49/52 discipline; the ROUND_HALF_UP rounding rule is owned
  by 47). Unicode angle brackets in prose are explanatory shorthand only —
  never a binding decimal-field value.
- The D2 cardinality matrix, supported-mode violations, display-flag gating
  variations, unhashable-token cases, and internal-render-failure cases are
  **unit-test scope** (65/92), not golden scope.
- Gradient items are unitless; integral items carry units per the adapter Unit
  Derivation Rule (85).

---

## M1 — id 1: Integral standard (frozen 46 Ex 1)

Expected render item:
- `kind`: `"standard"`, `exercise_label`: `"1"`
- `quantity_label`: `"A"` (inferred), `units`: `"u^2"`
- `solution_latex`: `"1"`, `decimal_string`: `"1.0000"`
- `show_symbolic`: true, `show_numeric`: true, `show_quantity`: true
- `show_input`: **false** (this document's `display_integral.show_input`)

## M2 — id 2: Gradient two-points anchor (frozen 51 G1 / 52 G1)

Expected render item: `kind`: `"gradient"`, `exercise_label`: `"2"`; all six
pieces present and numeric (every `show_*` true, every `*_numeric` true).

Symbolic `*_latex` fields — mathematical content per 52 G1 (e.g. the gradient
`∇f(x,y) = ⟨y³ e^{xy}, y e^{xy}(xy+2)⟩`, magnitude `4√5`, directional
derivative `6√2`, theta `atan(1/2)` — shorthand, captured byte-exact at test
time).

Decimal fields — **byte-exact** (frozen by 52 G1):

- `gradient_evaluated_decimal`:
  `\left\langle 8.0000, \; 4.0000 \right\rangle`
- `unit_vector_decimal`:
  `\left\langle 0.7071, \; 0.7071 \right\rangle`
- `magnitude_decimal_string`: `"8.9443"`
- `directional_derivative_decimal_string`: `"8.4853"` (ROUND_HALF_UP witness)
- `theta_max_decimal_string`: `"0.4636"` (radians)

## M3 — id 3: Integral component group (frozen 46 Ex 5 / 47 Ex 5)

Expected render item:
- `kind`: `"component_group"`, `exercise_label`: `"3"`
- `quantity_label`: `"A"`, `units`: `"u^2"`
- `total_latex`: `"1"`, `total_decimal_string`: `"1.0000"`
- `operation_latex`: `"\\frac{1}{2} + \\frac{1}{2}"`
- `operation_decimal_string`: `"0.5000 + 0.5000"`
- `components[0]`: `id_component=1`, `solution_latex="\\frac{1}{2}"`,
  `decimal_string="0.5000"`; `components[1]`: `id_component=2`, same values
- group-level flags all true (group display resolves from
  hardcoded → `display_default` → `display_integral`; bible 85)

## M4 — id 4: Gradient symbolic point (frozen 51 G6 / 52 G6)

Expected render item: `kind`: `"gradient"`, `exercise_label`: `"4"`.
- `show_gradient`: true — `gradient_latex`: `⟨2x, 2y⟩` (mathematical content)
- `show_gradient_evaluated`: true, `gradient_evaluated_numeric`: **false**,
  `gradient_evaluated_decimal`: `""` — evaluated latex `⟨2a, 2b⟩`
- `show_magnitude`: true, `magnitude_numeric`: **false**,
  `magnitude_decimal_string`: `""` — magnitude latex `2√(a² + b²)`
- `show_theta_max`: true, `theta_max_numeric`: **false**,
  `theta_max_decimal_string`: `""` — theta latex `atan2(2b, 2a)`
- `show_unit_vector`: **false**, `show_directional_derivative`: **false**
  (absent — no direction); their LaTeX/decimals: `""`

## M5 — id 5: Integral output group (frozen 46 Ex 6 / 47 Ex 6)

Expected render item:
- `kind`: `"output_group"`, `exercise_label`: `"5"`
- `outputs[0]`: `id_output=1`, `output_label="Resultado 1"`,
  `quantity_label="A"`, `units="u^2"`, `solution_latex="1"`,
  `decimal_string="1.0000"`, `show_quantity`/`show_symbolic`/`show_numeric`
  all true
- `outputs[1]`: `id_output=2`, `output_label="Resultado 2"`, same values

## M6 — id 6: symbolic Integral (frozen 48 Ex 1 / 49 Ex 1)

Expected render item:
- `kind`: `"standard"`, `exercise_label`: `"6"`
- `quantity_label`: `"A"` (inferred: 2 integrals + function "1")
- `units`: `"u^2"`
- `solution_latex`: `"a b"`
- `numeric_value` (source, Extended JSON): `null` — a SUCCESS, not an error
- `show_numeric`: **false** (RESOLVED off by Numeric-Availability Resolution)
- `decimal_string`: `""`
- `show_symbolic`: true, `show_quantity`: true
- `show_input`: **false** (this document's `display_integral.show_input`;
  display-context resolution — the frozen mathematical/result contract of
  48/49 Ex 1 is unchanged)

## M7 — id 7: intended authored error (frozen 46 Ex 9 / 47 Ex 9)

Expected render item:
- `kind`: `"error"`, `exercise_label`: `"7"`
- `message`: `"ERROR: no se pudo procesar este ejercicio."`
- exactly ONE generic marker for this position; the run does not halt.

---

## Order lock (binding — the D1 witness)

- `exercise_label` sequence: `["1", "2", "3", "4", "5", "6", "7"]`
- `kind` sequence:
  `["standard", "gradient", "component_group", "gradient", "output_group",
  "standard", "error"]`

Solver types interleave (I, G, I, G, I, I, I): this order cannot be produced
by any solver partitioning.

## Summary lock (binding — member-based)

`processing_summary`: `total_exercises: 9`, `successful: 8`, `errors: 1`
(authored exercise members, never render cards).

## Extended JSON metadata-absence lock (binding)

The 53 run's Extended JSON contains **no** shell metadata, fragment metadata,
registry metadata, routing metadata, and no `rendered_items` — in any
spelling. The exact internal shell-identifier value (`document.template` in
the render model) is **not** a golden contract; it is asserted only by narrow
implementation tests (92/85).

## TeX expectations (substring/order locks)

- M2's six gradient lines appear in contract order (85), with the two
  byte-exact decimal vectors above.
- M3's component lines and Total line appear per 47 Ex 5.
- M6's symbolic line renders `a b` with **no** decimal tail.
- Exactly one generic Spanish error marker (M7).
- No `û` / `D_u f` lines for M4.
- Document title/labels present. No whole-file TeX byte identity is required.

---

## Acceptance Rule (Phase 2B-M mixed contract)

A Phase 2B-M implementation is acceptance-correct when:
1. M1–M7 match the values above field-for-field (byte-exact decimals/flags;
   mathematically-equivalent LaTeX per Conventions).
2. The order lock and summary lock hold exactly.
3. The Extended JSON metadata-absence lock holds.
4. The full 53 run completes without halting (M7 does not stop processing).
5. The frozen goldens still pass UNCHANGED: 47 over 46, 49 over 48, 52
   over 51.
6. The pure-document universal-path TeX/PDF gate is satisfied per bible 92
   (owned there; not restated here).
