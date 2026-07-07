"""Common solver results contract (bible/75_json_output_spec_v3_2.md).

Solvers emit raw mathematical data only: LaTeX strings plus an unrounded
float. Formatted decimals and units are owned by the Render Adapter (bible
85); solver modules must never import render/formatting code (guarded by
tests/test_architecture.py).

Success results carry NO status key; ``status: "error"`` appears only on
error results — exactly the canonical shapes of bible 75.
"""

ERROR_PROBLEM_LATEX = r"\text{ERROR: Could not process exercise}"
ERROR_SOLUTION_LATEX = r"\text{ERROR}"


def success_result(
    problem_latex: str, solution_latex: str, numeric_value: float | None
) -> dict:
    """Bible 75 standard result: raw float (or None for a symbolic-only
    success), no rounding, no units, no status."""
    return {
        "problem_latex": problem_latex,
        "solution_latex": solution_latex,
        "numeric_value": numeric_value,
    }


def error_result(error_message: str) -> dict:
    """Bible 75 error result. error_message is an internal diagnostic; the
    PDF-facing text is the adapter's generic Spanish marker (bible 85)."""
    return {
        "status": "error",
        "problem_latex": ERROR_PROBLEM_LATEX,
        "solution_latex": ERROR_SOLUTION_LATEX,
        "error_message": error_message,
    }
