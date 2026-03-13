"""Integration tests for seed template files — load, validate, expand."""

from pathlib import Path

import pytest

from template_engine import load_template, expand_to_tasks
from demographics import ETHNICITIES, AGE_GROUPS, GENDERS

TEMPLATES_DIR = Path(__file__).parent.parent / "templates"

SEED_TEMPLATE_FILES = [
    TEMPLATES_DIR / "stem-lab.txt",
    TEMPLATES_DIR / "stem-electronics-pair.txt",
    TEMPLATES_DIR / "student-portrait.txt",
    TEMPLATES_DIR / "science-jump.txt",
]

STYLE_KEYWORDS = {
    "lighting", "framing", "background", "photorealistic",
    "Canon", "lens", "bokeh", "studio",
}


def test_all_seed_templates_exist():
    """4 .txt files exist in templates/ directory."""
    for path in SEED_TEMPLATE_FILES:
        assert path.exists(), f"Missing seed template: {path}"


def test_each_seed_template_loads():
    """load_template() succeeds for each of the 4 files without TemplateValidationError."""
    for path in SEED_TEMPLATE_FILES:
        tmpl = load_template(path)
        assert tmpl is not None, f"load_template returned None for {path}"


def test_each_seed_template_has_name():
    """Each loaded TemplateFile has a non-empty name from ## name: header."""
    for path in SEED_TEMPLATE_FILES:
        tmpl = load_template(path)
        assert tmpl.name, f"Template {path.name} has empty name"
        assert tmpl.name != path.stem, (
            f"Template {path.name} name falls back to filename stem — "
            f"## name: header may be missing"
        )


def test_each_seed_template_has_style_directives():
    """Each template body contains at least one photography directive keyword."""
    for path in SEED_TEMPLATE_FILES:
        tmpl = load_template(path)
        body_lower = tmpl.body.lower()
        # Check both lowercase and original-case keywords
        found = any(kw.lower() in body_lower for kw in STYLE_KEYWORDS)
        assert found, (
            f"Template {path.name} body has no photography style directive. "
            f"Expected one of: {STYLE_KEYWORDS}"
        )


def test_each_seed_template_renders():
    """expand_to_tasks with 1 template x 1 ethnicity x 1 age x 1 gender = 1 task dict."""
    for path in SEED_TEMPLATE_FILES:
        tmpl = load_template(path)
        tasks = expand_to_tasks(
            templates=[tmpl],
            ethnicities=["East Asian"],
            ages={"High School (14-17)": AGE_GROUPS["High School (14-17)"]},
            genders=["female"],
            output_dir=Path("/tmp/test_output"),
        )
        assert len(tasks) == 1, (
            f"Template {path.name}: expected 1 task, got {len(tasks)}"
        )
        task = tasks[0]
        assert "prompt" in task, f"Template {path.name}: task missing 'prompt' key"
        assert "output_path" in task, f"Template {path.name}: task missing 'output_path' key"


def test_full_expansion_count():
    """expand_to_tasks with all 4 templates x 8 ethnicities x 4 ages x 2 genders = 256."""
    templates = [load_template(p) for p in SEED_TEMPLATE_FILES]
    tasks = expand_to_tasks(
        templates=templates,
        ethnicities=ETHNICITIES,
        ages=AGE_GROUPS,
        genders=GENDERS,
        output_dir=Path("/tmp/test_output"),
    )
    expected = 4 * 8 * 4 * 2
    assert len(tasks) == expected, (
        f"Expected {expected} tasks, got {len(tasks)}"
    )
