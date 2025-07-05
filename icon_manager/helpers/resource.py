import os

from icon_manager.interfaces.path import ConfigFile, JsonFile


def __resources_path(file_name: str) -> str:
    paths = [os.path.dirname(os.path.abspath(__file__)), "..", "resources"]
    paths.append(file_name)
    return os.path.join(*paths)


CONFIG_TEMPLATE_NAME: str = "icon_config_template.json"


def icon_setting_template_path() -> str:
    return __resources_path(CONFIG_TEMPLATE_NAME)


def icon_setting_template() -> JsonFile:
    return JsonFile(icon_setting_template_path())


EXCLUDE_RULES_TEMPLATE_NAME: str = "exclude_rules_template.config"


def exclude_rules_template_path() -> str:
    return __resources_path(EXCLUDE_RULES_TEMPLATE_NAME)


def excluded_rules_template_file() -> ConfigFile:
    return ConfigFile(exclude_rules_template_path())


USER_TEMPLATE_NAME: str = "template_user.config"


def user_config_template_path() -> str:
    return __resources_path(USER_TEMPLATE_NAME)


def user_config_template_file() -> ConfigFile:
    return ConfigFile(user_config_template_path())


APP_TEMPLATE_NAME: str = "template_app.config"


def app_config_template_path() -> str:
    return __resources_path(APP_TEMPLATE_NAME)


def app_config_template_file() -> ConfigFile:
    return ConfigFile(app_config_template_path())
