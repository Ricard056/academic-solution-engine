"""Tests for the Component Aggregation stage (bible 90/75).

Aggregation sums valid component groups only, writes the identical
results.component object onto every member, and leaves everything else —
standard exercises, output groups, invalid groups, failed members —
completely untouched (pass-through by reference).
"""

import copy

import pytest

from solucionario.aggregation import aggregate_components
from solucionario.solvers.base import error_result
from solucionario.solvers.integral import solve_integral

COMPONENT_KEYS = {"total_value", "total_latex", "operation", "operation_latex"}


def solved(id, *, letter=None, component=None, output=None,
           solution_latex="1", symbolic="1", numeric=1.0):
    """A hand-built solved exercise (bible 75 results + _symbolic_result)."""
    exercise = {
        "id": id,
        "type": "integral",
        "function": "1",
        "integrals": [
            {"var": "y", "lower": "0", "upper": "x"},
            {"var": "x", "lower": "0", "upper": "1"},
        ],
        "results": {
            "problem_latex": r"\int\limits_{0}^{1}\int\limits_{0}^{x} 1\, dy\, dx",
            "solution_latex": solution_latex,
            "numeric_value": numeric,
            "_symbolic_result": symbolic,
        },
    }
    if letter is not None:
        exercise["id_letter"] = letter
    if component is not None:
        exercise["id_component"] = component
    if output is not None:
        exercise["id_output"] = output
    return exercise


def halves(id=5):
    """Golden Ex 5 shape: two components of 1/2 each (bible 47)."""
    return [
        solved(id, component=1, solution_latex=r"\frac{1}{2}", symbolic="1/2", numeric=0.5),
        solved(id, component=2, solution_latex=r"\frac{1}{2}", symbolic="1/2", numeric=0.5),
    ]


# ---------------------------------------------------------------------------
# Aggregation of valid component groups
# ---------------------------------------------------------------------------

def test_two_component_sum_matches_golden_ex5():
    out = aggregate_components(halves())
    component = out[0]["results"]["component"]
    assert component["total_value"] == 1.0
    assert component["total_latex"] == "1"
    assert component["operation"] == "sum"
    assert component["operation_latex"] == r"\frac{1}{2} + \frac{1}{2}"


def test_bible_75_example_values():
    # 1/4 + 7/12 = 5/6 — the worked example of bible 75.
    members = [
        solved(3, component=1, solution_latex=r"\frac{1}{4}", symbolic="1/4", numeric=0.25),
        solved(3, component=2, solution_latex=r"\frac{7}{12}", symbolic="7/12",
               numeric=0.5833333333333334),
    ]
    component = aggregate_components(members)[0]["results"]["component"]
    assert component["total_latex"] == r"\frac{5}{6}"
    assert component["total_value"] == pytest.approx(5 / 6, rel=1e-12)
    assert component["operation_latex"] == r"\frac{1}{4} + \frac{7}{12}"


def test_identical_component_object_on_every_member():
    out = aggregate_components(halves())
    first = out[0]["results"]["component"]
    second = out[1]["results"]["component"]
    assert first == second
    assert first is second  # the IDENTICAL object, not a copy (bible 90)


def test_component_order_by_id_component_regardless_of_input_order():
    members = [
        solved(3, component=2, solution_latex=r"\frac{7}{12}", symbolic="7/12",
               numeric=0.5833333333333334),
        solved(3, component=1, solution_latex=r"\frac{1}{4}", symbolic="1/4", numeric=0.25),
    ]
    component = aggregate_components(members)[0]["results"]["component"]
    # operation_latex joins in id_component order even though c2 came first.
    assert component["operation_latex"] == r"\frac{1}{4} + \frac{7}{12}"


def test_single_component_group_aggregates():
    members = [solved(4, component=1, solution_latex=r"\frac{1}{2}",
                      symbolic="1/2", numeric=0.5)]
    component = aggregate_components(members)[0]["results"]["component"]
    assert component["total_latex"] == r"\frac{1}{2}"
    assert component["total_value"] == 0.5
    assert component["operation_latex"] == r"\frac{1}{2}"


def test_output_order_is_input_order():
    standard = solved(9)
    c2, c1 = halves()[1], halves()[0]
    out = aggregate_components([standard, c2, c1])
    assert out[0] is standard  # untouched pass-through, same position
    assert out[1]["id_component"] == 2  # replaced in place, order preserved
    assert out[2]["id_component"] == 1


# ---------------------------------------------------------------------------
# Pass-through cases (no aggregation)
# ---------------------------------------------------------------------------

def test_standard_exercises_pass_through_by_reference():
    standard = solved(1)
    out = aggregate_components([standard])
    assert out[0] is standard
    assert "component" not in out[0]["results"]


def test_output_groups_are_not_aggregated():
    members = [solved(6, output=1), solved(6, output=2)]
    out = aggregate_components(members)
    assert out[0] is members[0] and out[1] is members[1]
    assert all("component" not in e["results"] for e in out)


def test_invalid_group_sequence_gap_is_not_aggregated():
    members = [solved(5, component=1), solved(5, component=3)]  # gap
    out = aggregate_components(members)
    assert out[0] is members[0] and out[1] is members[1]
    assert all("component" not in e["results"] for e in out)


def test_invalid_component_operation_is_not_aggregated():
    members = halves()
    members[0]["component_operation"] = "product"
    out = aggregate_components(members)
    assert all("component" not in e["results"] for e in out)


def test_member_error_prevents_aggregation():
    members = halves()
    members[1]["results"] = error_result("Cannot solve integral: boom")
    out = aggregate_components(members)
    assert out[0] is members[0] and out[1] is members[1]
    assert "component" not in out[0]["results"]


def test_member_missing_symbolic_handoff_is_not_aggregated():
    members = halves()
    del members[1]["results"]["_symbolic_result"]
    out = aggregate_components(members)
    assert all("component" not in e["results"] for e in out)


def test_null_numeric_member_group_is_not_aggregated():
    # Component sums are numeric-only (bible 90): a symbolic-only member
    # (numeric_value: null) must refuse the whole group.
    members = [
        solved(3, component=1, solution_latex=r"\frac{1}{2}", symbolic="1/2", numeric=0.5),
        solved(3, component=2, solution_latex="a", symbolic="a", numeric=None),
    ]
    out = aggregate_components(members)
    assert out[0] is members[0] and out[1] is members[1]
    assert all("component" not in e["results"] for e in out)


def test_real_solver_chain_symbolic_member_not_aggregated():
    # bible 48 Ex3 shape: one numeric component, one symbolic component.
    exercises = [
        {
            "id": 3, "id_component": 1, "type": "integral", "quantity": "A",
            "function": "1",
            "integrals": [{"var": "y", "lower": "0", "upper": "x"},
                          {"var": "x", "lower": "0", "upper": "1"}],
        },
        {
            "id": 3, "id_component": 2, "type": "integral", "quantity": "A",
            "function": "1",
            "integrals": [{"var": "y", "lower": "0", "upper": "a"},
                          {"var": "x", "lower": "1", "upper": "2"}],
        },
    ]
    for exercise in exercises:
        exercise["results"] = solve_integral(exercise)
    assert exercises[1]["results"]["numeric_value"] is None  # sanity check

    out = aggregate_components(exercises)
    assert "component" not in out[0]["results"]
    assert "component" not in out[1]["results"]


# ---------------------------------------------------------------------------
# Purity of the output (bible 75/90)
# ---------------------------------------------------------------------------

def test_component_object_has_no_formatting_fields():
    out = aggregate_components(halves())
    component = out[0]["results"]["component"]
    assert set(component) == COMPONENT_KEYS
    assert "decimal_string" not in component
    assert "total_decimal_string" not in component
    assert "operation_decimal_string" not in component
    assert "units" not in component


def test_aggregation_only_adds_component_to_results():
    members = halves()
    out = aggregate_components(members)
    assert set(out[0]["results"]) == set(members[0]["results"]) | {"component"}
    # Exercise-level fields are untouched apart from the replaced results.
    for original, aggregated in zip(members, out):
        assert {k: v for k, v in aggregated.items() if k != "results"} == {
            k: v for k, v in original.items() if k != "results"
        }


def test_input_is_never_mutated():
    members = halves() + [solved(9), solved(6, output=1)]
    snapshot = copy.deepcopy(members)
    out = aggregate_components(members)
    assert members == snapshot  # originals byte-for-byte intact
    assert out is not members
    assert out[0] is not members[0]  # aggregated members are new dicts
    assert "component" not in members[0]["results"]


# ---------------------------------------------------------------------------
# Real solver chain (golden Ex 5 end to end through solve + aggregate)
# ---------------------------------------------------------------------------

def test_real_solver_chain_golden_ex5():
    exercises = [
        {
            "id": 5, "id_component": 1, "type": "integral", "quantity": "A",
            "function": "1",
            "integrals": [{"var": "y", "lower": "0", "upper": "x"},
                          {"var": "x", "lower": "0", "upper": "1"}],
        },
        {
            "id": 5, "id_component": 2, "type": "integral", "quantity": "A",
            "function": "1",
            "integrals": [{"var": "y", "lower": "0", "upper": "2 - x"},
                          {"var": "x", "lower": "1", "upper": "2"}],
        },
    ]
    for exercise in exercises:
        exercise["results"] = solve_integral(exercise)

    out = aggregate_components(exercises)
    component = out[0]["results"]["component"]
    assert component["total_latex"] == "1"
    assert component["total_value"] == pytest.approx(1.0, rel=1e-14)
    assert component["operation"] == "sum"
    assert component["operation_latex"] == r"\frac{1}{2} + \frac{1}{2}"
    assert out[1]["results"]["component"] is component
