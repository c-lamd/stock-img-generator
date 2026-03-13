#!/usr/bin/env python3
"""
Stock Image Generator - Batch generate diverse student stock photos.

Interactive CLI that generates images across combinations of
ethnicity, age, and gender using scene templates and your choice of AI provider.
"""

import argparse
import asyncio
import os
import sys
from pathlib import Path

import questionary
from dotenv import load_dotenv
from tabulate import tabulate

from demographics import AGE_GROUPS, ETHNICITIES, GENDERS
from providers import PROVIDERS, generate_batch
from template_engine import TemplateFile, expand_to_tasks, load_templates_dir

# -- Policy Keywords --

POLICY_KEYWORDS = (
    "content_policy_violation",
    "safety system",
    "content restrictions",
    "ResponsibleAIPolicyViolation",
    "NSFW",
    "content_policy",
    "blocked",
    "policy",
)


# -- Interactive Selection -----------------------------------------------------


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


def select_resolution(provider_name):
    """Pick an image size from the provider's supported options."""
    provider = PROVIDERS[provider_name]
    sizes = provider["sizes"]
    default = provider["default_size"]

    choice = questionary.select(
        "Select image size:",
        choices=list(sizes.keys()),
        default=default,
    ).ask()
    if not choice:
        sys.exit(0)
    return choice, sizes[choice]


def select_templates(templates_dir="templates"):
    """Load templates from templates_dir and present a checkbox for user selection."""
    templates = load_templates_dir(templates_dir)
    if not templates:
        print(f"No templates found in {templates_dir}/. Add .txt files to get started.")
        sys.exit(1)

    choices = [
        questionary.Choice(title=f"{t.name}  ({t.slug})", value=t)
        for t in templates
    ]
    selected = questionary.checkbox(
        "Select templates to generate:",
        choices=choices,
        validate=lambda x: len(x) > 0 or "Select at least one template",
    ).ask()
    if not selected:
        sys.exit(0)
    return selected


def select_demographics():
    """Interactive multi-select for ethnicities, age groups, and genders.

    Returns dict with keys:
        "ethnicities": list[str]
        "ages": dict[str, str] — subset of AGE_GROUPS
        "genders": list[str]
    """
    print()

    ethnicities = questionary.checkbox(
        "Select ethnicities:",
        choices=ETHNICITIES,
        validate=lambda x: len(x) > 0 or "Select at least one",
    ).ask()
    if not ethnicities:
        sys.exit(0)

    age_keys = questionary.checkbox(
        "Select age groups:",
        choices=list(AGE_GROUPS.keys()),
        validate=lambda x: len(x) > 0 or "Select at least one",
    ).ask()
    if not age_keys:
        sys.exit(0)

    genders = questionary.checkbox(
        "Select genders:",
        choices=GENDERS,
        validate=lambda x: len(x) > 0 or "Select at least one",
    ).ask()
    if not genders:
        sys.exit(0)

    ages = {k: AGE_GROUPS[k] for k in age_keys}
    return {"ethnicities": ethnicities, "ages": ages, "genders": genders}


# -- Template-Based Generation ------------------------------------------------


def apply_demographic_restrictions(tmpl, ethnicities, ages, genders):
    """Filter demographics based on template metadata restrictions.

    Reads tmpl.metadata for "restrict_ages" and "restrict_genders" keys.
    Filters ages dict and genders list using case-insensitive matching.
    Ethnicities pass through unchanged (no restrict_ethnicities feature).

    Returns:
        (ethnicities, ages, genders) — filtered copies.
    """
    restricted_ages_raw = tmpl.metadata.get("restrict_ages", "")
    restricted_genders_raw = tmpl.metadata.get("restrict_genders", "")

    if restricted_ages_raw:
        # Build set of lowercase allowed age keys for case-insensitive matching
        allowed_ages_lower = {a.strip().lower() for a in restricted_ages_raw.split(",")}
        ages = {k: v for k, v in ages.items() if k.lower() in allowed_ages_lower}

    if restricted_genders_raw:
        allowed_genders = {g.strip().lower() for g in restricted_genders_raw.split(",")}
        genders = [g for g in genders if g.lower() in allowed_genders]

    return ethnicities, ages, genders


def show_cost_confirmation(template_task_counts, cost_per_image, requires_confirm=True):
    """Print per-template cost breakdown and enforce 50-image gate.

    Args:
        template_task_counts: list of (template_name, count) tuples
        cost_per_image: float — cost per image in USD
        requires_confirm: bool — if True, always prompt for confirmation

    Returns:
        True if user confirms or no confirmation needed.
        Exits via sys.exit(0) if user declines.
    """
    total = sum(c for _, c in template_task_counts)

    print(f"\n{'─' * 50}")
    for name, count in template_task_counts:
        subtotal = count * cost_per_image
        print(f"  {name}: {count} combos x ${cost_per_image:.3f} = ${subtotal:.2f}")
    print(f"  {'─' * 40}")
    print(f"  Total: {total} images, est. ${total * cost_per_image:.2f}")
    print(f"{'─' * 50}")

    if total > 50:
        print(f"\n  Warning: {total} images exceeds the 50-image threshold.")
        if not questionary.confirm("This is a large batch. Proceed?", default=False).ask():
            sys.exit(0)
    elif requires_confirm:
        if not questionary.confirm("Proceed with generation?", default=True).ask():
            sys.exit(0)

    return True


# -- Error Classification and Reporting ----------------------------------------


def classify_failure(failure_dict):
    """Return 'policy' or 'network' based on error string content.

    Checks error string (case-insensitive) against POLICY_KEYWORDS.
    Returns 'policy' if any keyword matches, 'network' otherwise.
    """
    error = failure_dict.get("error", "").lower()
    if any(kw.lower() in error for kw in POLICY_KEYWORDS):
        return "policy"
    return "network"


def print_failure_report(failed, tasks_by_path):
    """Print failures grouped by type (policy vs network).

    Policy failures show the exact prompt text for debugging.
    Network failures show the error string.

    Args:
        failed: list of {"path": str, "error": str} dicts
        tasks_by_path: dict mapping output_path str -> prompt str
    """
    policy_failures = [f for f in failed if classify_failure(f) == "policy"]
    network_failures = [f for f in failed if classify_failure(f) == "network"]

    if policy_failures:
        print(f"\n  Content policy rejections ({len(policy_failures)}):")
        for f in policy_failures:
            prompt = tasks_by_path.get(f["path"], "[prompt unavailable]")
            print(f"    POLICY: {f['path']}")
            print(f"      Prompt: {prompt[:200]}")

    if network_failures:
        print(f"\n  Network/API errors ({len(network_failures)}):")
        for f in network_failures:
            print(f"    ERROR: {f['path']}: {f['error'][:150]}")


# -- Preview Loop Stub (implemented in Plan 02-02) ----------------------------


def run_template_preview_loop():
    raise NotImplementedError("Plan 02-02")


# -- Main ---------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(description="Batch stock image generator")
    parser.add_argument(
        "--output", default="output", help="Output directory (default: output)"
    )
    parser.add_argument(
        "--no-preview", action="store_true",
        help="Skip preview mode, generate full batch immediately"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Print all rendered prompts as a table without making any API calls (Plan 02-02)"
    )
    args = parser.parse_args()

    load_dotenv()

    print("Stock Image Generator")
    print("=" * 40)

    # -- Provider and resolution selection --
    provider_name = select_provider()
    size_label, size_value = select_resolution(provider_name)
    provider = PROVIDERS[provider_name]
    cost_per_image = provider["cost_per_image"]

    # -- Template and demographic selection --
    selected_templates = select_templates()
    demographics = select_demographics()

    # -- Expand tasks per template, applying demographic restrictions --
    output_dir = Path(args.output)
    all_tasks = []
    template_task_counts = []

    for tmpl in selected_templates:
        eth, ages, genders = apply_demographic_restrictions(
            tmpl,
            demographics["ethnicities"],
            demographics["ages"],
            demographics["genders"],
        )
        tasks = expand_to_tasks([tmpl], eth, ages, genders, output_dir)
        all_tasks.extend(tasks)
        template_task_counts.append((tmpl.name, len(tasks)))

    # -- Dry-run placeholder (Plan 02-02) --
    if args.dry_run:
        print("  [dry-run not yet implemented — Plan 02-02]")
        return

    # -- Preview loop placeholder (Plan 02-02) --
    if not args.no_preview:
        pass  # run_template_preview_loop() — implemented in Plan 02-02

    # -- Cost confirmation --
    api_key = os.getenv(provider["env_var"])
    show_cost_confirmation(template_task_counts, cost_per_image)

    # -- Generate --
    tasks_by_path = {str(t["output_path"]): t["prompt"] for t in all_tasks}
    failure_count = asyncio.run(generate_batch(provider_name, api_key, all_tasks, size_value))

    # -- Failure report --
    if failure_count:
        # Note: generate_batch returns count; actual failed dicts not available in this skeleton
        print(f"\n  {failure_count} image(s) failed. Check output for details.")

    total_images = len(all_tasks)
    print(f"\nDone! {total_images} images saved to {output_dir}/")


if __name__ == "__main__":
    main()
