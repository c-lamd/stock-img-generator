# Roadmap: Stock Image Generator v2

## Overview

This milestone replaces the existing variable-combination prompt system with a template-based model. Users author rich scene templates once; the tool generates each scene across the full demographic matrix. Three phases build in strict dependency order: the template engine (pure logic, no CLI risk), the generation refactor (highest regression risk, done with stable engine beneath it), and the template management CLI (pure addition, zero regression risk).

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Template Engine** - Build the data layer: demographics constants, template file format, loader, validation, and Cartesian expansion — no CLI changes (completed 2026-03-13)
- [ ] **Phase 2: Generation Refactor** - Replace the variable-combination workflow in generate.py with template-based generation, preserving the preview loop and adding dry-run and improved cost display
- [ ] **Phase 3: Template Management CLI** - Add the interactive template creation wizard and list/view commands as a standalone templates.py module

## Phase Details

### Phase 1: Template Engine
**Goal**: The template engine is complete, tested, and ready to be called by generate.py — demographics constants exist, templates can be loaded and validated, and the full demographic Cartesian product can be assembled into prompt+path task dicts
**Depends on**: Nothing (brownfield — existing generate.py and providers.py are not touched in this phase)
**Requirements**: TMPL-01, TMPL-02, TMPL-03, TMPL-05, DEMO-01, DEMO-02, UX-01
**Success Criteria** (what must be TRUE):
  1. A .txt template file with {ethnicity}, {age}, {gender} placeholders can be loaded and produces one rendered prompt per demographic combination
  2. A template with a missing or misspelled placeholder (e.g., {age_group} instead of {age}) is caught at load time with an error that names the bad placeholder and its source file — before any API call
  3. A template file with per-scene photography style directives (lighting, framing, background) produces prompts that include those directives verbatim in every rendered output
  4. Multiple scene templates stored in a single collection file are each expanded independently across the full demographic matrix
  5. The four seed templates (STEM lab, STEM electronics pair, student portrait, science jump) exist on disk and generate valid prompts when loaded
**Plans:** 3/3 plans complete

Plans:
- [x] 01-01-PLAN.md — Demographics constants module (ETHNICITIES, AGE_GROUPS, GENDERS) and test infrastructure
- [x] 01-02-PLAN.md — Template engine core (loader, validator, expander, assembler)
- [ ] 01-03-PLAN.md — Four seed template files and integration tests

### Phase 2: Generation Refactor
**Goal**: Users can run the tool end-to-end using templates — selecting templates instead of pose/props variables, seeing per-template cost breakdowns, previewing one sample per template, and running dry-run to inspect all prompts before spending credits
**Depends on**: Phase 1
**Requirements**: GEN-01, GEN-02, GEN-03, GEN-04, GEN-05, GEN-06, DEMO-03, UX-02
**Success Criteria** (what must be TRUE):
  1. User can select one or more templates from the templates/ directory, select demographics, and generate images — the tool produces one image per template × ethnicity × age × gender combination with no extra steps
  2. User can run with --dry-run and see a table of all rendered prompts (template, demographic combo, full prompt text) without making any API calls or spending any credits
  3. Cost confirmation shows a per-template breakdown ("Template X: 48 combos × $0.04 = $1.92") and warns with a confirmation gate when the total batch exceeds 50 images
  4. Output files are organized under output/{template_slug}/{age}/{ethnicity}/ so two templates with the same demographics never overwrite each other
  5. Preview mode presents one sample image per template (using the first demographic combination) and lets the user approve, skip, or abort per template before the full batch runs
  6. Failed generations report whether each failure was a content policy rejection or a network/API error, with the exact prompt logged for policy rejections
**Plans**: TBD

### Phase 3: Template Management CLI
**Goal**: Users can create, list, and inspect templates from the CLI without manually editing files — the wizard produces valid template files and the list command shows enough of each template to make a selection decision
**Depends on**: Phase 2
**Requirements**: TMPL-04, TMPL-06
**Success Criteria** (what must be TRUE):
  1. User can run `python templates.py create` and complete a step-by-step wizard that writes a valid .txt template file (with correct placeholders and style directives) to the templates/ directory
  2. User can run `python templates.py list` and see each template's name, scene description preview (first 2-3 lines of body), and demographic restriction if any
  3. A template file created by the wizard loads and validates successfully in the template engine without errors
**Plans**: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Template Engine | 3/3 | Complete   | 2026-03-13 |
| 2. Generation Refactor | 0/TBD | Not started | - |
| 3. Template Management CLI | 0/TBD | Not started | - |
