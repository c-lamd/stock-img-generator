# Coding Conventions

**Analysis Date:** 2026-03-12

## Naming Patterns

**Files:**
- Lowercase with underscores: `generate.py`, `providers.py`
- Module names describe functionality clearly

**Functions:**
- Lowercase with underscores for public functions: `select_provider()`, `build_prompts()`, `slugify()`
- Prefix with underscore for internal/private async handlers: `_generate_openai()`, `_generate_fal()`, `_request()`
- No special naming convention for async functions beyond the underscore prefix

**Variables:**
- Lowercase with underscores: `api_key`, `output_dir`, `total_images`, `max_retries`
- Descriptive names preferred: `provider_name` instead of `p`, `cost_per_image` instead of `cost`
- Dictionary keys use underscores: `"env_var"`, `"cost_per_image"`, `"max_concurrent"`
- Abbreviations acceptable in specific contexts: `sem` for semaphore (clear from context), `pct` for percentage, `resp` for response

**Types:**
- No explicit type hints in function signatures (Python 3.7 compatible style)
- Type information provided in docstrings: `"""Create a prompt dict for every combination of selected variables."""`
- Dictionary structures documented in context (PROVIDERS dict at top of `providers.py`)

**Constants:**
- Uppercase with underscores for module-level constants: `ETHNICITIES`, `AGE_GROUPS`, `POSES`, `PROPS`, `PROMPT_TEMPLATE`, `PROVIDERS`, `_GENERATORS`
- Constants grouped at module level, near imports

## Code Style

**Formatting:**
- Standard Python style (PEP 8 compatible)
- Indentation: 4 spaces
- Line length: Generally under 100 characters, max observed ~90 characters
- No explicit formatter configured (no `.prettierrc`, `black` config, or `autopep8` config)

**Linting:**
- No linter configuration detected (no `.eslintrc`, `pylint.rc`, or `flake8` config)
- Code appears to follow implicit style standards

**Decorations:**
- Section markers used for visual organization: `# ── Variable Options ──...──`
- Comment blocks separate logical sections in `generate.py` and `providers.py`
- Each section clearly delineated with header comments

## Import Organization

**Order:**
1. Standard library imports: `argparse`, `asyncio`, `json`, `os`, `sys`, `base64`
2. Third-party imports: `httpx`, `questionary`, `dotenv`
3. Local imports: `from providers import ...`

**Path Aliases:**
- Not used (no alias configuration needed in small project)
- Direct relative imports: `from providers import PROVIDERS, generate_batch`
- Standard library imports use full module paths: `from pathlib import Path`

**Examples from `generate.py` (lines 9-20):**
```python
import argparse
import asyncio
import json
import os
import sys
from itertools import product
from pathlib import Path

import questionary
from dotenv import load_dotenv

from providers import PROVIDERS, generate_batch
```

## Error Handling

**Patterns:**
- Try-except at task level for batch operations: `try: await generator(...) except Exception as e:` (line 154-157 in `providers.py`)
- HTTP status code checking before raising: `resp.raise_for_status()` after non-429 responses
- Exit on missing credentials: `sys.exit(1)` for critical configuration issues (line 90 in `generate.py`)
- Failed tasks collected and reported at end of batch rather than failing fast
- Specific tracking of failures with path and error message: `failed.append({"path": str(...), "error": str(e)})`

**Error Recovery:**
- Exponential backoff for rate-limited requests (429 status code): retry with 5s, 10s, 20s delays
- Telemetry collection: failed tasks printed in summary (up to 10 shown, count shown for remainder)

## Logging

**Framework:** `sys.stdout` and `sys.stderr` (no logging library)

**Patterns:**
- Progress output during batch generation: `sys.stdout.write()` with `\r` for overwriting same line (line 161)
- User-facing messages via `print()` for headers and summaries
- Error messages prefixed with context (path and error string)
- Minimal logging: no timestamp, no severity levels
- Real-time progress: percentage and completed/total count updated in place

**Example from `providers.py` (line 161):**
```python
sys.stdout.write(f"\r  Generating: {completed}/{total} ({pct:.0f}%)")
sys.stdout.flush()
```

## Comments

**When to Comment:**
- Section headers for major code blocks (see organizational markers above)
- Docstrings for all public functions
- Inline comments for non-obvious algorithm details (e.g., exponential backoff calculation at line 38 in `providers.py`: `wait = 2**attempt * 5  # 5s, 10s, 20s`)

**JSDoc/TSDoc:**
- Not applicable (Python project)
- Module-level docstring provided: `"""Stock Image Generator - Batch generate diverse student stock photos."""` (line 2-4 in `generate.py`)
- Function docstrings follow triple-quote format with one-liner plus optional detail

**Example docstring from `generate.py` (line 159-160):**
```python
def slugify(text):
    """Convert text to a filesystem-safe slug."""
```

## Function Design

**Size:**
- Mostly short functions (10-30 lines)
- Longest functions: `generate_batch()` (~30 lines), `main()` (~77 lines)
- Single responsibility per function

**Parameters:**
- Functions take only necessary parameters
- API key passed explicitly to generator functions (not stored in closure/class state)
- Semaphore passed to constraint concurrency within generator functions
- Config/options passed as dictionaries for batch operations

**Return Values:**
- `None` for side-effect functions (write to disk, print output)
- Dictionaries for structured data: `select_variables()` returns dict with `"ethnicities"`, `"ages"`, `"poses"`, `"props"`, `"count"` keys
- Lists for batch data: `build_prompts()` returns list of prompt dicts

**Example from `generate.py` (lines 147-153):**
```python
return {
    "ethnicities": ethnicities,
    "ages": ages,
    "poses": poses,
    "props": props,
    "count": int(count),
}
```

## Module Design

**Exports:**
- Clear separation: `generate.py` imports from `providers.py`, not vice versa
- `providers.py` exports `PROVIDERS` dict and `generate_batch()` function
- Underscore-prefixed functions in `providers.py` treated as internal (not imported)

**File Organization:**
- `providers.py`: Provider registry + async HTTP helpers + provider implementations + batch orchestration
- `generate.py`: CLI orchestration + variable selection + prompt building + main entry point

**Barrel Files:**
- Not applicable (small project, direct imports sufficient)

---

*Convention analysis: 2026-03-12*
