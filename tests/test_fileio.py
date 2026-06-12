"""Tests for fileio M7B1: naming + read helpers (bible 55/80/75).

Locks the slot/underscore naming rules, production/testing modes with a
deterministic injected `now`, UTC normalization for aware datetimes,
processed_info shape, read-only input behavior, and the M7B1 scope itself
(no write helpers, no outputs/ management, no subprocess imports).
"""

import ast
import copy
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from solucionario import fileio
from solucionario.fileio import (
    DISPLAY_DEFAULTS_PATH,
    filename_base,
    load_display_defaults,
    processed_info,
    read_input_json,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
NOW = datetime(2026, 1, 21, 16, 11, 59)  # naive: treated as deterministic/UTC


def metadata(**overrides) -> dict:
    data = {
        "institution": "itson",
        "course_code": "c3",
        "course": "Calculus 3",
        "assignment": {"type": "hw", "number": 16},
    }
    data.update(overrides)
    return data


# ---------------------------------------------------------------------------
# filename_base
# ---------------------------------------------------------------------------

def test_production_filename_full_slots():
    assert filename_base(metadata()) == "itson_c3_hw_16"


@pytest.mark.parametrize(
    "drop, expected",
    [
        (["course_code"], "itson_hw_16"),
        (["institution"], "c3_hw_16"),
        (["institution", "course_code"], "hw_16"),
    ],
)
def test_production_filename_omits_absent_optional_slots(drop, expected):
    data = metadata()
    for key in drop:
        del data[key]
    assert filename_base(data) == expected


def test_empty_optional_slots_are_omitted_too():
    assert filename_base(metadata(institution="", course_code=None)) == "hw_16"


def test_testing_filename_appends_deterministic_timestamp():
    data = metadata(file_naming_mode="testing")
    assert filename_base(data, NOW) == "itson_c3_hw_16_20260121_161159"


def test_bible_46_metadata_shape():
    data = metadata(
        file_naming_mode="testing",
        assignment={"type": "test", "number": 9001},
    )
    assert filename_base(data, NOW) == "itson_c3_test_9001_20260121_161159"


@pytest.mark.parametrize("mode", [None, "production", "junk", 42])
def test_non_testing_modes_name_like_production(mode):
    # Constraint 2: file_naming_mode is NOT a validation rule — only the
    # exact string "testing" changes naming behavior.
    data = metadata()
    if mode is not None:
        data["file_naming_mode"] = mode
    assert filename_base(data, NOW) == "itson_c3_hw_16"


@pytest.mark.parametrize("number, expected", [(16, "16"), (16.0, "16"), (21.5, "21.5")])
def test_assignment_number_formatting(number, expected):
    data = metadata(assignment={"type": "hw", "number": number})
    assert filename_base(data) == f"itson_c3_hw_{expected}"


def test_aware_now_is_normalized_to_utc():
    # Constraint 1: 17:11:59 at UTC+1 == 16:11:59 UTC.
    aware = datetime(2026, 1, 21, 17, 11, 59, tzinfo=timezone(timedelta(hours=1)))
    data = metadata(file_naming_mode="testing")
    assert filename_base(data, aware) == "itson_c3_hw_16_20260121_161159"


# ---------------------------------------------------------------------------
# processed_info
# ---------------------------------------------------------------------------

def test_processed_info_shape_and_consistency_production():
    info = processed_info(metadata(), NOW)
    assert info == {
        "timestamp": "2026-01-21T16:11:59Z",
        "filename": "itson_c3_hw_16_extended.json",
        "filename_base": "itson_c3_hw_16",
        "naming_mode": "production",
    }
    assert info["filename"] == info["filename_base"] + "_extended.json"
    assert info["filename_base"] == filename_base(metadata(), NOW)


def test_processed_info_testing_mode_shares_the_same_instant():
    data = metadata(file_naming_mode="testing")
    info = processed_info(data, NOW)
    assert info["naming_mode"] == "testing"
    assert info["filename_base"] == "itson_c3_hw_16_20260121_161159"
    assert info["timestamp"] == "2026-01-21T16:11:59Z"  # same NOW everywhere


def test_processed_info_normalizes_aware_now_to_utc():
    aware = datetime(2026, 1, 21, 17, 11, 59, tzinfo=timezone(timedelta(hours=1)))
    info = processed_info(metadata(), aware)
    assert info["timestamp"] == "2026-01-21T16:11:59Z"


def test_processed_info_default_now_is_utc_shaped():
    info = processed_info(metadata())
    assert info["timestamp"].endswith("Z")
    datetime.strptime(info["timestamp"], "%Y-%m-%dT%H:%M:%SZ")  # parses


# ---------------------------------------------------------------------------
# read_input_json (read-only, bible 55)
# ---------------------------------------------------------------------------

def test_read_input_json_round_trip_without_mutation(tmp_path):
    data = {"metadata": metadata(), "exercises": [{"id": 1, "type": "integral"}]}
    input_file = tmp_path / "itson_c3_hw_16.json"
    input_file.write_text(json.dumps(data), encoding="utf-8")
    bytes_before = input_file.read_bytes()
    mtime_before = input_file.stat().st_mtime_ns

    loaded = read_input_json(input_file)

    assert loaded == data
    assert input_file.read_bytes() == bytes_before  # untouched content
    assert input_file.stat().st_mtime_ns == mtime_before  # untouched file


def test_read_input_json_tolerates_windows_bom(tmp_path):
    input_file = tmp_path / "bom.json"
    input_file.write_text('{"id": 1}', encoding="utf-8-sig")
    assert read_input_json(input_file) == {"id": 1}


def test_read_input_json_missing_file(tmp_path):
    missing = tmp_path / "nope.json"
    with pytest.raises(FileNotFoundError, match="nope.json"):
        read_input_json(missing)


def test_read_input_json_invalid_json(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("{not json", encoding="utf-8")
    with pytest.raises(ValueError, match="bad.json"):
        read_input_json(bad)


# ---------------------------------------------------------------------------
# load_display_defaults
# ---------------------------------------------------------------------------

def test_load_display_defaults_reads_current_config():
    defaults = load_display_defaults()
    direct = json.loads(DISPLAY_DEFAULTS_PATH.read_text(encoding="utf-8"))
    assert defaults == direct
    assert defaults["decimal_places"] == 4  # bible 50 spot check


# ---------------------------------------------------------------------------
# M7B1 scope locks (constraint 3)
# ---------------------------------------------------------------------------

def test_no_write_helpers_exist_yet():
    for forbidden in ("write_extended_json", "write_tex", "compile_pdf"):
        assert not hasattr(fileio, forbidden)


def test_module_imports_are_read_only_safe():
    tree = ast.parse(Path(fileio.__file__).read_text(encoding="utf-8"))
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported |= {alias.name.split(".")[0] for alias in node.names}
        elif isinstance(node, ast.ImportFrom):
            imported.add((node.module or "").split(".")[0])
    assert imported == {"json", "datetime", "pathlib"}  # no subprocess/os/shutil


def test_no_outputs_directory_interaction(tmp_path):
    outputs = PROJECT_ROOT / "outputs"
    listing_before = sorted(p.name for p in outputs.iterdir()) if outputs.is_dir() else None

    # Exercise the entire public API.
    filename_base(metadata(file_naming_mode="testing"), NOW)
    processed_info(metadata(), NOW)
    load_display_defaults()
    sample = tmp_path / "in.json"
    sample.write_text("{}", encoding="utf-8")
    read_input_json(sample)

    listing_after = sorted(p.name for p in outputs.iterdir()) if outputs.is_dir() else None
    assert listing_after == listing_before
