"""Integral solver — the only Phase 1 solver.

One generic recursive integrator handles 1D/2D/3D (and nD) definite
integrals: the ``integrals`` list is ordered innermost -> outermost
(bible 80), and each integration result feeds the next outer one. Do NOT
add a separate single-integral solver (bible 90).

The solver integrates exactly what it is given: ``coordinate_system`` is
never read and no Jacobian is ever injected — the author writes any
Jacobian into ``function`` (bible 80, P5). Math fields are expected to be
already cleaned (the pipeline runs the cleaner first); parsing uses the
same dialect as the cleaner's validation — standard transformations only
(no implicit multiplication) plus ``float`` so cleaned infinity bounds
(``float('inf')``) parse to SymPy oo.

The final result is classified (bible 90, symbolic-only success contract):
a result with no free symbols must still be a finite real number, or the
exercise is an error; a result WITH free symbols is a SUCCESS with
``numeric_value: None`` unless it contains oo/-oo/zoo/nan or an unevaluated
``Integral``, in which case it remains an error.

Per-exercise and independent: no aggregation, no document assembly, no
formatting (bible 90/75).
"""

import math

import sympy
from sympy.parsing.sympy_parser import parse_expr, standard_transformations

from solucionario.solvers.base import error_result, success_result


def solve_integral(exercise: dict) -> dict:
    """Solve one cleaned integral exercise. Never raises.

    Returns a bible-75 results dict: ``{problem_latex, solution_latex,
    numeric_value}`` on success, or ``{status: "error", ...}`` on failure.
    """
    try:
        integrand = _parse(exercise["function"])
        limits = [
            (sympy.Symbol(bound["var"]), _parse(bound["lower"]), _parse(bound["upper"]))
            for bound in exercise["integrals"]
        ]

        if limits:
            problem_latex = sympy.latex(sympy.Integral(integrand, *limits))
        else:
            problem_latex = sympy.latex(integrand)

        result = integrand
        for limit in limits:  # innermost -> outermost (bible 80)
            result = sympy.integrate(result, limit)

        numeric_value = _classify_result(result)
        results = success_result(problem_latex, sympy.latex(result), numeric_value)
        # In-memory handoff to the Component Aggregation stage (bible 90):
        # a sympify-able string, never serialized — the Extended JSON stage
        # strips underscore-prefixed keys (bible 75 stays canonical).
        results["_symbolic_result"] = str(result)
        return results
    except Exception as exc:
        return error_result(f"Cannot solve integral: {exc}")


def _parse(expression: str):
    """Parse one cleaned expression string into a SymPy object."""
    parsed = parse_expr(
        expression,
        transformations=standard_transformations,
        local_dict={"float": float},
    )
    return sympy.sympify(parsed)  # normalizes e.g. Python inf -> sympy oo


def _classify_result(result) -> float | None:
    """Bible 90 symbolic-only success guard, applied before the numeric path.

    A result with free symbols is a SUCCESS with numeric_value None unless it
    contains oo/-oo/zoo/nan or an unevaluated Integral (either of which keeps
    it an error — divergent/indeterminate symbolic results are never
    successes, and the symbolic path never accepts an unevaluated Integral,
    unlike the numeric path below which may still evalf one). A result with
    no free symbols takes the existing finite-numeric path unchanged.
    """
    if result.free_symbols:
        if result.has(sympy.oo, -sympy.oo, sympy.zoo, sympy.nan):
            raise ValueError(f"symbolic result is not finite: {result}")
        if result.has(sympy.Integral):
            raise ValueError(
                f"symbolic result contains an unevaluated Integral: {result}"
            )
        return None  # symbolic-only success (bible 90)
    return _finite_float(result)


def _finite_float(result) -> float:
    """Convert a symbol-free result to a raw float, verifying it is a finite
    real number (no oo / -oo / zoo / nan). numeric_value must never be inf or
    nan."""
    evaluated = result.evalf()
    if evaluated.is_real is not True or evaluated.is_finite is not True:
        raise ValueError(f"result is not a finite real number: {result}")

    numeric = float(result)  # full double precision from the exact result
    if not math.isfinite(numeric):
        raise ValueError(f"result is not a finite real number: {result}")
    return numeric
