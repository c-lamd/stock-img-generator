#!/usr/bin/env python3
"""
Stock Image Generator - Batch generate diverse student stock photos.

Interactive CLI that generates images across combinations of
ethnicity, age, pose, and props using your choice of AI provider.
"""

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

# ── Variable Options ──────────────────────────────────────────────────────────

ETHNICITIES = [
    "East Asian",
    "South Asian",
    "Black / African American",
    "Hispanic / Latino",
    "White / Caucasian",
    "Middle Eastern",
    "Southeast Asian",
    "Pacific Islander",
]

AGE_GROUPS = {
    "Elementary (6-10)": "young elementary school age (6-10 years old)",
    "Middle School (11-13)": "middle school age (11-13 years old)",
    "High School (14-17)": "high school age (14-17 years old)",
    "College (18-22)": "college age (18-22 years old)",
}

POSES = [
    "sitting at a desk writing",
    "standing with a backpack",
    "reading a book",
    "raising their hand",
    "working on a laptop",
    "in a group discussion",
    "walking in a hallway",
    "presenting in front of a class",
]

PROPS = [
    "Backpack",
    "Books and notebooks",
    "Laptop",
    "Pencil and paper",
    "Lab coat and safety goggles",
    "Art supplies",
    "Calculator",
    "No props",
]

PROMPT_TEMPLATE = (
    "Professional stock photograph of a {age_desc} {ethnicity} student "
    "{pose}. {props}. Clean studio background, professional lighting, "
    "high resolution, photorealistic, natural expression and pose"
)


# ── Interactive Selection ─────────────────────────────────────────────────────


def select_provider():
    """Pick an image generation provider (only shows those with API keys set)."""
    available = []
    for name, info in PROVIDERS.items():
        key = os.getenv(info["env_var"])
        status = "ready" if key else "no key"
        available.append(
            questionary.Choice(
                title=f"{name} — ${info['cost_per_image']}/img ({status})",
                value=name,
                disabled=None if key else f"Set {info['env_var']} in .env",
            )
        )

    if not any(not c.disabled for c in available):
        print("\nNo API keys configured. Copy .env.example to .env and add at least one key.")
        sys.exit(1)

    default = os.getenv("IMAGE_PROVIDER")
    provider = questionary.select(
        "Select image provider:",
        choices=available,
        default=default if default in PROVIDERS else None,
    ).ask()
    if not provider:
        sys.exit(0)
    return provider


def select_variables():
    """Interactive multi-select for each generation variable."""
    print()

    ethnicities = questionary.checkbox(
        "Select ethnicities:",
        choices=ETHNICITIES,
        validate=lambda x: len(x) > 0 or "Select at least one",
    ).ask()
    if not ethnicities:
        sys.exit(0)

    ages = questionary.checkbox(
        "Select age groups:",
        choices=list(AGE_GROUPS.keys()),
        validate=lambda x: len(x) > 0 or "Select at least one",
    ).ask()
    if not ages:
        sys.exit(0)

    poses = questionary.checkbox(
        "Select poses:",
        choices=POSES,
        validate=lambda x: len(x) > 0 or "Select at least one",
    ).ask()
    if not poses:
        sys.exit(0)

    props = questionary.checkbox(
        "Select props:",
        choices=PROPS,
        validate=lambda x: len(x) > 0 or "Select at least one",
    ).ask()
    if not props:
        sys.exit(0)

    count = questionary.text(
        "Images per combination:",
        default="1",
        validate=lambda x: x.isdigit() and int(x) > 0 or "Enter a positive number",
    ).ask()
    if not count:
        sys.exit(0)

    return {
        "ethnicities": ethnicities,
        "ages": ages,
        "poses": poses,
        "props": props,
        "count": int(count),
    }


# ── Prompt Building ──────────────────────────────────────────────────────────


def slugify(text):
    """Convert text to a filesystem-safe slug."""
    return (
        text.lower()
        .replace(" / ", "-")
        .replace("/", "-")
        .replace(" ", "-")
        .replace("(", "")
        .replace(")", "")
        .replace(",", "")
        .replace("'", "")
    )


def build_prompts(variables):
    """Create a prompt dict for every combination of selected variables."""
    combos = list(
        product(
            variables["ethnicities"],
            variables["ages"],
            variables["poses"],
            variables["props"],
        )
    )
    prompts = []
    for ethnicity, age_key, pose, prop in combos:
        age_desc = AGE_GROUPS[age_key]
        props_text = f"Props: {prop}" if prop != "No props" else "No visible props"
        prompt = PROMPT_TEMPLATE.format(
            age_desc=age_desc,
            ethnicity=ethnicity,
            pose=pose,
            props=props_text,
        )
        prompts.append(
            {
                "prompt": prompt,
                "ethnicity": ethnicity,
                "age": age_key,
                "pose": pose,
                "prop": prop,
            }
        )
    return prompts


# ── Main ─────────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(description="Batch stock image generator")
    parser.add_argument(
        "--config", help="Load a saved config JSON instead of interactive prompts"
    )
    parser.add_argument(
        "--output", default="output", help="Output directory (default: output)"
    )
    parser.add_argument(
        "--save-config", help="Save current selections to a JSON file for reuse"
    )
    args = parser.parse_args()

    load_dotenv()

    print("Stock Image Generator")
    print("=" * 40)

    # ── Load or interactively select ──
    if args.config:
        with open(args.config) as f:
            config = json.load(f)
        provider_name = config["provider"]
        variables = config["variables"]
        print(f"\nLoaded config from {args.config}")
    else:
        provider_name = select_provider()
        variables = select_variables()

    # ── Optionally save config for repeat runs ──
    if args.save_config:
        with open(args.save_config, "w") as f:
            json.dump({"provider": provider_name, "variables": variables}, f, indent=2)
        print(f"\nConfig saved to {args.save_config}")

    # ── Build generation tasks ──
    prompts = build_prompts(variables)
    total_images = len(prompts) * variables["count"]
    provider = PROVIDERS[provider_name]
    cost = total_images * provider["cost_per_image"]

    print(f"\n{'─' * 40}")
    print(f"  {len(prompts)} combinations x {variables['count']} each = {total_images} images")
    print(f"  Provider: {provider_name}")
    print(f"  Estimated cost: ${cost:.2f}")
    print(f"{'─' * 40}")

    if not questionary.confirm("\nProceed with generation?", default=True).ask():
        print("Cancelled.")
        return

    output_dir = Path(args.output)
    tasks = []
    for prompt_info in prompts:
        age_slug = slugify(prompt_info["age"])
        eth_slug = slugify(prompt_info["ethnicity"])
        pose_slug = slugify(prompt_info["pose"])
        prop_slug = slugify(prompt_info["prop"])
        for i in range(variables["count"]):
            img_dir = output_dir / age_slug / eth_slug
            filename = f"{pose_slug}_{prop_slug}_{i + 1:03d}.png"
            tasks.append(
                {
                    "prompt": prompt_info["prompt"],
                    "output_path": img_dir / filename,
                }
            )

    # ── Generate ──
    api_key = os.getenv(provider["env_var"])
    asyncio.run(generate_batch(provider_name, api_key, tasks))

    print(f"\nDone! {total_images} images saved to {output_dir}/")


if __name__ == "__main__":
    main()
