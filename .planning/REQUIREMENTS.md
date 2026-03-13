# Requirements: Stock Image Generator v2

**Defined:** 2026-03-12
**Core Value:** Generate high-quality, diverse student stock photos from reusable scene templates — same scene, varied demographics

## v1 Requirements

### Template System

- [x] **TMPL-01**: User can create scene templates as YAML files with `{ethnicity}`, `{age}`, `{gender}` demographic placeholders
- [x] **TMPL-02**: User can include per-template photography style directives (lighting, background, framing) within each template
- [x] **TMPL-03**: Templates are validated at load time — missing or misnamed placeholders are caught before any API calls
- [x] **TMPL-04**: User can create templates interactively through a CLI wizard (guided step-by-step)
- [x] **TMPL-05**: User can store multiple scene templates in a single YAML collection file
- [x] **TMPL-06**: User can list, view, and manage existing templates from the CLI

### Generation Workflow

- [x] **GEN-01**: Tool generates one image per template × demographic combination (scene × ethnicity × age × gender)
- [x] **GEN-02**: User can dry-run to preview all rendered prompts as text before any API calls are made
- [x] **GEN-03**: Cost confirmation shows per-template breakdown and total (not just total)
- [x] **GEN-04**: Output file paths include template slug to prevent cross-template file overwrites
- [x] **GEN-05**: Preview mode works with template-based prompts (1 sample per template, review, tweak, approve)
- [x] **GEN-06**: Failed generations distinguish content policy rejections from network/API errors in failure reports

### User Experience

- [x] **UX-01**: Tool ships with seed templates based on proven prompts (STEM lab, STEM electronics pair, student portrait, science jump) so users can generate immediately without authoring templates first
- [x] **UX-02**: Default workflow requires minimal steps — select templates, select demographics, generate (no unnecessary confirmations or config)

### Demographics

- [x] **DEMO-01**: Gender is a demographic variable (male, female) selectable alongside ethnicity and age
- [x] **DEMO-02**: Existing ethnicity and age group options are preserved from current tool
- [x] **DEMO-03**: Templates can optionally restrict which demographics they apply to (e.g., college-only scene, female-only scene)

## v2 Requirements

### Template Enhancements

- **TMPL-07**: AI-assisted prompt writing for template authoring
- **TMPL-08**: Template versioning and history

### Generation Enhancements

- **GEN-07**: Batch scheduling (queue runs for later)
- **GEN-08**: Image quality scoring / auto-reject low quality results

## Out of Scope

| Feature | Reason |
|---------|--------|
| Shared/global photography style suffix | Per-template style gives full control; global suffix removed |
| Web UI | CLI-only tool per project scope |
| Multi-subject demographic mixing | Demographics apply uniformly to all subjects in a template |
| Non-binary gender support | Model support is inconsistent across providers; defer until tested |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| TMPL-01 | Phase 1 | Complete (01-02) |
| TMPL-02 | Phase 1 | Complete (01-02) |
| TMPL-03 | Phase 1 | Complete (01-02) |
| TMPL-04 | Phase 3 | Complete |
| TMPL-05 | Phase 1 | Complete (01-02) |
| TMPL-06 | Phase 3 | Complete |
| GEN-01 | Phase 2 | Complete |
| GEN-02 | Phase 2 | Complete |
| GEN-03 | Phase 2 | Complete |
| GEN-04 | Phase 2 | Complete |
| GEN-05 | Phase 2 | Complete |
| GEN-06 | Phase 2 | Complete |
| DEMO-01 | Phase 1 | Complete (01-01) |
| DEMO-02 | Phase 1 | Complete (01-01) |
| DEMO-03 | Phase 2 | Complete |
| UX-01 | Phase 1 | Complete |
| UX-02 | Phase 2 | Complete |

**Coverage:**
- v1 requirements: 17 total
- Mapped to phases: 17
- Unmapped: 0

---
*Requirements defined: 2026-03-12*
*Last updated: 2026-03-13 after 01-02 completion (TMPL-01, TMPL-02, TMPL-03, TMPL-05 complete)*
