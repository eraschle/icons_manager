import pytest
from unittest.mock import Mock
from icon_manager.rules.manager import AttributeChecker, RuleChecker, RuleManager, ExcludeManager
from icon_manager.rules.base import ISingleRule, Operator, RuleAttribute
from icon_manager.interfaces.path import JsonFile, Folder
from icon_manager.interfaces.managers import IRuleChecker


class TestAttributeChecker:
    
    @pytest.fixture
    def mock_rule(self):
        rule = Mock(spec=ISingleRule)
        rule.is_empty.return_value = False
        rule.is_allowed.return_value = True
        return rule

    @pytest.fixture
    def checker(self, mock_rule):
        return AttributeChecker(RuleAttribute.PATH, Operator.ANY, [mock_rule])

    def test_init_creates_checker_with_params(self, mock_rule):
        checker = AttributeChecker(RuleAttribute.PATH, Operator.ANY, [mock_rule])
        
        assert checker.attribute == RuleAttribute.PATH
        assert checker.operator == Operator.ANY
        assert checker.rules == [mock_rule]

    def test_name_returns_formatted_attribute_name(self, checker):
        assert checker.name == '"PATH" Checker'

    def test_is_empty_returns_true_when_all_rules_empty(self):
        rule1 = Mock(spec=ISingleRule)
        rule1.is_empty.return_value = True
        rule2 = Mock(spec=ISingleRule)
        rule2.is_empty.return_value = True
        
        checker = AttributeChecker(RuleAttribute.PATH, Operator.ANY, [rule1, rule2])
        
        assert checker.is_empty() is True

    def test_is_empty_returns_false_when_any_rule_not_empty(self):
        rule1 = Mock(spec=ISingleRule)
        rule1.is_empty.return_value = True
        rule2 = Mock(spec=ISingleRule)
        rule2.is_empty.return_value = False
        
        checker = AttributeChecker(RuleAttribute.PATH, Operator.ANY, [rule1, rule2])
        
        assert checker.is_empty() is False

    def test_clean_empty_removes_empty_rules(self):
        rule1 = Mock(spec=ISingleRule)
        rule1.is_empty.return_value = True
        rule2 = Mock(spec=ISingleRule)
        rule2.is_empty.return_value = False
        
        checker = AttributeChecker(RuleAttribute.PATH, Operator.ANY, [rule1, rule2])
        checker.clean_empty()
        
        assert checker.rules == [rule2]

    def test_is_allowed_with_all_operator_returns_true_when_all_rules_allow(self):
        rule1 = Mock(spec=ISingleRule)
        rule1.is_allowed.return_value = True
        rule2 = Mock(spec=ISingleRule)
        rule2.is_allowed.return_value = True
        
        checker = AttributeChecker(RuleAttribute.PATH, Operator.ALL, [rule1, rule2])
        folder = Mock(spec=Folder)
        
        assert checker.is_allowed(folder) is True

    def test_is_allowed_with_all_operator_returns_false_when_any_rule_denies(self):
        rule1 = Mock(spec=ISingleRule)
        rule1.is_allowed.return_value = True
        rule2 = Mock(spec=ISingleRule)
        rule2.is_allowed.return_value = False
        
        checker = AttributeChecker(RuleAttribute.PATH, Operator.ALL, [rule1, rule2])
        folder = Mock(spec=Folder)
        
        assert checker.is_allowed(folder) is False

    def test_is_allowed_with_any_operator_returns_true_when_any_rule_allows(self):
        rule1 = Mock(spec=ISingleRule)
        rule1.is_allowed.return_value = False
        rule2 = Mock(spec=ISingleRule)
        rule2.is_allowed.return_value = True
        
        checker = AttributeChecker(RuleAttribute.PATH, Operator.ANY, [rule1, rule2])
        folder = Mock(spec=Folder)
        
        assert checker.is_allowed(folder) is True

    def test_setup_rules_calls_setup_on_all_rules(self, checker):
        rule1 = Mock(spec=ISingleRule)
        rule2 = Mock(spec=ISingleRule)
        checker.rules = [rule1, rule2]
        
        before_or_after = ['before', 'after']
        checker.setup_rules(before_or_after)
        
        rule1.set_before_or_after.assert_called_once_with(before_or_after)
        rule1.setup_filter_rule.assert_called_once()
        rule2.set_before_or_after.assert_called_once_with(before_or_after)
        rule2.setup_filter_rule.assert_called_once()


class TestRuleChecker:
    
    @pytest.fixture
    def mock_attribute_checker(self):
        checker = Mock(spec=AttributeChecker)
        checker.attribute = RuleAttribute.PATH
        checker.is_empty.return_value = False
        checker.is_allowed.return_value = True
        return checker

    @pytest.fixture
    def rule_checker(self, mock_attribute_checker):
        return RuleChecker([mock_attribute_checker], Operator.ANY)

    def test_init_creates_checker_with_params(self, mock_attribute_checker):
        checker = RuleChecker([mock_attribute_checker], Operator.ANY)
        
        assert checker.checkers == [mock_attribute_checker]
        assert checker.operator == Operator.ANY

    def test_name_returns_formatted_checker_names(self, mock_attribute_checker):
        checker = RuleChecker([mock_attribute_checker], Operator.ANY)
        
        assert checker.name == 'Rule Checker [PATH]'

    def test_is_empty_returns_true_when_all_checkers_empty(self):
        checker1 = Mock(spec=AttributeChecker)
        checker1.is_empty.return_value = True
        checker2 = Mock(spec=AttributeChecker)
        checker2.is_empty.return_value = True
        
        rule_checker = RuleChecker([checker1, checker2], Operator.ANY)
        
        assert rule_checker.is_empty() is True

    def test_clean_empty_removes_empty_checkers(self):
        checker1 = Mock(spec=AttributeChecker)
        checker1.is_empty.return_value = True
        checker2 = Mock(spec=AttributeChecker)
        checker2.is_empty.return_value = False
        
        rule_checker = RuleChecker([checker1, checker2], Operator.ANY)
        rule_checker.clean_empty()
        
        assert rule_checker.checkers == [checker2]

    def test_is_allowed_with_all_operator_returns_true_when_all_checkers_allow(self):
        checker1 = Mock(spec=AttributeChecker)
        checker1.is_allowed.return_value = True
        checker2 = Mock(spec=AttributeChecker)
        checker2.is_allowed.return_value = True
        
        rule_checker = RuleChecker([checker1, checker2], Operator.ALL)
        folder = Mock(spec=Folder)
        
        assert rule_checker.is_allowed(folder) is True

    def test_setup_rules_calls_setup_on_all_checkers(self, rule_checker):
        checker1 = Mock(spec=AttributeChecker)
        checker2 = Mock(spec=AttributeChecker)
        rule_checker.checkers = [checker1, checker2]
        
        before_or_after = ['before', 'after']
        rule_checker.setup_rules(before_or_after)
        
        checker1.setup_rules.assert_called_once_with(before_or_after)
        checker2.setup_rules.assert_called_once_with(before_or_after)


class TestRuleManager:
    
    @pytest.fixture
    def mock_json_file(self):
        json_file = Mock(spec=JsonFile)
        json_file.name_wo_extension = 'test_config'
        return json_file

    @pytest.fixture
    def mock_rule_checker(self):
        checker = Mock(spec=RuleChecker)
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
        assert manager.weight == 10
        assert manager.copy_icon is True

    def test_name_returns_config_name(self, rule_manager):
        assert rule_manager.name == 'test_config'

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
        before_or_after = ['before', 'after']
        rule_manager.setup_rules(before_or_after)
        
        rule_manager.checker.setup_rules.assert_called_once_with(before_or_after)

    def test_str_returns_formatted_name(self, rule_manager):
        assert str(rule_manager) == '"TEST_CONFIG" Manager'


class TestExcludeManager:
    
    @pytest.fixture
    def mock_rule_checker(self):
        checker = Mock(spec=IRuleChecker)
        checker.is_empty.return_value = False
        checker.is_valid.return_value = True
        checker.is_allowed.return_value = True
        return checker

    @pytest.fixture
    def exclude_manager(self, mock_rule_checker):
        return ExcludeManager([mock_rule_checker])

    def test_init_creates_manager_with_checkers(self, mock_rule_checker):
        manager = ExcludeManager([mock_rule_checker])
        
        assert manager.checkers == [mock_rule_checker]

    def test_is_empty_returns_true_when_all_checkers_empty(self):
        checker1 = Mock(spec=IRuleChecker)
        checker1.is_empty.return_value = True
        checker2 = Mock(spec=IRuleChecker)
        checker2.is_empty.return_value = True
        
        manager = ExcludeManager([checker1, checker2])
        
        assert manager.is_empty() is True

    def test_is_valid_returns_true_when_all_checkers_valid(self):
        checker1 = Mock(spec=IRuleChecker)
        checker1.is_valid.return_value = True
        checker2 = Mock(spec=IRuleChecker)
        checker2.is_valid.return_value = True
        
        manager = ExcludeManager([checker1, checker2])
        
        assert manager.is_valid() is True

    def test_clean_empty_removes_empty_checkers(self):
        checker1 = Mock(spec=IRuleChecker)
        checker1.is_empty.return_value = True
        checker2 = Mock(spec=IRuleChecker)
        checker2.is_empty.return_value = False
        
        manager = ExcludeManager([checker1, checker2])
        manager.clean_empty()
        
        assert manager.checkers == [checker2]

    def test_is_allowed_returns_true_when_empty(self):
        manager = ExcludeManager([])
        folder = Mock(spec=Folder)
        
        assert manager.is_allowed(folder) is True

    def test_is_allowed_returns_true_when_any_checker_allows(self):
        checker1 = Mock(spec=IRuleChecker)
        checker1.is_allowed.return_value = False
        checker2 = Mock(spec=IRuleChecker)
        checker2.is_allowed.return_value = True
        
        manager = ExcludeManager([checker1, checker2])
        folder = Mock(spec=Folder)
        
        assert manager.is_allowed(folder) is True

    def test_is_excluded_returns_false_when_empty(self):
        manager = ExcludeManager([])
        folder = Mock(spec=Folder)
        
        assert manager.is_excluded(folder) is False

    def test_is_excluded_returns_same_as_is_allowed(self, exclude_manager):
        folder = Mock(spec=Folder)
        exclude_manager.checkers[0].is_allowed.return_value = True
        
        assert exclude_manager.is_excluded(folder) is True

    def test_setup_rules_calls_setup_on_all_checkers(self, exclude_manager):
        checker1 = Mock(spec=IRuleChecker)
        checker2 = Mock(spec=IRuleChecker)
        exclude_manager.checkers = [checker1, checker2]
        
        before_or_after = ['before', 'after']
        exclude_manager.setup_rules(before_or_after)
        
        checker1.setup_rules.assert_called_once_with(before_or_after)
        checker2.setup_rules.assert_called_once_with(before_or_after)

    def test_str_returns_formatted_count(self, exclude_manager):
        assert str(exclude_manager) == 'Exclude Manager [1]'