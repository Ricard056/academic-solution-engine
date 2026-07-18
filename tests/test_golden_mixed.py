"""Golden acceptance tests — mixed contract (bible/54_golden_expected_mixed_v3_2.md).

Runs the REAL in-memory pipeline over bible/53_test_data_mixed_v3_2.json and
asserts the bible-54 expected render-model values: M1 (integral standard),
M2 (gradient two-points anchor, fully pinned incl. the ROUND_HALF_UP witness
8.4853), M3 (integral component group), M4 (gradient symbolic point), M5
(integral output group), M6 (symbolic integral, null numeric_value success),
and M7 (intended authored error) — plus the binding order lock (the D1
canonical-interleaving witness), the member-based summary lock 9/8/1, the
output-item cardinality (7 items for 9 members), simultaneous display-block
isolation, the Extended JSON metadata-absence lock, and the bible-54 TeX
substring/order locks.

Expectation sources, per the bible-54 conventions:
- decimal strings and boolean flags are BYTE-EXACT literals from 54;
- LaTeX fields are pinned as MATHEMATICAL content constructed HERE via
  public sympy.latex (the 49/52 discipline); bible 54 is the source of truth
  — no solver output is frozen.

This file never touches bibles 45-52: the pure goldens (47 over 46, 49 over
48, 52 over 51) stay frozen and keep passing unchanged.
"""

import json
from pathlib import Path

import pytest
import sympy

from solucionario.fileio import load_display_defaults
from solucionario.pipeline import process_document

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BIBLE_53_PATH = PROJECT_ROOT / "bible" / "53_test_data_mixed_v3_2.json"

PROCESSED_INFO = {
    "timestamp": "2026-07-17T10:00:00Z",
    "filename": "itson_c3_hw_9013_20260717_100000_extended.json",
    "filename_base": "itson_c3_hw_9013_20260717_100000",
    "naming_mode": "testing",
}

# bible 54 / 85: the generic Spanish render marker — the contractual
# expectation, deliberately NOT imported from production code.
GENERIC_ERROR_MESSAGE = "ERROR: no se pudo procesar este ejercicio."

X, Y, A, B = sympy.symbols("x y a b")


def vector(first, second) -> str:
    """bible 52/54/85 canonical vector delimiter mandate."""
    return (
        r"\left\langle " + sympy.latex(first)
        + r", \; " + sympy.latex(second) + r" \right\rangle"
    )


# --- bible 54 M2 pinned mathematical content (frozen 52 G1) ------------------
M2_GRADIENT_LATEX = vector(
    Y**3 * sympy.exp(X * Y), Y * (X * Y + 2) * sympy.exp(X * Y)
)
M2_EVALUATED_LATEX = vector(sympy.Integer(8), sympy.Integer(4))
M2_MAGNITUDE_LATEX = sympy.latex(4 * sympy.sqrt(5))
M2_UNIT_VECTOR_LATEX = vector(sympy.sqrt(2) / 2, sympy.sqrt(2) / 2)
M2_DERIVATIVE_LATEX = sympy.latex(6 * sympy.sqrt(2))
M2_THETA_LATEX = sympy.latex(sympy.atan(sympy.Rational(1, 2)))

# --- bible 54 M4 pinned mathematical content (frozen 52 G6) ------------------
M4_GRADIENT_LATEX = vector(2 * X, 2 * Y)
M4_EVALUATED_LATEX = vector(2 * A, 2 * B)
M4_MAGNITUDE_LATEX = sympy.latex(2 * sympy.sqrt(A**2 + B**2))
M4_THETA_LATEX = sympy.latex(sympy.atan2(2 * B, 2 * A))


@pytest.fixture(scope="module")
def golden_run():
    input_json = json.loads(BIBLE_53_PATH.read_text(encoding="utf-8"))
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


def walk_keys(value):
    if isinstance(value, dict):
        for key, inner in value.items():
            yield key
            yield from walk_keys(inner)
    elif isinstance(value, list):
        for inner in value:
            yield from walk_keys(inner)


# ---------------------------------------------------------------------------
# Order, kind coverage, and cardinality (binding — the D1 witness)
# ---------------------------------------------------------------------------

def test_canonical_interleaving_order_lock(golden_run):
    items = golden_run["render_model"]["items"]
    assert [i["exercise_label"] for i in items] == ["1", "2", "3", "4", "5", "6", "7"]
    assert [i["kind"] for i in items] == [
        "standard", "gradient", "component_group", "gradient",
        "output_group", "standard", "error",
    ]


def test_all_five_render_kinds_present(golden_run):
    kinds = {i["kind"] for i in golden_run["render_model"]["items"]}
    assert kinds == {"standard", "gradient", "component_group", "output_group", "error"}


def test_output_item_cardinality_seven_items_for_nine_members(golden_run):
    assert len(golden_run["render_model"]["items"]) == 7
    assert len(golden_run["extended_json"]["exercises"]) == 9


# ---------------------------------------------------------------------------
# M1 — integral standard (display_integral.show_input isolation)
# ---------------------------------------------------------------------------

def test_m1_integral_standard(golden_run):
    m1 = item(golden_run, "1")
    assert m1["kind"] == "standard"
    assert m1["quantity_label"] == "A"
    assert m1["units"] == "u^2"
    assert m1["solution_latex"] == "1"
    assert m1["decimal_string"] == "1.0000"
    assert m1["show_symbolic"] is True
    assert m1["show_numeric"] is True
    assert m1["show_quantity"] is True
    assert m1["show_input"] is False  # display_integral wins over display_default


# ---------------------------------------------------------------------------
# M2 — gradient two-points anchor (all six pieces, byte-exact decimals)
# ---------------------------------------------------------------------------

def test_m2_gradient_anchor_flags_and_decimals(golden_run):
    m2 = item(golden_run, "2")
    assert m2["kind"] == "gradient"
    for piece in (
        "gradient", "gradient_evaluated", "magnitude", "unit_vector",
        "directional_derivative", "theta_max",
    ):
        assert m2[f"show_{piece}"] is True
    for piece in (
        "gradient_evaluated", "magnitude", "unit_vector",
        "directional_derivative", "theta_max",
    ):
        assert m2[f"{piece}_numeric"] is True
    # byte-exact decimals (bible 54; ROUND_HALF_UP witness 8.4853)
    assert m2["gradient_evaluated_decimal"] == r"\left\langle 8.0000, \; 4.0000 \right\rangle"
    assert m2["unit_vector_decimal"] == r"\left\langle 0.7071, \; 0.7071 \right\rangle"
    assert m2["magnitude_decimal_string"] == "8.9443"
    assert m2["directional_derivative_decimal_string"] == "8.4853"
    assert m2["theta_max_decimal_string"] == "0.4636"


def test_m2_gradient_anchor_latex(golden_run):
    m2 = item(golden_run, "2")
    assert m2["gradient_latex"] == M2_GRADIENT_LATEX
    assert m2["gradient_evaluated_latex"] == M2_EVALUATED_LATEX
    assert m2["magnitude_latex"] == M2_MAGNITUDE_LATEX
    assert m2["unit_vector_latex"] == M2_UNIT_VECTOR_LATEX
    assert m2["directional_derivative_latex"] == M2_DERIVATIVE_LATEX
    assert m2["theta_max_latex"] == M2_THETA_LATEX


# ---------------------------------------------------------------------------
# M3 — integral component group
# ---------------------------------------------------------------------------

def test_m3_component_group(golden_run):
    m3 = item(golden_run, "3")
    assert m3["kind"] == "component_group"
    assert m3["quantity_label"] == "A"
    assert m3["units"] == "u^2"
    assert m3["total_latex"] == "1"
    assert m3["total_decimal_string"] == "1.0000"
    assert m3["operation_latex"] == r"\frac{1}{2} + \frac{1}{2}"
    assert m3["operation_decimal_string"] == "0.5000 + 0.5000"
    for flag in (
        "show_quantity", "show_numeric", "show_component_total",
        "show_component_symbolic", "show_component_operation",
    ):
        assert m3[flag] is True
    assert [c["id_component"] for c in m3["components"]] == [1, 2]
    for component in m3["components"]:
        assert component["solution_latex"] == r"\frac{1}{2}"
        assert component["decimal_string"] == "0.5000"


# ---------------------------------------------------------------------------
# M4 — gradient symbolic point (per-piece suppression)
# ---------------------------------------------------------------------------

def test_m4_gradient_symbolic_point(golden_run):
    m4 = item(golden_run, "4")
    assert m4["kind"] == "gradient"
    assert m4["show_gradient"] is True
    assert m4["gradient_latex"] == M4_GRADIENT_LATEX
    assert m4["show_gradient_evaluated"] is True
    assert m4["gradient_evaluated_latex"] == M4_EVALUATED_LATEX
    assert m4["gradient_evaluated_numeric"] is False
    assert m4["gradient_evaluated_decimal"] == ""
    assert m4["show_magnitude"] is True
    assert m4["magnitude_latex"] == M4_MAGNITUDE_LATEX
    assert m4["magnitude_numeric"] is False
    assert m4["magnitude_decimal_string"] == ""
    assert m4["show_theta_max"] is True
    assert m4["theta_max_latex"] == M4_THETA_LATEX
    assert m4["theta_max_numeric"] is False
    assert m4["theta_max_decimal_string"] == ""
    # absent pieces (no direction): resolved off, empty strings
    assert m4["show_unit_vector"] is False
    assert m4["unit_vector_latex"] == ""
    assert m4["unit_vector_numeric"] is False
    assert m4["unit_vector_decimal"] == ""
    assert m4["show_directional_derivative"] is False
    assert m4["directional_derivative_latex"] == ""
    assert m4["directional_derivative_numeric"] is False
    assert m4["directional_derivative_decimal_string"] == ""


# ---------------------------------------------------------------------------
# M5 — integral output group
# ---------------------------------------------------------------------------

def test_m5_output_group(golden_run):
    m5 = item(golden_run, "5")
    assert m5["kind"] == "output_group"
    assert [o["id_output"] for o in m5["outputs"]] == [1, 2]
    for n, output in zip((1, 2), m5["outputs"]):
        assert output["output_label"] == f"Resultado {n}"
        assert output["quantity_label"] == "A"
        assert output["units"] == "u^2"
        assert output["solution_latex"] == "1"
        assert output["decimal_string"] == "1.0000"
        assert output["show_quantity"] is True
        assert output["show_symbolic"] is True
        assert output["show_numeric"] is True


# ---------------------------------------------------------------------------
# M6 — symbolic integral inside a mixed document
# ---------------------------------------------------------------------------

def test_m6_symbolic_integral(golden_run):
    m6 = item(golden_run, "6")
    assert m6["kind"] == "standard"
    assert m6["quantity_label"] == "A"
    assert m6["units"] == "u^2"
    assert m6["solution_latex"] == "a b"
    assert m6["show_numeric"] is False  # Numeric-Availability Resolution
    assert m6["decimal_string"] == ""
    assert m6["show_symbolic"] is True
    assert m6["show_quantity"] is True
    assert m6["show_input"] is False  # display_integral.show_input


def test_m6_source_numeric_value_is_null_success(golden_run):
    (m6_source,) = [
        e for e in golden_run["extended_json"]["exercises"] if e.get("id") == 6
    ]
    assert m6_source["results"]["numeric_value"] is None
    assert m6_source["results"].get("status") != "error"


# ---------------------------------------------------------------------------
# M7 — intended authored error (run does not halt)
# ---------------------------------------------------------------------------

def test_m7_intended_error_is_exactly_the_generic_item(golden_run):
    m7 = item(golden_run, "7")
    assert m7 == {
        "kind": "error",
        "exercise_label": "7",
        "message": GENERIC_ERROR_MESSAGE,
    }


# ---------------------------------------------------------------------------
# Summary lock (binding — member-based)
# ---------------------------------------------------------------------------

def test_member_based_summary_lock(golden_run):
    summary = golden_run["extended_json"]["metadata"]["processing_summary"]
    assert summary["total_exercises"] == 9
    assert summary["successful"] == 8
    assert summary["errors"] == 1


# ---------------------------------------------------------------------------
# Extended JSON metadata-absence lock (binding, bible 92 non-persistence)
# ---------------------------------------------------------------------------

def test_extended_json_contains_no_render_routing_metadata(golden_run):
    # Substring match catches ANY spelling of shell/fragment/registry/
    # routing metadata and rendered_items (bible 54 lock).
    forbidden_substrings = ("template", "fragment", "registry", "shell", "render")
    offenders = [
        key
        for key in walk_keys(golden_run["extended_json"])
        if any(sub in str(key).lower() for sub in forbidden_substrings)
    ]
    assert offenders == []


# ---------------------------------------------------------------------------
# TeX expectations (bible 54 substring/order locks)
# ---------------------------------------------------------------------------

def test_tex_m2_six_lines_in_contract_order_with_decimals(golden_run):
    tex = golden_run["tex_string"]
    markers = [
        r"\nabla f(x, y) = " + M2_GRADIENT_LATEX,
        r"\nabla f(P) = " + M2_EVALUATED_LATEX
        + r" = \left\langle 8.0000, \; 4.0000 \right\rangle",
        r"\left| \nabla f(P) \right| = " + M2_MAGNITUDE_LATEX + " = 8.9443",
        r"\hat{u} = " + M2_UNIT_VECTOR_LATEX
        + r" = \left\langle 0.7071, \; 0.7071 \right\rangle",
        r"D_{\hat{u}} f = " + M2_DERIVATIVE_LATEX + " = 8.4853",
        r"\theta_{\max} = " + M2_THETA_LATEX + " = 0.4636",
    ]
    positions = [tex.find(marker) for marker in markers]
    assert all(position >= 0 for position in positions), (markers, positions)
    assert positions == sorted(positions)


def test_tex_m3_component_and_total_lines(golden_run):
    tex = golden_run["tex_string"]
    assert "Componente 1: " in tex
    assert "Componente 2: " in tex
    assert r"\frac{1}{2} + \frac{1}{2} = " in tex  # operation_latex in Total
    assert "= 0.5000 + 0.5000" in tex
    assert "Total: " in tex
    assert "= 1.0000" in tex


def test_tex_m6_symbolic_line_has_no_decimal_tail(golden_run):
    tex = golden_run["tex_string"]
    assert r"A = a b\, \mathrm{ u^2 }" in tex
    assert "a b =" not in tex


def test_tex_exactly_one_generic_error_marker(golden_run):
    assert golden_run["tex_string"].count(GENERIC_ERROR_MESSAGE) == 1


def test_tex_no_unit_vector_or_derivative_lines_for_m4(golden_run):
    # M2 contributes the only û / D_û f lines; M4 (no direction) adds none.
    tex = golden_run["tex_string"]
    assert tex.count(r"\hat{u} = ") == 1
    assert tex.count(r"D_{\hat{u}} f = ") == 1
    assert tex.count(r"\theta_{\max} = ") == 2  # M2 and M4 both show theta


def test_tex_document_header_and_completeness(golden_run):
    tex = golden_run["tex_string"]
    assert isinstance(tex, str)
    assert "TAREA 9013" in tex
    assert "Solucionario" in tex
    assert r"\end{document}" in tex