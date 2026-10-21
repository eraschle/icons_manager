import os

RESOURCE_FOLDER = "resources"


def _resource_path(file_name: str) -> str:
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(here, "..", RESOURCE_FOLDER, file_name)


CONFIG_TEMPLATE_NAME: str = "icon_config_template.json"
EXCLUDE_RULES_TEMPLATE_NAME: str = "exclude_rules_template.json"
USER_TEMPLATE_NAME: str = "template_user.config"
APP_TEMPLATE_NAME: str = "template_app.config"


def icon_setting_template_path() -> str:
    return _resource_path(CONFIG_TEMPLATE_NAME)


def exclude_rules_template_path() -> str:
    return _resource_path(EXCLUDE_RULES_TEMPLATE_NAME)


def user_config_template_path() -> str:
    return _resource_path(USER_TEMPLATE_NAME)


def app_config_template_path() -> str:
    return _resource_path(APP_TEMPLATE_NAME)
