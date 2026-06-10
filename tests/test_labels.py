"""Tests for render-only labels and quantity/unit resolution (bible 85/70/65).

Locks the "1"/"1.a" label convention, the "Resultado N" output labels, the
85 §5 quantity precedence (override -> explicit -> inferred), the Unit
Derivation Rule (units_override verbatim, A/V exponents, "u" fallback), and
the purity of the module (no imports, no mutation, plain-string outputs).
"""

import ast
import copy
from pathlib import Path

import pytest

from solucionario.render import labels
from solucionario.render.labels import (
    derive_units,
    exercise_label,
    output_label,
    resolve_quantity_label,
)
from solucionario.validation import _resolved_quantity_label


def integral(function="1", n_integrals=2, **extra) -> dict:
    bound = {"var": "x", "lower": "0", "upper": "1"}
    exercise = {
        "id": 1,
        "type": "integral",
        "function": function,
        "integrals": [dict(bound) for _ in range(n_integrals)],
    }
    exercise.update(extra)
    return exercise


# ---------------------------------------------------------------------------
# exercise_label / output_label (bible 85/65)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "exercise, expected",
    [
        ({"id": 1}, "1"),
        ({"id": 1, "id_letter": "a"}, "1.a"),
        ({"id": 2, "id_letter": "b"}, "2.b"),
        ({"id": 10}, "10"),
        ({"id": 1.0, "id_letter": "a"}, "1.a"),  # whole float: no ".0"
        ({"id": 1.5}, "1.5"),  # non-integer float stringifies as-is
        ({"id": "10"}, "10"),  # invalid string id: defensive label for error items
        ({"id": 9, "id_letter": ""}, "9"),  # empty letter = no letter
    ],
)
def test_exercise_label(exercise, expected):
    assert exercise_label(exercise) == expected


@pytest.mark.parametrize(
    "id_output, expected",
    [
        (1, "Resultado 1"),
        (2, "Resultado 2"),
        (1.0, "Resultado 1"),  # user constraint: integer-like floats normalize
        (2.0, "Resultado 2"),
        (2.5, "Resultado 2.5"),  # non-integer stringifies defensively
    ],
)
def test_output_label(id_output, expected):
    assert output_label(id_output) == expected


# ---------------------------------------------------------------------------
# Quantity label precedence (bible 85 §5)
# ---------------------------------------------------------------------------

def test_quantity_override_wins_over_explicit_and_inference():
    exercise = integral(quantity="A", display_override={"quantity_label": "Q"})
    assert resolve_quantity_label(exercise) == "Q"  # golden Ex 7


def test_explicit_quantity_wins_over_inference():
    # Function "1" with 2 integrals would infer "A"; explicit "M" wins.
    assert resolve_quantity_label(integral(quantity="M")) == "M"


@pytest.mark.parametrize(
    "function, n_integrals, expected",
    [
        ("1", 2, "A"),  # golden Ex 1 inference
        ("1", 3, "V"),
        ("1", 1, "R"),  # 1D never infers A/V
        ("1", 0, "R"),
        ("x + y", 2, "R"),  # function != "1"
        ("x*y", 2, "R"),
        (" 1 ", 2, "A"),  # whitespace-normalized comparison ("cleaned")
        ("2", 2, "R"),
    ],
)
def test_quantity_inference(function, n_integrals, expected):
    assert resolve_quantity_label(integral(function, n_integrals)) == expected


def test_coordinate_system_is_passive_in_resolution():
    # The Jacobian "r" defeats the function=="1" heuristic and the
    # coordinate_system label changes nothing (bible 80/90).
    exercise = integral("r", 3, coordinate_system="cylindrical")
    assert resolve_quantity_label(exercise) == "R"
    assert resolve_quantity_label(integral("r", 3)) == "R"  # identical without it


def test_junk_display_override_is_ignored():
    assert resolve_quantity_label(integral(display_override="nope")) == "A"


def test_agrees_with_validation_group_resolution():
    # validation.py keeps a private copy of this rule for group-conflict
    # checks (layering: validation must not import render). Lock both
    # implementations together so they cannot drift.
    cases = [
        integral(),
        integral("1", 3),
        integral("x + y", 2),
        integral(quantity="M"),
        integral(quantity="A", display_override={"quantity_label": "Q"}),
        integral("r", 3, coordinate_system="cylindrical"),
    ]
    for exercise in cases:
        assert resolve_quantity_label(exercise) == _resolved_quantity_label(exercise)


# ---------------------------------------------------------------------------
# Unit derivation (bible 85)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "quantity_label, display, expected",
    [
        ("A", {"default_units": "u"}, "u^2"),
        ("V", {"default_units": "u"}, "u^3"),
        ("R", {"default_units": "u"}, "u"),
        ("M", {"default_units": "u"}, "u"),
        ("Q", {"default_units": "u"}, "u"),
        ("T", {"default_units": "u"}, "u"),
        ("A", {"default_units": "cm"}, "cm^2"),  # custom base units
        ("V", {"default_units": "cm"}, "cm^3"),
        ("A", {}, "u^2"),  # default_units missing -> "u"
        ("R", {"default_units": ""}, "u"),  # empty -> "u"
        ("Q", {"default_units": "u", "units_override": "C"}, "C"),  # golden Ex 7
        ("M", {"default_units": "u", "units_override": "kg"}, "kg"),  # bible Ex 4
        ("A", {"default_units": "u", "units_override": "kg"}, "kg"),  # wins over A^2
        ("V", {"units_override": r"\,m^3"}, r"\,m^3"),  # verbatim, even LaTeX
    ],
)
def test_unit_derivation(quantity_label, display, expected):
    assert derive_units(quantity_label, display) == expected


def test_units_are_plain_tokens_never_mathrm_wrapped():
    # Wrapping in \mathrm{...} is the TEMPLATE's job (bible 85, P4).
    for label in ("A", "V", "R"):
        assert "mathrm" not in derive_units(label, {"default_units": "u"})


# ---------------------------------------------------------------------------
# Purity
# ---------------------------------------------------------------------------

def test_outputs_are_plain_strings():
    exercise = integral(display_override={"quantity_label": "Q"})
    assert isinstance(exercise_label(exercise), str)
    assert isinstance(output_label(1), str)
    assert isinstance(resolve_quantity_label(exercise), str)
    assert isinstance(derive_units("A", {"default_units": "u"}), str)


def test_inputs_are_not_mutated():
    exercise = integral(
        quantity="A",
        display_override={"quantity_label": "Q", "units_override": "C"},
        id_letter="a",
    )
    display = {"default_units": "u", "units_override": "C"}
    snapshots = copy.deepcopy((exercise, display))

    exercise_label(exercise)
    resolve_quantity_label(exercise)
    derive_units("A", display)

    assert (exercise, display) == snapshots


def test_module_has_no_imports_at_all():
    tree = ast.parse(Path(labels.__file__).read_text(encoding="utf-8"))
    imports = [
        node for node in ast.walk(tree)
        if isinstance(node, (ast.Import, ast.ImportFrom))
    ]
    assert imports == []  # pure string/dict helpers: zero dependencies
