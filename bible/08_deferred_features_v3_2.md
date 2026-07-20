# Deferred Features Reference — v3.2

> **Status**: NOT in Phase 1 scope. This file preserves feature ideas for future
> implementation.
> **v3.2 changes**: `component_operation` entry hardened — reserved but NOT valid
> input in Phase 1; any value other than `"sum"` is a group ERROR (P2). References
> updated to _v3_2.

---

## show_interpretations / interpretation field

**Concept**: Display interpretation text for an exercise (e.g. a sentence
explaining what the computed area/volume represents).

**Why deferred**: The `show_interpretations` flag existed in earlier specs, but
the `interpretation` exercise field was never given a schema (shape, length,
LaTeX vs plain text, placement in output). A half-defined flag is exactly the
kind of ambiguity Phase 1 v3.1 removes.

**If re-introduced**, the spec must define:
- `interpretation` field type (string? list of strings?) and whether it is LaTeX or plain text
- where it renders in each item kind (standard / component_group / output_group)
- escaping rules if plain text is allowed
- the render-model field name carrying it

**Priority**: Low. Not needed for answer-key output.

---

## show_id_component_process / show_id_component_accumulative

`show_id_component_process` displays per-component calculation steps. It depends
on step data, which is deferred (`show_steps`), so it is deferred too.

`show_id_component_accumulative` was a second name for "show the combined result,"
already covered by `show_component_total`. Removed from Phase 1 to keep one flag
per behavior. If re-introduced, it must alias `show_component_total`, not
duplicate it.

**Priority**: Low.

---

## show_steps (Step-by-Step Solution Display)

**Concept**: Display intermediate calculation steps in the PDF, not just the
final answer.

**Where it appeared**: Display scenario examples in original specs (testing
config, student config).

**Implementation notes**:
- Would be a global display field: `"show_steps": true/false`
- Each solver would need to generate step data in results
- Jinja2 template would need conditional blocks for steps
- Significant effort — each solver must define what "steps" means for its type

**Priority**: Low. Current use case (answer keys) doesn't require steps.

---

## show_all (Show Everything Shortcut)

**Concept**: A convenience flag that sets all `show_*` fields to `true` in one
line.

**Intended use**: Quick testing — verify everything renders correctly.

```json
{
  "display_default": {
    "show_all": true
  }
}
```

**Implementation**:
- ~5 lines of code: before merge, if `show_all` is true, set all `show_*` to true
- Then normal merge proceeds (so you can still override individual fields after)
- Example: `"show_all": true, "show_input": false` → everything visible except input

**Priority**: Low. Easy to add when needed. Not worth implementing before core
system works.

---

## warnings Channel

**Concept**: A structured warning channel in `processing_summary` and the render
model, surfacing non-fatal issues (e.g. `show_symbolic: false` AND
`show_numeric: false` → nothing to show for an exercise).

**Why deferred**: Phase 1 has no consumer for warnings in the PDF, and the
three-tier validation (hard stop vs ERROR item) covers fatal cases. Adding a
warning channel now would require render-model fields and template handling for
no current benefit.

**If re-introduced**, define: what generates a warning, the render-model field
that carries it, and how/where the template displays it.

**Priority**: Low.

---

## Per-Solver Default Config Files

**Concept**: Separate default config files per solver type.

```
config/display_defaults/
├── default.json          ← Global defaults (exists: 50_config_defaults_global_v3_2.json)
├── integral.json         ← Integral solver defaults (future)
├── gradient.json         ← Gradient solver defaults (future)
└── derivative.json       ← Derivative solver defaults (future)
```

**Merge chain would become**:

global defaults → solver defaults file → input display_default → input display_[solver] → display_override

**Priority**: Still deferred after Phase 2B-M. Multiple solvers are active, but
the current display contract intentionally uses one global hardcoded defaults
file plus the top-level `display_default` and `display_[solver]` blocks. Phase
2B-M expressly keeps per-solver config files out of scope (92); revisit only
through a separately approved future feature.

---

## CLAUDE.md (Project Index for IDE)

> **Current status**: COMPLETED. Root `CLAUDE.md` now exists as a navigation
> map only; it is not normative authority. The original concept, creation timing,
> and suggested content below are retained as historical planning context.

**Concept**: A single file at the project root that helps Claude (in Claude Code
or VSC) understand the project structure quickly.

**When to create**: After Phase 1 bible_files are finalized and before starting a
VSC project with bible_files in Git.

**Suggested content**:
- Project purpose (1-2 sentences)
- File list with one-line descriptions
- Phase 1 scope summary
- Key rules (input files read-only, solver independence, formatting ownership, etc.)

---

## Debug Logging System

**Concept**: Optional verbose logging for troubleshooting expression cleaning and
solver failures.

```python
DEBUG_EXPRESSION_CLEANING = False  # Toggle in main.py
```

**Priority**: Not needed for Phase 1. Generic ERROR markers in PDF are sufficient
for a single-user project.

---

## component_operation Override

**Concept**: Override the default component combination operation per exercise.

```json
{
  "id": 3,
  "id_component": 1,
  "component_operation": "product",
  "type": "integral"
}
```

**Phase 1**: Only `"sum"` is supported. `component_operation` is reserved but NOT
valid input in Phase 1 — an absent value or `"sum"` is accepted; any other value
makes the component group an ERROR (see 65_id_system_v3_2.md). Implementation of
other operations is deferred.
