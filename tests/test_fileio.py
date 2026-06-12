"""Tests for fileio: naming + read helpers (M7B1) and output writing +
pdflatex wrapper (M7B3). Bible 55/80/75.

Locks the slot/underscore naming rules, production/testing modes with a
deterministic injected `now`, UTC normalization, processed_info shape,
read-only input behavior, dumb UTF-8 writers (no mutation/enrichment/
validation), exact pdflatex argv/cwd via injected runners, failure behavior
that never deletes outputs, and the module's import surface.
"""

import ast
import copy
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest

from solucionario import fileio
from solucionario.fileio import (
    DISPLAY_DEFAULTS_PATH,
    OUTPUTS_DIR,
    PdfCompilationError,
    compile_pdf,
    filename_base,
    load_display_defaults,
    output_paths,
    processed_info,
    read_input_json,
    write_extended_json,
    write_tex,
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
# Output paths and writers (M7B3)
# ---------------------------------------------------------------------------

def test_output_paths_names_and_default_dir():
    paths = output_paths("itson_c3_hw_16", Path("X"))
    assert paths == {
        "extended_json": Path("X") / "itson_c3_hw_16_extended.json",
        "tex": Path("X") / "itson_c3_hw_16.tex",
        "pdf": Path("X") / "itson_c3_hw_16.pdf",
    }
    default = output_paths("base")
    assert default["tex"].parent == OUTPUTS_DIR
    assert OUTPUTS_DIR.name == "outputs"


def test_output_paths_creates_nothing(tmp_path):
    target = tmp_path / "not_yet"
    output_paths("base", target)
    assert not target.exists()


def test_write_extended_json_filename_and_utf8_round_trip(tmp_path):
    document = {"kind": "extended", "metadata": {"course_display": "Cálculo III"}}
    path = write_extended_json(document, "itson_c3_hw_16", tmp_path)
    assert path == tmp_path / "itson_c3_hw_16_extended.json"
    assert json.loads(path.read_text(encoding="utf-8")) == document
    assert "Cálculo".encode("utf-8") in path.read_bytes()  # ensure_ascii=False


def test_write_extended_json_serializes_the_object_only(tmp_path):
    document = {"kind": "extended", "exercises": [{"id": 1}]}
    snapshot = copy.deepcopy(document)
    path = write_extended_json(document, "base", tmp_path)
    assert document == snapshot  # no mutation
    assert json.loads(path.read_text(encoding="utf-8")) == snapshot  # nothing added


def test_write_tex_filename_and_utf8_accents(tmp_path):
    path = write_tex("\\textbf{Cálculo III}", "itson_c3_hw_16", tmp_path)
    assert path == tmp_path / "itson_c3_hw_16.tex"
    raw = path.read_bytes()
    assert b"C\xc3\xa1lculo" in raw  # UTF-8 bytes, not cp1252/UTF-16
    assert raw.decode("utf-8") == "\\textbf{Cálculo III}"


def test_writers_create_missing_output_dir(tmp_path):
    target = tmp_path / "deep" / "outputs"
    write_tex("x", "a", target)
    write_extended_json({}, "a", target)
    assert (target / "a.tex").is_file()
    assert (target / "a_extended.json").is_file()


def test_writers_overwrite_without_prompting(tmp_path):
    write_tex("first", "a", tmp_path)
    write_tex("second", "a", tmp_path)
    assert (tmp_path / "a.tex").read_text(encoding="utf-8") == "second"
    write_extended_json({"v": 1}, "a", tmp_path)
    write_extended_json({"v": 2}, "a", tmp_path)
    assert json.loads((tmp_path / "a_extended.json").read_text(encoding="utf-8")) == {"v": 2}


def test_writers_write_only_the_expected_files(tmp_path):
    write_tex("x", "a", tmp_path)
    write_extended_json({}, "a", tmp_path)
    assert sorted(p.name for p in tmp_path.iterdir()) == ["a.tex", "a_extended.json"]


# ---------------------------------------------------------------------------
# compile_pdf (M7B3) — injected runners, no real pdflatex needed
# ---------------------------------------------------------------------------

def make_runner(record, returncode=0, stdout="", stderr=""):
    def runner(argv, **kwargs):
        record.append((argv, kwargs))
        return SimpleNamespace(returncode=returncode, stdout=stdout, stderr=stderr)
    return runner


def test_compile_pdf_exact_argv_and_cwd(tmp_path):
    tex = tmp_path / "itson_c3_hw_16.tex"
    tex.write_text("x", encoding="utf-8")
    record = []

    pdf = compile_pdf(tex, runner=make_runner(record))

    assert pdf == tmp_path / "itson_c3_hw_16.pdf"
    ((argv, kwargs),) = record
    assert argv == ["pdflatex", "-interaction=nonstopmode", "itson_c3_hw_16.tex"]
    assert kwargs["cwd"] == tmp_path  # bare filename + cwd, never shell=True
    assert kwargs["capture_output"] is True
    assert kwargs["text"] is True


def test_compile_pdf_custom_executable(tmp_path):
    tex = tmp_path / "a.tex"
    tex.write_text("x", encoding="utf-8")
    record = []
    compile_pdf(tex, runner=make_runner(record), pdflatex=r"C:\MiKTeX\pdflatex.exe")
    assert record[0][0][0] == r"C:\MiKTeX\pdflatex.exe"


def test_compile_pdf_failure_raises_with_context_and_keeps_outputs(tmp_path):
    tex = write_tex("\\bad", "a", tmp_path)
    extended = write_extended_json({"kind": "extended"}, "a", tmp_path)
    runner = make_runner([], returncode=1, stdout="...\n! LaTeX Error: boom\n...")

    with pytest.raises(PdfCompilationError) as excinfo:
        compile_pdf(tex, runner=runner)

    message = str(excinfo.value)
    assert "a.tex" in message
    assert "exit code 1" in message
    assert "! LaTeX Error: boom" in message
    # Nothing was deleted or cleaned up (bible 55: keep derivatives).
    assert tex.is_file()
    assert extended.is_file()


def test_compile_pdf_missing_pdflatex_is_a_clear_error(tmp_path):
    tex = tmp_path / "a.tex"
    tex.write_text("x", encoding="utf-8")

    def runner(argv, **kwargs):
        raise FileNotFoundError(argv[0])

    with pytest.raises(PdfCompilationError, match="pdflatex not found"):
        compile_pdf(tex, runner=runner)


def test_compile_pdf_default_runner_is_monkeypatchable(tmp_path, monkeypatch):
    tex = tmp_path / "a.tex"
    tex.write_text("x", encoding="utf-8")
    record = []
    monkeypatch.setattr(fileio.subprocess, "run", make_runner(record))
    pdf = compile_pdf(tex)  # no runner injected: uses subprocess.run
    assert pdf == tmp_path / "a.pdf"
    assert record[0][0][1] == "-interaction=nonstopmode"


# ---------------------------------------------------------------------------
# Scope locks
# ---------------------------------------------------------------------------

def test_output_api_surface():
    for name in ("output_paths", "write_extended_json", "write_tex", "compile_pdf"):
        assert callable(getattr(fileio, name))


def test_module_import_surface():
    tree = ast.parse(Path(fileio.__file__).read_text(encoding="utf-8"))
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported |= {alias.name.split(".")[0] for alias in node.names}
        elif isinstance(node, ast.ImportFrom):
            imported.add((node.module or "").split(".")[0])
    # subprocess exists solely for compile_pdf; no os/shutil, and no
    # render/jinja2 (writers never render templates).
    assert imported == {"json", "datetime", "pathlib", "subprocess"}


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
