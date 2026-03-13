# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-03-12)

**Core value:** Generate diverse student stock photos from reusable scene templates — same scene, varied demographics — without manually rewriting prompts
**Current focus:** Phase 1 — Template Engine

## Current Position

Phase: 1 of 3 (Template Engine)
Plan: 1 of 4 in current phase
Status: In progress
Last activity: 2026-03-13 — Completed plan 01-01 (demographics constants and test infrastructure)

Progress: [█░░░░░░░░░] 10%

## Performance Metrics

**Velocity:**
- Total plans completed: 1
- Average duration: 1 min
- Total execution time: 1 min

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 01-template-engine | 1 | 1 min | 1 min |

**Recent Trend:**
- Last 5 plans: 01-01 (1 min)
- Trend: -

*Updated after each plan completion*

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- [Init]: Template file format is plain .txt with comment-style headers (not YAML) — prose editing UX beats parsing simplicity for user-authored files; changing after users have authored templates is HIGH recovery cost — decide explicitly at start of Phase 1
- [Init]: providers.py is not touched in any phase — it already consumes {"prompt": str, "output_path": Path} dicts
- [Init]: Four seed templates (STEM lab, STEM electronics pair, student portrait, science jump) ship with the tool as UX-01
- [01-01]: GENDERS = ["male", "female"] using bare strings — template authors add context in template body
- [01-01]: ETHNICITIES and AGE_GROUPS intentionally duplicated in demographics.py and generate.py for Phase 1 — deduplication deferred to Phase 2

### Pending Todos

None yet.

### Blockers/Concerns

- [Pre-Phase 1]: Template format final decision (`.txt` with comment headers vs YAML) must be made explicitly before any template files are authored — format change after the fact is high recovery cost
- [Pre-Phase 2]: Content policy false-positive rate for specific demographic combinations is untested against this codebase's prompt patterns — calibrate with smoke test during Phase 2 development
- [Pre-Phase 2]: OpenAI gpt-image-1 prompt length limit (4000 chars) is not tested with rich template bodies + long demographic labels — measure during Phase 2

## Session Continuity

Last session: 2026-03-13
Stopped at: Completed 01-01-PLAN.md (demographics constants and test infrastructure)
Resume file: None
