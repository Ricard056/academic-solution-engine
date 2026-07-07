# Render Adapter and Jinja2 Template Specification — v3.2

> **Status**: Phase 1 required bible file.
> **Purpose**: Defines the bridge between Extended JSON and Jinja2 templates.
> **v3.2 changes**: units wrapped in `\mathrm{...}` by the template, render-model
> `units` stays a plain token (P4); `output_group` template uses the standard
> three-case conditional, no leading `=` (P7); `show_input` declared
> standard-items-only (P8); `total_latex` always renders under
> `show_component_total` (P9); decimal formatting mandates `decimal.ROUND_HALF_UP`
> (P12); aggregation boundary noted (P1). v3.1 baseline: adapter owns all decimal
> formatting and unit derivation; document labels via explicit maps; closed render
> contract; StrictUndefined in dev/test; component display fields wired.
> **Phase 1.1 amendment**: Numeric-Availability Resolution — symbolic-only
> results (`numeric_value: null`) resolve `show_numeric` off in the adapter.

---

## Core Principle

The solver produces mathematical results (LaTeX strings + raw floats).
The render adapter prepares display-ready objects (formatted decimals, units, labels).
Jinja2 only renders those objects into LaTeX.

Jinja2 must NOT perform mathematical logic, display merging, sorting, grouping,
component combination, quantity inference, unit inference, decimal formatting,
or error interpretation.

A complicated adapter is acceptable. A complicated Jinja2 template is not.

---

## Pipeline Position

```
Input JSON
→ Validation
→ Expression Cleaner
→ Integral Solver
→ Component Aggregation
→ Extended JSON
→ Render Adapter
→ Jinja2 LaTeX Template
→ PDF
```

The Extended JSON remains the canonical processed DATA format (no formatted
decimals, no units — see 75_json_output_spec_v3_2.md). The render model is a
temporary PRESENTATION model used only for template rendering.

---

## Render Adapter Function

The implementation should expose a function equivalent to:

```python
build_render_model(extended_json: dict, defaults: dict) -> dict
```

- `extended_json`: the canonical processed data (see 75).
- `defaults`: the hardcoded display defaults template (see 50_config_defaults_global_v3_2.json).

The returned object is passed directly into the Jinja2 template.

---

## Render Adapter Responsibilities

The adapter receives Extended JSON and returns a render model. It must:

1. Build document metadata (see "Document Label Derivation" below):
   - title
   - subtitle
   - course
   - assignment_label

2. Sort exercises by:
   - `id`
   - `id_letter`
   - `id_component`
   - `id_output`

3. Build display-only labels:
   - `id=1` → `"1"`
   - `id=1`, `id_letter="a"` → `"1.a"`
   - `id_output` appears in sublabels such as `"Resultado 1"`, not as a replacement for `id`
   - `id_component` appears in component lines, not in the main exercise label

4. Resolve display settings using the required hierarchy:
   - hardcoded defaults
   - `display_default`
   - `display_integral`
   - `display_override`

5. Resolve quantity label:
   - `display_override.quantity_label` if present
   - else exercise `quantity` if present
   - else inferred `quantity`

6. Derive units (see "Unit Derivation Rule" below).

7. Produce all formatted decimals (see "Decimal Formatting Rule" below).

8. Create render item types:
   - `standard`
   - `component_group`
   - `output_group`
   - `error`

9. Never omit failed exercises:
   - failed exercises become `kind="error"`
   - the PDF shows a generic ERROR marker
   - the pipeline continues

> **Aggregation boundary (v3.2):** the `results.component` object (`total_value`,
> `total_latex`, `operation`, `operation_latex`) is produced upstream by the
> Component Aggregation stage (see 90_phase1_scope_v3_2.md). The adapter consumes it
> as-is; it never computes symbolic combinations or totals. It only formats their
> decimals and assembles the `component_group` render item.

---

## Document Label Derivation (Authoritative)

The adapter builds `document` from `metadata` as follows:

| Render field | Source / rule |
|---|---|
| `assignment_label` | `<type_label> <number>`, where `type_label` comes from the type map below (e.g. type `"hw"`, number `21` → `"Tarea 21"`) |
| `title` | `assignment_label` upper-cased (`"TAREA 21"`) |
| `subtitle` | fixed Phase 1 string `"Solucionario"` |
| `course` | course display map below, falling back to `metadata.course` verbatim if unmapped |

**Assignment type map** (`metadata.assignment.type` → display label):

| `type` token | label |
|---|---|
| `hw` | Tarea |
| `exam` | Examen |
| `quiz` | Quiz |
| `test` | Prueba |
| `project` | Proyecto |

**Course display map** (`metadata.course` → display):

| input | display |
|---|---|
| `Calculus 3` | Cálculo III |

Unmapped values fall back to the raw input string. The adapter never fails on an
unknown type; it uses the token verbatim as the label.

---

## Adapter-Owned Formatting (Authoritative)

The solver produces no formatted decimals and no units. The adapter produces all
of them, because only the adapter has resolved `decimal_places`, `quantity`, and
`default_units`.

### Decimal Formatting Rule

Given a raw float `v` and resolved integer `decimal_places = n`, the adapter
produces a fixed-point string with exactly `n` digits after the decimal point,
using **round-half-up**. This MUST be implemented with `decimal.Decimal` and
`ROUND_HALF_UP` (e.g.
`Decimal(str(v)).quantize(Decimal(1).scaleb(-n), rounding=ROUND_HALF_UP)`).
Do NOT use `round()` or `f"{v:.nf}"`: both use round-half-to-even (banker's
rounding) and will silently violate this contract. Trailing zeros are kept
(e.g. `0.25 → "0.2500"` at n=4).

Render-model decimal fields and their sources:

| Render field | Source float | Notes |
|---|---|---|
| `decimal_string` | `results.numeric_value` | per item / component / output |
| `total_decimal_string` | `results.component.total_value` | component groups only |
| `operation_decimal_string` | each component's `numeric_value` | join formatted parts with `" + "` (Phase 1 sum) |

When `results.numeric_value` is `null`, no decimal is produced — see
Numeric-Availability Resolution below.

### Numeric-Availability Resolution

In the render model, `show_numeric` is a **resolved visibility flag**:
`author_requested_numeric AND numeric_value_exists`. It is not the raw author
preference. When `results.numeric_value` is `null` (symbolic-only success, see
75_json_output_spec_v3_2.md), the adapter resolves that render item's
`show_numeric` to `false` — regardless of the merged display configuration —
and populates `decimal_string` with the empty string to satisfy the closed
contract. The template never branches on nullness; it only reads the
already-resolved flags. This applies per output member inside `output_group`
items. Component groups never reach this rule: a symbolic-only member
invalidates the group upstream (see 90_phase1_scope_v3_2.md). If the author
also sets `show_symbolic: false`, the item renders an empty result body — the
same already-legal outcome as authored `show_symbolic: false` +
`show_numeric: false` (see 70_display_system_v3_2.md).

### Unit Derivation Rule

Applied in this order; first match wins:

1. If `display_override.units_override` is present → use it verbatim.
2. Else by resolved `quantity_label`:
   - `A` → `default_units + "^2"`
   - `V` → `default_units + "^3"`
   - anything else (`R`, `M`, `Q`, `T`, custom) → `default_units` (no exponent)
3. `default_units` comes from the resolved display config (default `"u"`).

**Rendering note (template responsibility):** the render-model `units` value is a
plain token (`"u"`, `"u^2"`, `"kg"`, `"C"`), NOT pre-wrapped LaTeX. The template
wraps it in `\mathrm{...}` so multi-letter and named units render upright instead of
as italic variable products. Single-letter generic units are unaffected. Authors who
need custom spacing/markup may pass LaTeX in `units_override`; it is still wrapped.

---

## Render Model Shape

```json
{
  "document": {
    "title": "TAREA 21",
    "subtitle": "Solucionario",
    "course": "Cálculo III",
    "assignment_label": "Tarea 21"
  },
  "items": [
    {
      "kind": "standard",
      "exercise_label": "1.a",
      "quantity_label": "R",
      "show_input": false,
      "show_symbolic": true,
      "show_numeric": true,
      "show_quantity": true,
      "problem_latex": "\\int ...",
      "solution_latex": "\\frac{23}{15}",
      "decimal_string": "1.5333",
      "units": "u"
    }
  ]
}
```

---

## Render Contract Closure Rule

The render model is a **closed contract**: a template may read a field only if
that field is declared on the corresponding render item below. The adapter MUST
populate every declared field on every item it emits — no field is optional at
render time. Inheritance and "missing means default" are resolved INSIDE the
adapter; the model handed to Jinja2 is already fully resolved.

---

## Jinja2 Undefined Policy

Templates are rendered with `undefined=StrictUndefined` during development and
testing. A reference to a missing render-model field raises an error rather than
rendering empty. This converts "silently dropped label/decimal" bugs into
immediate, locatable failures. Production may relax this only after the contract
is verified against the golden reference (see 90_phase1_scope_v3_2.md and
47_golden_expected_v3_2.md).

---

## Required Render Item Types

### 1. Standard Item

Used for normal exercises without `id_component` or `id_output`.

```json
{
  "kind": "standard",
  "exercise_label": "2.b",
  "quantity_label": "V",
  "show_input": true,
  "show_symbolic": true,
  "show_numeric": true,
  "show_quantity": true,
  "problem_latex": "...",
  "solution_latex": "64\\pi",
  "decimal_string": "201.0619",
  "units": "u^3"
}
```

### 2. Component Group

Used when multiple exercises share the same `id` and `id_letter` but have
different `id_component` values. Components combine mathematically;
Phase 1 operation: `sum`.

```json
{
  "kind": "component_group",
  "exercise_label": "5",
  "quantity_label": "A",
  "units": "u^2",

  "show_quantity": true,
  "show_numeric": true,
  "show_component_total": true,
  "show_component_symbolic": true,
  "show_component_operation": true,

  "total_latex": "1",
  "total_decimal_string": "1.0000",
  "operation_latex": "\\frac{1}{2} + \\frac{1}{2}",
  "operation_decimal_string": "0.5000 + 0.5000",

  "components": [
    {
      "id_component": 1,
      "quantity_label": "A",
      "units": "u^2",
      "show_component_quantity": true,
      "show_numeric": true,
      "problem_latex": "...",
      "solution_latex": "\\frac{1}{2}",
      "decimal_string": "0.5000"
    },
    {
      "id_component": 2,
      "quantity_label": "A",
      "units": "u^2",
      "show_component_quantity": true,
      "show_numeric": true,
      "problem_latex": "...",
      "solution_latex": "\\frac{1}{2}",
      "decimal_string": "0.5000"
    }
  ]
}
```

**Component-line symbolic policy:** Per-component lines always show
`solution_latex`; the global `show_symbolic` flag does not gate them, because the
breakdown's purpose is to show each part's exact value. Symbolic/decimal
*combination* visibility in the Total line is controlled by
`show_component_symbolic` and `show_component_operation`. The combined
`total_latex` itself always renders when `show_component_total` is true; it is not
gated by the global `show_symbolic`. This intentional difference from `standard`
items is by design.

**Group-level display resolution (Phase 1):** Group-level display fields on a
`component_group` — `show_quantity`, `show_numeric`, the four `show_component_*`
flags, and the `decimal_places` used for `total_decimal_string` and
`operation_decimal_string` — resolve from the merged
hardcoded/`display_default`/`display_integral` config for the `(id, id_letter)`
group; per-component `display_override` is not honored for group-level fields in
Phase 1.

### 3. Output Group

Used when multiple exercises share the same `id` and `id_letter` but have
different `id_output` values. Outputs are independent and do NOT combine.

```json
{
  "kind": "output_group",
  "exercise_label": "6",
  "outputs": [
    {
      "id_output": 1,
      "output_label": "Resultado 1",
      "quantity_label": "A",
      "units": "u^2",
      "show_quantity": true,
      "show_symbolic": true,
      "show_numeric": true,
      "problem_latex": "...",
      "solution_latex": "1",
      "decimal_string": "1.0000"
    },
    {
      "id_output": 2,
      "output_label": "Resultado 2",
      "quantity_label": "A",
      "units": "u^2",
      "show_quantity": true,
      "show_symbolic": true,
      "show_numeric": true,
      "problem_latex": "...",
      "solution_latex": "1",
      "decimal_string": "1.0000"
    }
  ]
}
```

### 4. Error Item

Used for any exercise whose `results.status == "error"`, that fails before
results generation, or whose component/output group has a structural problem
(sequence gap, duplicate/mixed IDs, conflicting component quantity, or invalid
`component_operation`).

```json
{
  "kind": "error",
  "exercise_label": "9",
  "message": "ERROR: no se pudo procesar este ejercicio."
}
```

---

## Template Responsibilities

Templates may:

- loop over prepared items
- show/hide sections based on already-resolved boolean fields
- render LaTeX strings
- format document structure

Templates must NOT:

- call SymPy
- compute results
- merge display settings
- infer quantity
- infer coordinate system
- format decimals
- derive units
- group components
- group outputs
- sort exercises
- inspect raw input or Extended JSON fields beyond prepared render fields

> **Phase 1 `show_input` scope:** `show_input` (and `problem_latex` rendering)
> applies ONLY to `standard` render items. `component_group` and `output_group`
> items never render problem setups in Phase 1; setting `show_input:true` on a
> grouped exercise has no effect (by design, not an error).

---

## Required Templates for Phase 1

```
templates/base.tex.j2
templates/solucionario_integrales.tex.j2
```

Optional after MVP:

```
templates/tarea_integrales.tex.j2
```

---

## Minimal `base.tex.j2`

```jinja2
\documentclass[12pt]{article}

\usepackage[letterpaper, margin=1in]{geometry}
\usepackage{amsmath, amssymb}
\usepackage{enumitem}
\usepackage{xcolor}

\setlength{\parindent}{0pt}
\setlength{\parskip}{6pt}

\begin{document}

{% block body %}{% endblock %}

\end{document}
```

---

## Minimal `solucionario_integrales.tex.j2`

```jinja2
{% extends "base.tex.j2" %}

{% block body %}

\begin{center}
{\Large \textbf{ {{ document.title }} }}\\
{\large {{ document.subtitle }}}\\
{% if document.course %}{{ document.course }}{% endif %}
\end{center}

\vspace{0.5cm}

\section*{Resultados}

{% for item in items %}

{% if item.kind == "error" %}
\textbf{ {{ item.exercise_label }}) } \textcolor{red}{ {{ item.message }} }

{% elif item.kind == "standard" %}
\textbf{ {{ item.exercise_label }}) }

{% if item.show_input %}
\[
{{ item.problem_latex }}
\]
{% endif %}

{% if item.show_symbolic and item.show_numeric %}
\[
{% if item.show_quantity %}{{ item.quantity_label }} = {% endif %}{{ item.solution_latex }} = {{ item.decimal_string }}\, \mathrm{ {{ item.units }} }
\]
{% elif item.show_symbolic %}
\[
{% if item.show_quantity %}{{ item.quantity_label }} = {% endif %}{{ item.solution_latex }}\, \mathrm{ {{ item.units }} }
\]
{% elif item.show_numeric %}
\[
{% if item.show_quantity %}{{ item.quantity_label }} = {% endif %}{{ item.decimal_string }}\, \mathrm{ {{ item.units }} }
\]
{% endif %}

{% elif item.kind == "component_group" %}
\textbf{ {{ item.exercise_label }}) }

{% for component in item.components %}
\[
\text{Componente {{ component.id_component }}: }
{% if component.show_component_quantity %}{{ component.quantity_label }} = {% endif %}
{{ component.solution_latex }}
{% if component.show_numeric %} = {{ component.decimal_string }}{% endif %}
\, \mathrm{ {{ component.units }} }
\]
{% endfor %}

{% if item.show_component_total %}
\[
\text{Total: }
{% if item.show_quantity %}{{ item.quantity_label }} = {% endif %}
{% if item.show_component_symbolic %}{{ item.operation_latex }} = {% endif %}
{{ item.total_latex }}
{% if item.show_component_operation %} = {{ item.operation_decimal_string }}{% endif %}
{% if item.show_numeric %} = {{ item.total_decimal_string }}{% endif %}
\, \mathrm{ {{ item.units }} }
\]
{% endif %}

{% elif item.kind == "output_group" %}
\textbf{ {{ item.exercise_label }}) }

{% for output in item.outputs %}
{% if output.show_symbolic and output.show_numeric %}
\[
\text{ {{ output.output_label }}: }{% if output.show_quantity %}{{ output.quantity_label }} = {% endif %}{{ output.solution_latex }} = {{ output.decimal_string }}\, \mathrm{ {{ output.units }} }
\]
{% elif output.show_symbolic %}
\[
\text{ {{ output.output_label }}: }{% if output.show_quantity %}{{ output.quantity_label }} = {% endif %}{{ output.solution_latex }}\, \mathrm{ {{ output.units }} }
\]
{% elif output.show_numeric %}
\[
\text{ {{ output.output_label }}: }{% if output.show_quantity %}{{ output.quantity_label }} = {% endif %}{{ output.decimal_string }}\, \mathrm{ {{ output.units }} }
\]
{% endif %}
{% endfor %}

{% endif %}

{% endfor %}

{% endblock %}
```

---

## Phase 1 Rendering Target

A compact solution manual similar to the old T21 PDF:

- title
- subtitle
- list of numbered results
- optional integral setup if `show_input` is true (standard items only)
- exact result if `show_symbolic` is true
- decimal result if `show_numeric` is true
- quantity label controlled by `show_quantity`
- units displayed after result
- generic ERROR marker for failed exercises

---

## Design Rule

The render adapter should be explicit and boring. The Jinja2 templates should
remain small and predictable. All ambiguity is resolved in the adapter so the
template never has to make a decision the data did not already make.
