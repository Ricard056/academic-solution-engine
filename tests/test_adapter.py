"""Tests for build_render_model closed-contract field population (bible 85).

Fixtures run the REAL upstream chain — solve_integral -> aggregate_components
-> build_extended_json — so the adapter is tested against canonical Extended
JSON, with the real config/display_defaults/default.json as the hardcoded
template. Exact key-set assertions enforce the closed render contract for
every item kind.
"""

import copy
import json
from pathlib import Path

from solucionario.aggregation import aggregate_components
from solucionario.extended_json import build_extended_json
from solucionario.render.adapter import ERROR_MESSAGE, build_render_model
from solucionario.solvers.base import error_result
from solucionario.solvers.integral import solve_integral

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULTS = json.loads(
    (PROJECT_ROOT / "config" / "display_defaults" / "default.json").read_text(
        encoding="utf-8"
    )
)

PROCESSED_INFO = {
    "timestamp": "2026-06-09T10:30:45Z",
    "filename": "itson_c3_hw_21_extended.json",
    "filename_base": "itson_c3_hw_21",
    "naming_mode": "production",
}

STANDARD_FIELDS = {
    "kind", "exercise_label", "quantity_label", "show_input", "show_symbolic",
    "show_numeric", "show_quantity", "problem_latex", "solution_latex",
    "decimal_string", "units",
}
COMPONENT_GROUP_FIELDS = {
    "kind", "exercise_label", "quantity_label", "units", "show_quantity",
    "show_numeric", "show_component_total", "show_component_symbolic",
    "show_component_operation", "total_latex", "total_decimal_string",
    "operation_latex", "operation_decimal_string", "components",
}
COMPONENT_FIELDS = {
    "id_component", "quantity_label", "units", "show_component_quantity",
    "show_numeric", "problem_latex", "solution_latex", "decimal_string",
}
OUTPUT_GROUP_FIELDS = {"kind", "exercise_label", "outputs"}
OUTPUT_FIELDS = {
    "id_output", "output_label", "quantity_label", "units", "show_quantity",
    "show_symbolic", "show_numeric", "problem_latex", "solution_latex",
    "decimal_string",
}
ERROR_FIELDS = {"kind", "exercise_label", "message"}

RENDER_ONLY_KEYS = {
    "decimal_string", "total_decimal_string", "operation_decimal_string",
    "units", "exercise_label", "output_label", "message",
}


def unit_square(function="1", **extra) -> dict:
    exercise = {
        "id": 1,
        "type": "integral",
        "function": function,
        "integrals": [
            {"var": "y", "lower": "0", "upper": "1"},
            {"var": "x", "lower": "0", "upper": "1"},
        ],
    }
    exercise.update(extra)
    return exercise


def solved(exercise: dict) -> dict:
    exercise["results"] = solve_integral(exercise)
    return exercise


def failed(exercise: dict) -> dict:
    exercise["results"] = error_result("Cannot parse expression: 2x")
    return exercise


def ex5_components() -> list[dict]:
    return [
        solved({
            "id": 5, "id_component": 1, "type": "integral", "quantity": "A",
            "function": "1",
            "integrals": [{"var": "y", "lower": "0", "upper": "x"},
                          {"var": "x", "lower": "0", "upper": "1"}],
        }),
        solved({
            "id": 5, "id_component": 2, "type": "integral", "quantity": "A",
            "function": "1",
            "integrals": [{"var": "y", "lower": "0", "upper": "2 - x"},
                          {"var": "x", "lower": "1", "upper": "2"}],
        }),
    ]


def ex6_outputs() -> list[dict]:
    return [
        solved(unit_square(id=6, id_output=1)),
        solved({
            "id": 6, "id_output": 2, "type": "integral", "function": "1",
            "integrals": [{"var": "y", "lower": "0", "upper": "1"},
                          {"var": "x", "lower": "1", "upper": "2"}],
        }),
    ]


def extended(exercises, **top_level) -> dict:
    input_json = {
        "metadata": {"course": "Calculus 3", "assignment": {"type": "hw", "number": 21}},
    }
    input_json.update(top_level)
    processed = aggregate_components(exercises)
    return build_extended_json(
        input_json, processed, processed_info=PROCESSED_INFO, processing_time_ms=1
    )


def model_for(exercises, **top_level) -> dict:
    return build_render_model(extended(exercises, **top_level), DEFAULTS)


def walk_keys(value):
    if isinstance(value, dict):
        for key, item in value.items():
            yield key
            yield from walk_keys(item)
    elif isinstance(value, list):
        for item in value:
            yield from walk_keys(item)


# ---------------------------------------------------------------------------
# Document block
# ---------------------------------------------------------------------------

def test_document_labels():
    document = model_for([solved(unit_square())])["document"]
    assert document == {
        "title": "TAREA 21",
        "subtitle": "Solucionario",
        "course": "Cálculo III",
        "assignment_label": "Tarea 21",
    }


def test_document_unmapped_fallbacks():
    extended_json = extended([solved(unit_square())])
    extended_json["metadata"]["assignment"] = {"type": "lab", "number": 3}
    extended_json["metadata"]["course"] = "Physics 1"
    document = build_render_model(extended_json, DEFAULTS)["document"]
    assert document["assignment_label"] == "lab 3"  # token verbatim, never fails
    assert document["title"] == "LAB 3"
    assert document["course"] == "Physics 1"  # unmapped course verbatim


# ---------------------------------------------------------------------------
# Standard items
# ---------------------------------------------------------------------------

def test_standard_item_golden_ex1():
    (item,) = model_for([solved(unit_square())])["items"]
    assert set(item) == STANDARD_FIELDS  # closed contract, exact
    assert item["kind"] == "standard"
    assert item["exercise_label"] == "1"
    assert item["quantity_label"] == "A"  # inferred: 2 integrals + "1"
    assert item["units"] == "u^2"
    assert item["solution_latex"] == "1"
    assert item["decimal_string"] == "1.0000"
    assert item["show_input"] is True
    assert item["show_symbolic"] is True
    assert item["show_numeric"] is True
    assert item["show_quantity"] is True


def test_standard_item_symbolic_success_show_numeric_forced_false():
    # bible 48 Ex1 shape: ∫₀ᵇ∫₀ᵃ 1 dy dx = a*b — symbolic-only success.
    exercise = solved({
        "id": 1, "type": "integral", "function": "1",
        "integrals": [{"var": "y", "lower": "0", "upper": "a"},
                      {"var": "x", "lower": "0", "upper": "b"}],
    })
    (item,) = model_for([exercise])["items"]
    assert set(item) == STANDARD_FIELDS  # closed contract shape unchanged
    assert item["quantity_label"] == "A"  # inferred: 2 integrals + function "1"
    assert item["units"] == "u^2"
    assert item["solution_latex"] == "a b"
    assert item["show_symbolic"] is True
    assert item["show_numeric"] is False  # RESOLVED off despite DEFAULTS true
    assert item["decimal_string"] == ""


def test_standard_item_symbolic_success_1d():
    # bible 48 Ex2 shape: ∫₀¹ k*x^2 dx = k/3 — parameter in the function, 1D.
    exercise = solved({
        "id": 2, "type": "integral", "function": "k*x**2",
        "integrals": [{"var": "x", "lower": "0", "upper": "1"}],
    })
    (item,) = model_for([exercise])["items"]
    assert item["quantity_label"] == "R"  # 1D never infers A/V
    assert item["units"] == "u"
    assert item["solution_latex"] == r"\frac{k}{3}"
    assert item["show_numeric"] is False
    assert item["decimal_string"] == ""


def test_standard_item_golden_ex7_overrides():
    exercise = solved({
        "id": 7, "type": "integral", "function": "x*y",
        "integrals": [{"var": "y", "lower": "0", "upper": "2"},
                      {"var": "x", "lower": "0", "upper": "2"}],
        "display_override": {
            "show_symbolic": False, "show_numeric": True, "decimal_places": 2,
            "quantity_label": "Q", "units_override": "C",
        },
    })
    (item,) = model_for([exercise])["items"]
    assert item["quantity_label"] == "Q"  # display_override.quantity_label wins
    assert item["units"] == "C"  # units_override verbatim
    assert item["show_symbolic"] is False
    assert item["show_numeric"] is True
    assert item["decimal_string"] == "4.00"  # TWO places: the B1 guard


# ---------------------------------------------------------------------------
# Output groups
# ---------------------------------------------------------------------------

def test_output_group_golden_ex6():
    (item,) = model_for(ex6_outputs())["items"]
    assert set(item) == OUTPUT_GROUP_FIELDS
    assert item["kind"] == "output_group"
    assert item["exercise_label"] == "6"
    first, second = item["outputs"]
    for output in (first, second):
        assert set(output) == OUTPUT_FIELDS
        assert output["quantity_label"] == "A"
        assert output["units"] == "u^2"
        assert output["solution_latex"] == "1"
        assert output["decimal_string"] == "1.0000"
        assert output["show_quantity"] is True
        assert output["show_symbolic"] is True
        assert output["show_numeric"] is True
    assert (first["id_output"], second["id_output"]) == (1, 2)
    assert first["output_label"] == "Resultado 1"
    assert second["output_label"] == "Resultado 2"


def test_output_group_member_symbolic_resolved_individually():
    # A symbolic-only member (numeric_value: null) is not a solver ERROR, so
    # bible 85 resolves show_numeric/decimal_string per member instead of
    # collapsing the whole output group.
    members = [
        solved(unit_square(id=6, id_output=1)),  # numeric: "1"
        solved({
            "id": 6, "id_output": 2, "type": "integral", "function": "1",
            "integrals": [{"var": "y", "lower": "0", "upper": "a"},
                          {"var": "x", "lower": "0", "upper": "1"}],
        }),  # symbolic: "a"
    ]
    (item,) = model_for(members)["items"]
    assert item["kind"] == "output_group"  # NOT collapsed to an error item
    numeric_output, symbolic_output = item["outputs"]
    assert numeric_output["show_numeric"] is True
    assert numeric_output["decimal_string"] == "1.0000"
    assert symbolic_output["show_numeric"] is False
    assert symbolic_output["decimal_string"] == ""
    assert symbolic_output["solution_latex"] == "a"


# ---------------------------------------------------------------------------
# Component groups
# ---------------------------------------------------------------------------

def test_component_group_golden_ex5():
    (item,) = model_for(ex5_components())["items"]
    assert set(item) == COMPONENT_GROUP_FIELDS
    assert item["kind"] == "component_group"
    assert item["exercise_label"] == "5"
    assert item["quantity_label"] == "A"
    assert item["units"] == "u^2"
    assert item["show_component_total"] is True
    assert item["show_component_symbolic"] is True
    assert item["show_component_operation"] is True
    assert item["show_numeric"] is True
    assert item["show_quantity"] is True
    assert item["total_latex"] == "1"
    assert item["total_decimal_string"] == "1.0000"
    assert item["operation_latex"] == r"\frac{1}{2} + \frac{1}{2}"
    assert item["operation_decimal_string"] == "0.5000 + 0.5000"
    for index, component in enumerate(item["components"], start=1):
        assert set(component) == COMPONENT_FIELDS
        assert component["id_component"] == index
        assert component["quantity_label"] == "A"
        assert component["units"] == "u^2"
        assert component["solution_latex"] == r"\frac{1}{2}"
        assert component["decimal_string"] == "0.5000"
        assert component["show_component_quantity"] is True
        assert component["show_numeric"] is True


def test_component_group_ignores_member_display_override():
    # Constraint 2: member-level display_override must not affect component
    # group formatting — group-level decimal_places (4) wins everywhere.
    members = ex5_components()
    members[0]["display_override"] = {"decimal_places": 2, "show_numeric": False}
    (item,) = model_for(members)["items"]
    assert item["total_decimal_string"] == "1.0000"
    assert item["operation_decimal_string"] == "0.5000 + 0.5000"
    assert item["components"][0]["decimal_string"] == "0.5000"
    assert item["show_numeric"] is True  # member flag override ignored too


def test_component_member_ordering_by_id_component():
    members = list(reversed(ex5_components()))  # c2 first in input
    (item,) = model_for(members)["items"]
    assert [c["id_component"] for c in item["components"]] == [1, 2]
    assert item["operation_decimal_string"] == "0.5000 + 0.5000"


# ---------------------------------------------------------------------------
# Errors: one generic message, no diagnostics exposed (constraint 1)
# ---------------------------------------------------------------------------

def test_per_exercise_error_item():
    (item,) = model_for([failed(unit_square(id=9, function="2x"))])["items"]
    assert set(item) == ERROR_FIELDS
    assert item == {"kind": "error", "exercise_label": "9", "message": ERROR_MESSAGE}


def test_structural_invalid_group_is_one_error_item():
    members = ex5_components()
    members[1]["id_component"] = 3  # gap: 1, 3
    items = model_for(members)["items"]
    assert items == [{"kind": "error", "exercise_label": "5", "message": ERROR_MESSAGE}]


def test_component_group_symbolic_member_collapses_to_error_item():
    # bible 48 Ex3: one numeric component + one symbolic component, both
    # quantity "A". Component sums are numeric-only (bible 90); aggregation
    # refuses the group, so the adapter collapses it to one error item.
    members = [
        solved({
            "id": 3, "id_component": 1, "type": "integral", "quantity": "A",
            "function": "1",
            "integrals": [{"var": "y", "lower": "0", "upper": "x"},
                          {"var": "x", "lower": "0", "upper": "1"}],
        }),
        solved({
            "id": 3, "id_component": 2, "type": "integral", "quantity": "A",
            "function": "1",
            "integrals": [{"var": "y", "lower": "0", "upper": "a"},
                          {"var": "x", "lower": "1", "upper": "2"}],
        }),
    ]
    items = model_for(members)["items"]
    assert items == [{"kind": "error", "exercise_label": "3", "message": ERROR_MESSAGE}]


def test_invalid_component_operation_is_one_error_item():
    members = ex5_components()
    members[0]["component_operation"] = "product"
    items = model_for(members)["items"]
    assert items == [{"kind": "error", "exercise_label": "5", "message": ERROR_MESSAGE}]


def test_component_member_error_collapses_group():
    members = ex5_components()
    members[1] = failed({
        "id": 5, "id_component": 2, "type": "integral", "quantity": "A",
        "function": "2x", "integrals": [{"var": "x", "lower": "0", "upper": "1"}],
    })
    items = model_for(members)["items"]
    assert items == [{"kind": "error", "exercise_label": "5", "message": ERROR_MESSAGE}]


def test_output_member_error_collapses_group():
    members = ex6_outputs()
    members[0] = failed(unit_square(id=6, id_output=1, function="2x"))
    items = model_for(members)["items"]
    assert items == [{"kind": "error", "exercise_label": "6", "message": ERROR_MESSAGE}]


def test_no_internal_diagnostics_leak_into_render_model():
    members = ex5_components()
    members[1] = failed(unit_square(id=5, id_component=2, function="2x"))
    model = model_for(members + [failed(unit_square(id=9, function="2x"))])
    serialized = json.dumps(model)
    assert "Cannot parse expression" not in serialized  # solver error_message
    assert "error_message" not in serialized
    assert "sequence gap" not in serialized  # validate_group diagnostics


# ---------------------------------------------------------------------------
# Ordering (bible 65) and purity
# ---------------------------------------------------------------------------

def test_items_ordered_by_id_and_letter():
    exercises = [
        solved(unit_square(id=2)),
        solved(unit_square(id=1, id_letter="b")),
        failed(unit_square(id=9, function="2x")),
        solved(unit_square(id=1, id_letter="a")),
    ]
    items = model_for(exercises)["items"]
    assert [item["exercise_label"] for item in items] == ["1.a", "1.b", "2", "9"]
    assert [item["kind"] for item in items] == [
        "standard", "standard", "standard", "error",
    ]


def test_extended_json_is_not_mutated():
    extended_json = extended(
        ex5_components() + ex6_outputs() + [solved(unit_square(id=1)),
                                            failed(unit_square(id=9, function="2x"))]
    )
    snapshot = copy.deepcopy(extended_json)
    build_render_model(extended_json, DEFAULTS)
    assert extended_json == snapshot


def test_no_render_fields_written_back_into_extended_json():
    extended_json = extended(ex5_components() + [solved(unit_square(id=1))])
    build_render_model(extended_json, DEFAULTS)
    offenders = [
        key for key in walk_keys(extended_json["exercises"])
        if key in RENDER_ONLY_KEYS
    ]
    assert offenders == []
