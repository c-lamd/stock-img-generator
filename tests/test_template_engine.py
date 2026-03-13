"""Unit tests for template_engine.py — covering TMPL-01, TMPL-02, TMPL-03, TMPL-05."""

import pathlib
import pytest

from template_engine import (
    TemplateFile,
    TemplateValidationError,
    load_template,
    load_collection,
    load_templates_dir,
    expand_to_tasks,
)

FIXTURES = pathlib.Path(__file__).parent / "fixtures"

# -- Subset demographics for expand_to_tasks tests (keep count small) --

SAMPLE_ETHNICITIES = ["East Asian", "South Asian"]
SAMPLE_AGES = {"High School (14-17)": "high school age (14-17 years old)"}
SAMPLE_GENDERS = ["male", "female"]


# -- Load and structure tests --


def test_load_valid_template():
    """load_template() on valid_template.txt returns TemplateFile with correct attributes."""
    tmpl = load_template(FIXTURES / "valid_template.txt")
    assert isinstance(tmpl, TemplateFile)
    assert tmpl.name == "Test Lab Scene"
    assert "{ethnicity}" in tmpl.body
    assert "{age}" in tmpl.body
    assert "{gender}" in tmpl.body


def test_style_directives_preserved(tmp_path):
    """Photography style directives in template body appear verbatim in every rendered prompt (TMPL-02)."""
    tmpl = load_template(FIXTURES / "valid_template.txt")
    tasks = expand_to_tasks(
        [tmpl],
        SAMPLE_ETHNICITIES,
        SAMPLE_AGES,
        SAMPLE_GENDERS,
        tmp_path,
        count=1,
    )
    for task in tasks:
        assert "soft diffused lighting" in task["prompt"]
        assert "Canon 5D Mark IV style" in task["prompt"]


# -- Validation tests --


def test_validation_catches_misspelled_placeholder():
    """load_template() on bad_placeholder.txt raises TemplateValidationError naming the bad key and file (TMPL-03)."""
    with pytest.raises(TemplateValidationError) as exc_info:
        load_template(FIXTURES / "bad_placeholder.txt")
    error_msg = str(exc_info.value)
    assert "age_group" in error_msg
    assert "bad_placeholder" in error_msg


def test_validation_catches_missing_required_placeholder(tmp_path):
    """A template missing {gender} raises TemplateValidationError mentioning 'gender'."""
    missing_gender = tmp_path / "no_gender.txt"
    missing_gender.write_text(
        "## name: No Gender\n\nA {ethnicity} student, {age}, in a classroom.\n",
        encoding="utf-8",
    )
    with pytest.raises(TemplateValidationError) as exc_info:
        load_template(missing_gender)
    assert "gender" in str(exc_info.value)


# -- Collection tests --


def test_collection_file_loads_multiple_scenes():
    """load_collection() returns list of 2 TemplateFile objects with distinct names (TMPL-05)."""
    scenes = load_collection(FIXTURES / "collection_template.txt")
    assert len(scenes) == 2
    names = [s.name for s in scenes]
    assert names[0] != names[1]
    assert all(isinstance(s, TemplateFile) for s in scenes)


def test_collection_scenes_expand_independently(tmp_path):
    """Each scene in a collection file produces its own set of task dicts across the full demographic matrix."""
    scenes = load_collection(FIXTURES / "collection_template.txt")
    # 2 scenes x 2 ethnicities x 1 age x 2 genders = 8 tasks
    tasks = expand_to_tasks(scenes, SAMPLE_ETHNICITIES, SAMPLE_AGES, SAMPLE_GENDERS, tmp_path)
    assert len(tasks) == 8


# -- expand_to_tasks tests --


def test_expand_to_tasks_produces_correct_count(tmp_path):
    """expand_to_tasks() with 2 ethnicities x 1 age x 2 genders = 4 task dicts per template (TMPL-01)."""
    tmpl = load_template(FIXTURES / "valid_template.txt")
    tasks = expand_to_tasks(
        [tmpl],
        SAMPLE_ETHNICITIES,
        SAMPLE_AGES,
        SAMPLE_GENDERS,
        tmp_path,
        count=1,
    )
    assert len(tasks) == 4  # 2 ethnicities x 1 age x 2 genders


def test_expand_to_tasks_dict_shape(tmp_path):
    """Each task dict has exactly 'prompt' (str) and 'output_path' (Path) keys."""
    tmpl = load_template(FIXTURES / "valid_template.txt")
    tasks = expand_to_tasks([tmpl], SAMPLE_ETHNICITIES, SAMPLE_AGES, SAMPLE_GENDERS, tmp_path)
    for task in tasks:
        assert set(task.keys()) == {"prompt", "output_path"}
        assert isinstance(task["prompt"], str)
        assert isinstance(task["output_path"], pathlib.Path)


def test_expand_to_tasks_output_path_includes_template_slug(tmp_path):
    """output_path contains the template slug derived from filename."""
    tmpl = load_template(FIXTURES / "valid_template.txt")
    tasks = expand_to_tasks([tmpl], SAMPLE_ETHNICITIES, SAMPLE_AGES, SAMPLE_GENDERS, tmp_path)
    for task in tasks:
        # slug from filename "valid_template" should appear somewhere in path
        path_str = str(task["output_path"])
        assert "valid_template" in path_str


def test_expand_to_tasks_with_count(tmp_path):
    """expand_to_tasks() with count=2 produces 2x tasks, with _001.png and _002.png suffixes."""
    tmpl = load_template(FIXTURES / "valid_template.txt")
    tasks = expand_to_tasks(
        [tmpl],
        SAMPLE_ETHNICITIES,
        SAMPLE_AGES,
        SAMPLE_GENDERS,
        tmp_path,
        count=2,
    )
    # 2 ethnicities x 1 age x 2 genders x 2 count = 8 tasks
    assert len(tasks) == 8
    filenames = [task["output_path"].name for task in tasks]
    assert any("_001.png" in f for f in filenames)
    assert any("_002.png" in f for f in filenames)


def test_expand_to_tasks_path_order_age_ethnicity_first(tmp_path):
    """output_path has age slug before ethnicity slug, and both before template slug."""
    tmpl = load_template(FIXTURES / "valid_template.txt")
    tasks = expand_to_tasks(
        [tmpl],
        SAMPLE_ETHNICITIES,
        SAMPLE_AGES,
        SAMPLE_GENDERS,
        tmp_path,
        count=1,
    )
    for task in tasks:
        parts = task["output_path"].parts
        # template slug, age slug, and ethnicity slug must all appear in path parts
        assert tmpl.slug in parts, f"Template slug '{tmpl.slug}' not in path parts: {parts}"
        # Find indices of each component
        slug_idx = parts.index(tmpl.slug)
        # There must be at least 2 parts before the slug (age and ethnicity)
        assert slug_idx >= 2, (
            f"Expected slug at index >= 2 (age and ethnicity before it), got index {slug_idx}"
        )
        age_slug = parts[slug_idx - 2]
        ethnicity_slug = parts[slug_idx - 1]
        # age slug should contain something from the age key (slugified "High School (14-17)")
        assert "high-school" in age_slug, f"Age slug '{age_slug}' missing 'high-school'"
        # ethnicity slug should correspond to one of the sample ethnicities
        assert age_slug != tmpl.slug, "Age and template slug must differ"
        assert ethnicity_slug != tmpl.slug, "Ethnicity and template slug must differ"
        # Age must come before ethnicity in path (index check)
        eth_idx_in_parts = slug_idx - 1
        age_idx_in_parts = slug_idx - 2
        assert age_idx_in_parts < eth_idx_in_parts < slug_idx, (
            f"Expected order: age({age_idx_in_parts}) < ethnicity({eth_idx_in_parts}) < slug({slug_idx})"
        )
