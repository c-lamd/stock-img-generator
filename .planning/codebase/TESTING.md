# Testing Patterns

**Analysis Date:** 2026-03-12

## Test Framework

**Status:** No testing framework currently in use

**Observation:** The project does not have any test files, test configuration, or test dependencies. This is typical for a very small project in early stages (single initial commit). No test runner (pytest, unittest, etc.) is configured.

## Test File Organization

**Current State:** Not applicable — no tests exist

**Recommendation for Future:** When testing is added, follow these conventions:
- **Location:** Co-locate with source files or use a `tests/` directory at project root
- **Naming:** Use `test_*.py` or `*_test.py` pattern (standard Python convention)
- **Structure:**
  ```
  stock-image-gen/
  ├── generate.py
  ├── providers.py
  ├── tests/
  │   ├── __init__.py
  │   ├── test_generate.py       # Tests for generate.py
  │   ├── test_providers.py       # Tests for providers.py
  │   └── fixtures/              # Shared test data
  ```

## Testing Priorities (Recommended)

Given the codebase structure and risk profile, prioritize testing in this order:

### High Priority (Test First)

**1. Provider API integrations (`providers.py`)**
- Each provider implementation is critical: `_generate_openai()`, `_generate_fal()`, `_generate_stability()`
- **What to test:**
  - Request format correctness (headers, JSON payload shape, multipart encoding for Stability)
  - Response parsing (base64 decoding for OpenAI/Stability, URL handling for fal.ai)
  - Error handling (rate-limit retries with exponential backoff)
  - File I/O (directory creation, file writing)

**Example test structure:**
```python
# tests/test_providers.py

import asyncio
import base64
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

@pytest.mark.asyncio
async def test_generate_openai_success(tmp_path):
    """Test successful image generation and file write."""
    mock_client = AsyncMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "data": [{"b64_json": base64.b64encode(b"fake_image_data").decode()}]
    }
    mock_client.post.return_value = mock_response

    output_path = tmp_path / "test.png"
    sem = asyncio.Semaphore(1)

    await _generate_openai(mock_client, "fake_key", "test prompt", output_path, sem)

    assert output_path.exists()
    assert output_path.read_bytes() == b"fake_image_data"

@pytest.mark.asyncio
async def test_request_retry_on_429(tmp_path):
    """Test exponential backoff on rate limit (429)."""
    mock_client = AsyncMock()
    # First two calls return 429, third succeeds
    mock_response_429 = MagicMock(status_code=429)
    mock_response_ok = MagicMock(status_code=200)
    mock_response_ok.json.return_value = {"data": [{"b64_json": base64.b64encode(b"img").decode()}]}

    mock_client.post.side_effect = [mock_response_429, mock_response_429, mock_response_ok]

    output_path = tmp_path / "test.png"
    sem = asyncio.Semaphore(1)

    # Should not raise; should retry and succeed
    await _generate_openai(mock_client, "key", "prompt", output_path, sem)
    assert output_path.exists()
```

**2. Prompt building (`generate.py`)**
- `build_prompts()` generates all combinations — logic is straightforward but high-value to verify
- **What to test:**
  - Correct cartesian product creation
  - Prompt template substitution (age_desc, ethnicity, pose, props)
  - Slug generation for filenames

**Example:**
```python
def test_build_prompts_combinations():
    """Test that all combinations are generated."""
    variables = {
        "ethnicities": ["A", "B"],
        "ages": ["Age1", "Age2"],
        "poses": ["Pose1"],
        "props": ["Prop1"],
    }
    prompts = build_prompts(variables)
    assert len(prompts) == 4  # 2 * 2 * 1 * 1

def test_slugify():
    """Test filesystem-safe slug conversion."""
    assert slugify("East Asian") == "east-asian"
    assert slugify("Middle Eastern") == "middle-eastern"
    assert slugify("No props") == "no-props"
    assert slugify("Lab coat and safety goggles") == "lab-coat-and-safety-goggles"
```

### Medium Priority

**3. Batch orchestration (`generate_batch()` in `providers.py`)**
- **What to test:**
  - Concurrency limit enforcement (semaphore)
  - Progress tracking accuracy
  - Error collection (failed tasks tracked correctly)
  - Exit behavior on all tasks complete/failed

**4. CLI selection (`generate.py`)**
- **What to test:**
  - Provider selection respects configured API keys
  - Variable selection produces correct output format
  - Config file loading/saving

## Test Framework Recommendation

For future test implementation, use **pytest** because:
- It's the modern Python standard (more approachable than unittest)
- Async support via `pytest-asyncio` (plugin) — critical for this codebase
- Fixture system is clean for mock setup
- Concise assertion syntax

**Required dependencies when adding tests:**
```txt
pytest>=7.0
pytest-asyncio>=0.20
pytest-mock>=3.10
httpx[testing]>=0.25  # httpx includes MockTransport for easy mocking
```

## Mocking Strategy

**What to Mock:**
- HTTP requests (use `AsyncMock` or `httpx.MockTransport`)
- File I/O (use `tmp_path` fixture for real but isolated temp files)
- Environment variables (use `monkeypatch` fixture)
- User input via `questionary` (mock the `.ask()` method)

**What NOT to Mock:**
- Core logic (async/await, loops, dictionaries)
- File writing (use `tmp_path` fixture to make it real but isolated)
- Semaphore behavior (test real concurrency constraints)

**Example mocking pattern for httpx:**
```python
@pytest.mark.asyncio
async def test_with_mock_httpx():
    """Use httpx.MockTransport for realistic request mocking."""
    def mock_openai_callback(request):
        return httpx.Response(200, json={
            "data": [{"b64_json": base64.b64encode(b"img").decode()}]
        })

    transport = httpx.MockTransport(mock_openai_callback)
    async with httpx.AsyncClient(transport=transport) as client:
        # Test with real httpx client using mocked transport
        pass
```

## Coverage Target

**Recommended:** 80%+ for provider implementations, 60%+ for CLI/orchestration

**Rationale:** Provider API handling is where bugs cost money (API charges). CLI is lower risk since it's directly tested by manual runs.

**View Coverage:**
```bash
pytest --cov=. --cov-report=term-missing --cov-report=html
# Requires: pip install pytest-cov
```

## Test Organization by Module

**`test_providers.py`:**
- Test each provider implementation separately
- Test retry logic in isolation
- Test batch orchestration with mock generators

**`test_generate.py`:**
- Test prompt building (combinatorics, template substitution)
- Test slugify() edge cases
- Test config file I/O

**`conftest.py` (optional, shared fixtures):**
```python
# tests/conftest.py
import asyncio
import pytest

@pytest.fixture
def event_loop():
    """Provide event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def mock_api_key():
    """Provide dummy API key for tests."""
    return "test_key_12345"
```

## Async Testing Pattern

For testing async functions in this project, use `pytest-asyncio`:

```python
import pytest

@pytest.mark.asyncio
async def test_async_function():
    """Async functions marked with @pytest.mark.asyncio."""
    result = await some_async_function()
    assert result is not None
```

**Setup in `pytest.ini` or `pyproject.toml`:**
```ini
[tool:pytest]
asyncio_mode = auto
```

## Error Testing Pattern

Test both happy path and error scenarios:

```python
@pytest.mark.asyncio
async def test_generate_openai_request_error():
    """Test handling of HTTP errors."""
    mock_client = AsyncMock()
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError("500", request=None)
    mock_client.post.return_value = mock_response

    with pytest.raises(httpx.HTTPStatusError):
        await _request(mock_client, "post", "http://example.com")
```

## Test Data / Fixtures

**Where to locate test data:**
- `tests/fixtures/` directory for JSON config examples
- Constants in test files for small datasets
- Use `tmp_path` fixture for file I/O tests (real but isolated)

**Example fixture file (reusable config):**
```json
{
  "provider": "OpenAI GPT Image",
  "variables": {
    "ethnicities": ["East Asian"],
    "ages": ["Elementary (6-10)"],
    "poses": ["sitting at a desk writing"],
    "props": ["Backpack"],
    "count": 2
  }
}
```

## Current State & Next Steps

**What exists:**
- No tests
- No test configuration
- No test dependencies

**What to add when testing is prioritized:**
1. Add test dependencies to `requirements.txt` (or create `requirements-dev.txt`)
2. Create `tests/` directory structure
3. Start with provider tests (highest risk, highest value)
4. Add CLI/prompt tests once provider tests are solid

---

*Testing analysis: 2026-03-12*
