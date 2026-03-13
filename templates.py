"""Template management CLI — create templates via interactive wizard, list existing templates."""

import argparse
import string
import sys
from pathlib import Path

import questionary

from tabulate import tabulate
from template_engine import load_template, load_templates_dir, slugify
from demographics import AGE_GROUPS, GENDERS

# -- Constants --

REQUIRED_PLACEHOLDERS = {"ethnicity", "age", "gender"}


# -- Validation ---------------------------------------------------------------


def validate_body(text):
    """Validate scene body text for required placeholders.

    Returns True on success, or an error string describing the problem.
    Called inline by questionary as a validate callback.
    """
    if not text.strip():
        return "Body cannot be empty"

    found = set()
    for _, field_name, _, _ in string.Formatter().parse(text):
        if field_name is not None:
            found.add(field_name)

    unknown = found - REQUIRED_PLACEHOLDERS
    if unknown:
        allowed = ", ".join(sorted(REQUIRED_PLACEHOLDERS))
        return f"Unknown placeholders: {sorted(unknown)} — allowed: {allowed}"

    missing = REQUIRED_PLACEHOLDERS - found
    if missing:
        return f"Missing required placeholders: {sorted(missing)}"

    return True


# -- Commands -----------------------------------------------------------------


def cmd_create(templates_dir="templates"):
    """Interactive wizard to create a new template file.

    Prompts the user for template metadata and body, validates the body,
    checks for filename collisions, writes the file, and verifies via
    load_template().
    """
    templates_dir = Path(templates_dir)

    # Step 1: Template name
    name = questionary.text("Template name:").ask()
    if name is None:
        sys.exit(0)
    name = name.strip()

    # Step 2: Derive slug and output path
    slug = slugify(name)
    output_path = templates_dir / f"{slug}.txt"

    # Step 3: Collision check
    if output_path.exists():
        overwrite = questionary.confirm(
            f"File already exists: {output_path}. Overwrite?", default=False
        ).ask()
        if not overwrite:
            sys.exit(0)

    # Step 4: Description (optional)
    description = questionary.text("Scene description (shown in list):").ask()
    if description is None:
        description = ""

    # Step 5: Tags (optional)
    tags = questionary.text("Tags (comma-separated):").ask()
    if tags is None:
        tags = ""

    # Step 6: Age restrictions (optional)
    restrict_ages = questionary.checkbox(
        "Restrict to age groups?", choices=list(AGE_GROUPS.keys())
    ).ask()
    if restrict_ages is None:
        restrict_ages = []

    # Step 7: Gender restrictions (optional)
    restrict_genders = questionary.checkbox(
        "Restrict to genders?", choices=GENDERS
    ).ask()
    if restrict_genders is None:
        restrict_genders = []

    # Step 8: Scene body with inline validation
    body = questionary.text(
        "Scene body (must include {ethnicity}, {age}, {gender}):",
        multiline=True,
        validate=validate_body,
    ).ask()
    if body is None:
        sys.exit(0)

    # Step 9: Build file content
    lines = []
    lines.append(f"## name: {name}")
    if description.strip():
        lines.append(f"## description: {description.strip()}")
    if tags.strip():
        lines.append(f"## tags: {tags.strip()}")
    if restrict_ages:
        lines.append(f"## restrict_ages: {', '.join(restrict_ages)}")
    if restrict_genders:
        lines.append(f"## restrict_genders: {', '.join(restrict_genders)}")
    lines.append("")  # blank line separating headers from body
    lines.append(body.strip())
    content = "\n".join(lines) + "\n"

    # Step 10: Write confirmation
    confirmed = questionary.confirm(
        f"Write to {output_path}?", default=True
    ).ask()
    if not confirmed:
        sys.exit(0)

    # Step 11: Write file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")
    print(f"\nTemplate written: {output_path}")

    # Step 12: Post-write verification
    load_template(output_path)
    print("Validation: OK")


def cmd_list(templates_dir="templates"):
    """Display all templates in templates_dir as a formatted table.

    Shows name, scene preview (first 2 body lines, truncated), and
    demographic restrictions.
    """
    templates = load_templates_dir(templates_dir)

    if not templates:
        print(f"No templates found in {templates_dir}/")
        return

    templates = sorted(templates, key=lambda t: t.name)

    rows = []
    for tmpl in templates:
        # Build scene preview from first 2 body lines, truncate to 100 chars
        body_lines = tmpl.body.split("\n")[:2]
        preview = " ".join(line.strip() for line in body_lines if line.strip())
        if len(preview) > 100:
            preview = preview[:97] + "..."

        # Build restriction string
        restrictions = []
        if tmpl.metadata.get("restrict_ages"):
            restrictions.append(tmpl.metadata["restrict_ages"])
        if tmpl.metadata.get("restrict_genders"):
            restrictions.append(tmpl.metadata["restrict_genders"])
        restriction_str = "; ".join(restrictions) if restrictions else "-"

        rows.append([tmpl.name, preview, restriction_str])

    print(tabulate(rows, headers=["Name", "Scene Preview", "Restrictions"], tablefmt="simple"))
    print(f"\nTotal: {len(templates)} template(s) in {templates_dir}/")


# -- Entry Point --------------------------------------------------------------


def main():
    """Parse CLI arguments and dispatch to subcommands."""
    parser = argparse.ArgumentParser(description="Template management tool")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("create", help="Create a new template via wizard")

    list_p = sub.add_parser("list", help="List templates in templates/ directory")
    list_p.add_argument("--dir", default="templates", help="Templates directory")

    args = parser.parse_args()

    if args.command == "create":
        cmd_create()
    elif args.command == "list":
        cmd_list(args.dir)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
