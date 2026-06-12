"""Golden acceptance tests (bible/47_golden_expected_v3_2.md).

Runs the REAL in-memory pipeline over
bible/46_test_data_integral_edge_cases_v3_2.json and asserts the bible-47
expected render-model values field-for-field for Ex 1, 7, 5, 6, and 9
(Ex 9 is an INTENDED ERROR: its error item passing is a success, not a bug),
plus the formatter Rounding Rule Guard and the acceptance rule that the full
run completes without halting. No pdflatex is required here; real PDF
compilation is the manual acceptance run.

Some assertions overlap test_adapter/test_pipeline by design: this file is
the bible-47 acceptance contract in one place.
"""

import json
from pathlib import Path

import pytest

from solucionario.fileio import load_display_defaults
from solucionario.pipeline import process_document
from solucionario.render.formatting import format_decimal

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BIBLE_46_PATH = PROJECT_ROOT / "bible" / "46_test_data_integral_edge_cases_v3_2.json"

PROCESSED_INFO = {
    "timestamp": "2026-06-12T10:00:00Z",
    "filename": "itson_c3_test_9001_20260612_100000_extended.json",
    "filename_base": "itson_c3_test_9001_20260612_100000",
    "naming_mode": "testing",
}


@pytest.fixture(scope="module")
def golden_run():
    input_json = json.loads(BIBLE_46_PATH.read_text(encoding="utf-8"))
    return process_document(
        input_json,
        processed_info=PROCESSED_INFO,
        display_defaults=load_display_defaults(),
    )


def item(golden_run, label: str) -> dict:
    matches = [
        i for i in golden_run["render_model"]["items"] if i["exercise_label"] == label
    ]
    assert len(matches) == 1
    return matches[0]


def extended_exercise(golden_run, id) -> dict:
    matches = [
        e for e in golden_run["extended_json"]["exercises"] if e.get("id") == id
    ]
    assert len(matches) == 1
    return matches[0]


# ---------------------------------------------------------------------------
# Ex 1 — Standard, double integral, function "1" (bible 47)
# ---------------------------------------------------------------------------

def test_ex1_standard(golden_run):
    ex1 = item(golden_run, "1")
    assert ex1["kind"] == "standard"
    assert ex1["exercise_label"] == "1"
    assert ex1["quantity_label"] == "A"  # inferred: 2 integrals + function "1"
    assert ex1["units"] == "u^2"
    assert ex1["solution_latex"] == "1"
    assert ex1["decimal_string"] == "1.0000"
    assert ex1["show_input"] is True
    assert ex1["show_symbolic"] is True
    assert ex1["show_numeric"] is True
    assert ex1["show_quantity"] is True
    # Source float per bible 47:
    assert extended_exercise(golden_run, 1)["results"]["numeric_value"] == 1.0


# ---------------------------------------------------------------------------
# Ex 7 — decimal override + quantity_label + units_override (bible 47)
# ---------------------------------------------------------------------------

def test_ex7_overrides(golden_run):
    ex7 = item(golden_run, "7")
    assert ex7["kind"] == "standard"
    assert ex7["exercise_label"] == "7"
    assert ex7["quantity_label"] == "Q"  # from display_override.quantity_label
    assert ex7["units"] == "C"  # from display_override.units_override, verbatim
    assert ex7["show_symbolic"] is False
    assert ex7["show_numeric"] is True
    # ∫₀²∫₀² x·y dy dx = 4 — and the B1 regression guard: TWO places.
    assert extended_exercise(golden_run, 7)["results"]["numeric_value"] == 4.0
    assert ex7["decimal_string"] == "4.00"


# ---------------------------------------------------------------------------
# Ex 5 — Component group (bible 47)
# ---------------------------------------------------------------------------

def test_ex5_component_group(golden_run):
    ex5 = item(golden_run, "5")
    assert ex5["kind"] == "component_group"
    assert ex5["exercise_label"] == "5"
    assert ex5["quantity_label"] == "A"
    assert ex5["units"] == "u^2"
    assert ex5["show_component_total"] is True
    assert ex5["show_component_symbolic"] is True
    assert ex5["show_component_operation"] is True
    assert ex5["show_numeric"] is True
    assert ex5["show_quantity"] is True
    assert ex5["total_latex"] == "1"
    assert ex5["total_decimal_string"] == "1.0000"
    assert ex5["operation_latex"] == r"\frac{1}{2} + \frac{1}{2}"
    assert ex5["operation_decimal_string"] == "0.5000 + 0.5000"

    first, second = ex5["components"]
    for expected_id, component in ((1, first), (2, second)):
        assert component["id_component"] == expected_id
        assert component["solution_latex"] == r"\frac{1}{2}"
        assert component["decimal_string"] == "0.5000"
        assert component["quantity_label"] == "A"
        assert component["units"] == "u^2"
        assert component["show_component_quantity"] is True
        assert component["show_numeric"] is True


# ---------------------------------------------------------------------------
# Ex 6 — Output group (bible 47)
# ---------------------------------------------------------------------------

def test_ex6_output_group(golden_run):
    ex6 = item(golden_run, "6")
    assert ex6["kind"] == "output_group"
    assert ex6["exercise_label"] == "6"
    first, second = ex6["outputs"]
    assert first["id_output"] == 1
    assert first["output_label"] == "Resultado 1"
    assert second["id_output"] == 2
    assert second["output_label"] == "Resultado 2"
    for output in (first, second):
        assert output["quantity_label"] == "A"
        assert output["units"] == "u^2"
        assert output["solution_latex"] == "1"
        assert output["decimal_string"] == "1.0000"
        assert output["show_quantity"] is True
        assert output["show_symbolic"] is True
        assert output["show_numeric"] is True


# ---------------------------------------------------------------------------
# Ex 9 — INTENDED ERROR (implicit multiplication; passing = success)
# ---------------------------------------------------------------------------

def test_ex9_intended_error(golden_run):
    assert item(golden_run, "9") == {
        "kind": "error",
        "exercise_label": "9",
        "message": "ERROR: no se pudo procesar este ejercicio.",
    }


# ---------------------------------------------------------------------------
# Rounding Rule Guard (formatter contract, exercise-independent)
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


# ---------------------------------------------------------------------------
# Acceptance rule 4: the full 46 run completes; Ex 9 does not stop Ex 10
# ---------------------------------------------------------------------------

def test_full_run_completes_and_ex10_processes(golden_run):
    items = golden_run["render_model"]["items"]
    # 12 exercises -> 10 items: Ex 5's two components and Ex 6's two outputs
    # each collapse into one group item.
    assert len(items) == 10
    assert [i["exercise_label"] for i in items] == [
        "1", "2", "3", "4", "5", "6", "7", "8", "9", "10",
    ]
    ex10 = item(golden_run, "10")
    assert ex10["kind"] == "standard"
    assert ex10["decimal_string"] == "0.3333"  # 1D ∫₀¹ x² dx = 1/3

    summary = golden_run["extended_json"]["metadata"]["processing_summary"]
    assert summary["total_exercises"] == 12
    assert summary["successful"] == 11
    assert summary["errors"] == 1


# ---------------------------------------------------------------------------
# Extended JSON purity after the golden run
# ---------------------------------------------------------------------------

def test_extended_json_purity(golden_run):
    forbidden = {
        "decimal_string", "total_decimal_string", "operation_decimal_string",
        "units", "exercise_label", "output_label", "message",
    }

    def walk(value):
        if isinstance(value, dict):
            for key, inner in value.items():
                yield key
                yield from walk(inner)
        elif isinstance(value, list):
            for inner in value:
                yield from walk(inner)

    keys = list(walk(golden_run["extended_json"]))
    assert [k for k in keys if str(k).startswith("_")] == []
    assert [k for k in keys if k in forbidden] == []
