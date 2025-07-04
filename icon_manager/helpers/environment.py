import os
import re

GROUP_NAME = "env"
ENV_PATTERN = re.compile(r"(?P<env>%[a-zA-Z0-9_-]*%)")


def get_env_var_value_of(value: str) -> str:
    matches = ENV_PATTERN.match(value)
    if matches is None:
        raise LookupError("No ENVIRONMENT variable found")
    match_groups = matches.groupdict()
    variable = match_groups.get(GROUP_NAME, None)
    if variable is None:
        raise LookupError("No pattern %%ENVIRONMENT%% found")
    return variable


def get_env_var_value(value: str) -> str | None:
    env_var_value = get_env_var_value_of(value)
    env_var = env_var_value[1:-1]
    env_value = os.getenv(env_var, None)
    if env_value is None:
        return None
    return env_value


def contains_env_var(value: str) -> bool:
    try:
        env_value = get_env_var_value(value)
        return env_value is not None
    except LookupError:
        return False


def get_env_path(value: str) -> str:
    env_value = get_env_var_value(value)
    if env_value is None:
        return value
    env_var_value = get_env_var_value_of(value)
    return value.replace(env_var_value, env_value)


def get_converted_env_path(value: str) -> str:
    if contains_env_var(value):
        value = get_env_path(value)
    return value
