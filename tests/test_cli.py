"""Tests for the CLI (M7B4).

All pdflatex interaction is faked via the test-only compile_pdf_func
injection point; outputs are isolated via the test-only output_dir kwarg.
Locks: success path, validate-before-processed_info ordering, hard-stop
no-output behavior, exercise errors not failing the CLI, pdflatex failure
keeping outputs, input immutability, the python -m entry point, and the
minimal CLI surface (one positional argument, no flags).
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

from solucionario import main as main_module
from solucionario import pipeline as pipeline_module
from solucionario.fileio import PdfCompilationError
from solucionario.main import main
from solucionario.render.latex import InternalRenderError

PROJECT_ROOT = Path(__file__).resolve().parent.parent

VALID_EXERCISE = {
    "id": 1,
    "type": "integral",
    "function": "1",
    "integrals": [
        {"var": "y", "lower": "0", "upper": "1"},
        {"var": "x", "lower": "0", "upper": "1"},
    ],
}
BROKEN_EXERCISE = {
    "id": 9,
    "type": "integral",
    "function": "2x",  # implicit multiplication: exercise-level ERROR
    "integrals": [
        {"var": "y", "lower": "0", "upper": "1"},
        {"var": "x", "lower": "0", "upper": "1"},
    ],
}


def write_input(tmp_path, *, exercises=None, metadata=None) -> Path:
    document = {
        "metadata": metadata
        or {
            "institution": "itson",
            "course_code": "c3",
            "course": "Calculus 3",
            "assignment": {"type": "hw", "number": 1},
        },
        "exercises": exercises or [VALID_EXERCISE],
    }
    path = tmp_path / "itson_c3_hw_1.json"
    path.write_text(json.dumps(document), encoding="utf-8")
    return path


def fake_compiler():
    def compile_pdf(tex_path):
        compile_pdf.calls.append(Path(tex_path))
        return Path(tex_path).with_suffix(".pdf")

    compile_pdf.calls = []
    return compile_pdf


# ---------------------------------------------------------------------------
# Success path
# ---------------------------------------------------------------------------

def test_success_path_writes_outputs_and_returns_zero(tmp_path, capsys):
    input_path = write_input(tmp_path)
    out_dir = tmp_path / "out"
    compiler = fake_compiler()

    code = main([str(input_path)], output_dir=out_dir, compile_pdf_func=compiler)

    assert code == 0
    assert (out_dir / "itson_c3_hw_1_extended.json").is_file()
    assert (out_dir / "itson_c3_hw_1.tex").is_file()
    assert compiler.calls == [out_dir / "itson_c3_hw_1.tex"]
    stdout = capsys.readouterr().out
    assert "itson_c3_hw_1: 1/1 exercises solved, 0 error(s)." in stdout
    assert "itson_c3_hw_1.pdf" in stdout


def test_processed_info_called_after_validation_on_valid_doc(tmp_path, monkeypatch):
    calls = []
    real = main_module.processed_info
    monkeypatch.setattr(
        main_module, "processed_info",
        lambda metadata: calls.append(True) or real(metadata),
    )
    code = main(
        [str(write_input(tmp_path))],
        output_dir=tmp_path / "out",
        compile_pdf_func=fake_compiler(),
    )
    assert code == 0
    assert calls == [True]


# ---------------------------------------------------------------------------
# Hard stop: no naming, no pipeline, no outputs
# ---------------------------------------------------------------------------

def test_invalid_document_returns_nonzero_and_writes_nothing(tmp_path, monkeypatch, capsys):
    input_path = write_input(tmp_path, metadata={"assignment": {"type": "hw"}})
    out_dir = tmp_path / "out"
    monkeypatch.setattr(
        main_module, "processed_info",
        lambda metadata: pytest.fail("processed_info must not run on a hard stop"),
    )
    monkeypatch.setattr(
        main_module, "process_document",
        lambda *a, **k: pytest.fail("pipeline must not run on a hard stop"),
    )

    code = main([str(input_path)], output_dir=out_dir, compile_pdf_func=fake_compiler())

    assert code == 1
    assert not out_dir.exists()  # nothing written, not even the directory
    assert "document validation failed" in capsys.readouterr().err


def test_missing_input_file(tmp_path, capsys):
    out_dir = tmp_path / "out"
    code = main(
        [str(tmp_path / "nope.json")],
        output_dir=out_dir,
        compile_pdf_func=fake_compiler(),
    )
    assert code == 1
    assert not out_dir.exists()
    assert "not found" in capsys.readouterr().err


def test_invalid_json_input_file(tmp_path, capsys):
    bad = tmp_path / "bad.json"
    bad.write_text("{not json", encoding="utf-8")
    out_dir = tmp_path / "out"
    code = main([str(bad)], output_dir=out_dir, compile_pdf_func=fake_compiler())
    assert code == 1
    assert not out_dir.exists()
    assert "not valid JSON" in capsys.readouterr().err


# ---------------------------------------------------------------------------
# Exercise errors are not CLI failures
# ---------------------------------------------------------------------------

def test_exercise_errors_still_exit_zero(tmp_path, capsys):
    input_path = write_input(tmp_path, exercises=[VALID_EXERCISE, BROKEN_EXERCISE])
    out_dir = tmp_path / "out"

    code = main([str(input_path)], output_dir=out_dir, compile_pdf_func=fake_compiler())

    assert code == 0
    extended = json.loads(
        (out_dir / "itson_c3_hw_1_extended.json").read_text(encoding="utf-8")
    )
    summary = extended["metadata"]["processing_summary"]
    assert summary == {**summary, "total_exercises": 2, "successful": 1, "errors": 1}
    assert "1 error(s)" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# pdflatex failure
# ---------------------------------------------------------------------------

def failing_compiler(tex_path):
    raise PdfCompilationError("pdflatex failed for itson_c3_hw_1.tex (exit code 1)")


def test_pdflatex_failure_keeps_outputs_and_returns_nonzero(tmp_path, capsys):
    input_path = write_input(tmp_path)
    out_dir = tmp_path / "out"

    code = main([str(input_path)], output_dir=out_dir, compile_pdf_func=failing_compiler)

    assert code == 1
    # Generated derivatives are kept for debugging (bible 55).
    assert (out_dir / "itson_c3_hw_1_extended.json").is_file()
    assert (out_dir / "itson_c3_hw_1.tex").is_file()
    stderr = capsys.readouterr().err
    assert "pdflatex failed" in stderr
    assert "kept for debugging" in stderr


# ---------------------------------------------------------------------------
# Internal rendering failure (bible 92/55): clean nonzero CLI, no writer
# invocation, pre-existing outputs byte-unchanged
# ---------------------------------------------------------------------------

def test_internal_render_failure_writes_nothing_and_preserves_outputs(
    tmp_path, monkeypatch, capsys
):
    input_path = write_input(tmp_path)
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    # Pre-seeded outputs from an earlier run: an internal render failure may
    # neither create nor overwrite ANY output file (bible 55, Phase 2B-M).
    seeded = {
        out_dir / "itson_c3_hw_1_extended.json": b'{"old": "extended"}',
        out_dir / "itson_c3_hw_1.tex": b"% old tex",
        out_dir / "itson_c3_hw_1.pdf": b"%PDF-old",
    }
    for path, content in seeded.items():
        path.write_bytes(content)

    def raising_render_tex(render_model, templates_dir=None):
        raise InternalRenderError("forced internal failure at item 0")

    # process_document renders fully in memory before main() writes anything;
    # a renderer failure must therefore abort before ANY writer runs.
    monkeypatch.setattr(pipeline_module, "render_tex", raising_render_tex)
    monkeypatch.setattr(
        main_module, "write_extended_json",
        lambda *a, **k: pytest.fail("write_extended_json must not run"),
    )
    monkeypatch.setattr(
        main_module, "write_tex",
        lambda *a, **k: pytest.fail("write_tex must not run"),
    )
    compiler = fake_compiler()

    code = main([str(input_path)], output_dir=out_dir, compile_pdf_func=compiler)

    assert code == 1
    stderr = capsys.readouterr().err
    assert "ERROR: internal rendering failure" in stderr
    assert "Traceback" not in stderr  # clean one-line report, no crash dump
    assert compiler.calls == []
    for path, content in seeded.items():
        assert path.read_bytes() == content  # byte-preserved
    assert sorted(p.name for p in out_dir.iterdir()) == sorted(
        p.name for p in seeded
    )  # nothing new appeared


# ---------------------------------------------------------------------------
# Input immutability
# ---------------------------------------------------------------------------

def test_input_file_unchanged_after_success_and_failure(tmp_path):
    input_path = write_input(tmp_path)
    bytes_before = input_path.read_bytes()
    mtime_before = input_path.stat().st_mtime_ns

    assert main([str(input_path)], output_dir=tmp_path / "a",
                compile_pdf_func=fake_compiler()) == 0
    assert main([str(input_path)], output_dir=tmp_path / "b",
                compile_pdf_func=failing_compiler) == 1

    assert input_path.read_bytes() == bytes_before
    assert input_path.stat().st_mtime_ns == mtime_before


# ---------------------------------------------------------------------------
# Entry point and CLI surface
# ---------------------------------------------------------------------------

def test_python_dash_m_entrypoint_runs(tmp_path):
    # An invalid document exercises the real entry point end to end without
    # needing pdflatex: hard stop -> nonzero exit, nothing written.
    bad_input = tmp_path / "bad_doc.json"
    bad_input.write_text(json.dumps({"metadata": {}, "exercises": []}), encoding="utf-8")

    completed = subprocess.run(
        [sys.executable, "-m", "solucionario", str(bad_input)],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 1
    assert "document validation failed" in completed.stderr


@pytest.mark.parametrize("argv", [[], ["--bogus", "x.json"], ["a.json", "b.json"]])
def test_cli_surface_is_one_positional_argument_only(argv):
    with pytest.raises(SystemExit) as excinfo:
        main(argv)
    assert excinfo.value.code == 2  # argparse usage error
