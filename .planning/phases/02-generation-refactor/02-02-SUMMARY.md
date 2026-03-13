---
phase: 02-generation-refactor
plan: "02"
subsystem: generation
tags: [python, tabulate, questionary, asyncio, template-engine, dry-run, preview-loop]

requires:
  - phase: 02-generation-refactor
    provides: "apply_demographic_restrictions, show_cost_confirmation, classify_failure, print_failure_report, select_templates, select_demographics — all Plan 01 core functions"
  - phase: 01-template-engine
    provides: "expand_to_tasks, load_templates_dir, TemplateFile — full template pipeline"

provides:
  - "print_dry_run_table() — tabulated prompt table with Template/Combo/Prompt columns, total count, [!] length warnings for prompts > 3800 chars"
  - "run_template_preview_loop() — sequential per-template preview with approve/skip/abort via questionary.select"
  - "main() complete wired flow: provider -> templates -> demographics -> expand+restrict -> dry-run OR cost gate -> preview -> generate"
  - "38 unit tests passing (17 for Plan 02 features + 21 from Plans 01+03)"

affects:
  - "End-to-end CLI usage (python generate.py)"
  - "03-quality phase (if any)"

tech-stack:
  added: []
  patterns:
    - "TDD RED/GREEN: failing tests committed first (69cc178), implementation second (cd05b68)"
    - "Sequential asyncio.run() per template in preview loop — documented anti-parallel pattern"
    - "tasks_by_template dict built during expansion for dry-run reuse without re-expanding"
    - "combo_label derived from output_path structure (slug/age/ethnicity/gender) for dry-run display"

key-files:
  created: []
  modified:
    - "generate.py — print_dry_run_table, run_template_preview_loop, complete main() wired flow"
    - "tests/test_generate.py — 5 new tests: test_gen02_dry_run_no_api_calls, test_gen02_dry_run_length_warning, test_gen05_preview_approves_subset, test_gen05_preview_abort, test_gen05_preview_generates_one_per_template"

key-decisions:
  - "Cost confirmation fires BEFORE preview loop — prevents spending preview money then declining full batch (Pitfall 2)"
  - "asyncio.run() called once per template in preview loop (sequential) — not refactored to asyncio.gather (Pitfall 1 / Anti-Pattern)"
  - "generate_batch failure count only: providers.py LOCKED, classify_failure/print_failure_report ready for future use (TODO comment)"
  - "combo_label derived from expand_to_tasks output_path structure rather than rebuilding from raw demographics"

patterns-established:
  - "Pattern: dry-run table built from tasks_by_template dict (slug -> list[task_info]) — same expansion, different display"
  - "Pattern: preview approved list drives task rebuild — only approved templates get full expansion"

requirements-completed: [GEN-02, GEN-05, UX-02]

duration: 5min
completed: 2026-03-13
---

# Phase 2 Plan 02: Dry-Run Table, Preview Loop, and main() Wiring Summary

**--dry-run tabulated prompt table with length warnings, per-template approve/skip/abort preview loop, and complete wired main() flow replacing old variable-combination generation**

## Performance

- **Duration:** ~5 min
- **Started:** 2026-03-13T04:19:41Z
- **Completed:** 2026-03-13T04:24:02Z
- **Tasks:** 2 auto (TDD RED + GREEN) + 1 checkpoint:human-verify (pending)
- **Files modified:** 2

## Accomplishments

- Implemented `print_dry_run_table()`: tabulate-formatted table with Template/Combo/Prompt columns, total count, and `[!] LENGTH WARNINGS` for prompts exceeding 3800 chars
- Implemented `run_template_preview_loop()`: sequential per-template preview using first demographic combo, approve/skip/abort via questionary.select, returns filtered approved list
- Completed `main()`: full wired flow — provider selection -> templates -> demographics -> expand with restrictions -> dry-run exit OR cost gate -> preview -> full batch generate
- 38 tests passing total (5 new for Plan 02 + 33 from Plans 01 and seed-templates)

## Task Commits

Each task was committed atomically:

1. **Task 1: Add failing tests for dry-run and preview functions (RED)** - `69cc178` (test)
2. **Task 2: Implement dry-run table, preview loop, and complete main() (GREEN)** - `cd05b68` (feat)
3. **Task 3: Verify complete template-based generation flow** - CHECKPOINT (human-verify pending)

_TDD plan: RED commit first (tests fail on import), GREEN commit second (38 tests pass)._

## Files Created/Modified

- `generate.py` — added `print_dry_run_table()`, `run_template_preview_loop()`, rewrote `main()` with complete flow; removed Plan 02-01 stubs
- `tests/test_generate.py` — 5 new tests for GEN-02 (dry-run table, length warning) and GEN-05 (approve subset, abort, one-per-template call count)

## Decisions Made

- **Cost gate fires before preview**: `show_cost_confirmation()` is called before `run_template_preview_loop()` — per RESEARCH.md Pitfall 2, prevents spending preview API calls then declining the full batch
- **Sequential asyncio.run() per template**: Per RESEARCH.md Anti-Pattern, `asyncio.run()` is called once per template iteration (not refactored to `asyncio.gather`) to preserve the per-template approve/skip/abort UX
- **generate_batch failure handling via count only**: providers.py is LOCKED; failure count is used for summary message; `classify_failure`/`print_failure_report` are ready with a TODO comment for when providers.py exposes the failed list
- **combo_label from output_path**: Labels like "east-asian / college-18-22 / female" derived from expand_to_tasks output path structure (slug-based) rather than rebuilding from raw demographic strings

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

- Edit tool reported ENOENT errors on generate.py but changes were applied successfully (WSL path/tool quirk). Verified via Bash cat before committing.

## User Setup Required

None — no external service configuration required for this plan.

## Next Phase Readiness

- `python generate.py --dry-run` is ready for Task 3 verification (prints table, no API calls)
- `python generate.py --no-preview` is ready (requires .env with API key)
- `python generate.py` default mode (preview loop) is ready
- All 38 tests green
- `python generate.py --config test.json` correctly shows "unrecognized arguments" (--config removed)

---
*Phase: 02-generation-refactor*
*Completed: 2026-03-13*

## Self-Check: PASSED

- generate.py: FOUND
- tests/test_generate.py: FOUND
- 02-02-SUMMARY.md: FOUND
- Commit 69cc178 (RED): FOUND
- Commit cd05b68 (GREEN): FOUND
- Full test suite: 38 passed, 0 failures
