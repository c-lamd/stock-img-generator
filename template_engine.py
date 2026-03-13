"""Template engine — load, validate, and expand scene templates into generation tasks."""

import string
from itertools import product
from pathlib import Path

from demographics import ETHNICITIES, AGE_GROUPS, GENDERS

# -- Constants --

REQUIRED_PLACEHOLDERS = {"ethnicity", "age", "gender"}


# -- Exceptions --


class TemplateValidationError(ValueError):
    """Raised when a template file contains invalid or missing placeholders."""


# -- Data Types --


class TemplateFile:
    """Represents a parsed and validated scene template."""

    def __init__(self, name, slug, body, metadata, source_path):
        self.name = name
        self.slug = slug
        self.body = body
        self.metadata = metadata
        self.source_path = source_path

    def __repr__(self):
        return f"TemplateFile(name={self.name!r}, slug={self.slug!r})"


# -- Internal Helpers --


def _parse_template_text(text, source_path):
    """Parse ## key: value header lines and return (metadata_dict, body_str).

    Header lines start with '##'. A blank line terminates the header block.
    Everything after the header block is the body (stripped).
    """
    metadata = {}
    lines = text.splitlines()
    body_lines = []
    in_header = True

    for line in lines:
        if in_header:
            if line.startswith("##"):
                # Parse 'key: value' after the '##' prefix
                content = line[2:].strip()
                if ":" in content:
                    key, _, value = content.partition(":")
                    metadata[key.strip()] = value.strip()
            elif line.strip() == "":
                # First blank line ends header block
                in_header = False
            else:
                # Non-header, non-blank line ends header block
                in_header = False
                body_lines.append(line)
        else:
            body_lines.append(line)

    body = "\n".join(body_lines).strip()
    return metadata, body


def _validate_placeholders(body, source_path):
    """Validate that body contains exactly REQUIRED_PLACEHOLDERS.

    Raises TemplateValidationError if unknown or missing placeholders found.
    Error messages include the bad placeholder name(s) and source file path.
    """
    found = set()
    for _, field_name, _, _ in string.Formatter().parse(body):
        if field_name is not None:
            found.add(field_name)

    unknown = found - REQUIRED_PLACEHOLDERS
    if unknown:
        raise TemplateValidationError(
            f"{source_path}: unrecognized placeholders: {unknown} "
            f"(allowed: {REQUIRED_PLACEHOLDERS})"
        )

    missing = REQUIRED_PLACEHOLDERS - found
    if missing:
        raise TemplateValidationError(
            f"{source_path}: missing required placeholders: {missing}"
        )


# -- Slug Utility --


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


# -- Public API --


def load_template(path):
    """Load and validate a single-scene .txt template file.

    Returns a TemplateFile. Raises TemplateValidationError if placeholders
    are invalid or missing.
    """
    path = Path(path)
    text = path.read_text(encoding="utf-8")
    metadata, body = _parse_template_text(text, path)
    _validate_placeholders(body, path)
    slug = path.stem
    name = metadata.get("name", path.stem)
    return TemplateFile(name, slug, body, metadata, path)


def load_collection(path):
    """Load a collection .txt file containing multiple scenes separated by '---'.

    Returns list[TemplateFile]. Each scene is validated independently.
    """
    path = Path(path)
    text = path.read_text(encoding="utf-8")
    # Split on '\n---\n' with surrounding newlines to avoid false splits on inline dashes
    blocks = text.split("\n---\n")
    templates = []
    for i, block in enumerate(blocks):
        block = block.strip()
        if not block:
            continue
        metadata, body = _parse_template_text(block, path)
        _validate_placeholders(body, path)
        # Use slugified name from metadata if available, else path.stem-{index}
        if "name" in metadata:
            slug = f"{path.stem}-{slugify(metadata['name'])}"
        else:
            slug = f"{path.stem}-{i}"
        name = metadata.get("name", f"{path.stem}-{i}")
        templates.append(TemplateFile(name, slug, body, metadata, path))
    return templates


def load_templates_dir(directory):
    """Load all .txt template files from a directory.

    Handles both single-scene files and collection files (containing '---').
    Returns flat list[TemplateFile].
    """
    templates = []
    for file_path in Path(directory).glob("*.txt"):
        text = file_path.read_text(encoding="utf-8")
        if "\n---\n" in text:
            templates.extend(load_collection(file_path))
        else:
            templates.append(load_template(file_path))
    return templates


def expand_to_tasks(templates, ethnicities, ages, genders, output_dir, count=1):
    """Expand templates across the demographic matrix into generation task dicts.

    Output path structure: output_dir / age_slug / ethnicity_slug / tmpl.slug / gender_NNN.png

    Grouping by age and ethnicity first makes it easy to compare the same demographic
    across different templates when browsing generated images.

    Args:
        templates: list[TemplateFile]
        ethnicities: list[str]
        ages: dict[str, str] mapping age key to descriptive label
        genders: list[str]
        output_dir: Path or str for the base output directory
        count: number of images to generate per demographic combination

    Returns:
        list[dict] with 'prompt' (str) and 'output_path' (Path) keys.
    """
    output_dir = Path(output_dir)
    tasks = []
    for tmpl, ethnicity, age_key, gender in product(templates, ethnicities, ages, genders):
        age_desc = ages[age_key]
        prompt = tmpl.body.format_map(
            {"ethnicity": ethnicity, "age": age_desc, "gender": gender}
        )
        for i in range(count):
            output_path = (
                output_dir
                / slugify(age_key)
                / slugify(ethnicity)
                / tmpl.slug
                / f"{gender.lower()}_{i + 1:03d}.png"
            )
            tasks.append({"prompt": prompt, "output_path": output_path})
    return tasks
