"""
Image generation providers — async implementations for OpenAI, fal.ai, Stability AI.
"""

import asyncio
import base64
import sys

import httpx

PROVIDERS = {
    "OpenAI GPT Image": {
        "env_var": "OPENAI_API_KEY",
        "cost_per_image": 0.009,
        "max_concurrent": 3,
    },
    "fal.ai Flux 2 Pro": {
        "env_var": "FAL_KEY",
        "cost_per_image": 0.03,
        "max_concurrent": 2,
    },
    "Stability AI SD 3.5": {
        "env_var": "STABILITY_API_KEY",
        "cost_per_image": 0.04,
        "max_concurrent": 10,
    },
}


# ── Retry helper ──────────────────────────────────────────────────────────────


async def _request(client, method, url, max_retries=3, **kwargs):
    """HTTP request with exponential backoff on 429 (rate limit)."""
    for attempt in range(max_retries + 1):
        resp = await getattr(client, method)(url, **kwargs)
        if resp.status_code == 429 and attempt < max_retries:
            wait = 2**attempt * 5  # 5s, 10s, 20s
            await asyncio.sleep(wait)
            continue
        resp.raise_for_status()
        return resp
    resp.raise_for_status()
    return resp


# ── Provider implementations ─────────────────────────────────────────────────


async def _generate_openai(client, api_key, prompt, output_path, sem):
    """Generate an image via OpenAI's gpt-image-1 API."""
    async with sem:
        resp = await _request(
            client,
            "post",
            "https://api.openai.com/v1/images/generations",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "gpt-image-1",
                "prompt": prompt,
                "n": 1,
                "size": "1024x1024",
                "quality": "low",
                "response_format": "b64_json",
            },
            timeout=180,
        )
        data = resp.json()
        img_bytes = base64.b64decode(data["data"][0]["b64_json"])

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(img_bytes)


async def _generate_fal(client, api_key, prompt, output_path, sem):
    """Generate an image via fal.ai's Flux 2 Pro endpoint."""
    async with sem:
        resp = await _request(
            client,
            "post",
            "https://fal.run/fal-ai/flux-2-pro",
            headers={
                "Authorization": f"Key {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "prompt": prompt,
                "image_size": "square_hd",
                "num_images": 1,
            },
            timeout=120,
        )
        data = resp.json()
        img_url = data["images"][0]["url"]

        img_resp = await _request(client, "get", img_url, timeout=60)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(img_resp.content)


async def _generate_stability(client, api_key, prompt, output_path, sem):
    """Generate an image via Stability AI's SD 3.5 API."""
    async with sem:
        resp = await _request(
            client,
            "post",
            "https://api.stability.ai/v2beta/stable-image/generate/sd3",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Accept": "application/json",
            },
            # Stability expects multipart form data
            files={
                "prompt": (None, prompt),
                "model": (None, "sd3.5-large"),
                "output_format": (None, "png"),
                "aspect_ratio": (None, "1:1"),
            },
            timeout=120,
        )
        data = resp.json()
        img_bytes = base64.b64decode(data["image"])

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(img_bytes)


_GENERATORS = {
    "OpenAI GPT Image": _generate_openai,
    "fal.ai Flux 2 Pro": _generate_fal,
    "Stability AI SD 3.5": _generate_stability,
}


# ── Batch orchestration ──────────────────────────────────────────────────────


async def generate_batch(provider_name, api_key, tasks):
    """Run all generation tasks in parallel with progress output."""
    provider = PROVIDERS[provider_name]
    generator = _GENERATORS[provider_name]
    sem = asyncio.Semaphore(provider["max_concurrent"])

    completed = 0
    total = len(tasks)
    failed = []

    async def run_task(client, task):
        nonlocal completed
        try:
            await generator(client, api_key, task["prompt"], task["output_path"], sem)
        except Exception as e:
            failed.append({"path": str(task["output_path"]), "error": str(e)})
        finally:
            completed += 1
            pct = completed / total * 100
            sys.stdout.write(f"\r  Generating: {completed}/{total} ({pct:.0f}%)")
            sys.stdout.flush()

    print(f"\n  Starting generation ({provider_name})...")
    async with httpx.AsyncClient() as client:
        await asyncio.gather(*[run_task(client, t) for t in tasks])
    print()

    if failed:
        print(f"\n  {len(failed)} images failed:")
        for f in failed[:10]:
            print(f"    {f['path']}: {f['error']}")
        if len(failed) > 10:
            print(f"    ... and {len(failed) - 10} more")
