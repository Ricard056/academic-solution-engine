# academic-solution-engine

Phase 1 — **integrals only**. A command-line tool that converts structured JSON
exercise definitions into PDF solution manuals (Cálculo III, ITSON) using SymPy
and Jinja2/LaTeX.

Authoritative rules live in [`bible/`](bible/). See [`CLAUDE.md`](CLAUDE.md) for
the navigation map.

## Setup

This project uses a `src/` layout, so the package is only importable after an
editable install:

```bash
python -m venv .venv
# Windows (PowerShell):
.venv\Scripts\Activate.ps1
# macOS / Linux:
# source .venv/bin/activate
pip install -e .
```

## External requirement

**LaTeX / `pdflatex` must be installed separately.** It is not a pip dependency;
it is invoked to compile generated `.tex` files into PDF.

## File handling

- `inputs/` — user-provided exercise JSON. **Read-only** at runtime: never moved,
  renamed, or modified in place.
- `outputs/` — generated extended JSON, `.tex`, and `.pdf`. Overwritable
  derivatives (gitignored).

## Status

Scaffold only. No application logic is implemented yet.
