# File Handling Rules — v3.2

> **v3.2 changes**: `file_naming_mode` source-of-truth note added (P10);
> references updated to _v3_2. v3.1 baseline: folder structure and example
> filenames use canonical `hw` type token.

## Core Principles

### 1. Input Files are Read-Only
- **NEVER move** input JSON files
- **NEVER rename** input JSON files
- **NEVER modify** input JSON files in place
- Input files remain in their original location

### 2. Output Generation
- Extended JSON, TEX, PDF are **generated** in output location
- Output files can be overwritten safely (they are derivatives)
- Always read from input, write to output

### 3. File Locations

#### Production Mode

```
/project
  /inputs
    itson_c3_hw_16.json              ← INPUT (read-only)
  /outputs
    itson_c3_hw_16_extended.json     ← OUTPUT (generated)
    itson_c3_hw_16.tex               ← OUTPUT (generated)
    itson_c3_hw_16.pdf               ← OUTPUT (generated)
```

#### Testing Mode (with timestamps)

```
/project
  /inputs
    itson_c3_hw_16.json                             ← INPUT (read-only)
  /outputs
    itson_c3_hw_16_20260121_161159_extended.json   ← OUTPUT (generated)
    itson_c3_hw_16_20260121_161159.tex
    itson_c3_hw_16_20260121_161159.pdf
    itson_c3_hw_16_20260121_162345_extended.json   ← Next test run
    itson_c3_hw_16_20260121_162345.tex
    itson_c3_hw_16_20260121_162345.pdf
```

---

## Processing Pipeline

### Safe Pipeline

```
Read input JSON from /inputs
Process with solvers
Generate extended JSON to /outputs
Generate TEX to /outputs
Generate PDF to /outputs
Original input remains untouched
```

### FORBIDDEN Operations

❌ Move input to /archive
❌ Rename input based on processing
❌ Modify input file with results
❌ Delete input after processing

---

## Error Handling

### If Processing Fails
- DO NOT delete or modify input
- DO show error message to console/terminal
- DO keep input file for retry

> A document-level validation failure (missing required top-level field, or any
> exercise missing `id`) aborts before any output is written; the input is left
> untouched. Exercise-level and group-level failures continue and produce ERROR
> items. See 90_phase1_scope_v3_2.md.

### If Output Exists
- DO overwrite output files (they are regenerated, not precious)
- DO NOT prompt for confirmation

---

## Philosophy

- **Input file** = source of truth (never touched, always protected)
- **Output files** = disposable derivatives (can regenerate anytime)
- **On error** = show message, let user fix input, retry from original

---

## Folder Structure

```
project_root/
├── inputs/              # User-created JSON (read-only)
├── outputs/             # Generated files (overwritable)
├── config/              # Templates and settings
│   └── display_defaults/
│       └── default.json # Hardcoded display defaults
├── templates/
│   └── jinja2/          # LaTeX templates
├── solvers/             # Solver modules
└── main.py              # Entry point
```

---

## File Naming Modes

**Production** (default): Clean names, no timestamps. `itson_c3_hw_16.json`

**Testing**: Includes timestamp YYYYMMDD_HHMMSS. Allows multiple test runs.
`itson_c3_hw_16_20260121_161159.json`

Controlled by `file_naming_mode` in metadata (defaults to "production"). Source of
truth is `metadata.file_naming_mode`; 50_config_defaults_global_v3_2.json's value
is a fallback default only and is not merged into per-exercise display config (see
70_display_system_v3_2.md).

---

## Reminder for Code Generation

When requesting code from Claude, include this context:

```
CRITICAL: Input files in /inputs are READ-ONLY.

Never move or rename input files.
Always generate outputs to /outputs folder.
Output files are safe to overwrite.
```
