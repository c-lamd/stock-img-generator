---
phase: 01-template-engine
plan: "03"
subsystem: template-engine
tags: [python, tdd, pytest, templates, seed-templates, demographics]

# Dependency graph
requires:
  - phase: 01-template-engine/01-02
    provides: template_engine.py with load_template, expand_to_tasks, TemplateFile API

provides:
  - templates/stem-lab.txt: STEM lab scene — student with circuit board in science lab
  - templates/stem-electronics-pair.txt: pair collaboration on robotics/electronics project
  - templates/student-portrait.txt: individual portrait in school hallway
  - templates/science-jump.txt: celebration jump outside school building
  - tests/test_seed_templates.py: 6 integration tests for seed template loading and expansion

affects:
  - 01-04 (generate.py integration will load seed templates from templates/ via load_templates_dir)
  - Phase 2 (content policy smoke test can use these 4 templates as test inputs)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "TDD red-green cycle — test commit (RED) followed by feat commit (GREEN)"
    - "Seed templates as living documentation — template files show users the expected format"
    - "All 3 required placeholders ({ethnicity}, {age}, {gender}) used inline in natural prose"

key-files:
  created:
    - templates/stem-lab.txt
    - templates/stem-electronics-pair.txt
    - templates/student-portrait.txt
    - templates/science-jump.txt
    - tests/test_seed_templates.py
  modified: []

key-decisions:
  - "Seed templates use ## name:/description:/tags: headers exactly matching the locked .txt format"
  - "Photography style directives embedded inline in template body (not as metadata) — richer prompts, composable with demographic fills"

patterns-established:
  - "Pattern 5: Photography directive inline pattern — Canon EOS 5D / lens / lighting / framing all within the prose body"

requirements-completed: [UX-01]

# Metrics
duration: 1min
completed: 2026-03-13
---

# Phase 1 Plan 03: Seed Templates Summary

**Four .txt seed templates (STEM lab, electronics pair, student portrait, science jump) with full {ethnicity}/{age}/{gender} placeholders and photography directives, validated by 6 integration tests confirming 256-task Cartesian expansion**

## Performance

- **Duration:** 1 min
- **Started:** 2026-03-13T03:43:16Z
- **Completed:** 2026-03-13T03:44:30Z
- **Tasks:** 1 (TDD: 2 commits)
- **Files modified:** 5

## Accomplishments

- Four seed templates created in templates/ directory, ready for immediate use without any user configuration
- All templates use all three required placeholders and include multiple photography style directives (Canon EOS 5D Mark IV, lens, lighting, framing)
- Full expansion verified: 4 templates x 8 ethnicities x 4 age groups x 2 genders = 256 task dicts
- 21 total tests pass (5 demographics + 10 template engine + 6 seed template integration)

## Task Commits

Each task was committed atomically:

1. **Task 1 (RED): Create failing integration tests for seed templates** - `084ca3b` (test)
2. **Task 1 (GREEN): Create four seed template files** - `c9d8b52` (feat)

**Plan metadata:** (docs commit follows)

_Note: TDD tasks have two commits — test (RED) then feat (GREEN)_

## Files Created/Modified

- `/mnt/c/Users/clamd/Projects/stock-image-gen/templates/stem-lab.txt` - STEM lab scene with circuit board adjustment, safety goggles, soft diffused lighting
- `/mnt/c/Users/clamd/Projects/stock-image-gen/templates/stem-electronics-pair.txt` - Pair collaboration on robotics, soldering iron, bright even lighting
- `/mnt/c/Users/clamd/Projects/stock-image-gen/templates/student-portrait.txt` - Individual portrait in school hallway, shallow depth of field, natural window lighting
- `/mnt/c/Users/clamd/Projects/stock-image-gen/templates/science-jump.txt` - Celebration jump outside school building, full body framing, bright daylight
- `/mnt/c/Users/clamd/Projects/stock-image-gen/tests/test_seed_templates.py` - 6 integration tests: file existence, load, name header, style directives, single render, full 256-count expansion

## Decisions Made

- **Photography directives inline:** Style directives (lighting, lens, framing) are embedded directly in the template body prose rather than stored as metadata headers. This produces richer, composable prompts since the directives get combined naturally with the filled demographics.
- **Template format exactly matches locked decision:** All four files use the ## name:/description:/tags: header pattern established in Plan 02, confirming the format is usable without edge cases.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- templates/ directory ready for load_templates_dir() in generate.py (Plan 04)
- Seed templates serve as living documentation for users who want to author custom templates
- 21 tests pass — full suite healthy for Phase 2 development

## Self-Check: PASSED

- templates/stem-lab.txt: FOUND
- templates/stem-electronics-pair.txt: FOUND
- templates/student-portrait.txt: FOUND
- templates/science-jump.txt: FOUND
- tests/test_seed_templates.py: FOUND
- Commit 084ca3b (test - RED phase): FOUND
- Commit c9d8b52 (feat - GREEN phase): FOUND

---
*Phase: 01-template-engine*
*Completed: 2026-03-13*
