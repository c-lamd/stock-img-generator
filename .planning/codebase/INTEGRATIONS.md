# External Integrations

**Analysis Date:** 2026-03-12

## APIs & External Services

**Image Generation (pluggable, select one at runtime):**

- **OpenAI GPT Image 1.5 (Low)**
  - What it's used for: Generate student stock photos with best-in-class quality at low cost ($0.009/image)
  - SDK/Client: httpx async calls to `https://api.openai.com/v1/images/generations`
  - Auth: Bearer token via `OPENAI_API_KEY` environment variable
  - Model: `gpt-image-1`
  - Output format: Base64-encoded JSON response, decoded to PNG bytes
  - Concurrency: 3 concurrent requests
  - Implementation: `_generate_openai()` in `providers.py`

- **fal.ai Flux 2 Pro**
  - What it's used for: Fast, high-quality image generation with excellent anatomy handling (1-3 min for 500 images)
  - SDK/Client: httpx async calls to `https://fal.run/fal-ai/flux-2-pro`
  - Auth: `Key {api_key}` header via `FAL_KEY` environment variable
  - Output: JSON response with image URL array, fetched separately via second httpx GET
  - Image size: `square_hd` (1024x1024)
  - Concurrency: 2 concurrent requests
  - Implementation: `_generate_fal()` in `providers.py`

- **Stability AI SD 3.5**
  - What it's used for: Stable Diffusion 3.5 model for budget-conscious generation or self-hosting alternative ($0.04/image)
  - SDK/Client: httpx async calls to `https://api.stability.ai/v2beta/stable-image/generate/sd3`
  - Auth: Bearer token via `STABILITY_API_KEY` environment variable
  - Model: `sd3.5-large`
  - Request format: Multipart form data (httpx `files` parameter)
  - Output format: Base64-encoded JSON response, decoded to PNG bytes
  - Concurrency: 10 concurrent requests
  - Implementation: `_generate_stability()` in `providers.py`

## Data Storage

**Databases:**
- None. Tool is stateless and generates images on-demand.

**File Storage:**
- Local filesystem only
- Output directory structure: `{output_dir}/{age_group_slug}/{ethnicity_slug}/{pose_slug}_{prop_slug}_{number:03d}.png`
- Age groups slugified from keys like "Elementary (6-10)" → "elementary-6-10"
- Ethnicities slugified from names like "East Asian" → "east-asian"
- Default output directory: `output/` relative to script location, configurable via `--output` flag
- Slug conversion handled by `slugify()` function in `generate.py`

**Caching:**
- None. All images generated fresh on each run.

## Authentication & Identity

**Auth Provider:**
- Custom: Direct API key authentication per provider
- No OAuth, no user sessions, no identity management
- Each provider uses its own authentication header format:
  - OpenAI: `Authorization: Bearer {key}`
  - fal.ai: `Authorization: Key {key}`
  - Stability: `Authorization: Bearer {key}`

**Environment Variables (required, set in `.env`):**
- `OPENAI_API_KEY` - For OpenAI GPT Image
- `FAL_KEY` - For fal.ai Flux
- `STABILITY_API_KEY` - For Stability AI
- `IMAGE_PROVIDER` (optional) - Skip prompt by setting default provider name

## Monitoring & Observability

**Error Tracking:**
- None. Errors captured locally and printed to stdout.

**Logs:**
- Console output only
- Progress: Real-time `{completed}/{total} ({percentage}%)`
- Failures: Up to 10 failed images printed with error message, summary of remaining failures
- Implementation: `sys.stdout.write()` and `sys.stdout.flush()` in `generate_batch()` in `providers.py`

## CI/CD & Deployment

**Hosting:**
- Local CLI tool (no server component)
- User clones repo and runs `python generate.py` locally

**CI Pipeline:**
- None detected. Tool is a standalone script with no build automation.

## Environment Configuration

**Required env vars (set one, others optional):**
- `OPENAI_API_KEY` - OpenAI API key from https://platform.openai.com/api-keys
- `FAL_KEY` - fal.ai key from https://fal.ai/dashboard/keys
- `STABILITY_API_KEY` - Stability AI key from https://platform.stability.ai/account/keys

**Optional env vars:**
- `IMAGE_PROVIDER` - Default provider name to skip interactive selection (e.g., "OpenAI GPT Image")

**Secrets location:**
- `.env` file in project root (not committed, see `.gitignore`)
- Template: `.env.example` with all required keys listed

## Configuration Presets

**Saved Configs:**
- JSON format: `{"provider": "OpenAI GPT Image", "variables": {"ethnicities": [...], "ages": [...], "poses": [...], "props": [...], "count": N}}`
- Loaded via `--config <path>` flag
- Saved via `--save-config <path>` flag
- Allows batch runs without interactive prompts

## Webhooks & Callbacks

**Incoming:**
- None. Tool is single-user CLI, no server or webhook endpoints.

**Outgoing:**
- None. Tool generates images via REST API calls, no callbacks or notifications to external services.

## Timeout & Reliability

**HTTP Timeouts (per provider in `providers.py`):**
- OpenAI: 180 seconds (gpt-image-1 can be slow)
- fal.ai: 120 seconds (image generation), 60 seconds (image URL fetch)
- Stability: 120 seconds

**Retry Behavior:**
- HTTP 429 (rate limit): Exponential backoff, max 3 retries (5s → 10s → 20s)
- Other errors: Fail immediately, collected and reported at end
- Implementation: `_request()` helper in `providers.py` lines 33-44

---

*Integration audit: 2026-03-12*
