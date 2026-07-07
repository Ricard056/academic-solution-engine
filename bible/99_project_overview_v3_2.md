# Project Overview — v3.2

> **v3.2 changes**: bible-file table updated to v3.2 filenames; Component
> Aggregation noted as a distinct pipeline stage (not a solver) under Key Design
> Decisions (P1). v3.1 baseline: added 47_golden_expected; formatting-ownership
> design decision noted.

## What Is This Project

A command-line tool that converts structured JSON exercise definitions into
professionally formatted PDF solution manuals for university calculus courses.
The system uses symbolic computation (SymPy) to solve exercises and Jinja2/LaTeX
templates to render results.

## Why It Exists

This project was created to support the mathematics department at ITSON
university. As an auxiliary professor, the author needed a way to:

1. **Generate solution manuals quickly** — When new homework assignments are
   designed, the department needs answer keys immediately
2. **Maintain consistency** — All solutions follow the same professional format
3. **Enable verification** — The generated solutions serve as references that
   humans still verify

The original proof-of-concept (Iteration 2) successfully generated PDFs for
integral exercises but became unmaintainable when expanding to additional solver
types. The LaTeX output was hardcoded rather than templated, making modifications
error-prone.

This iteration (v3) restarts with a modular architecture using Jinja2 templates,
enabling easy addition of new solver types, configurable output visibility, and
separation of computation logic from presentation. v3.1 hardened the spec
contracts before fresh code generation; v3.2 closes the remaining contract gaps
(component aggregation ownership, structural validation matrix, units rendering,
and golden coverage) identified in audit.

## What Problem It Solves

**Before**: Creating a 40-exercise solution manual required manual LaTeX writing
or unreliable copy-paste from computational tools.

**After**: Define exercises in JSON → run one command → get PDF solution manual.

## Current Scope

- **Single user**: The author (profesor auxiliar)
- **Single institution**: ITSON mathematics department
- **Course focus**: Calculus 3 (multivariable calculus)
- **Phase 1 solver**: Integrals (see 90_phase1_scope_v3_2.md)
- **Future solvers**: Gradients, Derivatives (see 09_deferred_solvers_v3_2.md)
- **No frontend**: Command-line only
- **No multi-user**: No authentication, no web interface

## Success Criteria (MVP)

1. Process the existing Calculus 3 assignments (20-40 exercises each)
2. Generate PDFs that match or exceed Iteration 2 quality
3. Match the render-model values in 47_golden_expected_v3_2.md for the named exercises
4. Add a new solver type without modifying existing solvers or templates
5. Processing time < 10 seconds for 40 exercises

## Non-Goals (Explicitly Out of Scope)

- Real-time solving or web API
- Student-facing interface
- Automatic difficulty assessment
- Step-by-step solution display (reserved for future)
- Multi-language support beyond es-MX
- Commercial deployment (portfolio/hobby project)

## Future Possibilities (Not MVP)

- Additional solvers: derivatives, gradients, vectors, series
- Frontend for JSON creation
- Integration with learning management systems

## Key Design Decisions

1. **JSON as single input format** — Easy for humans to write, easy for AI to generate
2. **Extended JSON preserves input** — Can re-run, debug, or use as template
3. **Extended JSON is pure data** — no formatted decimals, no units; formatting is
   owned by the Render Adapter so re-runs with new display settings reformat correctly
4. **Three-level display hierarchy** — Flexibility without per-exercise configuration burden
5. **Solvers are independent modules** — Adding new solvers doesn't touch existing ones
6. **Component Aggregation is a distinct pipeline stage** — It runs after the
   per-exercise solver and before Extended JSON; it computes cross-exercise
   component totals. This does NOT violate decision #5: solvers stay per-exercise,
   and aggregation is a separate stage, not solver code. See 90_phase1_scope_v3_2.md.
7. **coordinate_system is computationally passive in Phase 1** — author supplies the Jacobian
8. **Closed render-model contract + StrictUndefined** — missing render fields fail loudly, not silently
9. **Fail gracefully** — One bad exercise doesn't stop the entire assignment

## Bible Files Structure

| File | Responsibility |
|------|---------------|
| 99_project_overview_v3_2 (this file) | Project context and vision |
| 90_phase1_scope_v3_2 | What's in/out for current development phase |
| 85_render_adapter_and_jinja2_spec_v3_2 | Adapter contract, formatting ownership, templates |
| 80_json_input_spec_v3_2 | JSON input structure, examples, syntax |
| 75_json_output_spec_v3_2 | Extended JSON output schema (canonical, pure data) |
| 70_display_system_v3_2 | Display hierarchy, merge strategy, auto-inference |
| 65_id_system_v3_2 | Exercise identification concepts |
| 60_expression_cleaner_v3_2 | Mathematical expression preprocessing |
| 55_file_handling_v3_2 | File operation safety rules |
| 50_config_defaults_global_v3_2.json | Machine-readable default display values |
| 49_golden_expected_symbolic_v3_2 | Expected render-model values for the symbolic contract (Phase 1.1) |
| 48_test_data_symbolic_v3_2.json | Symbolic-contract test data (Phase 1.1) |
| 47_golden_expected_v3_2 | Expected render-model values for acceptance |
| 46_test_data_integral_edge_cases_v3_2.json | Edge-case test data |
| 45_test_data_T21_v3_2.json | Real assignment test data |
| 09_deferred_solvers_v3_2 | Gradient/derivative specs (future reference) |
| 08_deferred_features_v3_2 | Future feature notes (show_steps, show_all, interpretations, etc.) |
