"""Universal renderer tests (bible 85 "Document Shell and Item Fragments").

Locks the Phase 2B-M rendering substrate: the closed FRAGMENT_REGISTRY, the
complete position-independent whole-list preflight, the InternalRenderError
taxonomy (missing/null/non-string/unknown item.kind, stale registry entry,
missing fragment, invalid shell metadata, StrictUndefined in fragment and
shell), per-item failure attribution with the cause preserved, the fixed
blank-line separator policy (byte-equivalent to the legacy inter-item
shape), fragment context exactly {item}, shell context exactly
{document, rendered_items}, non-mutation, and string-out behavior.

The universal shell/fragment path is the ONLY rendering path (bible 92):
_shell_name carries the shell metadata semantics (absent -> neutral shell;
invalid -> internal failure) for every render_tex invocation. The
migration-only byte-equivalence comparisons against the legacy
full-document templates were retired with those templates at the Batch F
deletion gate; the fixed-separator lock below remains the permanent
composition witness.
"""

import copy
import shutil

import pytest
from jinja2.exceptions import UndefinedError

from solucionario.render.latex import (
    FRAGMENT_REGISTRY,
    KNOWN_SHELLS,
    SHELL_NAME,
    TEMPLATES_DIR,
    InternalRenderError,
    _shell_name,
    render_tex,
)

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


def gradient_item(**overrides) -> dict:
    item = {
        "kind": "gradient",
        "exercise_label": "2",
        "show_gradient": True,
        "gradient_latex": "GRLATEX",
        "show_gradient_evaluated": True,
        "gradient_evaluated_latex": "GELATEX",
        "gradient_evaluated_numeric": True,
        "gradient_evaluated_decimal": "GEDECIMAL",
        "show_magnitude": True,
        "magnitude_latex": "MAGLATEX",
        "magnitude_numeric": True,
        "magnitude_decimal_string": "8.9443",
        "show_unit_vector": True,
        "unit_vector_latex": "UVLATEX",
        "unit_vector_numeric": True,
        "unit_vector_decimal": "UVDECIMAL",
        "show_directional_derivative": True,
        "directional_derivative_latex": "DDLATEX",
        "directional_derivative_numeric": True,
        "directional_derivative_decimal_string": "8.4853",
        "show_theta_max": True,
        "theta_max_latex": "THETALATEX",
        "theta_max_numeric": True,
        "theta_max_decimal_string": "0.4636",
    }
    item.update(overrides)
    return item


def universal_model(*items, document=None) -> dict:
    base = dict(DOCUMENT) if document is None else dict(document)
    base["template"] = SHELL_NAME
    return {"document": base, "items": list(items)}


def render_universal(*items, document=None) -> str:
    return render_tex(universal_model(*items, document=document))


def copy_templates(tmp_path, exclude=()):
    """Copy the production templates into an isolated loader root."""
    target = tmp_path / "templates"
    target.mkdir()
    for path in TEMPLATES_DIR.glob("*.j2"):
        if path.name not in exclude:
            shutil.copy(path, target / path.name)
    return target


# ---------------------------------------------------------------------------
# Registry closure (bible 85: Python-literal closed mapping)
# ---------------------------------------------------------------------------

def test_fragment_registry_is_the_closed_five_kind_mapping():
    assert set(FRAGMENT_REGISTRY) == {
        "standard", "component_group", "output_group", "gradient", "error",
    }
    for kind, fragment in FRAGMENT_REGISTRY.items():
        assert isinstance(kind, str)
        assert isinstance(fragment, str)
        assert fragment.startswith("item_") and fragment.endswith(".tex.j2")


def test_known_shells_contains_exactly_the_neutral_shell():
    # Closed one-shell rule (bible 85/92): the shell allowlist is EXACTLY
    # the one neutral universal shell — nothing else is ever a shell.
    assert KNOWN_SHELLS == frozenset({SHELL_NAME})


# ---------------------------------------------------------------------------
# Preflight: item.kind taxonomy (bible 85, internal failures)
# ---------------------------------------------------------------------------

def test_missing_item_kind_is_internal_failure_with_index():
    with pytest.raises(InternalRenderError, match="item 0 has no render kind"):
        render_universal({"exercise_label": "1"})


@pytest.mark.parametrize("bad_kind", [None, 7, [], {}])
def test_non_string_item_kind_is_internal_failure(bad_kind):
    with pytest.raises(InternalRenderError, match="non-string render kind"):
        render_universal({"kind": bad_kind, "exercise_label": "1"})


def test_unknown_item_kind_is_internal_failure():
    with pytest.raises(InternalRenderError, match="unknown render kind: 'bogus_kind'"):
        render_universal({"kind": "bogus_kind", "exercise_label": "1"})


@pytest.mark.parametrize("bad_items", [None, {}, "items", 7])
def test_items_must_be_a_list(bad_items):
    model = {"document": {**DOCUMENT, "template": SHELL_NAME}, "items": bad_items}
    with pytest.raises(InternalRenderError, match="must be a list"):
        render_tex(model)


def test_preflight_is_whole_list_and_position_independent():
    """A bad kind at the END fails before ANY fragment renders: the first
    item is StrictUndefined-poisoned (rendering it would raise a wrapped
    fragment failure), yet the reported failure is the preflight unknown-kind
    diagnostic for the LAST item."""
    poisoned = {"kind": "standard", "exercise_label": "1"}  # missing fields
    with pytest.raises(InternalRenderError, match="item 1 has an unknown render kind"):
        render_universal(poisoned, {"kind": "bogus_kind", "exercise_label": "2"})


# ---------------------------------------------------------------------------
# Preflight: stale registry entry / missing fragment / missing shell
# ---------------------------------------------------------------------------

def test_stale_registry_entry_fails_even_when_kind_unused(tmp_path):
    """Preflight loads EVERY registry fragment: a missing fragment file
    fails the render even when no item of that kind is present."""
    templates = copy_templates(tmp_path, exclude=("item_gradient.tex.j2",))
    with pytest.raises(
        InternalRenderError, match="cannot load render template 'item_gradient.tex.j2'"
    ):
        render_tex(universal_model(standard_item()), templates_dir=templates)


def test_missing_shell_file_is_internal_failure(tmp_path):
    templates = copy_templates(tmp_path, exclude=(SHELL_NAME,))
    with pytest.raises(
        InternalRenderError, match=f"cannot load render template '{SHELL_NAME}'"
    ):
        render_tex(universal_model(standard_item()), templates_dir=templates)


# ---------------------------------------------------------------------------
# Shell metadata semantics (bible 85; final semantics carried by _shell_name)
# ---------------------------------------------------------------------------

def test_absent_template_resolves_to_the_neutral_shell():
    assert _shell_name(dict(DOCUMENT)) == SHELL_NAME


def test_explicit_neutral_shell_is_accepted():
    assert _shell_name({**DOCUMENT, "template": SHELL_NAME}) == SHELL_NAME


@pytest.mark.parametrize(
    "bad", [None, "", 7, "nonexistent.tex.j2", "base.tex.j2"]
)
def test_invalid_shell_metadata_is_internal_failure(bad):
    with pytest.raises(InternalRenderError, match="invalid document shell metadata"):
        _shell_name({**DOCUMENT, "template": bad})


# ---------------------------------------------------------------------------
# StrictUndefined failures: per-item attribution, cause preserved
# ---------------------------------------------------------------------------

def test_fragment_failure_carries_index_label_kind_and_fragment():
    incomplete = standard_item()
    del incomplete["units"]
    with pytest.raises(InternalRenderError) as excinfo:
        render_universal(ERROR_ITEM, incomplete)
    message = str(excinfo.value)
    assert "item 1" in message
    assert "exercise_label='1'" in message
    assert "kind='standard'" in message
    assert "fragment='item_standard.tex.j2'" in message
    assert isinstance(excinfo.value.__cause__, UndefinedError)


def test_shell_failure_after_fragments_is_same_class():
    document = dict(DOCUMENT)
    del document["title"]  # the shell reads document.title
    with pytest.raises(InternalRenderError) as excinfo:
        render_universal(ERROR_ITEM, document=document)
    assert "document shell" in str(excinfo.value)
    assert isinstance(excinfo.value.__cause__, UndefinedError)


def test_internal_failures_never_render_the_academic_error_marker():
    with pytest.raises(InternalRenderError) as excinfo:
        render_universal({"kind": "bogus_kind", "exercise_label": "1"})
    assert "no se pudo procesar" not in str(excinfo.value)


# ---------------------------------------------------------------------------
# Contexts: fragments get exactly {item}; the shell gets exactly
# {document, rendered_items}
# ---------------------------------------------------------------------------

def test_fragments_receive_no_document_context(tmp_path):
    templates = copy_templates(tmp_path)
    (templates / "item_error.tex.j2").write_text(
        "{{ document.title }}\n", encoding="utf-8"
    )
    with pytest.raises(InternalRenderError) as excinfo:
        render_tex(universal_model(ERROR_ITEM), templates_dir=templates)
    assert isinstance(excinfo.value.__cause__, UndefinedError)


def test_shell_receives_no_raw_items_context(tmp_path):
    templates = copy_templates(tmp_path)
    (templates / SHELL_NAME).write_text("{{ items }}\n", encoding="utf-8")
    with pytest.raises(InternalRenderError) as excinfo:
        render_tex(universal_model(ERROR_ITEM), templates_dir=templates)
    assert isinstance(excinfo.value.__cause__, UndefinedError)


# ---------------------------------------------------------------------------
# Fixed separator policy (bible 85 composition). The migration-only
# byte-equivalence comparisons against the legacy full-document templates
# were retired together with those templates at the Batch F deletion gate.
# ---------------------------------------------------------------------------

def test_fixed_blank_line_separator_between_items():
    """The documented separator policy: every fragment body is framed by the
    legacy blank-line shape, i.e. exactly seven newlines separate two
    consecutive error lines (body trailing newline + 3 framing + 3 framing)."""
    tex = render_universal(ERROR_ITEM, ERROR_ITEM)
    line = r"\textbf{ 9) } \textcolor{red}{ ERROR: no se pudo procesar este ejercicio. }"
    assert tex.count(line) == 2
    assert line + "\n\n\n\n\n\n\n" + line in tex


# ---------------------------------------------------------------------------
# Non-mutation and string-out
# ---------------------------------------------------------------------------

def test_universal_render_does_not_mutate_the_render_model():
    model = universal_model(standard_item(), gradient_item(), dict(ERROR_ITEM))
    snapshot = copy.deepcopy(model)
    render_tex(model)
    assert model == snapshot


def test_universal_render_returns_str():
    assert isinstance(render_universal(standard_item()), str)
