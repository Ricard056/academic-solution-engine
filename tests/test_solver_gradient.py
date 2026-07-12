"""Gradient solver unit tests (bible 91/75; anchors from bible 51/52).

solve_gradient is tested in isolation with CLEANED inputs — the pipeline
wires validation/cleaning in a later batch. Locks: the bible-75 results
skeleton (numeric_value None, solution_latex mirror, results.gradient), all
four direction modes plus point-only, per-piece symbolic nulls vs omitted
not-applicable keys, the canonical vector delimiter, raw-float values, and
the error guards (zero-length directions, max_ascent with zero gradient,
domain errors, never-raises).

Byte-exact LaTeX pinning for the G1/G6 acceptance anchors belongs to
tests/test_golden_gradient.py (bible 52 conventions). Here LaTeX is asserted
exactly only where the SymPy form is simple and stable, plus structural
delimiter checks.
"""

import math

import pytest

from solucionario.solvers.gradient import solve_gradient

# Standard success keys for non-zero-gradient cases; zero-gradient successes
# omit theta_max_* (bible 91/75).
BASE_KEYS = {
    "gradient_latex",
    "gradient_evaluated_latex",
    "gradient_evaluated_values",
    "magnitude_latex",
    "magnitude_value",
    "theta_max_latex",
    "theta_max_value",
}
# ...plus these when a direction was supplied (bible 75).
DIRECTION_KEYS = {
    "unit_vector_latex",
    "unit_vector_values",
    "directional_derivative_latex",
    "directional_derivative_value",
}
THETA_KEYS = {"theta_max_latex", "theta_max_value"}


def gradient_exercise(**overrides) -> dict:
    """A cleaned point-only gradient exercise; overrides replace or (None)
    drop keys."""
    exercise = {
        "id": 1,
        "type": "gradient",
        "function": "x**2 + y**2",
        "point": ["1", "3"],
    }
    for key, value in overrides.items():
        if value is None:
            exercise.pop(key, None)
        else:
            exercise[key] = value
    return exercise


# ---------------------------------------------------------------------------
# Results skeleton (bible 75)
# ---------------------------------------------------------------------------

def test_success_result_skeleton():
    results = solve_gradient(gradient_exercise())
    assert set(results) == {
        "problem_latex", "solution_latex", "numeric_value", "gradient",
    }
    assert "status" not in results
    assert results["problem_latex"] == r"\nabla f(x, y)"
    assert results["numeric_value"] is None  # every gradient SUCCESS
    # Non-rendered mirror of the authoritative sub-object (bible 75).
    assert results["solution_latex"] == results["gradient"]["gradient_latex"]


# ---------------------------------------------------------------------------
# G1 anchor — two points (Tarea 12 1a, bible 51/52)
# ---------------------------------------------------------------------------

def test_two_points_full_output_g1_anchor():
    results = solve_gradient(
        {
            "function": "y**2 * exp(x*y)",
            "initial_point": ["0", "2"],
            "final_point": ["5", "7"],
        }
    )
    assert "status" not in results
    gradient = results["gradient"]
    assert set(gradient) == BASE_KEYS | DIRECTION_KEYS

    # Evaluation point is initial_point (0, 2): ∇f(P) = ⟨8, 4⟩.
    assert gradient["gradient_evaluated_latex"] == r"\left\langle 8, \; 4 \right\rangle"
    assert gradient["gradient_evaluated_values"] == [8.0, 4.0]
    assert gradient["magnitude_latex"] == r"4 \sqrt{5}"
    assert gradient["magnitude_value"] == pytest.approx(math.sqrt(80), rel=1e-12)
    # Direction final − initial = ⟨5, 5⟩ normalizes to ⟨√2/2, √2/2⟩.
    assert gradient["unit_vector_values"] == pytest.approx(
        [math.sqrt(2) / 2, math.sqrt(2) / 2], rel=1e-12
    )
    assert gradient["directional_derivative_latex"] == r"6 \sqrt{2}"
    # 6√2 = 8.485281374238571 — the raw float behind the ROUND_HALF_UP
    # witness "8.4853" (formatted by the adapter, bible 52 G1).
    assert gradient["directional_derivative_value"] == pytest.approx(
        6 * math.sqrt(2), rel=1e-12
    )
    assert gradient["theta_max_value"] == pytest.approx(math.atan(0.5), rel=1e-12)


# ---------------------------------------------------------------------------
# G2 — point + vector (string coordinates, explicit-vector normalization)
# ---------------------------------------------------------------------------

def test_point_vector_g2():
    results = solve_gradient(
        gradient_exercise(
            function="x**2 * cos(x*y)",
            point=["sqrt(pi)", "sqrt(pi)"],
            vector=["4", "1"],
        )
    )
    assert "status" not in results
    gradient = results["gradient"]
    assert set(gradient) == BASE_KEYS | DIRECTION_KEYS

    # ∇f(√π, √π) = ⟨2√π·cos(π) − π√π·sin(π), −π√π·sin(π)⟩ = ⟨−2√π, 0⟩.
    assert gradient["gradient_evaluated_values"] == pytest.approx(
        [-2 * math.sqrt(math.pi), 0.0], abs=1e-12
    )
    assert gradient["magnitude_value"] == pytest.approx(
        2 * math.sqrt(math.pi), rel=1e-12
    )
    assert gradient["unit_vector_values"] == pytest.approx(
        [4 / math.sqrt(17), 1 / math.sqrt(17)], rel=1e-12
    )
    assert gradient["directional_derivative_value"] == pytest.approx(
        -8 * math.sqrt(math.pi) / math.sqrt(17), rel=1e-12
    )
    # ∇f(P) points along the negative x-axis: theta_max = π (radians).
    assert gradient["theta_max_value"] == pytest.approx(math.pi, rel=1e-12)


# ---------------------------------------------------------------------------
# G3 — point + angle (radians)
# ---------------------------------------------------------------------------

def test_point_angle_g3():
    results = solve_gradient(
        gradient_exercise(
            function="100 * exp(-x**2 - y**2)", point=["1", "3"], angle="pi/4"
        )
    )
    assert "status" not in results
    gradient = results["gradient"]
    assert set(gradient) == BASE_KEYS | DIRECTION_KEYS

    scale = math.exp(-10)
    assert gradient["gradient_evaluated_values"] == pytest.approx(
        [-200 * scale, -600 * scale], rel=1e-12
    )
    # û = ⟨cos(π/4), sin(π/4)⟩ — taken directly, not re-normalized (bible 80).
    assert gradient["unit_vector_values"] == pytest.approx(
        [math.sqrt(2) / 2, math.sqrt(2) / 2], rel=1e-12
    )
    assert gradient["directional_derivative_value"] == pytest.approx(
        -400 * math.sqrt(2) * scale, rel=1e-12
    )


# ---------------------------------------------------------------------------
# G4 — max_ascent and its defining identities (bible 91/52)
# ---------------------------------------------------------------------------

def test_max_ascent_identity_g4():
    results = solve_gradient(
        gradient_exercise(
            function="100 * exp(-x**2 - y**2)",
            point=["1", "3"],
            direction_source="max_ascent",
        )
    )
    assert "status" not in results
    gradient = results["gradient"]
    assert set(gradient) == BASE_KEYS | DIRECTION_KEYS

    # Binding identities: û ∥ ∇f(P) and D_u f == |∇f(P)|. The solver computes
    # D_u f through the generic dot-product path, so this is a real check.
    magnitude = gradient["magnitude_value"]
    assert gradient["directional_derivative_value"] == pytest.approx(
        magnitude, rel=1e-12
    )
    gx, gy = gradient["gradient_evaluated_values"]
    assert gradient["unit_vector_values"] == pytest.approx(
        [gx / magnitude, gy / magnitude], rel=1e-12
    )


# ---------------------------------------------------------------------------
# G5 — point-only: direction pieces OMITTED (not-applicable absence)
# ---------------------------------------------------------------------------

def test_point_only_omits_direction_pieces_g5():
    results = solve_gradient(
        gradient_exercise(function="100 * exp(-x**2 - y**2)")
    )
    assert "status" not in results
    gradient = results["gradient"]
    assert set(gradient) == BASE_KEYS  # û / D_u f keys absent entirely
    assert gradient["gradient_evaluated_values"] is not None
    assert gradient["magnitude_value"] is not None
    assert gradient["theta_max_value"] is not None


# ---------------------------------------------------------------------------
# G6 — symbolic point: per-piece None values, exact symbolic LaTeX
# ---------------------------------------------------------------------------

def test_symbolic_point_g6():
    results = solve_gradient(gradient_exercise(point=["a", "b"]))
    assert "status" not in results  # symbolic success, not error
    assert results["numeric_value"] is None
    gradient = results["gradient"]
    assert set(gradient) == BASE_KEYS

    assert gradient["gradient_latex"] == r"\left\langle 2 x, \; 2 y \right\rangle"
    assert (
        gradient["gradient_evaluated_latex"]
        == r"\left\langle 2 a, \; 2 b \right\rangle"
    )
    assert gradient["gradient_evaluated_values"] is None
    # Shared factor leaves the root: 2√(a² + b²) (bible 52 G6 form).
    assert gradient["magnitude_latex"] == r"2 \sqrt{a^{2} + b^{2}}"
    assert gradient["magnitude_value"] is None
    # atan2(2b, 2a): SymPy keeps atan2 unevaluated for symbolic arguments.
    assert "atan" in gradient["theta_max_latex"]
    assert gradient["theta_max_value"] is None


def test_partially_symbolic_point_nulls_whole_piece():
    results = solve_gradient(gradient_exercise(point=["1", "b"]))
    gradient = results["gradient"]
    # A piece is symbolic AS A WHOLE — never a mixed [2.0, None] array.
    assert gradient["gradient_evaluated_values"] is None
    assert gradient["magnitude_value"] is None


# ---------------------------------------------------------------------------
# Canonical vector delimiter (bible 75/85)
# ---------------------------------------------------------------------------

def test_canonical_vector_delimiter():
    results = solve_gradient(gradient_exercise(vector=["4", "1"]))
    gradient = results["gradient"]
    for field in ("gradient_latex", "gradient_evaluated_latex", "unit_vector_latex"):
        latex = gradient[field]
        assert latex.startswith(r"\left\langle "), field
        assert latex.endswith(r" \right\rangle"), field
        assert r", \; " in latex, field


# ---------------------------------------------------------------------------
# Zero gradient: theta_max omitted outside max_ascent (bible 91/75)
# ---------------------------------------------------------------------------

def test_zero_gradient_point_only_omits_theta():
    results = solve_gradient(gradient_exercise(point=["0", "0"]))
    assert "status" not in results  # SUCCESS: only theta_max is undefined
    gradient = results["gradient"]
    assert set(gradient) == BASE_KEYS - THETA_KEYS
    assert gradient["gradient_evaluated_values"] == [0.0, 0.0]
    assert gradient["magnitude_value"] == 0.0


def test_zero_gradient_with_explicit_direction_keeps_direction_pieces():
    results = solve_gradient(
        gradient_exercise(point=["0", "0"], vector=["1", "0"])
    )
    assert "status" not in results
    gradient = results["gradient"]
    assert set(gradient) == (BASE_KEYS | DIRECTION_KEYS) - THETA_KEYS
    assert gradient["unit_vector_values"] == [1.0, 0.0]
    assert gradient["directional_derivative_value"] == 0.0


# ---------------------------------------------------------------------------
# Error guards (bible 91): zero-length directions, domain errors, no raises
# ---------------------------------------------------------------------------

def test_zero_vector_direction_is_error_e2():
    results = solve_gradient(
        gradient_exercise(point=["1", "1"], vector=["0", "0"])
    )
    assert results["status"] == "error"


def test_direction_that_parses_to_zero_is_error():
    # bible 80 "parses to ⟨0, 0⟩" semantics: sin(0) is only zero after parsing.
    results = solve_gradient(gradient_exercise(vector=["sin(0)", "0"]))
    assert results["status"] == "error"


def test_coincident_two_points_is_error():
    results = solve_gradient(
        {
            "function": "x**2 + y**2",
            "initial_point": ["1", "2"],
            "final_point": ["1", "2"],
        }
    )
    assert results["status"] == "error"


def test_max_ascent_zero_gradient_is_error():
    # Unlike the omit-theta cases above, max_ascent NEEDS the direction (91).
    results = solve_gradient(
        gradient_exercise(point=["0", "0"], direction_source="max_ascent")
    )
    assert results["status"] == "error"


def test_pole_at_point_is_error():
    # fx = 1/x at x=0 -> zoo: divergent, never a symbolic success.
    results = solve_gradient(
        gradient_exercise(function="log(x) + y", point=["0", "1"])
    )
    assert results["status"] == "error"


def test_complex_value_at_point_is_error():
    # fx = 1/(2√x) at x=-1 is imaginary: domain error at the point.
    results = solve_gradient(
        gradient_exercise(function="sqrt(x) + y", point=["-1", "1"])
    )
    assert results["status"] == "error"


def test_unparseable_input_is_error_not_raise():
    # solve_gradient never raises (implicit multiplication never parses).
    results = solve_gradient(gradient_exercise(function="2x"))
    assert results["status"] == "error"
    assert "error_message" in results
