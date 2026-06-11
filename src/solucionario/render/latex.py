"""Jinja2 LaTeX string rendering (bible 85).

render_tex(render_model) -> str — the only public call. The loader root is
the project's templates/ directory, no subdirectory (CLAUDE.md). Every
render path uses undefined=StrictUndefined: a reference to a missing
render-model field raises instead of rendering empty (bible 85, Jinja2
Undefined Policy). autoescape stays off (LaTeX, not HTML).

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


def render_tex(render_model: dict, templates_dir=TEMPLATES_DIR) -> str:
    """Render the closed render model (bible 85) to a LaTeX string."""
    environment = Environment(
        loader=FileSystemLoader(str(templates_dir)),
        undefined=StrictUndefined,
        autoescape=False,
    )
    template = environment.get_template(TEMPLATE_NAME)
    return template.render(
        document=render_model["document"],
        items=render_model["items"],
    )
