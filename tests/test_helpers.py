from unittest.mock import Mock, patch

from icon_manager.helpers.path import (
    count_of,
    count_of_recursive,
    get_files,
    get_path,
    get_paths,
    is_file,
    is_file_extensions,
    total_count,
)
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
from icon_manager.interfaces.path import File, Folder


class TestPathHelpers:
    def test_get_path_joins_path_and_name(self):
        result = get_path("/test/path", "file.txt")
        assert result == "/test/path/file.txt"

    def test_get_paths_returns_list_of_joined_paths(self):
        names = ["file1.txt", "file2.txt", "file3.txt"]
        result = get_paths("/test/path", names)
        expected = [
            "/test/path/file1.txt",
            "/test/path/file2.txt",
            "/test/path/file3.txt",
        ]
        assert result == expected

    def test_is_file_returns_true_for_existing_file(self):
        with patch("os.path.isfile") as mock_isfile:
            mock_isfile.return_value = True

            result = is_file("/test/path", "file.txt")

            assert result is True
            mock_isfile.assert_called_once_with("/test/path/file.txt")

    def test_is_file_returns_false_for_non_existing_file(self):
        with patch("os.path.isfile") as mock_isfile:
            mock_isfile.return_value = False

            result = is_file("/test/path", "file.txt")

            assert result is False

    def test_is_file_checks_extension_when_provided(self):
        with patch("os.path.isfile") as mock_isfile:
            mock_isfile.return_value = True

            result = is_file("/test/path", "file.txt", ".txt")

            assert result is True

    def test_is_file_returns_false_for_wrong_extension(self):
        with patch("os.path.isfile") as mock_isfile:
            mock_isfile.return_value = True

            result = is_file("/test/path", "file.txt", ".pdf")

            assert result is False

    def test_is_file_adds_dot_to_extension_if_missing(self):
        with patch("os.path.isfile") as mock_isfile:
            mock_isfile.return_value = True

            result = is_file("/test/path", "file.txt", "txt")

            assert result is True

    def test_is_file_extensions_returns_true_for_matching_extension(self):
        file = Mock(spec=File)
        file.ext = ".txt"

        result = is_file_extensions(file, [".txt", ".pdf"])

        assert result is True

    def test_is_file_extensions_returns_false_for_non_matching_extension(self):
        file = Mock(spec=File)
        file.ext = ".jpg"

        result = is_file_extensions(file, [".txt", ".pdf"])

        assert result is False

    def test_is_file_extensions_returns_false_for_none_extension(self):
        file = Mock(spec=File)
        file.ext = None

        result = is_file_extensions(file, [".txt", ".pdf"])

        assert result is False

    def test_get_files_returns_files_with_extension(self):
        with patch("os.listdir") as mock_listdir:
            mock_listdir.return_value = ["file1.txt", "file2.pdf", "file3.txt"]
            with patch("icon_manager.helpers.path.is_file") as mock_is_file:
                mock_is_file.side_effect = lambda path, name, ext: name.endswith(ext or "")

                result = get_files("/test/path", ".txt")

                assert len(result) == 2
                assert "file1.txt" in result
                assert "file3.txt" in result

    def test_count_of_returns_folder_and_file_count(self):
        folder = Mock(spec=Folder)
        folder.folders = [Mock(), Mock()]
        folder.files = [Mock(), Mock(), Mock()]

        result = count_of(folder)

        assert result == (2, 3)

    def test_count_of_recursive_returns_all_counts(self):
        subfolder = Mock(spec=Folder)
        subfolder.folders = []
        subfolder.files = [Mock()]

        folder = Mock(spec=Folder)
        folder.folders = [subfolder]
        folder.files = [Mock(), Mock()]

        result = list(count_of_recursive(folder))

        assert result == [(1, 2), (0, 1)]

    def test_total_count_sums_all_counts(self):
        folder1 = Mock(spec=Folder)
        folder1.folders = [Mock()]
        folder1.files = [Mock(), Mock()]

        folder2 = Mock(spec=Folder)
        folder2.folders = []
        folder2.files = [Mock()]

        with patch("icon_manager.helpers.path.count_of_recursive") as mock_count:
            mock_count.side_effect = [[(1, 2)], [(0, 1)]]

            result = total_count([folder1, folder2])

            assert result == (1, 3)


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
