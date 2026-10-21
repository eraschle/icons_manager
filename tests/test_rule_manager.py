from unittest.mock import Mock

import pytest

from icon_manager.interfaces.path import Folder, JsonFile
from icon_manager.rules.base import FolderAction, FolderMatcher, Operator, RuleAttribute
from icon_manager.rules.manager import (
    AttributeRuleHandler,
    ConfigRuleController,
    ExcludeManager,
    ExcludeRule,
    RuleManager,
)


class TestAttributeChecker:
    @pytest.fixture
    def mock_rule(self):
        rule = Mock(spec=FolderMatcher)
        rule.is_empty.return_value = False
        rule.is_allowed.return_value = True
        return rule

    @pytest.fixture
    def checker(self, mock_rule):
        return AttributeRuleHandler(RuleAttribute.PATH, Operator.ANY, [mock_rule])

    def test_init_creates_checker_with_params(self, mock_rule):
        checker = AttributeRuleHandler(RuleAttribute.PATH, Operator.ANY, [mock_rule])

        assert checker.attribute == RuleAttribute.PATH
        assert checker.operator == Operator.ANY
        assert checker.rules == [mock_rule]

    def test_name_returns_formatted_attribute_name(self, checker):
        assert checker.name == '"PATH" Checker'

    def test_is_empty_returns_true_when_all_rules_empty(self):
        rule1 = Mock(spec=FolderMatcher)
        rule1.is_empty.return_value = True
        rule2 = Mock(spec=FolderMatcher)
        rule2.is_empty.return_value = True

        checker = AttributeRuleHandler(RuleAttribute.PATH, Operator.ANY, [rule1, rule2])

        assert checker.is_empty() is True

    def test_is_empty_returns_false_when_any_rule_not_empty(self):
        rule1 = Mock(spec=FolderMatcher)
        rule1.is_empty.return_value = True
        rule2 = Mock(spec=FolderMatcher)
        rule2.is_empty.return_value = False

        checker = AttributeRuleHandler(RuleAttribute.PATH, Operator.ANY, [rule1, rule2])

        assert checker.is_empty() is False

    def test_clean_empty_removes_empty_rules(self):
        rule1 = Mock(spec=FolderMatcher)
        rule1.is_empty.return_value = True
        rule2 = Mock(spec=FolderMatcher)
        rule2.is_empty.return_value = False

        checker = AttributeRuleHandler(RuleAttribute.PATH, Operator.ANY, [rule1, rule2])
        checker.clean_empty()

        assert checker.rules == [rule2]

    def test_is_allowed_with_all_operator_returns_true_when_all_rules_allow(self):
        rule1 = Mock(spec=FolderMatcher)
        rule1.is_allowed.return_value = True
        rule2 = Mock(spec=FolderMatcher)
        rule2.is_allowed.return_value = True

        checker = AttributeRuleHandler(RuleAttribute.PATH, Operator.ALL, [rule1, rule2])
        folder = Mock(spec=Folder)

        assert checker.is_allowed(folder) is True

    def test_is_allowed_with_all_operator_returns_false_when_any_rule_denies(self):
        rule1 = Mock(spec=FolderMatcher)
        rule1.is_allowed.return_value = True
        rule2 = Mock(spec=FolderMatcher)
        rule2.is_allowed.return_value = False

        checker = AttributeRuleHandler(RuleAttribute.PATH, Operator.ALL, [rule1, rule2])
        folder = Mock(spec=Folder)

        assert checker.is_allowed(folder) is False

    def test_is_allowed_with_any_operator_returns_true_when_any_rule_allows(self):
        rule1 = Mock(spec=FolderMatcher)
        rule1.is_allowed.return_value = False
        rule2 = Mock(spec=FolderMatcher)
        rule2.is_allowed.return_value = True

        checker = AttributeRuleHandler(RuleAttribute.PATH, Operator.ANY, [rule1, rule2])
        folder = Mock(spec=Folder)

        assert checker.is_allowed(folder) is True

    def test_setup_rules_calls_setup_on_all_rules(self, checker):
        rule1 = Mock(spec=FolderMatcher)
        rule2 = Mock(spec=FolderMatcher)
        checker.rules = [rule1, rule2]

        before_or_after = ["before", "after"]
        checker.setup_rules(before_or_after)

        rule1.setup_rules.assert_called_once_with(before_or_after)
        rule2.setup_rules.assert_called_once_with(before_or_after)


class TestRuleChecker:
    @pytest.fixture
    def mock_attribute_checker(self):
        checker = Mock(spec=AttributeRuleHandler)
        checker.attribute = RuleAttribute.PATH
        checker.is_empty.return_value = False
        checker.is_allowed.return_value = True
        return checker

    @pytest.fixture
    def rule_checker(self, mock_attribute_checker):
        return ConfigRuleController([mock_attribute_checker], Operator.ANY)

    def test_init_creates_checker_with_params(self, mock_attribute_checker):
        checker = ConfigRuleController([mock_attribute_checker], Operator.ANY)

        assert checker.controllers == [mock_attribute_checker]
        assert checker.operator == Operator.ANY

    def test_name_returns_formatted_checker_names(self, mock_attribute_checker):
        checker = ConfigRuleController([mock_attribute_checker], Operator.ANY)

        assert checker.name == "Rule Checker [PATH]"

    def test_is_empty_returns_true_when_all_checkers_empty(self):
        checker1 = Mock(spec=AttributeRuleHandler)
        checker1.is_empty.return_value = True
        checker2 = Mock(spec=AttributeRuleHandler)
        checker2.is_empty.return_value = True

        rule_checker = ConfigRuleController([checker1, checker2], Operator.ANY)

        assert rule_checker.is_empty() is True

    def test_clean_empty_removes_empty_checkers(self):
        checker1 = Mock(spec=AttributeRuleHandler)
        checker1.is_empty.return_value = True
        checker2 = Mock(spec=AttributeRuleHandler)
        checker2.is_empty.return_value = False

        rule_checker = ConfigRuleController([checker1, checker2], Operator.ANY)
        rule_checker.clean_empty()

        assert rule_checker.controllers == [checker2]

    def test_is_allowed_with_all_operator_returns_true_when_all_checkers_allow(self):
        checker1 = Mock(spec=AttributeRuleHandler)
        checker1.is_allowed.return_value = True
        checker2 = Mock(spec=AttributeRuleHandler)
        checker2.is_allowed.return_value = True

        rule_checker = ConfigRuleController([checker1, checker2], Operator.ALL)
        folder = Mock(spec=Folder)

        assert rule_checker.is_allowed(folder) is True

    def test_setup_rules_calls_setup_on_all_checkers(self, rule_checker):
        checker1 = Mock(spec=AttributeRuleHandler)
        checker2 = Mock(spec=AttributeRuleHandler)
        rule_checker.controllers = [checker1, checker2]

        before_or_after = ["before", "after"]
        rule_checker.setup_rules(before_or_after)

        checker1.setup_rules.assert_called_once_with(before_or_after)
        checker2.setup_rules.assert_called_once_with(before_or_after)


class TestRuleManager:
    @pytest.fixture
    def mock_json_file(self):
        json_file = Mock(spec=JsonFile)
        json_file.name_wo_extension = "test_config"
        return json_file

    @pytest.fixture
    def mock_rule_checker(self):
        checker = Mock(spec=ConfigRuleController)
        checker.is_empty.return_value = False
        checker.is_allowed.return_value = True
        return checker

    @pytest.fixture
    def rule_manager(self, mock_json_file, mock_rule_checker):
        return RuleManager(mock_json_file, mock_rule_checker, 10, True)

    def test_init_creates_manager_with_params(self, mock_json_file, mock_rule_checker):
        manager = RuleManager(mock_json_file, mock_rule_checker, 10, True)

        assert manager.config == mock_json_file
        assert manager.checker == mock_rule_checker
        assert manager.order == 10
        assert manager.copy_icon is True

    def test_name_returns_config_name(self, rule_manager):
        assert rule_manager.name == "test_config"

    def test_is_empty_delegates_to_checker(self, rule_manager):
        rule_manager.checker.is_empty.return_value = True

        assert rule_manager.is_empty() is True

    def test_clean_empty_delegates_to_checker(self, rule_manager):
        rule_manager.clean_empty()

        rule_manager.checker.clean_empty.assert_called_once()

    def test_is_allowed_delegates_to_checker(self, rule_manager):
        folder = Mock(spec=Folder)
        rule_manager.checker.is_allowed.return_value = True

        assert rule_manager.is_allowed(folder) is True

    def test_setup_rules_delegates_to_checker(self, rule_manager):
        before_or_after = ["before", "after"]
        rule_manager.setup_rules(before_or_after)

        rule_manager.checker.setup_rules.assert_called_once_with(before_or_after)

    def test_str_returns_formatted_name(self, rule_manager):
        assert str(rule_manager) == '"TEST_CONFIG" Manager'


class TestExcludeManager:
    """First matching section wins, and each carries its own action."""

    @staticmethod
    def matcher(matches: bool = False, empty: bool = False) -> Mock:
        mock = Mock(spec=FolderMatcher)
        mock.is_empty.return_value = empty
        mock.is_allowed.return_value = matches
        return mock

    @classmethod
    def rule(cls, matches: bool, action: FolderAction = FolderAction.SKIP) -> ExcludeRule:
        return ExcludeRule(cls.matcher(matches=matches), action)

    def test_no_section_matching_means_no_action(self):
        manager = ExcludeManager([self.rule(matches=False)])

        assert manager.action_for(Mock(spec=Folder)) is None

    def test_an_empty_manager_has_no_action(self):
        assert ExcludeManager([]).action_for(Mock(spec=Folder)) is None

    def test_the_matching_section_decides_the_action(self):
        manager = ExcludeManager([self.rule(matches=True, action=FolderAction.LEAF)])

        assert manager.action_for(Mock(spec=Folder)) is FolderAction.LEAF

    def test_the_first_matching_section_wins(self):
        manager = ExcludeManager(
            [
                self.rule(matches=False, action=FolderAction.LEAF),
                self.rule(matches=True, action=FolderAction.SKIP),
                self.rule(matches=True, action=FolderAction.LEAF),
            ]
        )

        assert manager.action_for(Mock(spec=Folder)) is FolderAction.SKIP

    def test_skip_is_the_default_action(self):
        matcher = Mock(spec=FolderMatcher)
        matcher.is_allowed.return_value = True

        assert ExcludeRule(matcher).action is FolderAction.SKIP

    def test_is_empty_when_every_section_is_empty(self):
        rules = [ExcludeRule(self.matcher(empty=True)), ExcludeRule(self.matcher(empty=True))]

        assert ExcludeManager(rules).is_empty() is True

    def test_clean_empty_drops_the_empty_sections(self):
        empty = ExcludeRule(self.matcher(empty=True))
        kept = ExcludeRule(self.matcher())

        manager = ExcludeManager([empty, kept])
        manager.clean_empty()

        assert manager.rules == [kept]

    def test_setup_rules_reaches_every_section(self):
        first, second = self.matcher(), self.matcher()
        manager = ExcludeManager([ExcludeRule(first), ExcludeRule(second)])

        manager.setup_rules(["_", "-"])

        first.setup_rules.assert_called_once_with(["_", "-"])
        second.setup_rules.assert_called_once_with(["_", "-"])

    def test_str_reports_the_section_count(self):
        assert str(ExcludeManager([self.rule(matches=False)])) == "Exclude Manager [1]"
