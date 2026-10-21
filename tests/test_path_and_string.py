from pathlib import Path

import pytest

from icon_manager.helpers.string import (
    ALIGN_CENTRE,
    ALIGN_LEFT,
    ALIGN_RIGHT,
    FILL_HYPHEN,
    FILL_SPACE,
    fixed_length,
    list_value,
    prefix_value,
)
from icon_manager.interfaces.path import get_files, is_file


class TestPathHelpers:
    """is_file/get_files against a real directory instead of a patched os."""

    @pytest.fixture
    def folder(self, tmp_path: Path) -> Path:
        (tmp_path / "first.txt").touch()
        (tmp_path / "second.pdf").touch()
        (tmp_path / "third.txt").touch()
        (tmp_path / "subfolder").mkdir()
        return tmp_path

    def test_is_file_accepts_an_existing_file(self, folder: Path):
        assert is_file(str(folder), "first.txt") is True

    def test_is_file_rejects_a_missing_name(self, folder: Path):
        assert is_file(str(folder), "nope.txt") is False

    def test_is_file_rejects_a_directory(self, folder: Path):
        assert is_file(str(folder), "subfolder") is False

    def test_is_file_checks_the_extension(self, folder: Path):
        assert is_file(str(folder), "first.txt", ".txt") is True
        assert is_file(str(folder), "first.txt", ".pdf") is False

    def test_is_file_accepts_an_extension_without_a_dot(self, folder: Path):
        assert is_file(str(folder), "first.txt", "txt") is True

    def test_get_files_returns_every_file_without_a_filter(self, folder: Path):
        assert sorted(get_files(str(folder))) == ["first.txt", "second.pdf", "third.txt"]

    def test_get_files_filters_by_extension(self, folder: Path):
        assert sorted(get_files(str(folder), ".txt")) == ["first.txt", "third.txt"]

    def test_get_files_leaves_out_directories(self, folder: Path):
        assert "subfolder" not in get_files(str(folder))


class TestStringHelpers:
    def test_fixed_length_formats_string_with_defaults(self):
        result = fixed_length("test", 10)
        assert result == "test      "

    def test_fixed_length_formats_string_with_custom_fill(self):
        result = fixed_length("test", 10, FILL_HYPHEN)
        assert result == "test------"

    def test_fixed_length_formats_string_with_right_align(self):
        result = fixed_length("test", 10, FILL_SPACE, ALIGN_RIGHT)
        assert result == "      test"

    def test_fixed_length_formats_string_with_center_align(self):
        result = fixed_length("test", 10, FILL_SPACE, ALIGN_CENTRE)
        assert result == "   test   "

    def test_prefix_value_uses_default_width(self):
        result = prefix_value("test")
        assert len(result) == 15
        assert result.startswith("test")

    def test_prefix_value_uses_custom_width(self):
        result = prefix_value("test", 8)
        assert len(result) == 8
        assert result == "test    "

    def test_prefix_value_uses_custom_alignment(self):
        result = prefix_value("test", 8, ALIGN_RIGHT)
        assert result == "    test"

    def test_list_value_formats_list_length(self):
        values = ["a", "b", "c"]
        result = list_value(values)
        assert "3" in result
        assert len(result) == 4

    def test_list_value_uses_custom_width(self):
        values = ["a", "b", "c"]
        result = list_value(values, 6)
        assert len(result) == 6
        assert result == "     3"

    def test_list_value_uses_custom_alignment(self):
        values = ["a", "b", "c"]
        result = list_value(values, 6, ALIGN_LEFT)
        assert result == "3     "
