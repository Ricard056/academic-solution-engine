"""Tests for render-time decimal formatting.

Covers the Rounding Rule Guard in bible/47_golden_expected_v3_2.md and the
Decimal Formatting Rule in bible/85_render_adapter_and_jinja2_spec_v3_2.md,
plus the defensive constraints: invalid decimal_places and non-finite values
raise ValueError instead of formatting silently.
"""

import ast
from pathlib import Path

import pytest

from solucionario.render import formatting
from solucionario.render.formatting import (
    format_decimal,
    format_operation_decimal_string,
)


# ---------------------------------------------------------------------------
# Rounding Rule Guard (bible 47) — ROUND_HALF_UP, not banker's rounding
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "value, places, expected",
    [
        (2.5, 0, "3"),  # banker's rounding would give "2"
        (0.125, 2, "0.13"),  # banker's rounding would give "0.12"
        (0.12345, 4, "0.1235"),
    ],
)
def test_rounding_rule_guard(value, places, expected):
    assert format_decimal(value, places) == expected


def test_half_up_differs_from_forbidden_f_string():
    # The forbidden implementations are half-to-even; prove we diverge.
    assert format_decimal(0.25, 1) == "0.3"
    assert f"{0.25:.1f}" == "0.2"
    assert format_decimal(0.25, 1) != f"{0.25:.1f}"


# ---------------------------------------------------------------------------
# Exact places, trailing zeros, integers, negatives, artifacts
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "value, places, expected",
    [
        (0.25, 4, "0.2500"),  # bible 85 example: trailing zeros kept
        (1.0, 4, "1.0000"),  # golden Ex 1
        (4.0, 2, "4.00"),  # golden Ex 7 (decimal_places override)
        (1.5333333333333334, 4, "1.5333"),  # bible 85 render sample (23/15)
        (0.6666666666666666, 4, "0.6667"),
        (0.3333333333333333, 4, "0.3333"),
        (3.7, 0, "4"),  # n=0: no decimal point
        (1.0, 0, "1"),
        (-2.5, 0, "-3"),  # ties away from zero
        (-0.125, 2, "-0.13"),
        (-1.5, 0, "-2"),
        (5, 2, "5.00"),  # int input
        (0, 3, "0.000"),
        (1000000, 0, "1000000"),
        (0.1 + 0.2, 4, "0.3000"),  # 0.30000000000000004 artifact
        (2.675, 2, "2.68"),  # Decimal(str(v)) beats binary 2.67499...
    ],
)
def test_fixed_point_formatting(value, places, expected):
    result = format_decimal(value, places)
    assert result == expected
    assert isinstance(result, str)


# ---------------------------------------------------------------------------
# Defensive constraints
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("places", [-1, 2.0, "4", True, False, None])
def test_invalid_decimal_places_raises(places):
    with pytest.raises(ValueError, match="decimal_places"):
        format_decimal(1.0, places)


@pytest.mark.parametrize(
    "value", [float("nan"), float("inf"), float("-inf")]
)
def test_non_finite_values_raise(value):
    with pytest.raises(ValueError, match="non-finite"):
        format_decimal(value, 4)


# ---------------------------------------------------------------------------
# operation_decimal_string join (bible 85)
# ---------------------------------------------------------------------------

def test_operation_join_golden_ex5():
    assert format_operation_decimal_string([0.5, 0.5], 4) == "0.5000 + 0.5000"


def test_operation_join_mixed_values():
    values = [0.25, 0.5833333333333334]  # bible 75 example components
    assert format_operation_decimal_string(values, 4) == "0.2500 + 0.5833"


def test_operation_join_single_and_empty():
    assert format_operation_decimal_string([0.5], 4) == "0.5000"
    assert format_operation_decimal_string([], 4) == ""


def test_operation_join_propagates_validation():
    with pytest.raises(ValueError, match="non-finite"):
        format_operation_decimal_string([0.5, float("inf")], 4)
    with pytest.raises(ValueError, match="decimal_places"):
        format_operation_decimal_string([0.5], -1)


def test_operation_join_does_not_mutate_input():
    values = [0.5, 0.25]
    format_operation_decimal_string(values, 4)
    assert values == [0.5, 0.25]


# ---------------------------------------------------------------------------
# Import purity: stdlib decimal only (no solver/aggregation/extended_json)
# ---------------------------------------------------------------------------

def test_module_imports_only_stdlib_decimal():
    tree = ast.parse(Path(formatting.__file__).read_text(encoding="utf-8"))
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported |= {alias.name.split(".")[0] for alias in node.names}
        elif isinstance(node, ast.ImportFrom):
            imported.add((node.module or "").split(".")[0])
    assert imported == {"decimal"}
