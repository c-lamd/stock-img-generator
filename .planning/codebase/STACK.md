# Technology Stack

**Analysis Date:** 2026-03-12

## Languages

**Primary:**
- Python 3 - Core language for CLI tool and async batch processing

## Runtime

**Environment:**
- CPython (standard Python runtime)

**Package Manager:**
- pip
- Lockfile: Not present (uses `requirements.txt` without pinned versions)

## Frameworks

**Core:**
- asyncio (built-in) - Concurrent request handling and batch parallelization across image generation providers

**CLI:**
- questionary 2.0+ - Interactive multi-select prompts for provider selection and variable combinations

**HTTP Client:**
- httpx 0.27+ - Async HTTP requests with session management, supports both sync and async APIs

## Key Dependencies

**Critical:**
- `httpx>=0.27` - Async HTTP client for all provider API calls (OpenAI, fal.ai, Stability AI). Handles authentication headers, multipart form data, timeouts, and base64 decoding of responses.
- `questionary>=2.0` - Interactive CLI prompts for selecting provider, ethnicities, age groups, poses, props, and image count. Provides UX for validating selections.
- `python-dotenv>=1.0` - Loads API keys from `.env` file. Prevents hardcoding secrets in source code.

## Configuration

**Environment:**
- Configured via `.env` file (see `.env.example` for template)
- Each image generation provider requires one API key from these environment variables:
  - `OPENAI_API_KEY` - OpenAI GPT Image API
  - `FAL_KEY` - fal.ai Flux 2 Pro
  - `STABILITY_API_KEY` - Stability AI SD 3.5
- Optional `IMAGE_PROVIDER` env var to skip provider selection prompt (values: "OpenAI GPT Image", "fal.ai Flux 2 Pro", "Stability AI SD 3.5")

**Build:**
- No build step. Tool runs directly via `python generate.py`
- Entry point: `/mnt/c/Users/clamd/Projects/stock-image-gen/generate.py`

## Platform Requirements

**Development:**
- Python 3.7+ (for asyncio and type hints)
- pip or equivalent package manager
- Virtual environment recommended (venv or poetry)

**Production:**
- Python 3.7+ runtime
- Network access to at least one image generation provider API
- Disk space for output images (typically 500KB-2MB per image depending on provider)

## Script Capabilities

**Entry Point:** `generate.py`

**Arguments:**
- `--config <path>` - Load saved configuration JSON instead of interactive prompts
- `--output <path>` - Output directory for generated images (default: `output/`)
- `--save-config <path>` - Save current selections to JSON file for reuse

**Configuration Presets:**
- Supports saving/loading configuration as JSON for batch reuse
- Config format: `{"provider": "OpenAI GPT Image", "variables": {...}}`

## Parallelization Configuration

**Concurrency Limits (per provider in `providers.py`):**
- OpenAI GPT Image: 3 concurrent requests
- fal.ai Flux 2 Pro: 2 concurrent requests
- Stability AI SD 3.5: 10 concurrent requests

**Implementation:** asyncio.Semaphore for concurrency control. Controlled by `max_concurrent` field in `PROVIDERS` dict in `providers.py`.

## API Rate Limiting & Retry Strategy

**Retry Logic:** Exponential backoff on HTTP 429 (rate limit) responses
- Max retries: 3 attempts
- Backoff delays: 5s → 10s → 20s (2^n * 5 seconds)
- Implemented in `_request()` helper in `providers.py`

---

*Stack analysis: 2026-03-12*
