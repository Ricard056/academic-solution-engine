"""Gradient solver — Phase 2A (bible 91).

2-variable scalar fields ``f(x, y)``, Cartesian, radians, fixed variable
order ``(x, y)``. Per-exercise and independent (bible 99 #5): nothing here
imports the integral solver — the small ``_parse``/``_finite_float`` helpers
are deliberate duplicates of integral.py's so that adding this solver leaves
Phase 1 code byte-identical (99 #4; guarded by tests/test_architecture.py).

Inputs arrive validated (bible 91 static matrix) and cleaned (bible 60): the
``function`` string, every ``point``/``initial_point``/``final_point``/
``vector`` entry, and ``angle`` are cleaned math strings. Direction modes
(bible 91): two points (evaluation point = ``initial_point``), point +
vector, point + angle (radians), ``direction_source: "max_ascent"``, or
point-only (no direction: the ``unit_vector_*``/``directional_derivative_*``
keys are omitted).

Results contract (bible 75): top-level ``numeric_value`` is ``None`` for
EVERY gradient success (the headline is vector-valued); ``solution_latex``
is a non-rendered mirror of ``results.gradient.gradient_latex``;
``results.gradient`` holds raw floats and LaTeX strings using the canonical
``\\left\\langle …, \\; … \\right\\rangle`` delimiter. Two kinds of absence:
OMITTED keys = not applicable (direction pieces without a direction;
``theta_max_*`` when the evaluated gradient is the zero vector), ``None``
values = applicable but symbolic — per piece, never a mixed float/None
array. Divergent/non-finite pieces, domain errors at the point, and
zero-length directions (including ``max_ascent`` with a zero gradient) are
ERRORs, never symbolic successes. No rounding, no formatting, no units
(bible 75/85).
"""

import math

import sympy
from sympy.parsing.sympy_parser import parse_expr, standard_transformations

from solucionario.solvers.base import error_result, success_result

PROBLEM_LATEX = r"\nabla f(x, y)"

_X, _Y = sympy.symbols("x y")


def solve_gradient(exercise: dict) -> dict:
    """Solve one cleaned gradient exercise. Never raises.

    Returns a bible-75 results dict: ``{problem_latex, solution_latex,
    numeric_value: None, gradient: {...}}`` on success, or
    ``{status: "error", ...}`` on failure.
    """
    try:
        function = _parse(exercise["function"])
        # factor() is the deterministic light canonicalization of the
        # symbolic components (bible 52 G1 anchor form, e.g.
        # y*(x*y + 2)*exp(x*y) instead of the raw expanded derivative).
        fx = sympy.factor(sympy.diff(function, _X))
        fy = sympy.factor(sympy.diff(function, _Y))

        point = _evaluation_point(exercise)
        substitutions = {_X: point[0], _Y: point[1]}
        gx = fx.subs(substitutions)
        gy = fy.subs(substitutions)
        zero_gradient = _is_zero(gx) and _is_zero(gy)

        gradient_latex = _vector_latex(fx, fy)
        gradient = {
            "gradient_latex": gradient_latex,
            "gradient_evaluated_latex": _vector_latex(gx, gy),
            "gradient_evaluated_values": _vector_values(gx, gy),
        }

        magnitude = _norm(gx, gy)
        gradient["magnitude_latex"] = sympy.latex(magnitude)
        gradient["magnitude_value"] = _scalar_value(magnitude)

        if not zero_gradient:
            theta_max = sympy.atan2(gy, gx)
            gradient["theta_max_latex"] = sympy.latex(theta_max)
            gradient["theta_max_value"] = _scalar_value(theta_max)
        # Zero gradient outside max_ascent: theta_max is undefined, so its
        # keys are OMITTED — not-applicable absence, still a SUCCESS (91/75).

        unit_vector = _unit_vector(exercise, (gx, gy), zero_gradient)
        if unit_vector is not None:
            ux, uy = unit_vector
            gradient["unit_vector_latex"] = _vector_latex(ux, uy)
            gradient["unit_vector_values"] = _vector_values(ux, uy)
            derivative = gx * ux + gy * uy
            gradient["directional_derivative_latex"] = sympy.latex(derivative)
            gradient["directional_derivative_value"] = _scalar_value(derivative)

        # solution_latex mirrors gradient_latex for skeleton uniformity; the
        # adapter renders only from results.gradient (bible 75).
        results = success_result(PROBLEM_LATEX, gradient_latex, None)
        results["gradient"] = gradient
        return results
    except Exception as exc:
        return error_result(f"Cannot solve gradient: {exc}")


def _parse(expression: str):
    """Parse one cleaned expression string into a SymPy object."""
    parsed = parse_expr(
        expression,
        transformations=standard_transformations,
        local_dict={"float": float},
    )
    return sympy.sympify(parsed)


def _evaluation_point(exercise: dict) -> list:
    """P as parsed coordinates; two-points mode evaluates at initial_point
    (bible 91)."""
    coordinates = exercise.get("point")
    if coordinates is None:
        coordinates = exercise["initial_point"]
    return [_parse(entry) for entry in coordinates]


def _unit_vector(exercise: dict, evaluated_gradient: tuple, zero_gradient: bool):
    """Resolve the direction mode (bible 91) into a unit vector ``(ux, uy)``,
    or None in point-only mode.

    Raises ValueError on a zero-length direction — ``final == initial``, a
    vector that parses to ⟨0, 0⟩, or max_ascent when the evaluated gradient
    is the zero vector — which the caller turns into an exercise ERROR.
    """
    if exercise.get("angle") is not None:
        theta = _parse(exercise["angle"])
        return (sympy.cos(theta), sympy.sin(theta))  # already unit (bible 80)

    if exercise.get("initial_point") is not None:
        initial = [_parse(entry) for entry in exercise["initial_point"]]
        final = [_parse(entry) for entry in exercise["final_point"]]
        direction = (final[0] - initial[0], final[1] - initial[1])
    elif exercise.get("vector") is not None:
        direction = tuple(_parse(entry) for entry in exercise["vector"])
    elif exercise.get("direction_source") == "max_ascent":
        if zero_gradient:
            raise ValueError(
                "max_ascent direction is undefined: gradient is zero at the point"
            )
        direction = evaluated_gradient
    else:
        return None  # point-only mode: no û, no D_u f (bible 91)

    if _is_zero(direction[0]) and _is_zero(direction[1]):
        raise ValueError("zero-length direction cannot be normalized")
    norm = _norm(direction[0], direction[1])
    return (direction[0] / norm, direction[1] / norm)


def _norm(a, b):
    """``|⟨a, b⟩|`` with the radicand factored so shared factors leave the
    root (e.g. sqrt(4a² + 4b²) -> 2·sqrt(a² + b²), the bible-52 G6 form)."""
    return sympy.sqrt(sympy.factor(a**2 + b**2))


def _is_zero(expr) -> bool:
    """Provably zero. Undecidable symbolic zero-ness counts as NON-zero so
    symbolic exercises stay symbolic successes (bible 91)."""
    return sympy.simplify(expr).is_zero is True


def _vector_latex(a, b) -> str:
    """Canonical vector delimiter (bible 75/85): no other delimiter is used."""
    return (
        r"\left\langle "
        + sympy.latex(a)
        + r", \; "
        + sympy.latex(b)
        + r" \right\rangle"
    )


def _vector_values(a, b) -> list | None:
    """Component floats, or None when the piece is symbolic — the piece is
    symbolic AS A WHOLE (bible 75): never a mixed float/None array."""
    first = _scalar_value(a)
    second = _scalar_value(b)
    if first is None or second is None:
        return None
    return [first, second]


def _scalar_value(expr) -> float | None:
    """Bible 91 per-piece classification: symbolic -> None (a success),
    divergent/indeterminate -> error, numeric -> finite raw float."""
    if expr.has(sympy.oo, -sympy.oo, sympy.zoo, sympy.nan):
        raise ValueError(f"result is not finite: {expr}")
    if expr.free_symbols:
        return None  # applicable but symbolic (bible 75/91)
    return _finite_float(expr)


def _finite_float(expr) -> float:
    """Convert a symbol-free result to a raw float, verifying it is a finite
    real number (no oo / -oo / zoo / nan, no complex domain escape)."""
    evaluated = expr.evalf()
    if evaluated.is_real is not True or evaluated.is_finite is not True:
        raise ValueError(f"result is not a finite real number: {expr}")

    numeric = float(expr)  # full double precision from the exact result
    if not math.isfinite(numeric):
        raise ValueError(f"result is not a finite real number: {expr}")
    return numeric
