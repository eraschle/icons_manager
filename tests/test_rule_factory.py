import pytest
from unittest.mock import Mock, patch
from icon_manager.rules.factory.manager import (
    AttributeCheckerFactory,
    SourceCheckerBuilder,
    AManagerFactory,
    RuleManagerFactory,
    ExcludeManagerFactory,
)
from icon_manager.rules.factory.rules import ConfigKeys
from icon_manager.rules.manager import AttributeChecker, RuleChecker, RuleManager, ExcludeManager
from icon_manager.rules.base import ISingleRule, IFilterRule, Operator, RuleAttribute
from icon_manager.data.base import Source
from icon_manager.data.json_source import JsonSource
from icon_manager.interfaces.path import JsonFile, ConfigFile


class TestAttributeCheckerFactory:
    @pytest.fixture
    def factory(self):
        return AttributeCheckerFactory()

    def test_init_creates_factory_with_builders(self):
        factory = AttributeCheckerFactory()
        assert factory.builders is not None

    @patch("icon_manager.rules.factory.manager.get_builders")
    def test_create_rule_uses_first_compatible_builder(self, mock_get_builders, factory):
        rule_config = {"type": "contains", "value": "test"}

        mock_builder1 = Mock()
        mock_builder1.can_build.return_value = False
        mock_builder2 = Mock()
        mock_builder2.can_build.return_value = True
        mock_rule = Mock(spec=IFilterRule)
        mock_builder2.create.return_value = mock_rule

        mock_get_builders.return_value = [mock_builder1, mock_builder2]
        factory.builders = [mock_builder1, mock_builder2]

        result = factory.create_rule(rule_config)

        mock_builder1.can_build.assert_called_once_with(rule_config)
        mock_builder2.can_build.assert_called_once_with(rule_config)
        mock_builder2.create.assert_called_once_with(rule_config)
        assert result == mock_rule

    def test_create_rule_raises_error_when_no_builder_found(self, factory):
        rule_config = {"type": "unknown", "value": "test"}

        mock_builder = Mock()
        mock_builder.can_build.return_value = False
        factory.builders = [mock_builder]

        with pytest.raises(RuntimeError, match="No Folder builder could be created"):
            factory.create_rule(rule_config)

    def test_create_rules_creates_list_of_rules(self, factory):
        config = {
            "rules": [{"type": "contains", "value": "test1"}, {"type": "equals", "value": "test2"}]
        }

        mock_rule1 = Mock(spec=IFilterRule)
        mock_rule2 = Mock(spec=IFilterRule)

        with patch.object(factory, "create_rule") as mock_create_rule:
            mock_create_rule.side_effect = [mock_rule1, mock_rule2]

            result = factory.create_rules(config)

            assert result == [mock_rule1, mock_rule2]
            assert mock_create_rule.call_count == 2

    def test_create_rules_returns_empty_list_when_no_rules(self, factory):
        config = {}

        result = factory.create_rules(config)

        assert result == []

    @patch("icon_manager.rules.factory.manager.pop_operator")
    def test_create_builds_attribute_checker(self, mock_pop_operator, factory):
        config = {"operator": "any", "rules": []}
        mock_pop_operator.return_value = Operator.ANY

        with patch.object(factory, "create_rules") as mock_create_rules:
            mock_rules = [Mock(spec=ISingleRule)]
            mock_create_rules.return_value = mock_rules

            result = factory.create(config, attribute=RuleAttribute.PATH)

            assert isinstance(result, AttributeChecker)
            assert result.attribute == RuleAttribute.PATH
            assert result.operator == Operator.ANY
            assert result.rules == mock_rules


class TestSourceCheckerBuilder:
    @pytest.fixture
    def mock_source(self):
        return Mock(spec=Source)

    @pytest.fixture
    def builder(self, mock_source):
        return SourceCheckerBuilder(mock_source)

    def test_init_creates_builder_with_source_and_factory(self, mock_source):
        builder = SourceCheckerBuilder(mock_source)

        assert builder.source == mock_source
        assert isinstance(builder.factory, AttributeCheckerFactory)

    def test_init_uses_default_json_source_when_not_provided(self):
        builder = SourceCheckerBuilder()

        assert isinstance(builder.source, JsonSource)

    @patch("icon_manager.rules.factory.manager.get_rule_attribute")
    def test_get_attribute_checkers_creates_checkers_for_each_attribute(
        self, mock_get_rule_attr, builder
    ):
        config = {
            "path": {"operator": "any", "rules": []},
            "name": {"operator": "all", "rules": []},
        }

        mock_path_attr = RuleAttribute.PATH
        mock_name_attr = RuleAttribute.NAME
        mock_get_rule_attr.side_effect = [mock_path_attr, mock_name_attr]

        mock_checker1 = Mock(spec=AttributeChecker)
        mock_checker2 = Mock(spec=AttributeChecker)
        builder.factory.create = Mock(side_effect=[mock_checker1, mock_checker2])

        result = builder.get_attribute_checkers(config)

        assert result == [mock_checker1, mock_checker2]
        assert builder.factory.create.call_count == 2

    @patch("icon_manager.rules.factory.manager.pop_operator")
    def test_create_builds_rule_checker(self, mock_pop_operator, builder):
        config = {"operator": "all", "path": {}, "name": {}}
        mock_pop_operator.return_value = Operator.ALL

        mock_checkers = [Mock(spec=AttributeChecker)]
        with patch.object(builder, "get_attribute_checkers") as mock_get_checkers:
            mock_get_checkers.return_value = mock_checkers

            result = builder.create(config)

            assert isinstance(result, RuleChecker)
            assert result.checkers == mock_checkers
            assert result.operator == Operator.ALL


class TestAManagerFactory:
    @pytest.fixture
    def mock_source(self):
        return Mock(spec=Source)

    @pytest.fixture
    def concrete_factory(self, mock_source):
        # Create a concrete implementation for testing
        class ConcreteManagerFactory(AManagerFactory):
            def create_with_content(self, config, **kwargs):
                return Mock(spec=RuleManager)

        return ConcreteManagerFactory(mock_source)

    def test_init_creates_factory_with_source_and_builder(self, mock_source):
        factory = RuleManagerFactory(mock_source)

        assert factory.source == mock_source
        assert isinstance(factory.builder, SourceCheckerBuilder)
        assert factory._template == {}

    def test_init_uses_default_json_source_when_not_provided(self):
        factory = RuleManagerFactory()

        assert isinstance(factory.source, JsonSource)

    def test_get_config_section_returns_config_section(self, concrete_factory):
        content = {"config": {"path": {}, "name": {}}}

        result = concrete_factory.get_config_section(content)

        assert result == {"path": {}, "name": {}}

    def test_get_config_section_raises_error_when_missing(self, concrete_factory):
        content = {"other_section": {}}

        with pytest.raises(ValueError, match=f'Key "{ConfigKeys.CONFIG}" does NOT'):
            concrete_factory.get_config_section(content)

    def test_create_reads_file_and_delegates_to_create_with_content(self, concrete_factory):
        mock_file = Mock(spec=JsonFile)
        mock_content = {"config": {"path": {}}}

        concrete_factory.source.read.return_value = mock_content

        with patch.object(concrete_factory, "create_with_content") as mock_create_with_content:
            mock_result = Mock(spec=RuleManager)
            mock_create_with_content.return_value = mock_result

            result = concrete_factory.create(mock_file)

            concrete_factory.source.read.assert_called_once_with(mock_file)
            mock_create_with_content.assert_called_once_with({"path": {}}, file=mock_file)
            assert result == mock_result


class TestRuleManagerFactory:
    @pytest.fixture
    def factory(self):
        return RuleManagerFactory()

    def test_create_with_content_builds_rule_manager(self, factory):
        config = {"copy_icon": True, "order": 10, "path": {"operator": "any", "rules": []}}
        mock_file = Mock(spec=JsonFile)

        mock_rule_checker = Mock(spec=RuleChecker)
        factory.builder.create = Mock(return_value=mock_rule_checker)

        result = factory.create_with_content(config, file=mock_file)

        assert isinstance(result, RuleManager)
        assert result.config == mock_file
        assert result.checker == mock_rule_checker
        assert result.weight == 10
        assert result.copy_icon is True

    def test_create_with_content_uses_defaults_for_missing_values(self, factory):
        config = {"path": {}}
        mock_file = Mock(spec=JsonFile)

        mock_rule_checker = Mock(spec=RuleChecker)
        factory.builder.create = Mock(return_value=mock_rule_checker)

        result = factory.create_with_content(config, file=mock_file)

        assert result.weight == 5  # default order
        assert result.copy_icon is None  # default copy_icon

    def test_create_with_content_raises_error_when_no_file(self, factory):
        config = {"path": {}}

        with pytest.raises(ValueError, match='"file" is not in kwargs or None'):
            factory.create_with_content(config)

    def test_update_updates_config_with_template(self, factory):
        mock_config = Mock(spec=JsonFile)
        mock_config.path = '/test/config.json'
        mock_template = Mock(spec=JsonFile)
        mock_template.path = '/test/template.json'

        existing_content = {"config": {"path": {"existing": "config"}}}
        template_content = {"config": {"template": "values"}, "other_section": {"template": "data"}}

        factory.source.read = Mock()
        factory.source.read.side_effect = [existing_content, template_content]
        factory.source.write = Mock()
        factory._template = {}

        factory.update(mock_config, mock_template)

        # Verify that write was called with updated content
        write_call_args = factory.source.write.call_args[0][1]
        assert write_call_args["config"] == {"path": {"existing": "config"}}
        assert write_call_args["other_section"] == {"template": "data"}


class TestExcludeManagerFactory:
    @pytest.fixture
    def factory(self):
        return ExcludeManagerFactory()

    def test_create_with_content_builds_exclude_manager(self, factory):
        config = [{"operator": "any", "path": {}}, {"operator": "all", "name": {}}]

        mock_checker1 = Mock(spec=RuleChecker)
        mock_checker2 = Mock(spec=RuleChecker)
        factory.builder.create = Mock(side_effect=[mock_checker1, mock_checker2])

        result = factory.create_with_content(config)

        assert isinstance(result, ExcludeManager)
        assert result.checkers == [mock_checker1, mock_checker2]
        assert factory.builder.create.call_count == 2

    def test_create_with_content_returns_empty_manager_for_empty_config(self, factory):
        config = []

        result = factory.create_with_content(config)

        assert isinstance(result, ExcludeManager)
        assert result.checkers == []

    @patch("icon_manager.rules.factory.manager.excluded_rules_template_file")
    def test_copy_template_copies_template_file(self, mock_template_func, factory):
        mock_config = Mock(spec=ConfigFile)
        mock_template = Mock()
        mock_template_func.return_value = mock_template

        factory.copy_template(mock_config)

        mock_template.copy_to.assert_called_once_with(mock_config)

    def test_prepare_template_reads_and_writes_content(self, factory):
        mock_config = Mock(spec=ConfigFile)
        mock_config.path = '/test/config.json'
        mock_content = {"config": []}

        # Reset any previous side_effect
        factory.source.read = Mock(return_value=mock_content)
        factory.source.write = Mock()

        factory.prepare_template(mock_config)

        factory.source.read.assert_called_once_with(mock_config)
        factory.source.write.assert_called_once_with(mock_config, mock_content)

    def test_create_template_combines_copy_and_prepare(self, factory):
        mock_config = Mock(spec=ConfigFile)

        with patch.object(factory, "copy_template") as mock_copy:
            with patch.object(factory, "prepare_template") as mock_prepare:
                result = factory.create_template(mock_config)

                mock_copy.assert_called_once_with(mock_config)
                mock_prepare.assert_called_once_with(mock_config)
                assert result == mock_config

    def test_integration_create_from_file(self, factory):
        # Integration test for the complete creation workflow
        mock_file = Mock(spec=JsonFile)
        mock_file.path = '/test/exclude.json'
        mock_content = {"config": [{"operator": "any", "path": {"rules": []}}]}

        # Reset any previous side_effect
        factory.source.read = Mock(return_value=mock_content)

        with patch.object(factory.builder, "create") as mock_builder_create:
            mock_checker = Mock(spec=RuleChecker)
            mock_builder_create.return_value = mock_checker

            result = factory.create(mock_file)

            assert isinstance(result, ExcludeManager)
            assert len(result.checkers) == 1
            assert result.checkers[0] == mock_checker
