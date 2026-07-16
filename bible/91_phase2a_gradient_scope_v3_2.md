# Phase 2A Scope Lock — Gradient — v3.2

> **Purpose**: Defines exactly what is IN and OUT of **Phase 2A** (the gradient
> solver). Parallel to `90_phase1_scope_v3_2.md` (Phase 1, integrals), which
> remains **frozen**. If something is not listed under "IN SCOPE", it does not
> exist for Phase 2A.
> **Relationship to Phase 1**: Phase 2A is purely additive. The integral solver,
> its acceptance (46/47), and the symbolic-only contract (48/49) are unchanged.
> Adding the gradient solver must not modify existing solvers or templates
> (project overview 99, success criteria #4/#5).
> **Phase 2B-M note**: exactly three single-solver-document clauses in this file
> (the single-solver rendering restriction, the document-level mixed-type hard
> stop, and the mixed-document deferral — each individually annotated below) are
> SUPERSEDED by `92_phase2bm_multisolver_scope_v3_2.md`. Everything else in this
> file remains authoritative Phase 2A history, including all gradient
> mathematics, validation, standard-items-only capability, outputs, display,
> Extended JSON behavior, and the frozen 51/52 acceptance.

---

## IN SCOPE — Phase 2A

### Solver
- **Gradient solver** for scalar fields, **2-variable `f(x, y)` only**.
  - The 2-variable limit is an explicit **Phase 2A restriction, not a permanent
    solver limitation.** Input/point/vector contracts are written so they can
    generalize to 3D later. When 3D lands (2B), directions come from **vectors
    first**, not a single `angle`; `angle` and `theta_max` are **2D-only**.
- **Cartesian only.** `coordinate_system` is not consulted for gradient in 2A;
  polar/cylindrical/spherical gradients are deferred.
- **Fixed variable order `(x, y)`** in 2A. (A future explicit `variables` field
  for 3D ordering is deferred — see OUT OF SCOPE.)

### Output set (full Tarea 12 set)
Every output is independently show/hide-able (see Display, below):

| Output | Meaning |
|---|---|
| `∇f(x, y)` | symbolic gradient vector |
| `∇f(P)` | gradient evaluated at the point |
| `\|∇f(P)\|` | magnitude (scalar) |
| `û` | unit vector of the chosen direction |
| `D_u f` | directional derivative (scalar) |
| `theta_max` | angle of steepest ascent (2D scalar, **radians**) |

### Direction modes (how a direction is supplied)
One direction source per exercise, all four supported in 2A:

1. **Two points** — `initial_point` + `final_point`; direction = `final − initial`,
   then normalized. The **evaluation point is `initial_point`**.
2. **Point + vector** — `point` + `vector`; the vector is normalized by the solver.
3. **Point + angle** — `point` + `angle` (a **radians** math string, e.g. `"pi/4"`);
   `û = ⟨cos θ, sin θ⟩`.
4. **Steepest ascent** — `point` + `direction_source: "max_ascent"`; the direction
   is `∇f(P)` itself, so `û ∥ ∇f(P)` and `D_u f == |∇f(P)|`.

**Point-only / no-direction mode is supported.** When no direction source is
given, the solver still returns `∇f`, `∇f(P)`, `|∇f(P)|`, and `theta_max`; `û`
and `D_u f` are simply absent, and the adapter resolves their `show_*` flags off.

### Angle units
- **Radians only in Phase 2A.** `angle` is a cleaned radians math string.
- **No `angle_unit` field in 2A.** Degree **input** and degree **display** are a
  matched pair, both deferred to 2B.

### Coordinates as strings
Point/vector entries are **sympy-parseable strings** (`"0"`, `"sqrt(pi)"`,
`"pi/4"`), each a 2-element array — the same convention as integral bounds. They
are cleaned like any math field (see 60).

### Symbolic-only tolerance (per piece)
A symbolic point or a symbolic function parameter yields symbolic outputs. Each
scalar/vector piece with no finite value carries `*_value: null` (its `*_latex`
is the exact symbolic form). This reuses the Phase 1.1 numeric-availability
contract, applied **per piece** (see 75/85). Divergent/undefined results
(`oo`/`-oo`/`zoo`/`nan`, or a domain error at the point) remain **errors**, never
symbolic successes.

### Formatting ownership (unchanged from Phase 1)
- Solver = LaTeX strings + raw floats (or `null`), including per-piece vector
  component arrays. No rounding, no units.
- Render Adapter = all formatted decimals (including assembled decimal vectors)
  and any units. Decimals MUST use `decimal.Decimal` + `ROUND_HALF_UP`.
- Template = render only; StrictUndefined in dev/test.
- Extended JSON carries NO formatted decimals and NO units.

### Display
- `display_gradient` is a **top-level, solver-specific** display block (parallel
  to `display_integral`); it is **not** placed inside exercises.
- Per-exercise overrides use the existing `display_override`.
- Merge chain: **hardcoded (50) → `display_default` → `display_gradient` →
  `display_override`**.
- Six gradient flags, default `true`: `show_gradient`, `show_gradient_evaluated`,
  `show_magnitude`, `show_unit_vector`, `show_directional_derivative`,
  `show_theta_max` (defaults in 50; see 70).
- **Gradient outputs are unitless in 2A** — no unit derivation, no `quantity`
  inference for gradient; `default_units`/`units_override`/`quantity_label` do
  not apply to gradient items.

### Extended JSON / results contract
- Top-level `numeric_value` is **`null`** for every gradient success (the headline
  is vector-valued; it has no single scalar). This is a SUCCESS, not an error.
- `results.gradient` is the **authoritative** sub-object for rendering (see 75).
- `solution_latex` is a **non-rendered mirror** of `results.gradient.gradient_latex`.

### Render / templates
- A **new render item kind `"gradient"`** with **per-piece Numeric-Availability
  Resolution** (see 85).
- **Canonical vector delimiter `\left\langle … \right\rangle`**, used by both the
  solver (symbolic `*_latex`) and the adapter (decimal vectors).
- A **new gradient template** and **`render/latex.py` routing** are specified in 85;
  the integral template is not modified. *(The template file and the routing code
  are created in the implementation milestone, not the spec milestone.)*
- **Single-solver documents only in 2A** — a document contains gradient exercises
  or integral exercises, not both. Mixed-solver documents are deferred to 2B.

  > **SUPERSEDED by 92 (Phase 2B-M):** mixed-solver documents are now
  > supported; rendering uses the neutral shell + item-fragment contract of 85.

### ID / grouping / aggregation
- Gradient supports **standard items only** in 2A.
- A gradient member carrying `id_component` **or** `id_output` makes the whole
  `(id, id_letter)` group a **group-level ERROR** (`kind:"error"`). This is a
  Phase 2A restriction, not a permanent rule.
- **Aggregation remains integral-only.** The Component Aggregation stage never
  runs for gradient (gradient has no `id_component`).
- `id`/`id_letter` labeling (`1.a`, `1.b`) works exactly as in Phase 1.

### Validation matrix (gradient)
- **Document-level (hard stop)** — the Phase 1 triggers (missing required
  top-level fields, empty `exercises`, non-object input, any exercise missing
  `id`), plus one Phase 2A trigger:
  - the document mixes `type: "gradient"` with any other exercise type —
    single-solver documents only in 2A; the template router is undefined for
    mixed documents, so this is a hard stop, not a per-exercise error.

    > **SUPERSEDED by 92 (Phase 2B-M):** the document-tier mixing hard stop is
    > removed; group-tier D2/supported-mode rules (65) govern mixed documents.
- **Exercise-level (render that one exercise as `kind:"error"`)**:
  - `type` is `"gradient"` but `function` is missing/not a string;
  - no evaluation point (neither `point` nor a complete
    `initial_point`+`final_point` pair);
  - `point` supplied together with `initial_point`/`final_point`, or an
    incomplete two-points pair (one of `initial_point`/`final_point` without
    the other);
  - more than one direction source: a complete `initial_point`+`final_point`
    pair, `vector`, `angle`, or `direction_source: "max_ascent"`; any
    combination of two or more is an exercise-level ERROR;
  - a point/vector entry or `angle` that is not a string (raw JSON numbers are
    rejected — coordinates are strings);
  - a `point`/`initial_point`/`final_point`/`vector` array whose length is not
    exactly 2 (Phase 2A is 2-variable);
  - a supplied point/vector/angle cannot be cleaned or parsed;
  - a zero-length direction (`final == initial`, `vector == ⟨0, 0⟩`, or
    `direction_source: "max_ascent"` when `∇f(P) == ⟨0, 0⟩`) — cannot be
    normalized;
  - the gradient cannot be evaluated at the point (domain error → non-finite).
- **Group-level (render the whole `(id, id_letter)` group as `kind:"error"`)**:
  - a gradient member carries `id_component` or `id_output` (2A restriction).

> **Zero-gradient note:** if `∇f(P) = ⟨0, 0⟩`, `theta_max` is undefined. Under
> `direction_source: "max_ascent"` this is an exercise ERROR (a direction is
> required but undefined — see matrix). In every other mode the exercise remains
> a SUCCESS and the `theta_max` piece is simply **omitted** (not-applicable
> absence, exactly like `û`/`D_u f` without a direction — see 75).

---

## OUT OF SCOPE — deferred to Phase 2B (or later)

- **3-variable `f(x, y, z)` gradients** (and generic n-variable). When added,
  direction comes from **vectors first**, not a single `angle`; `angle`/`theta_max`
  stay 2D-only.
- **Degree input** (`angle_unit: "degrees"`) and **degree display** of `theta_max`
  (a radian/degree display toggle) — deferred together.
- **`variables` field** for explicit variable ordering (needed for 3D).
- **`interpretation`** ("Descendiendo"/"Ascendiendo") — an author-filled field is a
  deferred feature (08); revisit later as solver-derived from `sign(D_u f)`.
- **`theta_min`**, **gradient units**.
- **`id_output`/`id_component` for gradient**.
- **Polar/cylindrical/spherical gradients.**
- **Mixed-solver documents** (gradient + integral in one document).

  > **SUPERSEDED by 92 (Phase 2B-M):** implemented by Phase 2B-M; no longer
  > deferred.
- **Derivative solver** (still deferred; see 09).

---

## Phase 2A Pipeline (gradient)

```
Input JSON
→ Validate                  (gradient tiers above)
→ Expression Cleaner        (function, point/vector/angle strings)
→ Gradient Solver           (per-exercise, independent; raw math only)
→ (Component Aggregation)   (integral-only; skipped for gradient)
→ Extended JSON             (numeric_value:null + results.gradient; pure data)
→ Render Adapter            (per-piece resolution, decimal formatting)
→ Jinja2/LaTeX              (gradient template, selected by router)
→ PDF
```

Each solver step is independent (99 #5): the gradient solver adds no dependency on
the integral solver, and vice versa.

---

## Acceptance (Phase 2A)

See `52_golden_expected_gradient_v3_2.md` over `51_test_data_gradient_v3_2.json`.
The Phase 1 golden set (47 over 46) and the Phase 1.1 symbolic set (49 over 48)
remain **frozen** and must continue to pass unchanged.
