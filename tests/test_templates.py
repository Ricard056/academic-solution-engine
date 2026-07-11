"""Template rendering tests (bible 85, M7A).

Hand-built closed-contract render models (exact M6B field sets) rendered to
LaTeX strings. Locks: document fragments, the standard/component/output/
error branches, \\mathrm unit wrapping in the TEMPLATE, show_input scoped to
standard items only (P8), no leading "=" in the numeric-only output branch
(P7), total_latex under show_component_total (P9), StrictUndefined on every
render path, string-out-only behavior (no disk writes, no subprocess).

Phase 2A adds the template-routing section (select exclusively by
document["template"]; absent -> integral back-compat; present-but-invalid ->
deterministic error) and the gradient template section (six pieces in
contract order, per-piece show_*/*_numeric gating, error branch reading only
exercise_label/message, no units/quantity/problem_latex ever rendered).
"""

import ast
import copy
from pathlib import Path

import pytest
from jinja2.exceptions import UndefinedError

from solucionario.render import latex
from solucionario.render.latex import render_tex

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DOCUMENT = {
    "title": "TAREA 21",
    "subtitle": "Solucionario",
    "course": "Cálculo III",
    "assignment_label": "Tarea 21",
}

ERROR_ITEM = {
    "kind": "error",
    "exercise_label": "9",
    "message": "ERROR: no se pudo procesar este ejercicio.",
}


def standard_item(**overrides) -> dict:
    item = {
        "kind": "standard",
        "exercise_label": "1",
        "quantity_label": "A",
        "show_input": True,
        "show_symbolic": True,
        "show_numeric": True,
        "show_quantity": True,
        "problem_latex": "PROBLEMMARKER",
        "solution_latex": "1",
        "decimal_string": "1.0000",
        "units": "u^2",
    }
    item.update(overrides)
    return item


def component_group_item(**overrides) -> dict:
    component_base = {
        "quantity_label": "A",
        "units": "u^2",
        "show_component_quantity": True,
        "show_numeric": True,
        "problem_latex": "P8MARKER",  # grouped items must never render this
        "solution_latex": r"\frac{1}{2}",
        "decimal_string": "0.5000",
    }
    item = {
        "kind": "component_group",
        "exercise_label": "5",
        "quantity_label": "A",
        "units": "u^2",
        "show_quantity": True,
        "show_numeric": True,
        "show_component_total": True,
        "show_component_symbolic": True,
        "show_component_operation": True,
        "total_latex": "1",
        "total_decimal_string": "1.0000",
        "operation_latex": r"\frac{1}{2} + \frac{1}{2}",
        "operation_decimal_string": "0.5000 + 0.5000",
        "components": [
            {"id_component": 1, **component_base},
            {"id_component": 2, **component_base},
        ],
    }
    item.update(overrides)
    return item


def output_member(n, **overrides) -> dict:
    output = {
        "id_output": n,
        "output_label": f"Resultado {n}",
        "quantity_label": "A",
        "units": "u^2",
        "show_quantity": True,
        "show_symbolic": True,
        "show_numeric": True,
        "problem_latex": "P8MARKER",  # grouped items must never render this
        "solution_latex": "1",
        "decimal_string": "1.0000",
    }
    output.update(overrides)
    return output


def output_group_item(outputs) -> dict:
    return {"kind": "output_group", "exercise_label": "6", "outputs": outputs}


def render(*items) -> str:
    return render_tex({"document": DOCUMENT, "items": list(items)})


GRADIENT_DOCUMENT = {**DOCUMENT, "template": "solucionario_gradientes.tex.j2"}


def gradient_item(**overrides) -> dict:
    """Closed gradient render item (bible 85) with marker values that make
    presence/absence in the TeX unambiguous."""
    item = {
        "kind": "gradient",
        "exercise_label": "1",
        "show_gradient": True,
        "gradient_latex": r"\left\langle GRLATEX \right\rangle",
        "show_gradient_evaluated": True,
        "gradient_evaluated_latex": r"\left\langle 8, \; 4 \right\rangle",
        "gradient_evaluated_numeric": True,
        "gradient_evaluated_decimal": r"\left\langle 8.0000, \; 4.0000 \right\rangle",
        "show_magnitude": True,
        "magnitude_latex": r"4 \sqrt{5}",
        "magnitude_numeric": True,
        "magnitude_decimal_string": "8.9443",
        "show_unit_vector": True,
        "unit_vector_latex": "UVLATEX",
        "unit_vector_numeric": True,
        "unit_vector_decimal": "UVDECIMAL",
        "show_directional_derivative": True,
        "directional_derivative_latex": r"6 \sqrt{2}",
        "directional_derivative_numeric": True,
        "directional_derivative_decimal_string": "8.4853",
        "show_theta_max": True,
        "theta_max_latex": "THETALATEX",
        "theta_max_numeric": True,
        "theta_max_decimal_string": "0.4636",
    }
    item.update(overrides)
    return item


def render_gradient(*items) -> str:
    return render_tex({"document": GRADIENT_DOCUMENT, "items": list(items)})


# ---------------------------------------------------------------------------
# Document and base-template inheritance
# ---------------------------------------------------------------------------

def test_document_fragments_and_base_inheritance():
    tex = render(standard_item())
    assert r"\documentclass[12pt]{article}" in tex  # {% extends %} works
    assert r"\begin{document}" in tex and r"\end{document}" in tex
    assert "TAREA 21" in tex
    assert "Solucionario" in tex
    assert "Cálculo III" in tex
    assert r"\section*{Resultados}" in tex


def test_render_with_no_items_still_produces_document():
    tex = render()
    assert "TAREA 21" in tex
    assert r"\end{document}" in tex


# ---------------------------------------------------------------------------
# Standard items
# ---------------------------------------------------------------------------

def test_standard_item_full_line_and_mathrm_units():
    tex = render(standard_item())
    assert r"\textbf{ 1) }" in tex
    assert "A = 1 = 1.0000" in tex  # quantity = symbolic = decimal
    assert r"\mathrm{ u^2 }" in tex  # template wraps the plain token (85 P4)


def test_show_input_true_renders_problem_latex():
    assert "PROBLEMMARKER" in render(standard_item(show_input=True))


def test_show_input_false_omits_problem_latex():
    assert "PROBLEMMARKER" not in render(standard_item(show_input=False))


def test_standard_symbolic_only_branch():
    tex = render(standard_item(show_numeric=False))
    assert "A = 1" in tex
    assert "1.0000" not in tex


def test_standard_numeric_only_without_quantity_has_no_leading_equals():
    tex = render(standard_item(show_symbolic=False, show_quantity=False))
    assert "1.0000" in tex
    assert "= 1.0000" not in tex


# ---------------------------------------------------------------------------
# Component groups
# ---------------------------------------------------------------------------

def test_component_group_lines_and_total():
    tex = render(component_group_item())
    assert r"\textbf{ 5) }" in tex
    assert "Componente 1: " in tex
    assert "Componente 2: " in tex
    assert r"\frac{1}{2} + \frac{1}{2} = " in tex  # operation_latex in Total line
    assert "= 0.5000 + 0.5000" in tex  # operation_decimal_string
    assert "= 1.0000" in tex  # total_decimal_string
    assert r"\mathrm{ u^2 }" in tex


def test_component_total_latex_renders_under_show_component_total():
    # total_latex ("1") always renders when show_component_total is true,
    # even with the combination displays off (85 P9).
    tex = render(
        component_group_item(
            show_component_symbolic=False,
            show_component_operation=False,
            show_numeric=False,
        )
    )
    assert "Total: " in tex
    assert "0.5000 + 0.5000" not in tex
    assert r"\frac{1}{2} + \frac{1}{2} = " not in tex


def test_component_total_hidden_when_flag_false():
    tex = render(component_group_item(show_component_total=False))
    assert "Total: " not in tex


# ---------------------------------------------------------------------------
# Output groups
# ---------------------------------------------------------------------------

def test_output_group_labels_and_lines():
    tex = render(output_group_item([output_member(1), output_member(2)]))
    assert r"\textbf{ 6) }" in tex
    assert "Resultado 1: " in tex
    assert "Resultado 2: " in tex
    assert "A = 1 = 1.0000" in tex


def test_output_numeric_only_has_no_leading_equals():
    # P7 guard: numeric-only branch must not emit "= 1.0000".
    member = output_member(1, show_symbolic=False, show_quantity=False)
    tex = render(output_group_item([member]))
    assert "Resultado 1: }1.0000" in tex
    assert "= 1.0000" not in tex


def test_grouped_items_never_render_problem_latex():
    # 85 P8: show_input/problem_latex are standard-items-only.
    tex = render(
        component_group_item(),
        output_group_item([output_member(1)]),
    )
    assert "P8MARKER" not in tex


# ---------------------------------------------------------------------------
# Error items
# ---------------------------------------------------------------------------

def test_error_item_renders_generic_spanish_marker_in_red():
    tex = render(ERROR_ITEM)
    assert r"\textbf{ 9) }" in tex
    assert "ERROR: no se pudo procesar este ejercicio." in tex
    assert r"\textcolor{red}" in tex


# ---------------------------------------------------------------------------
# StrictUndefined and string-out-only behavior
# ---------------------------------------------------------------------------

def test_missing_declared_field_raises_strict_undefined():
    incomplete = standard_item()
    del incomplete["units"]
    with pytest.raises(UndefinedError):
        render(incomplete)


def test_render_tex_returns_str():
    assert isinstance(render(standard_item()), str)


def test_render_writes_no_tex_files_to_disk():
    before = set(PROJECT_ROOT.rglob("*.tex"))
    render(standard_item(), component_group_item(), ERROR_ITEM)
    assert set(PROJECT_ROOT.rglob("*.tex")) == before


def test_latex_module_imports_no_subprocess_or_os():
    tree = ast.parse(Path(latex.__file__).read_text(encoding="utf-8"))
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported |= {alias.name.split(".")[0] for alias in node.names}
        elif isinstance(node, ast.ImportFrom):
            imported.add((node.module or "").split(".")[0])
    assert imported == {"pathlib", "jinja2"}  # no subprocess, no os, no fileio


# ---------------------------------------------------------------------------
# Template routing (bible 85, Phase 2A): document.template selects, nothing
# else — absent defaults to integral; present-but-invalid fails loudly
# ---------------------------------------------------------------------------

def test_missing_template_key_defaults_to_integral():
    # DOCUMENT has no "template" key: the Phase 1 legacy path.
    tex = render(standard_item())
    assert "A = 1 = 1.0000" in tex  # integral standard branch rendered


def test_explicit_integral_template_is_byte_identical_to_default():
    legacy = render_tex({"document": DOCUMENT, "items": [standard_item()]})
    explicit = render_tex({
        "document": {**DOCUMENT, "template": "solucionario_integrales.tex.j2"},
        "items": [standard_item()],
    })
    assert explicit == legacy


@pytest.mark.parametrize(
    "bad", [None, "", "tarea_integrales.tex.j2", "nonexistent.tex.j2", 7]
)
def test_present_but_invalid_template_fails_deterministically(bad):
    model = {"document": {**DOCUMENT, "template": bad}, "items": []}
    with pytest.raises(ValueError, match="unknown render template"):
        render_tex(model)


def test_base_template_is_not_an_accepted_routing_target():
    # A real file under templates/ is still rejected: the router accepts the
    # two known template names, not anything loadable.
    model = {"document": {**DOCUMENT, "template": "base.tex.j2"}, "items": []}
    with pytest.raises(ValueError, match="unknown render template"):
        render_tex(model)


def test_render_tex_does_not_mutate_render_model():
    model = {
        "document": dict(GRADIENT_DOCUMENT),
        "items": [gradient_item(), dict(ERROR_ITEM)],
    }
    snapshot = copy.deepcopy(model)
    render_tex(model)
    assert model == snapshot


# ---------------------------------------------------------------------------
# Gradient template (bible 85/52): six pieces in contract order, per-piece
# gating, error branch, no units/quantity/problem_latex
# ---------------------------------------------------------------------------

def test_gradient_document_fragments_and_base_inheritance():
    tex = render_gradient(gradient_item())
    assert r"\documentclass[12pt]{article}" in tex  # {% extends %} works
    assert "TAREA 21" in tex
    assert "Solucionario" in tex
    assert "Cálculo III" in tex
    assert r"\section*{Resultados}" in tex
    assert r"\end{document}" in tex


def test_gradient_full_numeric_item_renders_all_six_lines_in_order():
    tex = render_gradient(gradient_item())
    assert r"\textbf{ 1) }" in tex
    markers = [
        r"\nabla f(x, y) = \left\langle GRLATEX \right\rangle",
        r"\nabla f(P) = \left\langle 8, \; 4 \right\rangle"
        r" = \left\langle 8.0000, \; 4.0000 \right\rangle",
        r"\left| \nabla f(P) \right| = 4 \sqrt{5} = 8.9443",
        r"\hat{u} = UVLATEX = UVDECIMAL",
        r"D_{\hat{u}} f = 6 \sqrt{2} = 8.4853",
        r"\theta_{\max} = THETALATEX = 0.4636",
    ]
    positions = [tex.find(marker) for marker in markers]
    assert all(position >= 0 for position in positions), (markers, positions)
    assert positions == sorted(positions)  # bible 85 contract order


def test_gradient_error_item_reads_only_label_and_message():
    # ERROR_ITEM carries ONLY kind/exercise_label/message; a successful
    # StrictUndefined render proves the error branch reads nothing else.
    tex = render_gradient(dict(ERROR_ITEM))
    assert r"\textbf{ 9) }" in tex
    assert "ERROR: no se pudo procesar este ejercicio." in tex
    assert r"\textcolor{red}" in tex


def test_gradient_suppressed_piece_renders_neither_latex_nor_decimal():
    # G5 shape: absent piece resolved off upstream.
    item = gradient_item(show_unit_vector=False, unit_vector_numeric=False)
    tex = render_gradient(item)
    assert "UVLATEX" not in tex
    assert "UVDECIMAL" not in tex
    assert r"\hat{u} =" not in tex


def test_gradient_symbolic_piece_renders_latex_without_decimal_tail():
    # G6 shape: line visible, decimal tail resolved off.
    item = gradient_item(theta_max_numeric=False, theta_max_decimal_string="")
    tex = render_gradient(item)
    assert r"\theta_{\max} = THETALATEX" in tex
    assert "0.4636" not in tex
    assert "THETALATEX =" not in tex  # no dangling equals after the symbolic


def test_gradient_decimal_gated_by_numeric_flag_not_string_emptiness():
    item = gradient_item(
        magnitude_numeric=False, magnitude_decimal_string="GHOSTDECIMAL"
    )
    tex = render_gradient(item)
    assert r"4 \sqrt{5}" in tex  # symbolic line still renders
    assert "GHOSTDECIMAL" not in tex  # the FLAG gates, not the empty string


def test_gradient_hidden_gradient_line():
    tex = render_gradient(gradient_item(show_gradient=False))
    assert "GRLATEX" not in tex
    assert r"\nabla f(x, y) =" not in tex


def test_gradient_template_reads_only_declared_fields():
    # gradient_item() declares NO show_input/problem_latex/units/quantity
    # fields; a successful StrictUndefined render proves the template never
    # reads them, and no unit token is ever wrapped.
    tex = render_gradient(gradient_item())
    assert r"\mathrm" not in tex


def test_gradient_template_strict_undefined_on_missing_field():
    incomplete = gradient_item()
    del incomplete["magnitude_decimal_string"]
    with pytest.raises(UndefinedError):
        render_gradient(incomplete)


def test_gradient_template_ignores_other_item_kinds():
    # Only kind == "gradient" and kind == "error" render; anything else is
    # skipped (mixed documents are hard-stopped far upstream, bible 91).
    tex = render_gradient(standard_item())
    assert "PROBLEMMARKER" not in tex
    assert "A = 1" not in tex
