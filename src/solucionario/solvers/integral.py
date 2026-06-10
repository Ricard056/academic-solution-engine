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
(``float('inf')``) parse to SymPy oo. The final result must still be a
finite real number; otherwise the exercise is an error.

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

        numeric_value = _finite_float(result)
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


def _finite_float(result) -> float:
    """Convert the final symbolic result to a raw float, verifying first
    that it is numeric (no leftover free symbols) and a finite real number
    (no oo / -oo / zoo / nan). numeric_value must never be inf or nan."""
    if result.free_symbols:
        names = ", ".join(sorted(str(s) for s in result.free_symbols))
        raise ValueError(f"result is not numeric (free symbols: {names})")

    evaluated = result.evalf()
    if evaluated.is_real is not True or evaluated.is_finite is not True:
        raise ValueError(f"result is not a finite real number: {result}")

    numeric = float(result)  # full double precision from the exact result
    if not math.isfinite(numeric):
        raise ValueError(f"result is not a finite real number: {result}")
    return numeric
