"""Jinja2 LaTeX string rendering (bible 85).

render_tex(render_model) -> str — the only public call. The loader root is
the project's templates/ directory, no subdirectory (CLAUDE.md). Every
render path uses undefined=StrictUndefined: a reference to a missing
render-model field raises instead of rendering empty (bible 85, Jinja2
Undefined Policy). autoescape stays off (LaTeX, not HTML).

Template routing (bible 85, Phase 2A): the template is selected EXCLUSIVELY
by render_model["document"]["template"] — never inferred from items or
exercise data. An absent key defaults to the integral template (Phase 1
render models carry no template field and must render byte-identically); a
present but unknown/None/empty value raises ValueError deterministically,
never a silent fallback.

String-out only: no file writing, no output paths, no pdflatex — those are
pipeline/fileio responsibilities (M7B). The optional templates_dir parameter
is a read-only Jinja2 loader-root override for tests and must never grow
into output-path handling.

Templates render already-resolved fields only; all logic lives in the
render adapter.
"""

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined

TEMPLATES_DIR = Path(__file__).resolve().parents[3] / "templates"
TEMPLATE_NAME = "solucionario_integrales.tex.j2"
GRADIENT_TEMPLATE_NAME = "solucionario_gradientes.tex.j2"
KNOWN_TEMPLATES = frozenset({TEMPLATE_NAME, GRADIENT_TEMPLATE_NAME})


def render_tex(render_model: dict, templates_dir=TEMPLATES_DIR) -> str:
    """Render the closed render model (bible 85) to a LaTeX string."""
    environment = Environment(
        loader=FileSystemLoader(str(templates_dir)),
        undefined=StrictUndefined,
        autoescape=False,
    )
    template = environment.get_template(_template_name(render_model["document"]))
    return template.render(
        document=render_model["document"],
        items=render_model["items"],
    )


def _template_name(document: dict) -> str:
    """bible 85 routing: select by document["template"] alone. Absent key ->
    integral template (Phase 1 back-compat); a present but unknown value
    (including None/"") -> deterministic ValueError, no silent fallback."""
    if "template" not in document:
        return TEMPLATE_NAME
    name = document["template"]
    if name not in KNOWN_TEMPLATES:
        raise ValueError(f"unknown render template: {name!r}")
    return name
