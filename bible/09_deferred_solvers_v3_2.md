# Deferred Solvers Reference — v3.2

> **Status**: NOT in Phase 1 scope. This file preserves gradient and derivative
> specifications for future implementation.
> **When to use**: When starting Phase 2+ and adding new solver types.
> **v3.2 changes**: references/version label only. Content unchanged.

---

## Gradient Solver

### Exercise Input Examples

#### Point to Point
```json
{
  "id": 1,
  "type": "gradient",
  "function": "x^2 + y^2",
  "initial_point": [0, 0],
  "final_point": [1, 1]
}
```

#### Point with Vector Direction
```json
{
  "id": 1,
  "type": "gradient",
  "function": "x^2 + y^2",
  "point": [3, 4],
  "vector": [1, 2]
}
```

#### Point with Angle
```json
{
  "id": 1,
  "type": "gradient",
  "function": "x^2 + y^2",
  "point": [2, 3],
  "angle": 45
}
```

#### Angle with Radians
```json
{
  "id": 1,
  "type": "gradient",
  "function": "x^2 + y^2",
  "point": [2, 3],
  "angle": "pi/4"
}
```

```json
{
  "angle": 1.5708,
  "angle_unit": "radians"
}
```

### Gradient Results Structure (Extended JSON)
```json
"results": {
  "problem_latex": "\\nabla f(2,3)",
  "solution_latex": "\\langle 4, 6 \\rangle",
  "numeric_value": 7.211102551,
  "gradient_evaluated": [4, 6],
  "magnitude": 7.211102551,
  "unit_vector": [0.5547, 0.8321],
  "theta_max": 56.31
}
```

> **Note for Phase 2**: When implementing gradient, follow the v3.2 formatting
> ownership rule — the solver stores raw floats and LaTeX; the adapter formats
> decimals and derives any units. Add `display_gradient` render fields to the
> render-model contract in 85 before wiring templates.

### Gradient Display Fields (display_gradient)
```json
"display_gradient": {
  "show_magnitude": true,
  "show_unit_vector": true,
  "show_theta_max": true,
  "show_theta_min": false,
  "show_gradient": true,
  "show_gradient_evaluated": true,
  "show_directional_derivative": true,
  "decimal_places": 5
}
```

### Expression Cleaner — Gradient Specifics
- Clean `function` field
- Clean angle expressions when they contain math
- DO NOT process: `point`, `vector` arrays (already numeric)
- String with "pi" → radians
- Numeric value → check `angle_unit` field
- Default: degrees

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

When adding any new solver:
1. Create exercise examples in this file or a new deferred file
2. Define results structure following the same pattern as above (raw floats +
   LaTeX; adapter owns formatting)
3. Add solver-specific display fields if needed
4. Add the solver's render-item shape to the closed render-model contract (85)
5. Create Jinja2 template for the solver
6. No existing solver code needs modification (solver independence principle)
