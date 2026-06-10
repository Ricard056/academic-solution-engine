"""Extended JSON assembly (canonical, pure data).

Pure transformation from in-memory processed data to the canonical Extended
JSON document of bible/75_json_output_spec_v3_2.md. Carries no formatted
decimals and no units (render-adapter-only, bible 85). This module never
solves, validates, aggregates, infers, formats, or writes files (bible
90/55): paths/naming and the clock belong to fileio/pipeline and arrive via
the ``processed_info`` argument.

Closure guarantee: the assembled document passes through
strip_internal_keys() as a whole, so no underscore-prefixed internal key —
notably ``results._symbolic_result``, the solver -> aggregation handoff —
can leak into serialized output. tests/test_extended_json.py owns the
schema-closure test.

Pipeline obligation (tracked here so it is not lost): bible 75 reusability
point 2 says auto-inferred ``quantity``/``coordinate_system`` are explicit in
Extended JSON. The pipeline must enrich exercises BEFORE calling
build_extended_json — this module never infers.
"""

SCHEMA_VERSION = "1.0"
ALGORITHM_VERSION = "3.2"

# Canonical fields owned by build_extended_json: top-level extras preserved
# from the input for reusability may never override these.
_CANONICAL_TOP_LEVEL = frozenset(
    {
        "schema_version",
        "kind",
        "metadata",
        "display_default",
        "display_integral",
        "exercises",
        "processing_summary",
    }
)


def strip_internal_keys(value):
    """Recursively drop every dict key starting with "_" (dicts and lists).

    Returns new structures; never mutates the input.
    """
    if isinstance(value, dict):
        return {
            key: strip_internal_keys(item)
            for key, item in value.items()
            if not (isinstance(key, str) and key.startswith("_"))
        }
    if isinstance(value, list):
        return [strip_internal_keys(item) for item in value]
    return value


def processing_summary(exercises: list[dict], processing_time_ms) -> dict:
    """The bible 75 processing_summary (no warnings channel — deferred, 08).

    total_exercises = len(exercises). An exercise counts as an error when
    ``results.status == "error"`` — or, defensively, when ``results`` is
    missing or not a dict. Group structural errors are NOT counted here
    (unless already represented as ``results.status == "error"``); the
    adapter surfaces them later as group render errors (bible 75).
    """
    errors = 0
    for exercise in exercises:
        results = exercise.get("results") if isinstance(exercise, dict) else None
        if not isinstance(results, dict) or results.get("status") == "error":
            errors += 1
    return {
        "total_exercises": len(exercises),
        "successful": len(exercises) - errors,
        "errors": errors,
        "processing_time_ms": int(processing_time_ms),
    }


def build_extended_json(
    input_json: dict,
    exercises: list[dict],
    *,
    processed_info: dict,
    processing_time_ms,
) -> dict:
    """Assemble the canonical Extended JSON document (bible 75). Pure.

    - ``input_json``: the original input document; read-only, never mutated.
    - ``exercises``: the PROCESSED exercises (post solve/aggregation). This
      list is what lands in the output — never ``input_json["exercises"]``.
    - ``processed_info``: caller-supplied ``processed`` block fields
      (timestamp, filename, filename_base, naming_mode);
      ``algorithm_version`` is added here.
    - ``processing_time_ms``: measured by the caller.
    """
    metadata = dict(input_json.get("metadata") or {})
    metadata["processed"] = {**processed_info, "algorithm_version": ALGORITHM_VERSION}
    metadata["processing_summary"] = processing_summary(exercises, processing_time_ms)

    document = {
        "schema_version": SCHEMA_VERSION,
        "kind": "extended",
        "metadata": metadata,
        "display_default": input_json.get("display_default") or {},
        "display_integral": input_json.get("display_integral") or {},
    }

    # Reusability (bible 75): preserve unknown top-level input fields —
    # but canonical fields always win over input values.
    for key, value in input_json.items():
        if key not in _CANONICAL_TOP_LEVEL:
            document[key] = value

    document["exercises"] = list(exercises)

    return strip_internal_keys(document)
