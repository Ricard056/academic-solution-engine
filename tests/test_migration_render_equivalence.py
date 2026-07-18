"""TEMPORARY migration render-equivalence corpus tests (bible 92).

Proves render equivalence of the complete 45/46/48/51 corpus through the
legacy production-equivalent path and the universal shell/fragment path.
Each corpus document is processed ONCE by the real in-memory pipeline; the
resulting render model is rendered twice — once with the legacy
full-document template stamped, once with the neutral SHELL_NAME — and the
two TeX strings are compared.

Acceptance (bible 92 compatibility oracle): only reviewed whitespace-class
differences are permitted. The documented normalization lives in normalize()
below and DIES WITH THIS MODULE; it is deliberately narrow (strip trailing
spaces/tabs per line; collapse runs of blank lines; ignore leading/trailing
blank lines) — any remaining delta is a semantic or visible-content
difference and fails. Raw TeX difference information is captured in the
comparison record and surfaces in the assertion message on any failure.

This module is TEMPORARY by design: it is bible 45's first and only
executable coverage, and it is retired in the Batch F commit TOGETHER with
the two legacy templates it compares (bible 92 legacy-template lifecycle).
"""

import copy
import difflib
import json
from functools import lru_cache
from pathlib import Path

import pytest

from solucionario.fileio import load_display_defaults
from solucionario.pipeline import process_document
from solucionario.render.latex import SHELL_NAME, render_tex

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BIBLE_DIR = PROJECT_ROOT / "bible"

# The complete migration corpus (bible 92 deletion gate item 1) with each
# document's legacy production-equivalent full-document template.
CORPUS = (
    ("45_test_data_T21_v3_2.json", "solucionario_integrales.tex.j2"),
    ("46_test_data_integral_edge_cases_v3_2.json", "solucionario_integrales.tex.j2"),
    ("48_test_data_symbolic_v3_2.json", "solucionario_integrales.tex.j2"),
    ("51_test_data_gradient_v3_2.json", "solucionario_gradientes.tex.j2"),
)
CORPUS_NAMES = [name for name, _ in CORPUS]

PROCESSED_INFO = {
    "timestamp": "2026-07-17T10:00:00Z",
    "filename": "itson_c3_hw_0000_20260717_100000_extended.json",
    "filename_base": "itson_c3_hw_0000_20260717_100000",
    "naming_mode": "testing",
}


def normalize(tex: str) -> str:
    """The documented whitespace-class normalization (bible 92): strip
    trailing spaces/tabs per line; collapse every run of blank lines to one;
    ignore leading/trailing blank lines. NOTHING else — any surviving delta
    is a semantic/visible-content difference."""
    lines = [line.rstrip(" \t") for line in tex.split("\n")]
    collapsed: list[str] = []
    for line in lines:
        if line == "" and collapsed and collapsed[-1] == "":
            continue
        collapsed.append(line)
    while collapsed and collapsed[0] == "":
        collapsed.pop(0)
    while collapsed and collapsed[-1] == "":
        collapsed.pop()
    return "\n".join(collapsed)


@lru_cache(maxsize=None)
def comparison(name: str) -> dict:
    """Process one corpus document and render it through BOTH paths.

    Returns the full comparison record: raw TeX difference information plus
    the normalized comparison result (deletion-gate evidence, bible 92)."""
    legacy_template = dict(CORPUS)[name]
    input_json = json.loads((BIBLE_DIR / name).read_text(encoding="utf-8"))
    run = process_document(
        input_json,
        processed_info=PROCESSED_INFO,
        display_defaults=load_display_defaults(),
    )

    legacy_model = copy.deepcopy(run["render_model"])
    legacy_model["document"]["template"] = legacy_template
    universal_model = copy.deepcopy(run["render_model"])
    universal_model["document"]["template"] = SHELL_NAME

    legacy_tex = render_tex(legacy_model)
    universal_tex = render_tex(universal_model)

    raw_diff = list(
        difflib.unified_diff(
            legacy_tex.splitlines(keepends=True),
            universal_tex.splitlines(keepends=True),
            fromfile=f"legacy:{legacy_template}",
            tofile=f"universal:{SHELL_NAME}",
            n=1,
        )
    )
    return {
        "name": name,
        "legacy_template": legacy_template,
        "item_count": len(run["render_model"]["items"]),
        "legacy_tex": legacy_tex,
        "universal_tex": universal_tex,
        "raw_identical": legacy_tex == universal_tex,
        "raw_diff": raw_diff,
        "normalized_identical": normalize(legacy_tex) == normalize(universal_tex),
    }


def test_corpus_is_exactly_45_46_48_51():
    assert CORPUS_NAMES == [
        "45_test_data_T21_v3_2.json",
        "46_test_data_integral_edge_cases_v3_2.json",
        "48_test_data_symbolic_v3_2.json",
        "51_test_data_gradient_v3_2.json",
    ]
    for name in CORPUS_NAMES:
        assert (BIBLE_DIR / name).is_file()


@pytest.mark.parametrize("name", CORPUS_NAMES)
def test_corpus_normalized_equivalence(name):
    """The acceptance gate: after the documented whitespace normalization,
    both paths must produce identical TeX. The raw unified diff (the raw
    difference record) is attached to any failure."""
    record = comparison(name)
    assert record["normalized_identical"], (
        f"{name}: non-whitespace render delta between "
        f"{record['legacy_template']} and {SHELL_NAME}:\n"
        + "".join(record["raw_diff"])
    )


@pytest.mark.parametrize("name", CORPUS_NAMES)
def test_corpus_raw_delta_is_whitespace_class_only(name):
    """Independent guard on the RAW outputs: ignoring all whitespace, the
    two paths must emit the identical character stream — any visible-content
    delta fails here regardless of the normalization above."""
    record = comparison(name)
    assert "".join(record["legacy_tex"].split()) == "".join(
        record["universal_tex"].split()
    ), f"{name}: visible-content delta:\n" + "".join(record["raw_diff"])


@pytest.mark.parametrize("name", CORPUS_NAMES)
def test_corpus_documents_render_nonempty_item_lists(name):
    """Corpus sanity (bible 45 gains its first executable coverage here):
    every corpus document processes end to end and renders at least one
    item through both paths."""
    record = comparison(name)
    assert record["item_count"] > 0
    assert record["legacy_tex"].strip() and record["universal_tex"].strip()
