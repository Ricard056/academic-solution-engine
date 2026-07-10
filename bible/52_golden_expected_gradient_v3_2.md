# Golden Expected Reference — Gradient Contract (Phase 2A) — v3.2

> **Status**: Phase 2A acceptance reference (gradient solver).
> **Purpose**: Defines expected RENDER-MODEL values for
> `51_test_data_gradient_v3_2.json`, so the gradient contract is testable.
> **Source data**: 51_test_data_gradient_v3_2.json.
> **Note**: Values describe the render model produced by
> `build_render_model(extended_json, defaults)` — i.e. AFTER adapter resolution.
> The Phase 1 golden (47 over 46) and the Phase 1.1 symbolic golden (49 over 48)
> remain **frozen** and must continue to pass unchanged.

---

## Conventions

- 51 sets the six `show_gradient_*` flags true and `decimal_places` 4, so every
  resolved `*_numeric: false` below is RESOLVED by the adapter's per-piece
  Numeric-Availability Resolution (85), never authored.
- Per piece, the render item carries `show_<piece>` (symbolic line visible) and
  `<piece>_numeric` (decimal tail visible = `show_<piece>` AND value not null).
  An **absent** piece (no direction supplied) resolves `show_<piece>: false`.
- All vector LaTeX uses the canonical delimiter `\left\langle … \right\rangle`.
- Gradient items are **unitless** in Phase 2A (no `units`, no `quantity_label`).
- **Binding vs. illustrative**: G1 pins exact numeric values (hand-verified
  Tarea 12 1a) and doubles as a ROUND_HALF_UP witness. G6 pins the symbolic
  behavior exactly. G2–G5 bind the **structural contract** (which pieces are
  present/absent and the resolved `show_*`/`*_numeric` flags); their exact decimal
  strings and exact SymPy `*_latex` are captured from the solver when the Phase 2A
  golden test is written (ROUND_HALF_UP, 4 dp) and are not hand-derived here — the
  same discipline 49 uses (the rounding rule is owned by 47).
- **Shorthand vs. byte-exact**: decimal strings and boolean flags in G1/G6 are
  **byte-exact**. LaTeX fields throughout this file are pinned as MATHEMATICAL
  content in shorthand (e.g. `⟨8, 4⟩`, `atan(1/2)`); the byte-exact SymPy strings
  are captured when the golden test is written. "Field-for-field" in the
  Acceptance Rule means byte-exact for decimals/flags and
  mathematically-equivalent for LaTeX fields.
- **Display-flag gating is unit-test scope, not golden scope**: cases exercising
  `display_override` on `show_gradient_*` (and `id_component`/`id_output` on
  gradient) live in the implementation's unit tests, mirroring how 48/49 keep
  SymPy-version-sensitive and structural cases out of the golden.

---

## G1 — id 1: two-points anchor (Tarea 12 1a, fully pinned)

Input: `function="y**2 * exp(x*y)"`, `initial_point=["0","2"]`,
`final_point=["5","7"]`. Evaluation point = `initial_point = (0, 2)`; direction =
`final − initial = ⟨5, 5⟩`.

Expected render item:
- `kind`: `"gradient"`, `exercise_label`: `"1"`
- `show_gradient`: true — `gradient_latex` = `∇f(x,y) = ⟨y³ e^{xy}, y e^{xy}(xy+2)⟩`
- `show_gradient_evaluated`: true, `gradient_evaluated_numeric`: true
  - `gradient_evaluated_latex`: `⟨8, 4⟩`
  - `gradient_evaluated_decimal`: `\left\langle 8.0000, \; 4.0000 \right\rangle`
- `show_magnitude`: true, `magnitude_numeric`: true
  - `magnitude_latex`: `4\sqrt{5}`; `magnitude_decimal_string`: `8.9443`
- `show_unit_vector`: true, `unit_vector_numeric`: true
  - `unit_vector_latex`: `⟨√2/2, √2/2⟩`;
    `unit_vector_decimal`: `\left\langle 0.7071, \; 0.7071 \right\rangle`
- `show_directional_derivative`: true, `directional_derivative_numeric`: true
  - `directional_derivative_latex`: `6\sqrt{2}`;
    `directional_derivative_decimal_string`: **`8.4853`**
- `show_theta_max`: true, `theta_max_numeric`: true
  - `theta_max_latex`: `atan(1/2)`; `theta_max_decimal_string`: `0.4636` (radians)

Purpose: proves the two-points mode, the full output set, vector decimal assembly,
and the ROUND_HALF_UP rule (`Dᵤf = 6√2 = 8.485281… → 8.4853`, not the OCR's
truncated `8.4852`).

---

## G2 — id 2: point + vector (structural)

Input: `function="x**2 * cos(x*y)"`, `point=["sqrt(pi)","sqrt(pi)"]`,
`vector=["4","1"]`.

Expected render item:
- `kind`: `"gradient"`, `exercise_label`: `"2"`
- All six pieces **present and numeric**: `show_gradient`, `show_gradient_evaluated`,
  `show_magnitude`, `show_unit_vector`, `show_directional_derivative`,
  `show_theta_max` all true; every `*_numeric` true.
- Vector decimals are complete `\left\langle …, … \right\rangle` strings; scalar
  decimals are 4-dp ROUND_HALF_UP.

Purpose: string-coordinate cleaning (`sqrt(pi)`), explicit-vector normalization,
full output set. Exact decimals/LaTeX captured from the solver.

---

## G3 — id 3: point + angle (structural)

Input: `function="100 * exp(-x**2 - y**2)"`, `point=["1","3"]`, `angle="pi/4"`.

Expected render item:
- `kind`: `"gradient"`, `exercise_label`: `"3"`
- All six pieces present and numeric (as G2). `û = ⟨cos(π/4), sin(π/4)⟩`
  (`unit_vector_decimal` ≈ `⟨0.7071, 0.7071⟩`).

Purpose: angle mode; radians canonical (`pi/4`). Exact decimals/LaTeX captured
from the solver.

---

## G4 — id 4: max_ascent (structural + identities)

Input: `function="100 * exp(-x**2 - y**2)"`, `point=["1","3"]`,
`direction_source="max_ascent"`.

Expected render item:
- `kind`: `"gradient"`, `exercise_label`: `"4"`
- All six pieces present and numeric.
- **Identities (binding):** the direction is `∇f(P)` itself, so
  `û ∥ ∇f(P)` and `directional_derivative == magnitude`
  (`directional_derivative_decimal_string == magnitude_decimal_string`), and
  `theta_max` is the angle of `û`.

Purpose: the fourth direction mode and its defining identity `Dᵤf = |∇f(P)|`.

---

## G5 — id 5: point-only / no direction (present-vs-absent contract)

Input: `function="100 * exp(-x**2 - y**2)"`, `point=["1","3"]` (no direction).

Expected render item:
- `kind`: `"gradient"`, `exercise_label`: `"5"`
- **Present and numeric:** `show_gradient` true; `show_gradient_evaluated` true +
  `gradient_evaluated_numeric` true; `show_magnitude` true + `magnitude_numeric`
  true; `show_theta_max` true + `theta_max_numeric` true.
- **Absent (no direction):** `show_unit_vector`: **false**,
  `unit_vector_numeric`: false, `unit_vector_latex`/`unit_vector_decimal`: `""`;
  `show_directional_derivative`: **false**,
  `directional_derivative_numeric`: false, its LaTeX/decimal: `""`.

Purpose: proves the point-only mode — the direction-dependent pieces are omitted
upstream and the adapter resolves their `show_*` off (contract closure with empty
strings). Exact decimals for the present pieces captured from the solver.

---

## G6 — id 6: symbolic point (per-piece null suppression, pinned)

Input: `function="x**2 + y**2"`, `point=["a","b"]` (no direction).

Expected render item:
- `kind`: `"gradient"`, `exercise_label`: `"6"`
- `show_gradient`: true — `gradient_latex`: `⟨2x, 2y⟩`
- `show_gradient_evaluated`: **true** — `gradient_evaluated_latex`: `⟨2a, 2b⟩`;
  `gradient_evaluated_numeric`: **false** (symbolic, value null);
  `gradient_evaluated_decimal`: `""`
- `show_magnitude`: **true** — `magnitude_latex`: `2\sqrt{a² + b²}`;
  `magnitude_numeric`: **false**; `magnitude_decimal_string`: `""`
- `show_theta_max`: **true** — `theta_max_latex`: `atan2(2b, 2a)` (symbolic;
  SymPy does not cancel the shared factor for symbolic arguments);
  `theta_max_numeric`: **false**; `theta_max_decimal_string`: `""`
- `show_unit_vector`: **false**, `show_directional_derivative`: **false**
  (absent — no direction); their LaTeX/decimals: `""`

Purpose: the "Phase 1.1 for gradient" case — a symbolic point keeps every present
piece's **symbolic** `*_latex` visible while the adapter resolves each piece's
**decimal** off (`*_numeric: false`, decimal `""`). Symbolic success, not error.

---

## E1 / E2 — intended errors (must render as `kind:"error"`)

- **E1 — id 7**: `function="x**2 + y**2"`, no `point`/`initial_point`/`final_point`
  — no evaluation point → exercise ERROR.
- **E2 — id 8**: `function="x**2 + y**2"`, `point=["1","1"]`, `vector=["0","0"]`
  — zero-length direction, cannot normalize → exercise ERROR.

Expected: each renders as one `kind:"error"` item with the generic Spanish marker
(`exercise_label` `"7"` / `"8"`, `message`
`"ERROR: no se pudo procesar este ejercicio."`).

Purpose: the gradient contract must guard missing points and non-normalizable
directions, and must not halt the run.

---

## Acceptance Rule (Phase 2A)

A Phase 2A implementation is acceptance-correct when:
1. G1 matches the values above field-for-field, including
   `directional_derivative_decimal_string: "8.4853"` (ROUND_HALF_UP).
2. G6 matches the symbolic behavior field-for-field (present pieces show symbolic
   `*_latex`; every `*_numeric` false; decimals `""`; absent pieces `show_*` false).
3. G5 shows `unit_vector` and `directional_derivative` resolved **off** (absent),
   the other pieces present.
4. G2, G3, G4 render all six pieces present and numeric; G4 satisfies
   `directional_derivative == magnitude`.
5. E1 and E2 render as `kind:"error"` items; the full 51 run completes without
   halting.
6. The Phase 1 golden set (47 over 46) and the Phase 1.1 symbolic set (49 over 48)
   still pass UNCHANGED.
