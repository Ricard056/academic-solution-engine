"""Architecture-boundary tests.

Solvers emit raw mathematical data only (bible 90/75/85): formatting belongs
to the Render Adapter. Solver modules therefore must not import the render
package or formatting machinery (decimal). The guard is AST-based so it
catches any import form without executing the modules.
"""

import ast
from pathlib import Path

SOLVERS_DIR = Path(__file__).resolve().parent.parent / "src" / "solucionario" / "solvers"


def iter_imported_modules(path: Path):
    """Yield the dotted module name of every import in the file."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                yield alias.name
        elif isinstance(node, ast.ImportFrom):
            if node.level:  # relative import — resolve against the package
                base = "solucionario.solvers" if node.level == 1 else "solucionario"
                yield f"{base}.{node.module}" if node.module else base
            elif node.module:
                yield node.module


def is_forbidden(module: str) -> bool:
    segments = module.split(".")
    return segments[0] == "decimal" or "render" in segments


def test_solver_modules_do_not_import_render_or_formatting():
    solver_files = sorted(SOLVERS_DIR.glob("*.py"))
    assert solver_files, f"no solver modules found under {SOLVERS_DIR}"

    offenders = [
        f"{path.name} imports {module}"
        for path in solver_files
        for module in iter_imported_modules(path)
        if is_forbidden(module)
    ]
    assert offenders == []


def test_solver_modules_do_not_import_sibling_solvers():
    """Solvers are independent modules (bible 99 #5): adding one must never
    touch or depend on another. Within the solvers package, a solver may
    import only the package itself, solvers.base (the shared results
    contract), and its own module — never a sibling solver."""
    solver_files = sorted(SOLVERS_DIR.glob("*.py"))
    assert solver_files, f"no solver modules found under {SOLVERS_DIR}"

    offenders = []
    for path in solver_files:
        allowed = {"", "base", path.stem}
        for module in iter_imported_modules(path):
            parts = module.split(".")
            if parts[:2] != ["solucionario", "solvers"]:
                continue
            submodule = parts[2] if len(parts) > 2 else ""
            if submodule not in allowed:
                offenders.append(f"{path.name} imports {module}")
    assert offenders == []


def test_render_adapter_does_not_compute_math():
    """The adapter copies math from results.component and formats — it never
    computes: no SymPy, no solver imports, no aggregation imports (bible 85,
    aggregation boundary)."""
    adapter_path = SOLVERS_DIR.parent / "render" / "adapter.py"
    offenders = [
        module
        for module in iter_imported_modules(adapter_path)
        if module.split(".")[0] == "sympy"
        or module.startswith("solucionario.solvers")
        or module.startswith("solucionario.aggregation")
    ]
    assert offenders == []


def test_fragment_registry_covers_emittable_kinds_exactly():
    """Mandatory exact-coverage test (bible 85/92, Phase 2B-M): the closed
    fragment registry must cover the adapter's declared emittable kind set
    EXACTLY — any drift in either direction fails the suite — and every
    registry fragment file must exist under templates/."""
    # Runtime imports (not AST): this guard pins the live declared constants.
    from solucionario.render.adapter import EMITTABLE_KINDS
    from solucionario.render.latex import FRAGMENT_REGISTRY, TEMPLATES_DIR

    assert set(FRAGMENT_REGISTRY) == set(EMITTABLE_KINDS)
    missing = [
        name for name in FRAGMENT_REGISTRY.values()
        if not (TEMPLATES_DIR / name).is_file()
    ]
    assert missing == []
