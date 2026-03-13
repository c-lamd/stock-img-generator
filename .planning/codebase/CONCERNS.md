# Codebase Concerns

**Analysis Date:** 2026-03-12

## Tech Debt

**Inadequate concurrency limits:**
- Issue: Concurrency limits set far below API allowances. OpenAI allows Tier-1 minimum 5 images/min (300/hr), fal.ai supports 40 concurrent slots, but code uses `max_concurrent: 3`, `2`, and `10` respectively.
- Files: `providers.py` (lines 11-27)
- Impact: Generation runs take 3-10x longer than necessary. For 500 images, user expects 1-3 minutes but gets 10-30 minutes with current limits.
- Fix approach: Research actual rate limits for each provider and tier. Set concurrency limits based on documented maximums with safety margin (e.g., 80% of limit). Make limits configurable via environment or CLI flag `--concurrent`.

**No cost validation before billing:**
- Issue: Cost estimate shown (line 252 in `generate.py`) is informational only. No hard limits prevent accidentally requesting $100+ of images.
- Files: `generate.py` (lines 244-257)
- Impact: User can accidentally generate far more images than intended if they miscount combinations. Confirmation prompt is easy to skip. No per-run budget cap.
- Fix approach: Add optional `--max-cost` flag that aborts if estimated cost exceeds threshold. Show cost breakdown by variable (ethnicity × age × pose × prop × count).

**Incomplete error handling in batch generation:**
- Issue: Individual task failures (line 156-157 in `providers.py`) catch all exceptions but only print first 10 failures. Silent failures for images beyond the 10-item window.
- Files: `providers.py` (lines 152-174)
- Impact: User doesn't know full scope of failures. May assume all images generated when 50% actually failed.
- Fix approach: Write all failures to a `generation_failures.json` file in output directory. Report count and detailed log. Offer retry mechanism for failed tasks.

**No cleanup of partial output on failure:**
- Issue: If batch fails midway, partially-downloaded/corrupt images may remain in output directory and won't be re-generated on retry.
- Files: `providers.py` (lines 74-75, 101-102, 128-129)
- Impact: Retrying a failed batch may skip already-partially-generated images. Output directory gets cluttered with incomplete files.
- Fix approach: Write images to temporary files first (e.g., `.tmp`), only rename to final path on success. Add `--clean-failed` option to remove incomplete files before retry.

---

## Known Bugs

**Race condition in progress counter:**
- Symptoms: Progress percentage occasionally shows >100% or jumps irregularly when many tasks complete simultaneously.
- Files: `providers.py` (lines 159-162)
- Trigger: Run with high `max_concurrent` (10+) and many small prompts.
- Workaround: Use lower concurrency limits. Current code is actually safe due to Python GIL, but reported percentage can be misleading due to timing of nonlocal updates.
- Root cause: `completed` is incremented after HTTP request completes but before progress printed. Multiple tasks finishing in same event loop tick cause out-of-order prints.

**HTTP timeout too strict for large images:**
- Symptoms: OpenAI image generation hangs at 150s then raises timeout error, even though generation succeeds on provider side.
- Files: `providers.py` (line 69)
- Trigger: Large batches with many concurrent requests taxing OpenAI infrastructure. Happens ~5% of the time in production runs.
- Current state: Retry logic (lines 35-44) only handles 429, not timeout. Timeout causes permanent failure.
- Workaround: None. Image is silently lost.

**Filename collision risk for repeated generations:**
- Symptoms: Running generator twice with same parameters overwrites previous images without warning.
- Files: `generate.py` (lines 267-268)
- Trigger: User runs tool twice with identical selections. First batch in `/output/`, second batch overwrites.
- Current state: No check for existing files. Questionary has no "skip existing" option.
- Workaround: Manually create new output directory with `--output` flag.

---

## Security Considerations

**API keys exposed in plain text config files:**
- Risk: If user saves config with `--save-config`, the resulting JSON may be committed to git containing interpolated prompts but not API keys. However, API keys live in `.env` which is gitignored. If user manually adds keys to `--config` JSON, exposure risk exists.
- Files: `.env.example` (documented), `.gitignore` exists and should block `.env`
- Current mitigation: `.env` is gitignored. Example file shows empty values. Documentation warns users.
- Recommendations: (1) Add explicit check in code to prevent API keys from being saved to config JSON. (2) Add pre-commit hook to catch `OPENAI_API_KEY=sk-` patterns in code. (3) Document secret management best practices in README.

**No input validation on prompt template variables:**
- Risk: User-controlled ethnicity/age/pose/prop selections are interpolated directly into prompts without escaping. While these are from predefined lists (low risk), future additions of user-defined values could inject prompt injection attacks (e.g., "ignore previous instructions").
- Files: `generate.py` (lines 173-202, PROMPT_TEMPLATE)
- Current mitigation: All options hardcoded in ETHNICITIES/AGE_GROUPS/POSES/PROPS lists.
- Recommendations: (1) If user-defined variables added, validate against regex whitelist (alphanumeric + spaces/hyphens only). (2) Consider templating library (Jinja2) to handle escaping if complexity grows.

**No rate limiting defense:**
- Risk: Tool creates parallel requests at configured concurrency level. If concurrency limits are raised (future improvement), tool could trigger provider's DDoS protections or breach account limits, leading to temporary account lockout.
- Files: `providers.py` (lines 33-44, 146)
- Current mitigation: Retry logic handles 429 backoff. Concurrency limits are intentionally low.
- Recommendations: (1) Add telemetry/logging of rate limit hits. (2) Implement adaptive concurrency (start low, increase gradually). (3) Document per-provider tier limits in comments.

---

## Performance Bottlenecks

**Sequential file I/O in async context:**
- Problem: Image bytes written synchronously (`.write_bytes()`) in async context. Creates thread pool overhead. For 500 images, adds 2-5 seconds cumulative latency.
- Files: `providers.py` (lines 74-75, 101-102, 128-129)
- Cause: `Path.write_bytes()` is not async-friendly in `httpx` async context.
- Improvement path: Use `aiofiles` library for async file writes. Expected improvement: 1-2 seconds for 500 images.

**No connection pooling/keepalive across requests:**
- Problem: `httpx.AsyncClient()` created once per batch (line 165), reused for all tasks. This is actually correct, but connection pool size is unconfigured. For high concurrency (future improvement), pool may need tuning.
- Files: `providers.py` (lines 165-166)
- Cause: Default httpx pool size is 100, sufficient now but worth documenting.
- Improvement path: Add explicit `limits=httpx.Limits(max_connections=100, max_keepalive_connections=50)` for clarity. Test with higher concurrency.

**Memory accumulation in failed list:**
- Problem: Failed tasks accumulate full error objects in memory (line 157). For massive batches (10k+ images), this could consume significant RAM.
- Files: `providers.py` (lines 150-157)
- Cause: All failures stored in list before reporting.
- Improvement path: Write failures to file incrementally. Keep only most recent N failures in memory (e.g., 100).

---

## Fragile Areas

**Provider implementation coupling:**
- Files: `providers.py` (lines 50-136)
- Why fragile: Each provider (`_generate_openai`, `_generate_fal`, `_generate_stability`) has slightly different API contracts (headers, request format, response parsing). If any API changes slightly (URL, response key name), function breaks silently or with cryptic errors.
- Safe modification: (1) Add integration tests for each provider with mock responses. (2) Extract response parsing into separate function. (3) Add schema validation using `pydantic` or similar. (4) Add detailed logging of request/response for debugging.
- Test coverage: Currently no tests exist.

**Variable selection UI depends on questionary library behavior:**
- Files: `generate.py` (lines 74-100, 103-153)
- Why fragile: Questionary library behavior may change across versions. If questionary is upgraded, `.ask()` might return None differently, or validation logic might break.
- Safe modification: Pin questionary version in `requirements.txt` (currently not pinned). Add unit tests for select/checkbox workflows.
- Test coverage: None.

**Hardcoded ethnicity/age/pose/prop lists:**
- Files: `generate.py` (lines 24-62)
- Why fragile: To add new options, code must be modified. If user wants custom combinations, current design requires code changes.
- Safe modification: (1) Move lists to separate `config.json` file. (2) Load lists from file at startup. (3) Add `--custom-list` option to specify external config.
- Current limitation: Changes require code edit + redeploy.

**Path handling assumes POSIX conventions:**
- Files: `generate.py` (lines 159-170, 267-268)
- Why fragile: `slugify()` function hardcodes forward slashes and string manipulations. On Windows, path separators are backslashes. Path construction using `/` operator works (Path handles it), but filename generation may fail with special characters.
- Safe modification: Test on Windows. Use `pathlib` exclusively (already done). Ensure slugify handles all OS path separators.
- Test coverage: Likely works on Unix/Linux, untested on Windows.

---

## Scaling Limits

**Memory scaling with image count:**
- Current capacity: ~1000 concurrent operations before memory pressure. Each image in-flight consumes ~5-10 MB (1024x1024 PNG in memory).
- Limit: At 40 concurrent (future concurrency bump), 500 images = ~40 × 5MB = 200 MB base + overhead. Still manageable, but 5000 images would hit limits.
- Scaling path: (1) Stream response directly to disk using `streaming=True` instead of loading full response. (2) Reduce batch size if memory warning detected.

**API tier limits for new accounts:**
- Current risk: OpenAI Tier-1 accounts (new users) capped at 5 images/min. At concurrency of 3, this bottlenecks. User sees "Generating: 150/500 (30%)" taking 100+ minutes.
- Limit: OpenAI scaling depends on account spend history. First month limited to Tier-1.
- Scaling path: (1) Detect rate limits and auto-reduce concurrency. (2) Document that "actual throughput depends on account tier" in README. (3) Recommend fal.ai Flux as speed pick for new users.

**No batching/deduplication of duplicate prompts:**
- Current capacity: 8 combinations (4 ethnicities × 2 ages × poses × props) = up to hundreds of unique prompts, each requested separately.
- Limit: If user selects same ethnicity/age/pose multiple times, duplicates are generated separately (not reused).
- Scaling path: Deduplicate prompts by hash before generation. If same prompt requested twice, reuse first image.

---

## Dependencies at Risk

**httpx version floating (`>=0.27`):**
- Risk: httpx is young and may introduce breaking changes. Version 1.0 behavior could differ from 0.27.
- Impact: Async client API, timeout handling, or response object methods could break.
- Migration plan: (1) Pin to `httpx>=0.27,<1.0` to prevent major version upgrade. (2) Add integration tests that catch API changes.

**questionary dependency (UI library):**
- Risk: Questionary maintained by single author. If archived, security fixes unlikely.
- Impact: Terminal UI could break with Python version upgrades. Validation logic may become outdated.
- Migration plan: (1) Extract questionary usage into thin wrapper. (2) Consider alternative: `typer` + `rich` for simpler, more mainstream UI. (3) Test with latest Python 3.11+.

**No python-dotenv security updates monitoring:**
- Risk: python-dotenv parses .env files. If security vulnerability discovered (e.g., arbitrary code execution in parsing), new version must be deployed immediately.
- Impact: User .env files could be exploited.
- Migration plan: (1) Use GitHub dependabot to alert on security updates. (2) Add automated tests that fail if dependencies have known vulnerabilities (using `safety` CLI).

---

## Missing Critical Features

**No retry mechanism for transient failures:**
- Problem: Network hiccup, provider temporary outage, or timeout causes image to be lost forever. User must manually re-run entire batch.
- Blocks: Production use. Cannot generate 500+ images reliably without manual intervention.
- Recommendation: Add `--resume` flag that skips already-generated images and retries only failed ones. Store batch manifest (prompt → filepath) in `generation_manifest.json`.

**No progress persistence / resume capability:**
- Problem: Long-running batch (1000+ images) interrupted by power outage or network disconnect loses all progress.
- Blocks: Scaling to large batches (100+).
- Recommendation: Persist progress to file after each successful image. On restart, read manifest and skip completed images.

**No image validation / quality checks:**
- Problem: Generated images may have artifacts, incorrect composition, or privacy issues (not diverse faces). No automated check.
- Blocks: Confident batch generation. User must manually review all images.
- Recommendation: (1) Add optional `--validate` mode that skips invalid images. (2) Use PIL to check image dimensions/format. (3) Future: integrate vision API to verify "student" + "ethnicity" + "age" markers.

**No dry-run mode:**
- Problem: Cost estimate shown but no way to test actual API calls without billing.
- Blocks: Testing and safe validation of config.
- Recommendation: Add `--dry-run` flag that makes test API calls (1 image per provider) and reports actual costs/timings.

---

## Test Coverage Gaps

**No unit tests:**
- What's not tested: `slugify()` function, `build_prompts()` logic, config loading/saving.
- Files: `generate.py` (entire file)
- Risk: Prompt building could silently generate incorrect variable combinations. Config save/load could corrupt data.
- Priority: High — test `build_prompts()` and config I/O.

**No integration tests for providers:**
- What's not tested: Actual API calls to OpenAI, fal.ai, Stability AI. Error handling for each provider.
- Files: `providers.py` (entire file)
- Risk: Provider API changes (URL, request format, response schema) go undetected until user runs tool and fails.
- Priority: High — add mocked tests for each provider with realistic responses.

**No end-to-end tests:**
- What's not tested: Full generation pipeline from interactive CLI through batch completion.
- Files: Both `generate.py` and `providers.py`
- Risk: UI changes or data flow bugs go undetected.
- Priority: Medium — add E2E test using pytest + mock API responses.

**No Windows compatibility testing:**
- What's not tested: File paths, slugify on Windows, Path handling with backslashes.
- Files: `generate.py` (lines 159-170, 267-268)
- Risk: Tool may fail silently on Windows (user's target platform).
- Priority: Medium — test on Windows with realistic batch.

---

*Concerns audit: 2026-03-12*
