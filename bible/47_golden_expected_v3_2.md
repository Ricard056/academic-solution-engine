# Golden Expected Reference — v3.2

> **Status**: Phase 1 required acceptance reference.
> **Purpose**: Defines expected RENDER-MODEL values for selected exercises so that
> "correct" is testable, not subjective. A correct first run must match these.
> **Source data**: 46_test_data_integral_edge_cases_v3_2.json.
> **v3.2 changes**: added Ex 6 output-group golden case (P11); added a formatter
> Rounding Rule Guard for ROUND_HALF_UP (P12); acceptance rule updated.
> **Note**: Values describe the render model produced by
> build_render_model(extended_json, defaults), i.e. AFTER adapter formatting.

---

## Conventions

- `decimal_places` for this file's reference exercises is 4 unless the exercise
  overrides it.
- Units follow the adapter Unit Derivation Rule (see
  85_render_adapter_and_jinja2_spec_v3_2.md): `A → u^2`, `V → u^3`, other → `u`,
  `units_override` wins verbatim. The render-model `units` value is a plain token;
  the template wraps it in `\mathrm{...}`.
- The display block in 46 sets `show_input`, `show_symbolic`, `show_numeric`,
  `show_quantity` all true and `decimal_places` 4 at the default level, with
  `display_integral.show_input` true.

---

## Ex 1 — Standard, double integral, function "1"

Input: `id=1`, `function="1"`, two integrals over [0,1]×[0,1], no explicit
quantity.

Expected render item:
- `kind`: `"standard"`
- `exercise_label`: `"1"`
- `quantity_label`: `"A"`  (inferred: 2 integrals + function "1")
- `units`: `"u^2"`
- `solution_latex`: `"1"`
- `numeric_value` (source): `1.0`
- `decimal_string`: `"1.0000"`
- `show_input`: true, `show_symbolic`: true, `show_numeric`: true, `show_quantity`: true

Purpose: confirms quantity inference, area units, and 4-place formatting.

---

## Ex 7 — Standard, decimal override + quantity_label + units_override

Input: `id=7`, `function="x*y"`, two integrals over [0,2]×[0,2], with
`display_override`: `show_symbolic=false`, `show_numeric=true`,
`decimal_places=2`, `quantity_label="Q"`, `units_override="C"`.

Expected render item:
- `kind`: `"standard"`
- `exercise_label`: `"7"`
- `quantity_label`: `"Q"`  (from display_override.quantity_label)
- `units`: `"C"`  (from display_override.units_override, verbatim)
- `show_symbolic`: false, `show_numeric`: true
- `numeric_value` (source): `4.0`  (∫₀²∫₀² x·y dy dx = 4)
- `decimal_string`: `"4.00"`  (formatted to TWO places — proves the override
  reaches the adapter formatter; this is the B1 regression guard)

Purpose: confirms that a per-exercise `decimal_places` override actually changes
the formatted output, and that `quantity_label`/`units_override` win.

---

## Ex 5 — Component group (id_component 1 and 2)

Input: `id=5`, two components, both `quantity="A"`, both `function="1"`.
- Component 1: y from 0 to x, x from 0 to 1  → area 1/2
- Component 2: y from 0 to 2−x, x from 1 to 2 → area 1/2
- Total area = 1

Expected render item:
- `kind`: `"component_group"`
- `exercise_label`: `"5"`
- `quantity_label`: `"A"`
- `units`: `"u^2"`
- `show_component_total`: true, `show_component_symbolic`: true,
  `show_component_operation`: true, `show_numeric`: true, `show_quantity`: true
- `total_latex`: `"1"`
- `total_decimal_string`: `"1.0000"`
- `operation_latex`: `"\\frac{1}{2} + \\frac{1}{2}"`
- `operation_decimal_string`: `"0.5000 + 0.5000"`
- `components[0]`: `id_component=1`, `solution_latex="\\frac{1}{2}"`,
  `decimal_string="0.5000"`, `quantity_label="A"`, `units="u^2"`,
  `show_component_quantity`: true, `show_numeric`: true
- `components[1]`: `id_component=2`, `solution_latex="\\frac{1}{2}"`,
  `decimal_string="0.5000"`, `quantity_label="A"`, `units="u^2"`,
  `show_component_quantity`: true, `show_numeric`: true

Purpose: confirms component grouping, sum combination, and that every component
render field is populated (closed-contract guard).

---

## Ex 6 — Output group (id_output 1 and 2)

Input: `id=6`, two outputs, both `function="1"`, both double integrals.
- Output 1: x,y over [0,1]×[0,1] → 1
- Output 2: x over [1,2], y over [0,1] → 1
Outputs are independent (do NOT combine).

Expected render item:
- `kind`: `"output_group"`
- `exercise_label`: `"6"`
- `outputs[0]`: `id_output=1`, `output_label="Resultado 1"`, `quantity_label="A"`,
  `units="u^2"`, `solution_latex="1"`, `decimal_string="1.0000"`,
  `show_quantity`/`show_symbolic`/`show_numeric` all true
- `outputs[1]`: `id_output=2`, `output_label="Resultado 2"`, `quantity_label="A"`,
  `units="u^2"`, `solution_latex="1"`, `decimal_string="1.0000"`,
  `show_quantity`/`show_symbolic`/`show_numeric` all true

Purpose: confirms output grouping, independent (non-combining) results, per-output
labels, and that the numeric-only branch never emits a leading `=` (P7 guard).

---

## Ex 9 — Intended ERROR (implicit multiplication)

Input: `id=9`, `function="2x"`, two integrals over [0,1]×[0,1].

Expected render item:
- `kind`: `"error"`
- `exercise_label`: `"9"`
- `message`: generic Spanish ERROR marker
  (`"ERROR: no se pudo procesar este ejercicio."`)

Reason: `2x` relies on implicit multiplication, which is a REJECTED transformation
(see 60_expression_cleaner_v3_2.md). The cleaner does not guess `2*x`, so the
expression cannot be parsed and the exercise becomes an ERROR.

Purpose: confirms that an intended-failure case produces a clean ERROR item and
does not halt the pipeline. **This passing is a success, not a bug.** It is the
primary guard distinguishing "the cleaner correctly refuses to guess" from "the
solver is broken."

---

## Rounding Rule Guard (formatter contract)

These assert ROUND_HALF_UP at the formatter, independent of any exercise:
- `format(2.5, 0)` → `"3"`        (banker's rounding would give `"2"`)
- `format(0.125, 2)` → `"0.13"`   (banker's rounding would give `"0.12"`)
- `format(0.12345, 4)` → `"0.1235"`

Purpose: a passing golden set must also pass these, so a round-half-to-even
implementation cannot slip through. See the Decimal Formatting Rule in
85_render_adapter_and_jinja2_spec_v3_2.md.

---

## Acceptance Rule

A Phase 1 implementation is acceptance-correct for these cases when:
1. Ex 1, Ex 7, Ex 5, Ex 6 render items match the values above (field-for-field for
   the fields listed).
2. Ex 9 renders as a `kind:"error"` item with the generic marker.
3. The formatter passes the Rounding Rule Guard above.
4. The full 46 run completes without halting (the ERROR in Ex 9 does not stop
   processing of Ex 10).
