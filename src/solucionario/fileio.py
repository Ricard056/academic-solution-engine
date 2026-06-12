"""File handling — M7B1: read helpers and file naming only.

Inputs are read-only (bible 55): this module never moves, renames, modifies,
or deletes anything. Output writing, outputs/ management, and the pdflatex
wrapper arrive in M7B3 — no write helper exists here yet, and the module
imports no subprocess/os machinery (locked by tests/test_fileio.py).

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
from datetime import datetime, timezone
from pathlib import Path

TIMESTAMP_FORMAT = "%Y%m%d_%H%M%S"
PROCESSED_TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%SZ"  # bible 75 example shape

DISPLAY_DEFAULTS_PATH = (
    Path(__file__).resolve().parents[2] / "config" / "display_defaults" / "default.json"
)


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
