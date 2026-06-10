"""Tests for the integral solver.

Covers bible/90_phase1_scope_v3_2.md (one generic recursive integrator,
coordinate passivity, no auto-Jacobian) and bible/75_json_output_spec_v3_2.md
(raw results only: no status on success, no decimal_string, no units).
"""

import pytest
import sympy

from solucionario.cleaner import clean_expression
from solucionario.solvers.base import ERROR_PROBLEM_LATEX, ERROR_SOLUTION_LATEX
from solucionario.solvers.integral import solve_integral


def integral_exercise(function, bounds, **extra):
    """Build a cleaned integral exercise. bounds = [(var, lower, upper), ...]
    ordered innermost -> outermost (bible 80)."""
    exercise = {
        "id": 1,
        "type": "integral",
        "function": function,
        "integrals": [
            {"var": var, "lower": lower, "upper": upper} for var, lower, upper in bounds
        ],
    }
    exercise.update(extra)
    return exercise


# ---------------------------------------------------------------------------
# Dimensions: one generic integrator for 1D / 2D / 3D
# ---------------------------------------------------------------------------

def test_1d_integral():
    result = solve_integral(integral_exercise("x**2", [("x", "0", "1")]))
    assert result["solution_latex"] == r"\frac{1}{3}"
    assert result["numeric_value"] == pytest.approx(1 / 3, rel=1e-14)


def test_2d_integral():
    # Source of golden Ex 7 (bible 47): ∫₀²∫₀² x·y dy dx = 4.
    result = solve_integral(integral_exercise("x*y", [("y", "0", "2"), ("x", "0", "2")]))
    assert result["solution_latex"] == "4"
    assert result["numeric_value"] == 4.0


def test_3d_integral_unit_cube():
    bounds = [("z", "0", "1"), ("y", "0", "1"), ("x", "0", "1")]
    result = solve_integral(integral_exercise("1", bounds))
    assert result["solution_latex"] == "1"
    assert result["numeric_value"] == 1.0


def test_3d_integral_non_trivial():
    bounds = [("z", "0", "1"), ("y", "0", "1"), ("x", "0", "1")]
    result = solve_integral(integral_exercise("2*x*y", bounds))
    assert result["numeric_value"] == pytest.approx(0.5, rel=1e-14)


def test_variable_bounds():
    # Golden Ex 5 component 1 (bible 47): ∫₀¹∫₀ˣ 1 dy dx = 1/2.
    result = solve_integral(integral_exercise("1", [("y", "0", "x"), ("x", "0", "1")]))
    assert result["solution_latex"] == r"\frac{1}{2}"
    assert result["numeric_value"] == pytest.approx(0.5, rel=1e-14)


def test_variable_bounds_t21_1a():
    # T21 exercise 1.a (bible 45): ∫₀¹∫ₓ²ˣ∫₀^{x+y} 2xy dz dy dx = 23/15
    # (the worked example value of bible 85's render-model sample).
    bounds = [("z", "0", "x + y"), ("y", "x", "2*x"), ("x", "0", "1")]
    result = solve_integral(integral_exercise("2*x*y", bounds))
    assert result["solution_latex"] == r"\frac{23}{15}"
    assert result["numeric_value"] == pytest.approx(23 / 15, rel=1e-14)


# ---------------------------------------------------------------------------
# Coordinate passivity / no automatic Jacobian (bible 80 P5)
# ---------------------------------------------------------------------------

CYLINDRICAL_BOUNDS = [("z", "0", "1"), ("r", "0", "1"), ("theta", "0", "2*pi")]


def test_coordinate_system_is_passive():
    plain = solve_integral(integral_exercise("1", CYLINDRICAL_BOUNDS))
    labeled = solve_integral(
        integral_exercise("1", CYLINDRICAL_BOUNDS, coordinate_system="cylindrical")
    )
    assert plain == labeled  # the field has zero computational effect


def test_no_automatic_jacobian():
    # function "1" with cylindrical-looking vars integrates to 2π (NOT the
    # true cylinder volume π) because no Jacobian r is injected...
    without_jacobian = solve_integral(
        integral_exercise("1", CYLINDRICAL_BOUNDS, coordinate_system="cylindrical")
    )
    assert without_jacobian["numeric_value"] == pytest.approx(float(2 * sympy.pi), rel=1e-14)

    # ...and the author-supplied Jacobian in `function` is what produces π.
    with_jacobian = solve_integral(
        integral_exercise("r", CYLINDRICAL_BOUNDS, coordinate_system="cylindrical")
    )
    assert with_jacobian["numeric_value"] == pytest.approx(float(sympy.pi), rel=1e-14)


# ---------------------------------------------------------------------------
# Raw output contract (bible 75)
# ---------------------------------------------------------------------------

def test_success_result_has_exactly_the_bible_75_keys():
    result = solve_integral(integral_exercise("x**2", [("x", "0", "1")]))
    assert set(result) == {"problem_latex", "solution_latex", "numeric_value"}
    assert "status" not in result
    assert "decimal_string" not in result
    assert "units" not in result


def test_numeric_value_is_raw_unrounded_float():
    result = solve_integral(integral_exercise("x**2", [("x", "0", "1")]))
    value = result["numeric_value"]
    assert isinstance(value, float)
    assert value == pytest.approx(1 / 3, rel=1e-14)  # full double precision
    assert value != 0.3333  # NOT rounded to 4 places — formatting is the adapter's


def test_problem_latex_is_the_unevaluated_integral():
    result = solve_integral(integral_exercise("x*y", [("y", "0", "2"), ("x", "0", "2")]))
    assert "\\int" in result["problem_latex"]
    assert "dy" in result["problem_latex"] and "dx" in result["problem_latex"]


def test_solver_consumes_cleaner_output():
    # 46 Ex 8: function and bounds go through the real cleaner first.
    # ∫₁^e ∫₀^{π/2} (ln x + sin² y) dy dx = π/2 + π(e−1)/4.
    exercise = integral_exercise(
        clean_expression("ln(x) + sin^2(y)"),
        [
            ("y", clean_expression("0"), clean_expression("pi/2")),
            ("x", clean_expression("1"), clean_expression("exp(1)")),
        ],
    )
    result = solve_integral(exercise)
    expected = float(sympy.pi / 2 + sympy.pi * (sympy.E - 1) / 4)
    assert result["numeric_value"] == pytest.approx(expected, rel=1e-12)


# ---------------------------------------------------------------------------
# Failures (bible 75 error shape; constraint: finite real results only)
# ---------------------------------------------------------------------------

def assert_error_result(result):
    assert result["status"] == "error"
    assert result["problem_latex"] == ERROR_PROBLEM_LATEX
    assert result["solution_latex"] == ERROR_SOLUTION_LATEX
    assert result["error_message"]
    assert "numeric_value" not in result


def test_invalid_expression_is_error():
    result = solve_integral(integral_exercise("x +* y", [("x", "0", "1")]))
    assert_error_result(result)


def test_leftover_free_symbols_is_error():
    # q survives integration over x -> result is not numeric.
    result = solve_integral(integral_exercise("q", [("x", "0", "1")]))
    assert_error_result(result)
    assert "q" in result["error_message"]


def test_divergent_integral_is_error_not_inf():
    # Cleaned infinite bound parses (float('inf') -> oo), but ∫₀^∞ x dx
    # diverges: must be an error result, never numeric_value = inf.
    result = solve_integral(
        integral_exercise("x", [("x", "0", clean_expression("inf"))])
    )
    assert_error_result(result)


def test_convergent_improper_integral_succeeds():
    # ∫₀^∞ e^(−x) dx = 1: infinite bounds are allowed when the result is finite.
    result = solve_integral(
        integral_exercise("exp(-x)", [("x", "0", clean_expression("inf"))])
    )
    assert result["numeric_value"] == pytest.approx(1.0, rel=1e-14)
    assert result["solution_latex"] == "1"
