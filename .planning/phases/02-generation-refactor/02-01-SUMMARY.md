---
phase: 02-generation-refactor
plan: "01"
subsystem: generation
tags: [python, tabulate, questionary, template-engine, demographics]

requires:
  - phase: 01-template-engine
    provides: "load_templates_dir, expand_to_tasks, TemplateFile, slugify — full template pipeline"
  - phase: 01-template-engine
    provides: "demographics.py with ETHNICITIES, AGE_GROUPS, GENDERS constants"

provides:
  - "apply_demographic_restrictions() — filters ages/genders per template metadata with case-insensitive matching"
  - "show_cost_confirmation() — per-template cost breakdown with 50-image gate"
  - "classify_failure() — content policy vs network/API error classification using POLICY_KEYWORDS"
  - "print_failure_report() — failure report grouped by policy vs network failures"
  - "select_templates() — template selection via questionary.checkbox"
  - "select_demographics() — ethnicity/age/gender selection replacing old pose/props flow"
  - "generate.py main() skeleton wiring all new functions"
  - "tests/test_generate.py — 12 unit tests for all new functions"

affects:
  - 02-02-PLAN
  - providers.py integration

tech-stack:
  added:
    - "tabulate 0.10.0 — ASCII table formatting for dry-run output"
  patterns:
    - "TDD RED/GREEN: failing tests committed first, then implementation"
    - "POLICY_KEYWORDS tuple for multi-provider content policy classification"
    - "Case-insensitive demographic restriction matching via .lower() on both sides"
    - "Demographic restriction filtering before expand_to_tasks() call — template_engine unchanged"

key-files:
  created:
    - "tests/test_generate.py — 12 unit tests for GEN-01, GEN-04, DEMO-03, GEN-03, GEN-06"
  modified:
    - "generate.py — old pose/props code removed, new template-based functions implemented"
    - "requirements.txt — tabulate>=0.9.0 added"

key-decisions:
  - "POLICY_KEYWORDS includes 'blocked' and 'policy' for broad fal.ai coverage (low-confidence keywords documented)"
  - "show_cost_confirmation accepts cost_per_image float directly (not provider name) — more testable, no provider lookup in tests"
  - "12 tests created (11 specified + 1 bonus: test_demo03_restrict_ages_case_insensitive) — case-insensitive matching was a plan pitfall"
  - "run_template_preview_loop() stub raises NotImplementedError('Plan 02-02') — not left as pass"

patterns-established:
  - "Pattern: demographic restriction filtering happens in generate.py before calling template_engine.expand_to_tasks() — template_engine stays generic"
  - "Pattern: POLICY_KEYWORDS tuple at module level — easy to extend with new provider keywords"

requirements-completed: [GEN-01, GEN-03, GEN-04, GEN-06, DEMO-03]

duration: 3min
completed: 2026-03-13
---

# Phase 2 Plan 01: Generate.py Core Functions Summary

**generate.py rewritten with template-based pipeline: old pose/props constants removed, ETHNICITIES/AGE_GROUPS imported from demographics.py, six new pure functions implemented and tested with 12 unit tests (33 total pass)**

## Performance

- **Duration:** ~3 min
- **Started:** 2026-03-13T04:14:29Z
- **Completed:** 2026-03-13T04:16:58Z
- **Tasks:** 2 (TDD: RED then GREEN)
- **Files modified:** 3

## Accomplishments

- Removed all old variable-combination code (POSES, PROPS, PROMPT_TEMPLATE, build_prompts, build_tasks, build_preview_tasks, slugify, select_variables, --config/--save-config) from generate.py
- Implemented six new pure/testable functions: select_templates, select_demographics, apply_demographic_restrictions, show_cost_confirmation, classify_failure, print_failure_report
- 12 new unit tests covering all specified behaviors; full suite 33 tests passing with no regressions
- tabulate installed and added to requirements.txt

## Task Commits

Each task was committed atomically:

1. **Task 1: Create test_generate.py with failing unit tests (RED)** - `e8451a1` (test)
2. **Task 2: Implement core functions in generate.py (GREEN)** - `1bc2f4b` (feat)

_TDD plan: RED commit first (tests fail), GREEN commit second (tests pass)._

## Files Created/Modified

- `tests/test_generate.py` — 12 unit tests for GEN-01, GEN-04, DEMO-03 (restrict_ages, restrict_genders, no-restrictions, case-insensitive), GEN-03 (cost breakdown, 50-image gate), GEN-06 (classify_policy_openai, classify_network, classify_stability_nsfw, failure_report)
- `generate.py` — complete rewrite: old code removed, six new functions + updated main() skeleton
- `requirements.txt` — tabulate>=0.9.0 added

## Decisions Made

- `show_cost_confirmation` signature takes `cost_per_image` float directly rather than `provider_name` — enables clean unit testing without provider dict lookup
- POLICY_KEYWORDS includes broad keywords (`"blocked"`, `"policy"`) for speculative fal.ai coverage; these are documented as low-confidence in RESEARCH.md
- Added `test_demo03_restrict_ages_case_insensitive` beyond the 11 specified — the case-insensitive pitfall was explicitly called out in RESEARCH.md as a common bug
- `run_template_preview_loop()` raises `NotImplementedError("Plan 02-02")` rather than being a silent `pass` stub — cleaner failure mode

## Deviations from Plan

None — plan executed exactly as written. The one extra test (case-insensitive matching) was added within the stated behavior for DEMO-03 rather than as scope expansion.

## Issues Encountered

- `python` command not found on this system — used `python3` for all commands. pytest.ini may need shebang adjustment if this is consistent.
- httpx, questionary, and other runtime deps not installed in test environment — installed via pip3 before tests could run (not a code issue).

## Next Phase Readiness

- All six core functions ready for Plan 02-02 wiring (dry-run table, preview loop, full main() integration)
- generate.py main() skeleton calls all new functions in correct order
- Plan 02-02 can focus on: --dry-run table output (tabulate already imported), per-template preview loop (run_template_preview_loop stub in place), and failure_report integration with generate_batch() actual failed list

---
*Phase: 02-generation-refactor*
*Completed: 2026-03-13*

## Self-Check: PASSED

- tests/test_generate.py: FOUND
- generate.py: FOUND
- 02-01-SUMMARY.md: FOUND
- Commit e8451a1 (RED): FOUND
- Commit 1bc2f4b (GREEN): FOUND
- Full test suite: 33 passed, 0 failures
