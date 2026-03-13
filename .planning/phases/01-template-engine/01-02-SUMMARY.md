---
phase: 01-template-engine
plan: "02"
subsystem: template-engine
tags: [python, tdd, pytest, templates, demographics, itertools, string-formatting]

# Dependency graph
requires:
  - phase: 01-template-engine/01-01
    provides: demographics.py with ETHNICITIES, AGE_GROUPS, GENDERS constants and pytest infrastructure
provides:
  - template_engine.py module with full public API (TemplateFile, TemplateValidationError, load_template, load_collection, load_templates_dir, expand_to_tasks)
  - 3 test fixture files (valid_template.txt, collection_template.txt, bad_placeholder.txt)
  - 10 unit tests covering TMPL-01, TMPL-02, TMPL-03, TMPL-05
affects:
  - 01-03 (generate.py integration will import from template_engine)
  - 01-04 (seed templates will be loaded by template_engine)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "TDD red-green cycle — test commit (RED) followed by feat commit (GREEN)"
    - "Plain class (not dataclass) for TemplateFile — consistent with codebase style"
    - "string.Formatter().parse() for safe placeholder enumeration without executing format"
    - "Split on newline---newline to avoid false splits on inline dashes in collection files"
    - "Slug derived from filename stem (not display name) for stable output paths"

key-files:
  created:
    - template_engine.py
    - tests/fixtures/valid_template.txt
    - tests/fixtures/collection_template.txt
    - tests/fixtures/bad_placeholder.txt
    - tests/test_template_engine.py
  modified: []

key-decisions:
  - "Slug derived from filename stem not display name — output paths stable if user renames template display name"
  - "Collection scene slug format: {path.stem}-{slugify(name)} — human-readable and avoids collisions"
  - "load_templates_dir() detects collection vs single-scene by presence of newline---newline in file content"
  - "expand_to_tasks() output path: output_dir/tmpl.slug/age_slug/ethnicity_slug/gender_NNN.png"

patterns-established:
  - "Pattern 3: string.Formatter().parse() for safe placeholder extraction (no format execution)"
  - "Pattern 4: Internal helpers prefixed with _ (_parse_template_text, _validate_placeholders)"

requirements-completed: [TMPL-01, TMPL-02, TMPL-03, TMPL-05]

# Metrics
duration: 1min
completed: 2026-03-13
---

# Phase 1 Plan 02: Template Engine Summary

**template_engine.py with load/validate/expand pipeline using string.Formatter placeholder extraction, itertools.product Cartesian expansion, and ## header format for .txt template files**

## Performance

- **Duration:** 1 min
- **Started:** 2026-03-13T03:38:55Z
- **Completed:** 2026-03-13T03:40:24Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments

- template_engine.py delivers all 6 public exports matching the plan contract: TemplateFile, TemplateValidationError, load_template, load_collection, load_templates_dir, expand_to_tasks
- Placeholder validation at load time names the bad placeholder and source file path in the error message (TMPL-03 requirement satisfied)
- expand_to_tasks() returns list of {"prompt": str, "output_path": Path} dicts matching the shape providers.py already consumes
- Collection files with --- separator produce independent TemplateFile objects, each expanding across the full demographic matrix (TMPL-05)
- All 15 tests pass: 5 demographics + 10 template engine

## Task Commits

Each task was committed atomically:

1. **Task 1: Create test fixtures and test stubs for template_engine** - `375e81e` (test — RED)
2. **Task 2: Implement template_engine.py and go GREEN** - `d816d5f` (feat — GREEN)

**Plan metadata:** (docs commit follows)

_Note: TDD tasks have two commits — test (RED) then feat (GREEN)_

## Files Created/Modified

- `/mnt/c/Users/clamd/Projects/stock-image-gen/template_engine.py` - Full template engine: TemplateFile class, TemplateValidationError, load/expand public API
- `/mnt/c/Users/clamd/Projects/stock-image-gen/tests/test_template_engine.py` - 10 unit tests covering TMPL-01, TMPL-02, TMPL-03, TMPL-05
- `/mnt/c/Users/clamd/Projects/stock-image-gen/tests/fixtures/valid_template.txt` - Single-scene fixture with style directives and all required placeholders
- `/mnt/c/Users/clamd/Projects/stock-image-gen/tests/fixtures/collection_template.txt` - Two-scene collection fixture separated by ---
- `/mnt/c/Users/clamd/Projects/stock-image-gen/tests/fixtures/bad_placeholder.txt` - Fixture with {age_group} misspelling for validation error testing

## Decisions Made

- **Slug from filename stem:** Template slug is derived from `path.stem` (filename without extension), not the `## name:` display header. This keeps output paths stable if the user renames the template's display name without renaming the file.
- **Collection scene slug format:** `{path.stem}-{slugify(name)}` (e.g., `collection_template-scene-alpha`) — human-readable and avoids numeric index collisions when names are available.
- **Collection detection in load_templates_dir():** Detects collection vs single-scene files by checking for `"\n---\n"` in file content before deciding which loader to call. Simple and reliable.
- **Output path structure:** `output_dir/tmpl.slug/age_slug/ethnicity_slug/gender_NNN.png` — template, then age, then ethnicity, then gender+index. Produces a clear directory tree for batch output.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- template_engine.py is ready to import in generate.py (Plan 03): `from template_engine import load_template, load_collection, load_templates_dir, expand_to_tasks`
- Seed templates (Plan 04) can be authored in .txt format and loaded via load_templates_dir()
- All 15 tests pass, pytest infrastructure confirmed working for Phase 2

## Self-Check: PASSED

- template_engine.py: FOUND
- tests/test_template_engine.py: FOUND
- tests/fixtures/valid_template.txt: FOUND
- tests/fixtures/collection_template.txt: FOUND
- tests/fixtures/bad_placeholder.txt: FOUND
- Commit 375e81e (test - RED phase): FOUND
- Commit d816d5f (feat - GREEN phase): FOUND

---
*Phase: 01-template-engine*
*Completed: 2026-03-13*
