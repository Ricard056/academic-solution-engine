# Expression Cleaner Specification — v3.2

> **v3.2 changes**: references/version label only. Content unchanged.
> **Phase 2A amendment**: gradient's string coordinate entries
> (`point`/`initial_point`/`final_point`/`vector`) and its radians `angle` string
> are cleaned like any math field; the cleaner performs no unit conversion (there is
> no `angle_unit` in 2A). This supersedes 09's "point/vector are already numeric".
> Integral cleaning is unchanged. See `91_phase2a_gradient_scope_v3_2.md`.

## Purpose
Provide safe, predictable transformations for mathematical expressions in JSON
input to ensure Python compatibility while maintaining user-friendly notation.

## Design Philosophy
- **Minimal intervention**: Only fix unambiguous, common notation differences
- **No guessing**: Never attempt to interpret ambiguous notation
- **Fail gracefully**: Mark ERROR in PDF rather than crash
- **Single responsibility**: Clean expressions, don't validate math
- **Field selective**: Only process mathematical fields that go to solvers

---

## Field Filtering — Only Process Solver Fields

### Core Principle
The cleaner ONLY processes fields containing mathematical expressions that will
be evaluated by solvers. Metadata, display settings, and descriptive fields are
NEVER processed.

### Fields TO Process (Mathematical)
- `function` — the integrand/expression (integral) or scalar field (gradient)
- `integrals[].lower` — integration bounds
- `integrals[].upper` — integration bounds
- Gradient (Phase 2A): each string entry of `point`, `initial_point`,
  `final_point`, and `vector`; and the `angle` string (radians math)

### Fields NOT TO Process
- Identifiers: `id`, `id_letter`, `id_component`, `id_output`
- Labels: `quantity`, `var`, `variable`, `coordinate_system`
- Metadata: All `metadata` objects
- Display: All `display_*` configurations
- Solver configuration: `type`, `units`

### Why This Matters
Prevents corruption of non-mathematical data, avoids transforming descriptive
text, ensures variable names remain unchanged, and preserves metadata integrity.

---

## Transformation Rules

### SAFE Transformations (Implement)

#### 1. Exponentiation
`^` → `**`

Examples: `x^2` → `x**2`, `(x+1)^3` → `(x+1)**3`

#### 2. Whitespace Normalization
Remove extra spaces, trim edges.

Examples: `  x + y  ` → `x + y`, `x    +    y` → `x + y`

#### 3. Logarithms
- `ln(x)` → `log(x)` (Python's log is natural log)
- `log10(x)` → `log10(x)` (already compatible)
- `log2(x)` → `log2(x)` (already compatible)
- `log[base](x)` → `log(x, [base])` (for other bases: log5, log7, etc.)

Examples: `ln(x)` → `log(x)`, `log7(x)` → `log(x, 7)`

#### 4. Inverse Trigonometric Functions and Trigonometric Powers

**Processing Order (CRITICAL)**: Apply in this sequence:
1. First: Inverse functions (^-1 cases)
2. Then: General powers (^2, ^3, ^n)

Inverse functions:
- `sin^-1(x)` → `asin(x)`, `arcsin(x)` → `asin(x)`
- `cos^-1(x)` → `acos(x)`, `arccos(x)` → `acos(x)`
- `tan^-1(x)` → `atan(x)`, `arctan(x)` → `atan(x)`

Trigonometric powers:
- `sin^2(x)` → `sin(x)**2`
- `cos^2(x)` → `cos(x)**2`
- `tan^n(x)` → `tan(x)**n` (for any power)

#### 5. Infinity Constants
`inf` → `float('inf')`, `-inf` → `float('-inf')`

Context: Primarily for integral bounds.

### Global Transformation Order

Global order: apply the log, inverse-trig, and trig-power transformations (which
match the `ln`/`logN`/`^-1`/`^n` forms) first; the generic `^` → `**` conversion
runs last, on whatever carets remain.

### REJECTED Transformations (Don't Implement)

| Notation | Why Rejected | User Responsibility |
|----------|-------------|-------------------|
| `2x` → `2*x` | Ambiguous: is `sin2x` → `sin(2*x)` or `sin(2)*x`? | Write explicit `*` |
| `√x` → `sqrt(x)` | Cannot determine scope of radical | Use `sqrt()` |
| `\|x\|` → `abs(x)` | Complex parsing of balanced pipes | Use `abs()` |
| standalone `e` constant | Conflicts with scientific notation, `exp()`, `sec()`, and ordinary variable names | Use `exp(1)` for Euler's number and `exp(x)` for exponential functions |

---

## Golden Test Cases

| Input Expression | Output Expression | Notes |
|-----------------|-------------------|-------|
| `x^2 + y^2` | `x**2 + y**2` | Basic exponentiation |
| `sin^-1(x/2)` | `asin(x/2)` | Inverse trig (priority 1) |
| `sin^2(x) + cos^2(x)` | `sin(x)**2 + cos(x)**2` | Trig powers (priority 2) |
| `ln(x) + log10(y)` | `log(x) + log10(y)` | Natural log conversion |
| `log7(x^2)` | `log(x**2, 7)` | Custom base log |
| `inf` | `float('inf')` | Infinity constant |
| `  x +  y  ` | `x + y` | Whitespace cleanup |
| `tan^3(theta)` | `tan(theta)**3` | Higher trig powers |
| `arccos(0.5)` | `acos(0.5)` | Arc- prefix conversion |
| `2*sin(x)` | `2*sin(x)` | Already valid (no change) |
| `2x` | (ERROR) | Implicit multiplication rejected; becomes ERROR exercise |

---

## Error Handling

When cleaner cannot process an expression:
1. Don't stop processing other exercises
2. Mark ERROR in PDF for this exercise (generic message)
3. Continue with next exercise

```json
{
  "id": 2,
  "type": "integral",
  "function": "√(x+y)",
  "results": {
    "status": "error",
    "problem_latex": "\\text{ERROR: Could not process exercise}",
    "solution_latex": "\\text{ERROR}",
    "error_message": "Cannot parse expression: √(x+y)"
  }
}
```

---

## Integration with Pipeline

```
JSON Input → Field Filter → Expression Cleaner → Solver → Results → JSON Extended
                ↓                   ↓
        Skip non-math         If cleaning fails
        fields                      ↓
                            Mark ERROR in PDF
```

### Cleaner Scope for Integral Solver
- Clean `function` field
- Clean integral bounds (`lower`, `upper`)
- Handle infinity in bounds
- DO NOT process: `quantity`, `var`, `coordinate_system`

### Cleaner Scope for Gradient Solver (Phase 2A)
- Clean `function` field
- Clean each string entry of `point`, `initial_point`, `final_point`, `vector`
- Clean the `angle` string (radians math, e.g. `pi/4`)
- No unit conversion — `angle` is radians; there is no `angle_unit` in 2A
- DO NOT process: `type`, `direction_source`, `id`/`id_letter`, `display_*`

---

## Non-Goals
- **Not a math parser**: Won't interpret complex notation
- **Not a validator**: Won't check mathematical correctness
- **Not configurable**: Same rules for all exercises
- **Not in JSON Extended**: No transformation logs in output

---

## Euler Constant Policy

Standalone `e` is NOT supported as a mathematical constant in Phase 1 input.

Use:
- `exp(1)` for Euler's number
- `exp(x)` for e raised to x
- `exp(3*x)` for e raised to 3x

Do not write:
- `e`
- `e^x`
- `e**x`

Reason: automatic conversion of standalone `e` can corrupt expressions containing
scientific notation, `exp()`, `sec()`, or variables named with the letter `e`.
