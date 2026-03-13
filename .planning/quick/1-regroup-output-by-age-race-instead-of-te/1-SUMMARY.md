---
phase: quick-1
plan: "01"
subsystem: template-engine, generation-pipeline
tags: [output-paths, directory-structure, cleanup, dry-run]
dependency_graph:
  requires: []
  provides: [age-ethnicity-first-output-paths, output-dir-cleanup-on-run]
  affects: [generate.py combo_label, expand_to_tasks path structure]
tech_stack:
  added: [shutil]
  patterns: [path-component-index-parsing]
key_files:
  created: []
  modified:
    - template_engine.py
    - generate.py
    - tests/test_template_engine.py
decisions:
  - "Output path order changed to age/ethnicity/slug for demographic-first browsing"
  - "combo_label now parses slug_idx-2 (age) and slug_idx-1 (ethnicity) from new path order"
  - "Output cleanup guarded by `if not dry_run` — dry-run never touches filesystem"
metrics:
  duration: "~8 minutes"
  completed_date: "2026-03-13T07:28:21Z"
  tasks_completed: 2
  files_modified: 3
---

# Phase quick-1 Plan 01: Regroup Output by Age/Ethnicity Summary

**One-liner:** Restructured output path from template-first (slug/age/ethnicity) to demographic-first (age/ethnicity/slug) and added shutil.rmtree cleanup before each generation run.

## What Was Built

### Task 1: Reorder output path to age/ethnicity/template (TDD)

Changed `expand_to_tasks()` in `template_engine.py` from:
```
output_dir / tmpl.slug / age_slug / ethnicity_slug / gender_NNN.png
```
to:
```
output_dir / age_slug / ethnicity_slug / tmpl.slug / gender_NNN.png
```

This allows browsing generated images grouped by demographic first (e.g., `output/high-school-14-17/east-asian/`) and then comparing different templates within that demographic.

Added `test_expand_to_tasks_path_order_age_ethnicity_first` which verifies:
- Template slug appears in path parts
- Slug index is >= 2 (age and ethnicity come before it)
- Age slug contains expected demographic string
- Path part order: age (slug_idx-2) < ethnicity (slug_idx-1) < slug

### Task 2: Fix combo_label parsing and add output cleanup

Updated the combo_label derivation in `generate.py main()` to match the new path order. Previously it read `slug_idx+1`, `slug_idx+2` for age/ethnicity (template-first); now reads `slug_idx-2`, `slug_idx-1`:

```python
age_slug = parts[slug_idx - 2] if slug_idx >= 2 else "?"
ethnicity_slug = parts[slug_idx - 1] if slug_idx >= 1 else "?"
gender_file = parts[slug_idx + 1] if slug_idx + 1 < len(parts) else "?"
```

Added output directory cleanup before generation (after the dry-run early return):

```python
if output_dir.exists():
    shutil.rmtree(output_dir)
output_dir.mkdir(parents=True, exist_ok=True)
```

This wipes both the output images and the `_preview` subdirectory (since _preview lives inside output_dir), ensuring each run starts clean.

## Verification

Full test suite: 50 tests passed, 0 failed.

Sample output path with new structure:
```
output/high-school-14-17/east-asian/stem-lab/female_001.png
```

## Deviations from Plan

None — plan executed exactly as written.

## Self-Check: PASSED

- `template_engine.py` modified: age/ethnicity/slug ordering confirmed
- `generate.py` modified: shutil import, combo_label fix, cleanup block confirmed
- `tests/test_template_engine.py` modified: new path-order test confirmed
- Task 1 commit: `31c2480`
- Task 2 commit: `34e430a`
- All 50 tests pass
