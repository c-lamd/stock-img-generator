"""Unit tests for templates.py CLI — create wizard and list command.

Tests cover:
  TMPL-04: Wizard writes valid .txt files that load_template() accepts
  TMPL-06: List command shows name, scene preview, and demographic restrictions
  SC-3: Wizard-produced files validated via post-write load_template() call
"""
from io import StringIO
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from template_engine import load_template
from templates import cmd_create, cmd_list, validate_body


# -- Helpers ------------------------------------------------------------------


def _make_questionary_mock(
    name="Test Scene",
    description="A test",
    tags="test",
    restrict_ages=None,
    restrict_genders=None,
    body="A {ethnicity} {gender} student, {age}.",
    confirm_write=True,
    overwrite=None,
):
    """Return a mock questionary module whose .text/.confirm/.checkbox calls
    return the provided values in cmd_create's call sequence:

    1. text("Template name:")               -> name
    2. [optional] confirm("overwrite?")     -> overwrite (only if file exists)
    3. text("Scene description ...")        -> description
    4. text("Tags ...")                     -> tags
    5. checkbox("Restrict to age groups?")  -> restrict_ages list
    6. checkbox("Restrict to genders?")     -> restrict_genders list
    7. text("Scene body ...")               -> body
    8. confirm("Write to ...?")             -> confirm_write
    """
    if restrict_ages is None:
        restrict_ages = []
    if restrict_genders is None:
        restrict_genders = []

    mock_q = MagicMock()

    # text() calls return a prompt object whose .ask() returns the value
    def _text_side_effect(prompt, **kwargs):
        obj = MagicMock()
        if "name" in prompt.lower() and "template" in prompt.lower():
            obj.ask.return_value = name
        elif "description" in prompt.lower():
            obj.ask.return_value = description
        elif "tags" in prompt.lower():
            obj.ask.return_value = tags
        elif "body" in prompt.lower():
            obj.ask.return_value = body
        else:
            obj.ask.return_value = ""
        return obj

    mock_q.text.side_effect = _text_side_effect

    # checkbox() calls
    checkbox_calls = [restrict_ages, restrict_genders]
    checkbox_iter = iter(checkbox_calls)

    def _checkbox_side_effect(prompt, **kwargs):
        obj = MagicMock()
        obj.ask.return_value = next(checkbox_iter)
        return obj

    mock_q.checkbox.side_effect = _checkbox_side_effect

    # confirm() calls — order: maybe overwrite confirm, then write confirm
    confirm_queue = []
    if overwrite is not None:
        confirm_queue.append(overwrite)
    confirm_queue.append(confirm_write)
    confirm_iter = iter(confirm_queue)

    def _confirm_side_effect(prompt, **kwargs):
        obj = MagicMock()
        obj.ask.return_value = next(confirm_iter)
        return obj

    mock_q.confirm.side_effect = _confirm_side_effect

    return mock_q


# -- validate_body tests ------------------------------------------------------


def test_validate_body_valid():
    result = validate_body("A {ethnicity} {gender}, {age}")
    assert result is True


def test_validate_body_missing_placeholder():
    result = validate_body("A {ethnicity} {gender}")
    assert isinstance(result, str)
    assert "Missing required placeholders" in result
    assert "age" in result


def test_validate_body_unknown_placeholder():
    result = validate_body("A {ethnicity} {gender} {age} {mood}")
    assert isinstance(result, str)
    assert "Unknown placeholders" in result
    assert "mood" in result


def test_validate_body_empty():
    result = validate_body("  ")
    assert isinstance(result, str)
    assert "Body cannot be empty" in result


# -- cmd_create tests (TMPL-04) -----------------------------------------------


def test_tmpl04_wizard_writes_valid_file(tmp_path):
    """Wizard writes a .txt file that load_template() accepts."""
    mock_q = _make_questionary_mock(
        name="Test Scene",
        description="A test",
        tags="test",
        restrict_ages=[],
        restrict_genders=[],
        body="A {ethnicity} {gender} student, {age}.",
        confirm_write=True,
    )
    with patch("templates.questionary", mock_q):
        cmd_create(templates_dir=tmp_path)

    file_path = tmp_path / "test-scene.txt"
    assert file_path.exists(), "Expected test-scene.txt to be created"
    content = file_path.read_text(encoding="utf-8")
    assert "## name: Test Scene" in content
    # load_template must succeed without raising
    tmpl = load_template(file_path)
    assert tmpl.name == "Test Scene"


def test_tmpl04_wizard_validates_body_before_write():
    """validate_body rejects body missing {age} placeholder before file write."""
    # Test validate_body directly — it prevents bad input before write
    result = validate_body("A {ethnicity} {gender} student.")
    assert isinstance(result, str)
    assert "age" in result


def test_tmpl04_wizard_collision_abort(tmp_path):
    """When file exists and user declines overwrite, original file is unchanged."""
    file_path = tmp_path / "test-scene.txt"
    original_content = "original content"
    file_path.write_text(original_content, encoding="utf-8")

    mock_q = _make_questionary_mock(
        name="Test Scene",
        overwrite=False,  # triggers collision path
    )
    with patch("templates.questionary", mock_q):
        with pytest.raises(SystemExit):
            cmd_create(templates_dir=tmp_path)

    assert file_path.read_text(encoding="utf-8") == original_content


# -- cmd_list tests (TMPL-06) -------------------------------------------------


def test_tmpl06_list_shows_all_templates(tmp_path, capsys):
    """List command shows all template names."""
    (tmp_path / "alpha.txt").write_text(
        "## name: Alpha Scene\n\nA {ethnicity} {gender} student, {age}.\n",
        encoding="utf-8",
    )
    (tmp_path / "beta.txt").write_text(
        "## name: Beta Scene\n\nA {ethnicity} {gender} learner, {age}.\n",
        encoding="utf-8",
    )
    cmd_list(templates_dir=tmp_path)
    out = capsys.readouterr().out
    assert "Alpha Scene" in out
    assert "Beta Scene" in out


def test_tmpl06_list_shows_restrictions(tmp_path, capsys):
    """List command shows age restriction in output."""
    (tmp_path / "restricted.txt").write_text(
        "## name: Restricted Scene\n"
        "## restrict_ages: College (18-22)\n\n"
        "A {ethnicity} {gender} student, {age}.\n",
        encoding="utf-8",
    )
    cmd_list(templates_dir=tmp_path)
    out = capsys.readouterr().out
    assert "College" in out


def test_tmpl06_list_empty_dir(tmp_path, capsys):
    """List command reports no templates when directory is empty."""
    cmd_list(templates_dir=tmp_path)
    out = capsys.readouterr().out
    assert "No templates found" in out


# -- SC-3: Wizard-produced file loads clean -----------------------------------


def test_sc3_written_file_loads_clean(tmp_path):
    """Full wizard flow with demographic restrictions writes a file that loads cleanly."""
    mock_q = _make_questionary_mock(
        name="Science Lab",
        description="Students in a science lab",
        tags="stem, lab",
        restrict_ages=["College (18-22)"],
        restrict_genders=["female"],
        body="A {ethnicity} {gender} student, {age}, in a science lab.",
        confirm_write=True,
    )
    with patch("templates.questionary", mock_q):
        cmd_create(templates_dir=tmp_path)

    file_path = tmp_path / "science-lab.txt"
    assert file_path.exists()
    tmpl = load_template(file_path)
    assert tmpl.name == "Science Lab"
    assert "{ethnicity}" in tmpl.body
    assert "{gender}" in tmpl.body
    assert "{age}" in tmpl.body
    assert tmpl.metadata.get("restrict_ages") == "College (18-22)"
