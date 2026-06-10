"""Tests for Extended JSON assembly and internal-key stripping (bible 75).

Locks the canonical document shape, the underscore schema-closure guarantee
(M4B rule 8: no internal keys leak into serialized output), the canonical-
field override protection, and the processing_summary counting rules.
"""

import copy
import json

from solucionario.aggregation import aggregate_components
from solucionario.extended_json import (
    ALGORITHM_VERSION,
    SCHEMA_VERSION,
    build_extended_json,
    processing_summary,
    strip_internal_keys,
)
from solucionario.solvers.base import error_result
from solucionario.solvers.integral import solve_integral

PROCESSED_INFO = {
    "timestamp": "2026-06-09T10:30:45Z",
    "filename": "itson_c3_hw_18_extended.json",
    "filename_base": "itson_c3_hw_18",
    "naming_mode": "production",
}

# Render/template fields that must never appear anywhere in Extended JSON.
# (units_override / quantity_label inside display_override are INPUT fields
# and are legitimate; the exact keys below are adapter/render-model-only.)
FORBIDDEN_KEYS = {
    "decimal_string",
    "total_decimal_string",
    "operation_decimal_string",
    "units",
    "exercise_label",
    "output_label",
    "message",
}


def make_input(**overrides) -> dict:
    document = {
        "metadata": {
            "institution": "itson",
            "course_code": "c3",
            "course": "Calculus 3",
            "assignment": {"type": "hw", "number": 18},
        },
        "display_default": {"show_input": False, "decimal_places": 4},
        "exercises": [{"id": 1, "type": "integral", "function": "1", "integrals": []}],
    }
    document.update(overrides)
    return document


def success_exercise(id=1, **extra) -> dict:
    """A really-solved exercise: results include _symbolic_result."""
    exercise = {
        "id": id,
        "type": "integral",
        "function": "x**2",
        "integrals": [{"var": "x", "lower": "0", "upper": "1"}],
    }
    exercise["results"] = solve_integral(exercise)
    exercise.update(extra)
    return exercise


def golden_ex5_aggregated() -> list[dict]:
    """Golden Ex 5 solved + aggregated: results carry component AND the
    internal _symbolic_result handoff."""
    members = [
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
    for member in members:
        member["results"] = solve_integral(member)
    return aggregate_components(members)


def build(exercises, input_json=None, time_ms=312):
    return build_extended_json(
        input_json if input_json is not None else make_input(),
        exercises,
        processed_info=PROCESSED_INFO,
        processing_time_ms=time_ms,
    )


def walk_keys(value):
    if isinstance(value, dict):
        for key, item in value.items():
            yield key
            yield from walk_keys(item)
    elif isinstance(value, list):
        for item in value:
            yield from walk_keys(item)


# ---------------------------------------------------------------------------
# Stripping
# ---------------------------------------------------------------------------

def test_symbolic_result_stripped_from_solver_results():
    exercise = success_exercise()
    assert "_symbolic_result" in exercise["results"]  # present in memory
    document = build([exercise])
    results = document["exercises"][0]["results"]
    assert "_symbolic_result" not in results
    assert "_symbolic_result" in exercise["results"]  # original untouched


def test_underscore_keys_stripped_recursively():
    value = {
        "_top": 0,
        "keep": {
            "_nested": 1,
            "inner": [{"_deep": 2, "ok": 3}, {"_x": 4}, 5],
        },
    }
    assert strip_internal_keys(value) == {"keep": {"inner": [{"ok": 3}, {}, 5]}}


def test_component_object_preserved_while_internals_stripped():
    document = build(golden_ex5_aggregated())
    for exercise in document["exercises"]:
        results = exercise["results"]
        assert "_symbolic_result" not in results
        component = results["component"]
        assert set(component) == {
            "total_value", "total_latex", "operation", "operation_latex",
        }
        assert component["total_latex"] == "1"
        assert component["total_value"] == 1.0
        assert component["operation"] == "sum"
        assert component["operation_latex"] == r"\frac{1}{2} + \frac{1}{2}"


def test_error_result_shape_preserved():
    exercise = {"id": 9, "type": "integral", "function": "2x",
                "integrals": [], "results": error_result("Cannot parse expression: 2x")}
    document = build([exercise])
    results = document["exercises"][0]["results"]
    assert results == {
        "status": "error",
        "problem_latex": r"\text{ERROR: Could not process exercise}",
        "solution_latex": r"\text{ERROR}",
        "error_message": "Cannot parse expression: 2x",
    }


def test_success_result_shape_is_bible_75_canonical():
    document = build([success_exercise()])
    results = document["exercises"][0]["results"]
    assert set(results) == {"problem_latex", "solution_latex", "numeric_value"}
    assert results["solution_latex"] == r"\frac{1}{3}"
    assert isinstance(results["numeric_value"], float)


# ---------------------------------------------------------------------------
# Schema closure: no internal keys, no render/template fields, serializable
# ---------------------------------------------------------------------------

def full_document():
    """Success + component group + error + display overrides in one document."""
    error_exercise = {"id": 9, "type": "integral", "function": "2x",
                      "integrals": [], "results": error_result("boom")}
    override_exercise = success_exercise(
        id=7, display_override={"quantity_label": "M", "units_override": "kg"}
    )
    exercises = [success_exercise()] + golden_ex5_aggregated() + [
        override_exercise, error_exercise,
    ]
    return build(exercises, input_json=make_input(display_integral={"show_input": True}))


def test_schema_closure_no_underscore_keys_anywhere():
    document = full_document()
    offenders = [key for key in walk_keys(document) if str(key).startswith("_")]
    assert offenders == []


def test_no_render_or_template_fields_anywhere():
    document = full_document()
    offenders = [key for key in walk_keys(document) if key in FORBIDDEN_KEYS]
    assert offenders == []
    # ...while the legitimate INPUT override fields survive verbatim:
    override = next(e for e in document["exercises"] if e["id"] == 7)
    assert override["display_override"] == {"quantity_label": "M", "units_override": "kg"}


def test_json_serializable_round_trip():
    document = full_document()
    assert json.loads(json.dumps(document)) == document


# ---------------------------------------------------------------------------
# Document structure and canonical-field ownership
# ---------------------------------------------------------------------------

def test_document_structure():
    document = build([success_exercise()])
    assert document["schema_version"] == SCHEMA_VERSION
    assert document["kind"] == "extended"
    assert document["metadata"]["processed"] == {
        **PROCESSED_INFO, "algorithm_version": ALGORITHM_VERSION,
    }
    assert document["metadata"]["course"] == "Calculus 3"
    assert document["display_default"] == {"show_input": False, "decimal_places": 4}
    assert document["display_integral"] == {}  # absent in input -> {}


def test_canonical_fields_win_over_input_extras():
    input_json = make_input(
        schema_version="9.9",  # canonical: must NOT win
        kind="hacked",
        processing_summary={"bogus": True},
        custom_note="keep me",  # extra: must survive (reusability)
    )
    document = build([success_exercise()], input_json=input_json)
    assert document["schema_version"] == SCHEMA_VERSION
    assert document["kind"] == "extended"
    assert "processing_summary" not in {
        k: v for k, v in document.items() if k != "metadata"
    }
    assert document["custom_note"] == "keep me"


def test_output_exercises_are_the_processed_ones_not_input():
    processed = [success_exercise(id=42)]
    document = build(processed, input_json=make_input())  # input has id=1, no results
    assert [e["id"] for e in document["exercises"]] == [42]
    assert "results" in document["exercises"][0]


# ---------------------------------------------------------------------------
# processing_summary (constraint 3)
# ---------------------------------------------------------------------------

def test_processing_summary_counts_and_shape():
    exercises = [
        success_exercise(id=1),
        success_exercise(id=2),
        {"id": 3, "type": "integral", "function": "2x", "integrals": [],
         "results": error_result("boom")},
        {"id": 4, "type": "integral"},  # defensively: missing results = error
    ]
    summary = processing_summary(exercises, 312)
    assert summary == {
        "total_exercises": 4,
        "successful": 2,
        "errors": 2,
        "processing_time_ms": 312,
    }
    document = build(exercises)
    assert document["metadata"]["processing_summary"] == summary


def test_processing_summary_ignores_group_structural_errors():
    # A gapped component group: both members solved fine, no aggregation
    # happened. They count as successful here; the ADAPTER will surface the
    # group error later as a render item (bible 75).
    gapped = [
        success_exercise(id=5, id_component=1),
        success_exercise(id=5, id_component=3),
    ]
    summary = processing_summary(gapped, 1)
    assert summary["successful"] == 2
    assert summary["errors"] == 0


# ---------------------------------------------------------------------------
# Purity
# ---------------------------------------------------------------------------

def test_inputs_are_not_mutated():
    input_json = make_input(display_integral={"show_input": True})
    exercises = golden_ex5_aggregated() + [success_exercise(id=9)]
    input_snapshot = copy.deepcopy(input_json)
    exercises_snapshot = copy.deepcopy(exercises)

    build(exercises, input_json=input_json)

    assert input_json == input_snapshot
    assert exercises == exercises_snapshot  # _symbolic_result still in memory
