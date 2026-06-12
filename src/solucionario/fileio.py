"""File handling: read-only inputs, naming modes, output writes, pdflatex.

Inputs are read-only (bible 55): nothing here ever moves, renames, modifies,
or deletes an input file — input paths never even reach the writers. Outputs
are disposable derivatives written ONLY into an explicit output directory
(default: the project's outputs/), overwritten without prompting, and never
cleaned up (not even on pdflatex failure — they are useful for debugging).

The writers are deliberately dumb: write_extended_json serializes exactly
the object it is given (no mutation, enrichment, validation, purity cleanup,
or added fields) and write_tex writes an already-rendered string (it never
renders templates). Document-level hard-stop ordering — validate/process
first, write after — is the caller's wiring (M7B4), not enforced here.

subprocess usage is isolated to compile_pdf (argv list, never shell=True);
render/latex.py stays string-only.

Naming (bible 80/55): slots <institution>_<course_code>_<type>_<number>,
absent optional slots omitted, single-underscore joins. The naming-mode
source of truth is metadata.file_naming_mode; exactly "testing" appends a
_YYYYMMDD_HHMMSS timestamp, anything else (including absent) behaves as
production FOR NAMING PURPOSES ONLY — no validation rule here.

One `now` instant feeds both the filename timestamp and processed.timestamp
so they can never disagree. A timezone-aware `now` is normalized to UTC
before any formatting with a trailing "Z"; a naive `now` is used as-is
(deterministic tests treat it as UTC).
"""

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

TIMESTAMP_FORMAT = "%Y%m%d_%H%M%S"
PROCESSED_TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%SZ"  # bible 75 example shape

DISPLAY_DEFAULTS_PATH = (
    Path(__file__).resolve().parents[2] / "config" / "display_defaults" / "default.json"
)
OUTPUTS_DIR = Path(__file__).resolve().parents[2] / "outputs"


class PdfCompilationError(RuntimeError):
    """pdflatex failed or is unavailable; generated outputs are left intact."""


def _format_number(value) -> str:
    """Assignment number without a spurious ".0" (16 -> "16", 16.0 -> "16")."""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def _naming_mode(metadata: dict) -> str:
    """Exactly "testing" or "production" — junk values name like production."""
    return "testing" if metadata.get("file_naming_mode") == "testing" else "production"


def _normalized_now(now: datetime | None) -> datetime:
    """Default to UTC now; normalize aware datetimes to UTC; naive pass through."""
    if now is None:
        return datetime.now(timezone.utc)
    if now.tzinfo is not None:
        return now.astimezone(timezone.utc)
    return now


def filename_base(metadata: dict, now: datetime | None = None) -> str:
    """The shared base name for extended JSON / TEX / PDF (bible 80/55)."""
    assignment = metadata.get("assignment") or {}
    slots = [
        metadata.get("institution"),  # optional slot
        metadata.get("course_code"),  # optional slot
        str(assignment.get("type")),
        _format_number(assignment.get("number")),
    ]
    base = "_".join(str(slot) for slot in slots if slot)
    if _naming_mode(metadata) == "testing":
        base += "_" + _normalized_now(now).strftime(TIMESTAMP_FORMAT)
    return base


def processed_info(metadata: dict, now: datetime | None = None) -> dict:
    """The metadata.processed fields owned by fileio (bible 75); the
    extended_json stage adds algorithm_version."""
    instant = _normalized_now(now)
    base = filename_base(metadata, instant)
    return {
        "timestamp": instant.strftime(PROCESSED_TIMESTAMP_FORMAT),
        "filename": f"{base}_extended.json",
        "filename_base": base,
        "naming_mode": _naming_mode(metadata),
    }


def read_input_json(path) -> dict:
    """Read one input JSON file. Strictly read-only (bible 55).

    utf-8-sig tolerates a Windows BOM harmlessly. Raises FileNotFoundError
    for a missing file and ValueError for invalid JSON, both naming the path.
    """
    file_path = Path(path)
    if not file_path.is_file():
        raise FileNotFoundError(f"Input file not found: {file_path}")
    text = file_path.read_text(encoding="utf-8-sig")
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Input file is not valid JSON: {file_path}: {exc}") from exc


def load_display_defaults() -> dict:
    """Load the hardcoded display defaults template (bible 50). Read-only;
    merging belongs to display.py, never here."""
    return json.loads(DISPLAY_DEFAULTS_PATH.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Output writing + pdflatex (M7B3)
# ---------------------------------------------------------------------------

def output_paths(filename_base: str, output_dir=OUTPUTS_DIR) -> dict:
    """Paths of the three outputs sharing one filename_base (bible 80/55).

    Pure path arithmetic: creates no directories, touches nothing.
    """
    directory = Path(output_dir)
    return {
        "extended_json": directory / f"{filename_base}_extended.json",
        "tex": directory / f"{filename_base}.tex",
        "pdf": directory / f"{filename_base}.pdf",
    }


def write_extended_json(
    extended_json: dict, filename_base: str, output_dir=OUTPUTS_DIR
) -> Path:
    """Write <filename_base>_extended.json (UTF-8, readable JSON).

    Serializes exactly the object it is given — no mutation, no enrichment,
    no validation, no added fields, no purity cleanup (those are upstream
    guarantees). Creates the output directory if missing; overwrites
    silently (bible 55). Returns the written path.
    """
    path = output_paths(filename_base, output_dir)["extended_json"]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(extended_json, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return path


def write_tex(tex_string: str, filename_base: str, output_dir=OUTPUTS_DIR) -> Path:
    """Write <filename_base>.tex with explicit UTF-8 (accented es-MX strings
    must survive byte-for-byte). Receives an already-rendered string — never
    renders templates. Creates the output directory if missing; overwrites
    silently. Returns the written path."""
    path = output_paths(filename_base, output_dir)["tex"]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(tex_string, encoding="utf-8")
    return path


def compile_pdf(tex_path, *, runner=None, pdflatex: str = "pdflatex") -> Path:
    """Compile one generated .tex into a PDF next to it.

    Runs ``pdflatex -interaction=nonstopmode <name>.tex`` as an argv list
    (never shell=True) with cwd set to the tex file's parent, passing the
    bare filename. Returns the expected PDF path when the return code is 0;
    no existence check is performed (an injected runner produces no real
    file, and nonstopmode reports failure through the return code).

    On failure raises PdfCompilationError with the return code and the tail
    of pdflatex output. Never deletes or cleans up anything — .tex/.json/
    .aux/.log outputs are disposable derivatives kept for debugging
    (bible 55). ``runner`` is an injection point for tests (defaults to
    subprocess.run).
    """
    tex_path = Path(tex_path)
    run = runner if runner is not None else subprocess.run
    argv = [pdflatex, "-interaction=nonstopmode", tex_path.name]
    try:
        completed = run(argv, cwd=tex_path.parent, capture_output=True, text=True)
    except FileNotFoundError as exc:
        raise PdfCompilationError(
            f"pdflatex not found ({pdflatex!r}) — is MiKTeX/TeX Live installed "
            "and on PATH?"
        ) from exc
    if completed.returncode != 0:
        raise PdfCompilationError(
            f"pdflatex failed for {tex_path.name} "
            f"(exit code {completed.returncode}):\n{_output_tail(completed)}"
        )
    return tex_path.with_suffix(".pdf")


def _output_tail(completed, limit: int = 25) -> str:
    """The last lines of pdflatex output (errors go to stdout)."""
    lines = (completed.stdout or "").splitlines()[-limit:]
    if completed.stderr:
        lines += ["--- stderr ---", *completed.stderr.splitlines()[-limit:]]
    return "\n".join(lines)
