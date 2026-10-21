"""Which command line options trigger which operations.

The dispatch used to call three methods that no longer existed
(async_find_existing_content, async_delete_icon_settings,
async_find_and_apply_matches), so --content failed with an AttributeError.
A spec'd double catches that: a call to a method IconsAppService does not
have raises here.
"""

from unittest.mock import Mock

import pytest

from icon_manager.__main__ import get_namespace_from_args, run
from icon_manager.services.app_service import IconsAppService


def called(service: Mock) -> list[str]:
    """The service methods ``run`` invoked, in order."""
    return [name for name, _, _ in service.mock_calls]


@pytest.fixture
def service() -> Mock:
    return Mock(spec=IconsAppService)


def dispatch(service: Mock, *argv: str) -> list[str]:
    run(service, get_namespace_from_args(list(argv)))
    return called(service)


class TestAlwaysDoneFirst:
    def test_the_library_is_read_before_any_option(self, service: Mock):
        calls = dispatch(service, "--library", "--create")

        assert calls[:2] == ["setup", "create_settings"]

    def test_without_a_scope_nothing_but_the_setup_runs(self, service: Mock):
        assert dispatch(service) == ["setup", "create_settings"]


class TestLibraryOptions:
    @pytest.mark.parametrize(
        ("option", "expected"),
        [
            ("--create", "create_library_configs"),
            ("--update", "update_library_configs"),
            ("--delete", "delete_library_configs"),
            ("--archive", "archive_icons_and_configs"),
        ],
    )
    def test_each_option_runs_its_operation(self, service: Mock, option: str, expected: str):
        assert dispatch(service, "--library", option)[2:] == [expected]

    def test_create_and_update_both_run(self, service: Mock):
        # --create used to be unreachable whenever --update was given
        calls = dispatch(service, "--library", "--create", "--update")

        assert calls[2:] == ["create_library_configs", "update_library_configs"]

    def test_content_operations_are_not_touched(self, service: Mock):
        calls = dispatch(service, "--library", "--create")

        assert "find_and_apply_matches" not in calls
        assert "setup_and_merge_user_service" not in calls


class TestContentOptions:
    def test_create_applies_the_matches(self, service: Mock):
        calls = dispatch(service, "--content", "--create")

        assert calls[2:] == ["setup_and_merge_user_service", "find_and_apply_matches"]

    def test_delete_catalogs_the_existing_content_first(self, service: Mock):
        calls = dispatch(service, "--content", "--delete")

        assert calls[2:] == [
            "setup_and_merge_user_service",
            "find_existing_content",
            "delete_icon_settings",
        ]

    def test_re_create_catalogs_the_existing_content_first(self, service: Mock):
        calls = dispatch(service, "--content", "--re-create")

        assert calls[2:] == [
            "setup_and_merge_user_service",
            "find_existing_content",
            "re_apply_matched_icons",
        ]

    def test_the_existing_content_is_only_catalogued_once(self, service: Mock):
        calls = dispatch(service, "--content", "--delete", "--re-create")

        assert calls.count("find_existing_content") == 1

    def test_library_operations_are_not_touched(self, service: Mock):
        calls = dispatch(service, "--content", "--delete")

        assert "delete_library_configs" not in calls


class TestScopesAreExclusive:
    def test_library_wins_when_both_are_given(self, service: Mock):
        calls = dispatch(service, "--library", "--content", "--create")

        assert calls[2:] == ["create_library_configs"]


class TestShortOptions:
    @pytest.mark.parametrize(
        ("argv", "expected"),
        [
            (("-l", "-a"), "create_library_configs"),
            (("-l", "-u"), "update_library_configs"),
            (("-l", "-v"), "archive_icons_and_configs"),
            (("-c", "-a"), "find_and_apply_matches"),
            (("-c", "-r"), "re_apply_matched_icons"),
        ],
    )
    def test_the_short_form_dispatches_like_the_long_one(self, service: Mock, argv, expected: str):
        assert expected in dispatch(service, *argv)
