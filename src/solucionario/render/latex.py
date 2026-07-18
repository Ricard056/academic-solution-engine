"""Jinja2 LaTeX string rendering (bible 85).

render_tex(render_model) -> str — the only public call. The loader root is
the project's templates/ directory, no subdirectory (CLAUDE.md). Every
render path uses undefined=StrictUndefined: a reference to a missing
render-model field raises instead of rendering empty (bible 85, Jinja2
Undefined Policy). autoescape stays off (LaTeX, not HTML).

Universal path (bible 85, "Document Shell and Item Fragments", Phase 2B-M):
ONE neutral document shell plus five closed item fragments selected through
the Python-literal FRAGMENT_REGISTRY — no path is ever constructed from
authored or render-model data. A complete, position-independent preflight
runs over the whole item list before any fragment render; fragments render
in list order with context exactly {item}; the shell renders with context
exactly {document, rendered_items}; no second escaping pass is applied to
rendered LaTeX. Internal failures are deterministic InternalRenderError with
per-item attribution (index, exercise_label, kind, fragment) and are never
converted to academic ERROR items (bible 92 trust boundaries).

Migration-window routing (bible 85, Phase 2A — removed at Phase 2B-M
closeout): the template is selected EXCLUSIVELY by
render_model["document"]["template"] — never inferred from items or exercise
data. An absent key defaults to the legacy integral template (Phase 1 render
models carry no template field and must render byte-identically);
SHELL_NAME routes to the universal path; a present but unknown/None/empty
value raises ValueError deterministically, never a silent fallback.

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

# Universal production rendering path (bible 85/92, Phase 2B-M).
SHELL_NAME = "solucionario.tex.j2"
KNOWN_SHELLS = frozenset({SHELL_NAME})

# Closed item.kind -> fragment-file registry (bible 85): values are Python
# literals; the mandatory architecture test pins exact coverage against the
# adapter's EMITTABLE_KINDS.
FRAGMENT_REGISTRY = {
    "standard": "item_standard.tex.j2",
    "component_group": "item_component_group.tex.j2",
    "output_group": "item_output_group.tex.j2",
    "gradient": "item_gradient.tex.j2",
    "error": "item_error.tex.j2",
}

# Migration window only (bible 92, legacy-template lifecycle): the legacy
# full-document templates stay routable until the Phase 2B-M deletion gate
# passes; they are never a production path after cutover.
TEMPLATE_NAME = "solucionario_integrales.tex.j2"
GRADIENT_TEMPLATE_NAME = "solucionario_gradientes.tex.j2"
KNOWN_TEMPLATES = frozenset({TEMPLATE_NAME, GRADIENT_TEMPLATE_NAME})


class InternalRenderError(RuntimeError):
    """Deterministic internal rendering failure (bible 85/92).

    System defect, never an authored academic outcome: raised by preflight
    (invalid shell metadata, malformed items, unknown/missing item.kind,
    stale registry entry, missing fragment) or wrapped around a fragment or
    shell render failure with the original cause preserved. Never converted
    to the generic academic ERROR item; aborts before any output writing.
    """


def render_tex(render_model: dict, templates_dir=TEMPLATES_DIR) -> str:
    """Render the closed render model (bible 85) to a LaTeX string."""
    environment = Environment(
        loader=FileSystemLoader(str(templates_dir)),
        undefined=StrictUndefined,
        autoescape=False,
    )
    name = _template_name(render_model["document"])
    if name in KNOWN_SHELLS:
        return _render_universal(render_model, environment)
    template = environment.get_template(name)
    return template.render(
        document=render_model["document"],
        items=render_model["items"],
    )


def _template_name(document: dict) -> str:
    """Migration-window router (deleted at Phase 2B-M closeout): select by
    document["template"] alone. Absent key -> legacy integral template
    (Phase 1 back-compat); SHELL_NAME -> universal path; legacy names ->
    legacy full-document path; anything else (including None/"") ->
    deterministic ValueError, no silent fallback."""
    if "template" not in document:
        return TEMPLATE_NAME
    name = document["template"]
    if isinstance(name, str) and (name in KNOWN_TEMPLATES or name in KNOWN_SHELLS):
        return name
    raise ValueError(f"unknown render template: {name!r}")


# ---------------------------------------------------------------------------
# Universal path (bible 85, Document Shell and Item Fragments)
# ---------------------------------------------------------------------------

def _shell_name(document: dict) -> str:
    """Shell metadata semantics (bible 85): absent -> the one default
    neutral shell; present but null/non-string/unknown -> deterministic
    internal failure. Identifiers are closed; no filesystem path derives
    from the value."""
    if "template" not in document:
        return SHELL_NAME
    name = document["template"]
    if isinstance(name, str) and name in KNOWN_SHELLS:
        return name
    raise InternalRenderError(f"invalid document shell metadata: {name!r}")


def _preflight(render_model: dict, environment: Environment) -> tuple:
    """Complete whole-list preflight (bible 85): runs before ANY fragment
    render and is position-independent. Validates the shell identifier, the
    items container, every item.kind against the closed registry, and that
    the shell and EVERY registry fragment resolve and load."""
    shell_name = _shell_name(render_model["document"])

    items = render_model["items"]
    if not isinstance(items, list):
        raise InternalRenderError(
            f"render model items must be a list, got {type(items).__name__}"
        )

    for index, item in enumerate(items):
        if not isinstance(item, dict) or "kind" not in item:
            raise InternalRenderError(f"item {index} has no render kind")
        kind = item["kind"]
        if not isinstance(kind, str):
            raise InternalRenderError(
                f"item {index} has a non-string render kind: {kind!r}"
            )
        if kind not in FRAGMENT_REGISTRY:
            raise InternalRenderError(
                f"item {index} has an unknown render kind: {kind!r}"
            )

    for name in (shell_name, *FRAGMENT_REGISTRY.values()):
        try:
            environment.get_template(name)
        except Exception as exc:  # stale registry entry / missing fragment
            raise InternalRenderError(
                f"cannot load render template {name!r}: {exc}"
            ) from exc

    return shell_name, items


def _render_universal(render_model: dict, environment: Environment) -> str:
    """Neutral shell + closed fragments (bible 85): fragments render in list
    order with context exactly {item}; bodies compose through the shell's
    fixed blank-line framing (the documented separator policy, chosen to
    reproduce the legacy inter-item byte shape); the shell renders with
    context exactly {document, rendered_items}."""
    shell_name, items = _preflight(render_model, environment)

    rendered_items = []
    for index, item in enumerate(items):
        fragment_name = FRAGMENT_REGISTRY[item["kind"]]
        fragment = environment.get_template(fragment_name)
        try:
            rendered_items.append(fragment.render(item=item))
        except Exception as exc:
            label = item.get("exercise_label")
            raise InternalRenderError(
                f"internal rendering failure at item {index} "
                f"(exercise_label={label!r}, kind={item['kind']!r}, "
                f"fragment={fragment_name!r}): {exc}"
            ) from exc

    shell = environment.get_template(shell_name)
    try:
        return shell.render(
            document=render_model["document"],
            rendered_items=rendered_items,
        )
    except Exception as exc:
        raise InternalRenderError(
            f"internal rendering failure in document shell {shell_name!r}: {exc}"
        ) from exc
