# Architecture

**Analysis Date:** 2026-03-12

## Pattern Overview

**Overall:** Layered CLI application with pluggable provider abstraction

**Key Characteristics:**
- Command-line interface (questionary-driven interactive prompts)
- Pluggable provider pattern for multiple image generation APIs
- Asyncio-based concurrent request orchestration with semaphore-controlled concurrency
- Combinatorial generation from configuration variables
- File system output organization by demographic attributes

## Layers

**Presentation (CLI):**
- Purpose: Interactive user prompts for configuration and feedback
- Location: `generate.py` (lines 71-153)
- Contains: Interactive selection functions using questionary library
- Depends on: Configuration models (PROVIDERS, variable options)
- Used by: Main entry point to drive user interaction flow

**Configuration & Orchestration:**
- Purpose: Parse user selections, build generation tasks, coordinate execution
- Location: `generate.py` (lines 156-280)
- Contains: Prompt building, task list creation, cost calculation, main control flow
- Depends on: Presentation layer (for user input), Provider abstraction (for execution)
- Used by: CLI entry point (`main()`)

**Provider Abstraction:**
- Purpose: Unified interface to multiple image generation APIs with consistent error handling
- Location: `providers.py`
- Contains: Provider registry, generator implementations, HTTP request handling
- Depends on: HTTP client (httpx), asyncio
- Used by: Orchestration layer (via `generate_batch()`)

**Network & Persistence:**
- Purpose: HTTP communication and file I/O operations
- Location: `providers.py` (lines 33-129)
- Contains: Retry logic with exponential backoff, base64 decoding, file writes
- Depends on: httpx async client, pathlib
- Used by: Provider implementations

## Data Flow

**Configuration Selection Flow:**

1. User launches CLI (`python generate.py`)
2. Load .env file for API credentials
3. Interactive selection of:
   - Image provider (filtered by available API keys)
   - Ethnicities (multi-select from ETHNICITIES list)
   - Age groups (multi-select from AGE_GROUPS)
   - Poses (multi-select from POSES)
   - Props (multi-select from PROPS)
   - Images per combination (count)
4. Optional save configuration to JSON for reuse

**Generation Task Building:**

1. `build_prompts()` creates cartesian product of selected variables
2. Each combination generates a prompt using PROMPT_TEMPLATE
3. For each combination, create N task objects (where N = images per combination)
4. Each task contains:
   - Full prompt (formatted with ethnicity, age, pose, props)
   - Output path (computed as `output/{age_slug}/{ethnicity_slug}/{pose}_{prop}_{counter:03d}.png`)

**Concurrent Generation:**

1. Spawn async context with httpx.AsyncClient
2. Create asyncio.Semaphore with max_concurrent limit from PROVIDERS registry
3. Gather all tasks and execute them concurrently
4. Each task acquires semaphore, makes API call, saves image
5. Track progress and collect failures
6. Report completion with failure summary

**State Management:**

- Provider configuration: Registry dict in `providers.py` (immutable reference data)
- User selections: Dict with keys "ethnicities", "ages", "poses", "props", "count" (in-memory during run)
- Task queue: List of dicts, each containing "prompt" and "output_path" (in-memory during run)
- Generated images: Persisted to filesystem at computed paths
- Failures: Collected in list during generation, reported at end

## Key Abstractions

**Provider Registry:**
- Purpose: Define supported image generation APIs with metadata (env var, cost, concurrency limits)
- Examples: `PROVIDERS["OpenAI GPT Image"]`, `PROVIDERS["fal.ai Flux 2 Pro"]`
- Pattern: Dict-based configuration with pluggable generator functions in `_GENERATORS`

**Generator Function:**
- Purpose: Implement API-specific image generation logic
- Examples: `_generate_openai()`, `_generate_fal()`, `_generate_stability()`
- Pattern: Async function taking (client, api_key, prompt, output_path, sem) → writes image to disk

**HTTP Request Wrapper:**
- Purpose: Centralized retry logic with exponential backoff for rate limits
- Location: `_request()` function
- Pattern: Wraps httpx methods with 429 handling (wait 5s, 10s, 20s on attempts 1-3)

**Variable Options:**
- Purpose: Define selectable combinations for image generation
- Examples: ETHNICITIES, AGE_GROUPS, POSES, PROPS, PROMPT_TEMPLATE
- Pattern: Lists/dicts at module level, consumed by interactive selection and prompt building

## Entry Points

**CLI Entry:**
- Location: `generate.py` main() function and `if __name__ == "__main__"` block
- Triggers: `python generate.py [--config FILE] [--output DIR] [--save-config FILE]`
- Responsibilities:
  - Parse command-line arguments
  - Load .env credentials
  - Orchestrate interactive selection or load saved config
  - Build task list
  - Execute generation batch
  - Report results

**Batch Generation Entry:**
- Location: `providers.py` `generate_batch()` function
- Triggers: Called from main() with (provider_name, api_key, tasks)
- Responsibilities:
  - Create async context and semaphore
  - Spawn concurrent worker tasks
  - Track progress
  - Collect and report failures

## Error Handling

**Strategy:** Graceful degradation with collection and reporting

**Patterns:**

- **API Rate Limits (429):** Exponential backoff in `_request()` with up to 3 retries (5s, 10s, 20s waits)
- **Individual Image Failures:** Caught in `run_task()`, added to `failed` list, generation continues
- **Missing API Keys:** Detected in `select_provider()`, disable unavailable providers with explanation
- **User Cancellation:** Early exit via None return from questionary prompts
- **File I/O Errors:** Caught at provider level, converted to task failure entry

## Cross-Cutting Concerns

**Logging:** Console-based progress reporting
- Real-time generation counter: `Generating: {completed}/{total} ({pct:.0f}%)`
- Failure summary printed to stdout with up to 10 examples
- Configuration details (combinations, cost, provider) printed before generation

**Validation:**
- Provider selection: Ensures at least one API key is configured
- Variable selection: Each questionary prompt validates at least one item selected
- Count validation: Images per combination must be positive integer
- Slug generation: Converts variable names to filesystem-safe strings (lowercase, replace spaces/slashes/special chars)

**Authentication:**
- Credentials loaded from .env file via dotenv
- Environment variables passed to generator functions and used in HTTP Authorization headers
- No credentials hardcoded; validation in select_provider() catches missing keys

**API Integration:**
- Three provider implementations with consistent interface
- Each provider sends differently-formatted requests to different endpoints
- Response parsing varies (OpenAI: b64_json, fal.ai: URL redirect, Stability: b64_json)
- All providers support concurrent requests with provider-specific rate limits

---

*Architecture analysis: 2026-03-12*
