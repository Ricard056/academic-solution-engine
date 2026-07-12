"""CLI entry point (M7B4): python -m solucionario <input.json>.

Flow (bible 55/90): read input -> DOCUMENT HARD-STOP VALIDATION before any
metadata-derived naming (processed_info), before output filename calculation,
and before any writing -> in-memory pipeline -> write Extended JSON + TEX
(outputs/, overwriting silently) -> compile PDF -> concise summary.

Exit codes: 0 = document processed and PDF compiled (exercise-level and
group-level ERROR items are NOT CLI failures; they show up in the summary
and processing_summary); 1 = unreadable/invalid input file, document hard
stop, or pdflatex failure; 2 = argparse usage error (argparse default).

output_dir and compile_pdf_func are TEST-ONLY injection points (keyword
arguments, never CLI flags): output_dir resolves to fileio.OUTPUTS_DIR at
call time, compile_pdf_func to fileio.compile_pdf. Inputs are never moved,
renamed, modified, or deleted; pdflatex failure leaves the generated
Extended JSON/TEX in place (disposable derivatives, bible 55).
"""

import argparse
import sys

from solucionario import fileio
from solucionario.fileio import (
    PdfCompilationError,
    load_display_defaults,
    processed_info,
    read_input_json,
    write_extended_json,
    write_tex,
)
from solucionario.pipeline import process_document
from solucionario.validation import DocumentValidationError, validate_document


def main(argv=None, *, output_dir=None, compile_pdf_func=None) -> int:
    parser = argparse.ArgumentParser(
        prog="solucionario",
        description=(
            "Generate a PDF solution manual from a supported math JSON input."
        ),
    )
    parser.add_argument(
        "input_path", help="path to the input exercise JSON (read-only)"
    )
    args = parser.parse_args(argv)

    out_dir = output_dir if output_dir is not None else fileio.OUTPUTS_DIR
    compile_pdf = (
        compile_pdf_func if compile_pdf_func is not None else fileio.compile_pdf
    )

    try:
        input_json = read_input_json(args.input_path)
    except (FileNotFoundError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    # Hard stop BEFORE processed_info / output naming / any writing.
    try:
        validate_document(input_json)
    except DocumentValidationError as exc:
        print(f"ERROR: document validation failed: {exc}", file=sys.stderr)
        return 1

    info = processed_info(input_json["metadata"])
    try:
        result = process_document(
            input_json,
            processed_info=info,
            display_defaults=load_display_defaults(),
        )
    except DocumentValidationError as exc:
        # Defensive re-validation inside process_document; still no outputs.
        print(f"ERROR: document validation failed: {exc}", file=sys.stderr)
        return 1

    base = info["filename_base"]
    extended_path = write_extended_json(result["extended_json"], base, out_dir)
    tex_path = write_tex(result["tex_string"], base, out_dir)

    try:
        pdf_path = compile_pdf(tex_path)
    except PdfCompilationError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        print(
            f"Generated outputs kept for debugging: {extended_path}, {tex_path}",
            file=sys.stderr,
        )
        return 1

    summary = result["extended_json"]["metadata"]["processing_summary"]
    print(
        f"{base}: {summary['successful']}/{summary['total_exercises']} "
        f"exercises solved, {summary['errors']} error(s)."
    )
    print(f"  {extended_path}")
    print(f"  {tex_path}")
    print(f"  {pdf_path}")
    return 0
