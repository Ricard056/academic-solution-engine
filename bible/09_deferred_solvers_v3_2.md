# Deferred Solvers Reference — v3.2

> **Status**: The **gradient** section is SUPERSEDED by the active Phase 2A bibles
> (91/80/75/85/70/65/60 + acceptance 51/52) — see the neutralized section below. The
> **derivative** section remains deferred, preserved for future implementation.
> **When to use**: For the derivative solver, when starting a later phase. For
> gradient, use the Phase 2A bibles, not this file.
> **v3.2 changes**: references/version label only. Content unchanged.
> **Phase 2A**: gradient section neutralized (superseded pointer); derivative
> section unchanged.

---

## Gradient Solver — SUPERSEDED (see Phase 2A bibles)

> **This section is neutralized.** The gradient solver is now active in Phase 2A;
> its authoritative contract lives in the active bibles, not here:
> - Scope: `91_phase2a_gradient_scope_v3_2.md`
> - Input: `80_json_input_spec_v3_2.md` ("Gradient Solver — Exercise Examples")
> - Output/results: `75_json_output_spec_v3_2.md` ("Results Structure — Gradient")
> - Render/display/template: `85_render_adapter_and_jinja2_spec_v3_2.md`,
>   `70_display_system_v3_2.md`
> - Cleaner/grouping: `60_expression_cleaner_v3_2.md`, `65_id_system_v3_2.md`
> - Acceptance: `51_test_data_gradient_v3_2.json`, `52_golden_expected_gradient_v3_2.md`
>
> **Choices from the old draft that Phase 2A OVERRODE — do NOT follow them here:**
> - `numeric_value = magnitude` → Phase 2A uses top-level `numeric_value: null`
>   plus a `results.gradient` sub-object (authoritative for rendering).
> - Angle default degrees / `angle_unit` → Phase 2A is **radians only**; no
>   `angle_unit` field.
> - `point`/`vector` "already numeric" → Phase 2A uses **cleaned string** entries.
> - `show_theta_min` → deferred (not in Phase 2A).
> - Ad-hoc `display_gradient` field list → replaced by the six `show_gradient_*`
>   flags standardized in 70/50.

---

## Derivative Solver

### Exercise Input Examples

#### Single Output
```json
{
  "id": 1,
  "type": "derivative",
  "function": "x^2 * y",
  "variable": "x",
  "order": 1
}
```

#### Multiple Outputs (using id_output)
```json
[
  {
    "id": 2,
    "id_letter": "a",
    "id_output": 1,
    "type": "derivative",
    "function": "x^2 * y",
    "variable": "x"
  },
  {
    "id": 2,
    "id_letter": "a",
    "id_output": 2,
    "type": "derivative",
    "function": "x^2 * y",
    "variable": "y"
  }
]
```

### Derivative Results Structure (Extended JSON)
```json
"results": {
  "problem_latex": "\\frac{\\partial z}{\\partial x}",
  "solution_latex": "2xy",
  "numeric_value": null
}
```

### Derivative Solver Required Fields
- `function` (string)
- `variable` (string) — the variable to differentiate with respect to

---

## Future Solvers (Conceptual)

These have no specification yet:

- **Vector solver**: Vector operations, cross products, etc.
- **Series solver**: Taylor/Maclaurin series, convergence tests

> **SUPERSEDED as current registration guidance (Phase 2B-M).** The checklist
> below is retained only as historical planning context. Do not use it as the
> process for adding a solver. The exhaustive current bounded registration path
> is in `92_phase2bm_multisolver_scope_v3_2.md`; supported structural modes are
> declared in the single table owned by `65_id_system_v3_2.md`; presentation-
> contract reuse and any new render-kind/fragment/registry registration are
> controlled by `85_render_adapter_and_jinja2_spec_v3_2.md`. A future solver
> reuses an existing presentation contract when it fits and adds a fragment and
> registry entry only for a genuinely new presentation contract.
>
> **Historical checklist (non-controlling):**
1. Create exercise examples in this file or a new deferred file
2. Define results structure following the same pattern as above (raw floats +
   LaTeX; adapter owns formatting)
3. Add solver-specific display fields if needed
4. Add the solver's render-item shape to the closed render-model contract (85)
5. Create Jinja2 template for the solver
6. No existing solver code needs modification (solver independence principle)
