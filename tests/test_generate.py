"""Unit tests for generate.py core functions — template-based generation pipeline.

Tests cover:
  GEN-01: Task count (templates x ethnicities x ages x genders)
  GEN-04: Output paths include template slug (no cross-template overwrites)
  DEMO-03: Demographic restrictions (restrict_ages, restrict_genders metadata)
  GEN-03: Cost breakdown and 50-image gate
  GEN-06: Error classification and failure report
  GEN-02: Dry-run table output (no API calls)
  GEN-05: Preview loop (approve/skip/abort per template)
"""
import io
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, call, patch

import pytest

from template_engine import TemplateFile, expand_to_tasks

# Functions under test — these don't exist yet in generate.py (RED phase)
from generate import (
    apply_demographic_restrictions,
    classify_failure,
    print_dry_run_table,
    print_failure_report,
    run_template_preview_loop,
    show_cost_confirmation,
)


# -- Fixtures -----------------------------------------------------------------


def make_template(slug, body=None, metadata=None, name=None):
    """Create a TemplateFile fixture with minimal required fields."""
    if body is None:
        body = "A {ethnicity} {gender} student, {age}, in a classroom."
    if metadata is None:
        metadata = {}
    if name is None:
        name = slug.replace("-", " ").title()
    return TemplateFile(name=name, slug=slug, body=body, metadata=metadata, source_path=None)


ETHNICITIES_2 = ["East Asian", "South Asian"]
AGES_2 = {
    "Elementary (6-10)": "young elementary school age (6-10 years old)",
    "College (18-22)": "college age (18-22 years old)",
}
GENDERS_2 = ["male", "female"]

ALL_AGES = {
    "Elementary (6-10)": "young elementary school age (6-10 years old)",
    "Middle School (11-13)": "middle school age (11-13 years old)",
    "High School (14-17)": "high school age (14-17 years old)",
    "College (18-22)": "college age (18-22 years old)",
}
ALL_GENDERS = ["male", "female"]
ALL_ETHNICITIES = [
    "East Asian",
    "South Asian",
    "Black / African American",
    "Hispanic / Latino",
    "White / Caucasian",
    "Middle Eastern",
    "Southeast Asian",
    "Pacific Islander",
]


# -- GEN-01: Task count -------------------------------------------------------


def test_gen01_task_count(tmp_path):
    """2 templates x 2 ethnicities x 2 ages x 2 genders = 16 tasks."""
    tmpl_a = make_template("scene-a")
    tmpl_b = make_template("scene-b")

    tasks = expand_to_tasks(
        [tmpl_a, tmpl_b],
        ETHNICITIES_2,
        AGES_2,
        GENDERS_2,
        tmp_path,
    )

    assert len(tasks) == 16, f"Expected 16 tasks, got {len(tasks)}"


# -- GEN-04: Output paths include slug ----------------------------------------


def test_gen04_output_paths_include_slug(tmp_path):
    """Two templates with same demographics produce paths containing different slugs."""
    tmpl_a = make_template("stem-lab")
    tmpl_b = make_template("portrait")

    tasks_a = expand_to_tasks([tmpl_a], ETHNICITIES_2, AGES_2, GENDERS_2, tmp_path)
    tasks_b = expand_to_tasks([tmpl_b], ETHNICITIES_2, AGES_2, GENDERS_2, tmp_path)

    paths_a = {str(t["output_path"]) for t in tasks_a}
    paths_b = {str(t["output_path"]) for t in tasks_b}

    # Each path from template A must contain "stem-lab"
    assert all("stem-lab" in p for p in paths_a), "stem-lab slug missing from paths"
    # Each path from template B must contain "portrait"
    assert all("portrait" in p for p in paths_b), "portrait slug missing from paths"
    # No overlap between the two sets
    assert paths_a.isdisjoint(paths_b), "Cross-template path collision detected"


# -- DEMO-03: Demographic restrictions ----------------------------------------


def test_demo03_restrict_ages():
    """Template with restrict_ages='College (18-22)' filters ages to only College entry."""
    tmpl = make_template("college-only", metadata={"restrict_ages": "College (18-22)"})

    _, filtered_ages, _ = apply_demographic_restrictions(tmpl, ALL_ETHNICITIES, ALL_AGES, ALL_GENDERS)

    assert list(filtered_ages.keys()) == ["College (18-22)"], (
        f"Expected only College (18-22), got {list(filtered_ages.keys())}"
    )


def test_demo03_restrict_ages_case_insensitive():
    """Case-insensitive matching: 'college (18-22)' matches 'College (18-22)' key."""
    tmpl = make_template("college-only", metadata={"restrict_ages": "college (18-22)"})

    _, filtered_ages, _ = apply_demographic_restrictions(tmpl, ALL_ETHNICITIES, ALL_AGES, ALL_GENDERS)

    assert list(filtered_ages.keys()) == ["College (18-22)"], (
        f"Expected case-insensitive match; got {list(filtered_ages.keys())}"
    )


def test_demo03_restrict_genders():
    """Template with restrict_genders='female' filters genders to ['female'] only."""
    tmpl = make_template("female-only", metadata={"restrict_genders": "female"})

    _, _, filtered_genders = apply_demographic_restrictions(
        tmpl, ALL_ETHNICITIES, ALL_AGES, ALL_GENDERS
    )

    assert filtered_genders == ["female"], f"Expected ['female'], got {filtered_genders}"


def test_demo03_no_restrictions():
    """Template without restrict metadata returns all demographics unchanged."""
    tmpl = make_template("no-restrictions", metadata={})

    returned_ethnicities, returned_ages, returned_genders = apply_demographic_restrictions(
        tmpl, ALL_ETHNICITIES, ALL_AGES, ALL_GENDERS
    )

    assert returned_ethnicities == ALL_ETHNICITIES
    assert returned_ages == ALL_AGES
    assert returned_genders == ALL_GENDERS


# -- GEN-03: Cost breakdown and 50-image gate ---------------------------------


def test_gen03_cost_breakdown(capsys):
    """show_cost_confirmation prints per-template lines with count x cost math."""
    template_task_counts = [
        ("STEM Lab Scene", 8),
        ("Portrait", 4),
    ]
    cost_per_image = 0.04

    # requires_confirm=False to avoid blocking on questionary.confirm
    show_cost_confirmation(template_task_counts, cost_per_image, requires_confirm=False)

    captured = capsys.readouterr()
    output = captured.out

    # Should show per-template lines
    assert "STEM Lab Scene" in output, "Template name missing from output"
    assert "Portrait" in output, "Template name missing from output"
    # Should show cost calculations
    assert "0.04" in output or "$0.04" in output, "Cost per image missing"
    # Should show total
    assert "12" in output, "Total image count (12) missing from output"


def test_gen03_fifty_image_gate():
    """show_cost_confirmation triggers questionary.confirm when total > 50."""
    template_task_counts = [("Big Batch", 60)]
    cost_per_image = 0.04

    with patch("generate.questionary") as mock_q:
        mock_confirm = MagicMock()
        mock_confirm.ask.return_value = True
        mock_q.confirm.return_value = mock_confirm

        show_cost_confirmation(template_task_counts, cost_per_image, requires_confirm=True)

        # questionary.confirm should have been called (50-image gate)
        mock_q.confirm.assert_called_once()


# -- GEN-06: Error classification and failure report --------------------------


def test_gen06_classify_policy_openai():
    """classify_failure returns 'policy' for errors containing 'content_policy_violation'."""
    failure = {
        "path": "output/scene/image.png",
        "error": '{"code": "content_policy_violation", "message": "rejected by safety system"}',
    }
    assert classify_failure(failure) == "policy"


def test_gen06_classify_network():
    """classify_failure returns 'network' for generic HTTP/connection errors."""
    failure = {
        "path": "output/scene/image.png",
        "error": "Connection timeout after 30s",
    }
    assert classify_failure(failure) == "network"


def test_gen06_classify_stability_nsfw():
    """classify_failure returns 'policy' for Stability AI NSFW errors."""
    failure = {
        "path": "output/scene/image.png",
        "error": "NSFW content detected in generated image",
    }
    assert classify_failure(failure) == "policy"


def test_gen06_failure_report(capsys):
    """print_failure_report outputs policy failures with prompt text and network with error."""
    policy_failure = {
        "path": "output/stem-lab/image.png",
        "error": "content_policy_violation: your request was rejected",
    }
    network_failure = {
        "path": "output/portrait/image.png",
        "error": "HTTP 503 Service Unavailable",
    }
    failed = [policy_failure, network_failure]

    tasks_by_path = {
        "output/stem-lab/image.png": "A East Asian female student in a STEM lab.",
        "output/portrait/image.png": "A South Asian male student in a portrait setting.",
    }

    print_failure_report(failed, tasks_by_path)

    captured = capsys.readouterr()
    output = captured.out

    # Policy failure: should show the prompt text
    assert "East Asian female" in output or "stem-lab" in output.lower(), (
        "Policy failure prompt text missing from report"
    )
    # Network failure: should show error text
    assert "503" in output or "portrait" in output.lower(), (
        "Network failure error text missing from report"
    )


# -- GEN-02: Dry-run table output ---------------------------------------------


def test_gen02_dry_run_no_api_calls(capsys):
    """print_dry_run_table prints tabulated table with Template/Combo/Prompt columns and total."""
    tasks_by_template = {
        "stem-lab": [
            {"combo_label": "East Asian / College / female", "prompt": "A East Asian female student in a STEM lab."},
            {"combo_label": "South Asian / College / male", "prompt": "A South Asian male student in a STEM lab."},
        ],
        "portrait": [
            {"combo_label": "East Asian / College / female", "prompt": "A East Asian female student in a portrait setting."},
        ],
    }

    # This should NOT call generate_batch — no mock needed, just call the function
    print_dry_run_table(tasks_by_template)

    captured = capsys.readouterr()
    output = captured.out

    # Headers present
    assert "Template" in output, "Missing 'Template' column header"
    assert "Combo" in output, "Missing 'Combo' column header"
    assert "Prompt" in output, "Missing 'Prompt' column header"

    # Template slugs present
    assert "stem-lab" in output, "Missing 'stem-lab' template slug"
    assert "portrait" in output, "Missing 'portrait' template slug"

    # Combo labels present
    assert "East Asian" in output, "Missing combo label content"

    # Total count present
    assert "3" in output, "Missing total count (3 prompts)"


def test_gen02_dry_run_length_warning(capsys):
    """print_dry_run_table flags prompts > 3800 chars with a warning marker."""
    long_prompt = "A " + "x" * 3900  # well over 3800 chars
    short_prompt = "A short prompt."

    tasks_by_template = {
        "scene-a": [
            {"combo_label": "East Asian / College / female", "prompt": long_prompt},
            {"combo_label": "South Asian / College / male", "prompt": short_prompt},
        ],
    }

    print_dry_run_table(tasks_by_template)

    captured = capsys.readouterr()
    output = captured.out

    # A warning marker should appear for the long prompt
    assert "[!]" in output or "WARNING" in output or "LENGTH" in output, (
        "Missing length warning marker for prompt > 3800 chars"
    )


# -- GEN-05: Preview loop -----------------------------------------------------


def test_gen05_preview_approves_subset(tmp_path):
    """run_template_preview_loop with 3 templates: approve first, skip second, approve third — returns [first, third]."""
    tmpl_a = make_template("scene-a")
    tmpl_b = make_template("scene-b")
    tmpl_c = make_template("scene-c")

    demographics = {
        "ethnicities": ["East Asian"],
        "ages": {"College (18-22)": "college age (18-22 years old)"},
        "genders": ["female"],
    }

    with patch("generate.asyncio") as mock_asyncio, \
         patch("generate.questionary") as mock_q, \
         patch("generate.expand_to_tasks") as mock_expand:

        # expand_to_tasks returns a single task for each call
        mock_expand.return_value = [{"prompt": "test", "output_path": tmp_path / "test.png"}]
        # asyncio.run is a no-op
        mock_asyncio.run.return_value = 0

        # questionary.select returns approve/skip/approve in sequence
        mock_select_a = MagicMock()
        mock_select_a.ask.return_value = "Approve — include in full batch"
        mock_select_b = MagicMock()
        mock_select_b.ask.return_value = "Skip — exclude this template"
        mock_select_c = MagicMock()
        mock_select_c.ask.return_value = "Approve — include in full batch"
        mock_q.select.side_effect = [mock_select_a, mock_select_b, mock_select_c]

        approved = run_template_preview_loop(
            provider_name="OpenAI GPT Image",
            api_key="test-key",
            templates=[tmpl_a, tmpl_b, tmpl_c],
            demographics=demographics,
            output_dir=tmp_path,
            size_value="1024x1024",
        )

    assert len(approved) == 2, f"Expected 2 approved templates, got {len(approved)}"
    assert tmpl_a in approved, "scene-a should be approved"
    assert tmpl_b not in approved, "scene-b should be skipped"
    assert tmpl_c in approved, "scene-c should be approved"


def test_gen05_preview_abort(tmp_path):
    """run_template_preview_loop aborts on first template — calls sys.exit."""
    tmpl_a = make_template("scene-a")
    tmpl_b = make_template("scene-b")

    demographics = {
        "ethnicities": ["East Asian"],
        "ages": {"College (18-22)": "college age (18-22 years old)"},
        "genders": ["female"],
    }

    with patch("generate.asyncio") as mock_asyncio, \
         patch("generate.questionary") as mock_q, \
         patch("generate.expand_to_tasks") as mock_expand:

        mock_expand.return_value = [{"prompt": "test", "output_path": tmp_path / "test.png"}]
        mock_asyncio.run.return_value = 0

        mock_select = MagicMock()
        mock_select.ask.return_value = "Abort — cancel everything"
        mock_q.select.return_value = mock_select

        with pytest.raises(SystemExit):
            run_template_preview_loop(
                provider_name="OpenAI GPT Image",
                api_key="test-key",
                templates=[tmpl_a, tmpl_b],
                demographics=demographics,
                output_dir=tmp_path,
                size_value="1024x1024",
            )


def test_gen05_preview_generates_one_per_template(tmp_path):
    """run_template_preview_loop calls generate_batch exactly once per template with 1 task each."""
    tmpl_a = make_template("scene-a")
    tmpl_b = make_template("scene-b")

    demographics = {
        "ethnicities": ["East Asian"],
        "ages": {"College (18-22)": "college age (18-22 years old)"},
        "genders": ["female"],
    }

    with patch("generate.asyncio") as mock_asyncio, \
         patch("generate.questionary") as mock_q, \
         patch("generate.expand_to_tasks") as mock_expand, \
         patch("generate.generate_batch") as mock_gen_batch:

        # expand_to_tasks returns exactly 1 task per call
        mock_expand.return_value = [{"prompt": "test prompt", "output_path": tmp_path / "test.png"}]
        mock_asyncio.run.return_value = 0

        mock_select = MagicMock()
        mock_select.ask.return_value = "Approve — include in full batch"
        mock_q.select.return_value = mock_select

        run_template_preview_loop(
            provider_name="OpenAI GPT Image",
            api_key="test-key",
            templates=[tmpl_a, tmpl_b],
            demographics=demographics,
            output_dir=tmp_path,
            size_value="1024x1024",
        )

    # asyncio.run should be called exactly twice (once per template)
    assert mock_asyncio.run.call_count == 2, (
        f"Expected asyncio.run called 2 times, got {mock_asyncio.run.call_count}"
    )
    # Each call to expand_to_tasks should only produce 1 task
    # (already enforced by mock_expand.return_value = [single task])
    assert mock_expand.call_count == 2, (
        f"Expected expand_to_tasks called 2 times (once per template), got {mock_expand.call_count}"
    )
