"""Tests for demographics constants module."""

from demographics import AGE_GROUPS, ETHNICITIES, GENDERS


def test_genders_constant():
    """GENDERS constant contains exactly ['male', 'female']."""
    assert GENDERS == ["male", "female"]


def test_ethnicities_preserved():
    """ETHNICITIES matches the exact 8-item list from generate.py lines 24-33."""
    expected = [
        "East Asian",
        "South Asian",
        "Black / African American",
        "Hispanic / Latino",
        "White / Caucasian",
        "Middle Eastern",
        "Southeast Asian",
        "Pacific Islander",
    ]
    assert ETHNICITIES == expected


def test_age_groups_preserved():
    """AGE_GROUPS matches the exact 4-entry dict from generate.py lines 35-40."""
    expected = {
        "Elementary (6-10)": "young elementary school age (6-10 years old)",
        "Middle School (11-13)": "middle school age (11-13 years old)",
        "High School (14-17)": "high school age (14-17 years old)",
        "College (18-22)": "college age (18-22 years old)",
    }
    assert AGE_GROUPS == expected


def test_age_groups_values_are_descriptive():
    """Every value in AGE_GROUPS contains 'years old' (the descriptive form used in prompts)."""
    for key, value in AGE_GROUPS.items():
        assert "years old" in value, f"AGE_GROUPS[{key!r}] value {value!r} does not contain 'years old'"


def test_all_constants_are_lists_or_dicts():
    """ETHNICITIES and GENDERS are lists, AGE_GROUPS is a dict."""
    assert isinstance(ETHNICITIES, list)
    assert isinstance(GENDERS, list)
    assert isinstance(AGE_GROUPS, dict)
