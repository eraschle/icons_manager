import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path

from icon_manager.config.app import AppConfig, AppConfigFactory, AppConfigs
from icon_manager.data.json_source import JsonSource
from icon_manager.helpers.environment import get_converted_env_path
from icon_manager.helpers.logs import log_time
from icon_manager.helpers.resource import app_config_template_path
from icon_manager.interfaces.path import ConfigFile
from icon_manager.rules.factory.manager import ExcludeManagerFactory
from icon_manager.services.app_service import IconsAppService
from icon_manager.validation.configs import (
    libraries_of,
    read_json,
    validate_config_folder,
    validate_library,
)
from icon_manager.validation.problems import Severity, problem_report

log = logging.getLogger(__name__)


def console(level) -> logging.Handler:
    handler = logging.StreamHandler()
    handler.setLevel(level)
    # format_string = '%(levelname)-8s: %(name)-12s: %(funcName)s - %(message)s'
    # format_string = '%(levelname)-8s %(funcName)-30s>> %(message)s'
    format_string = "%(levelname)-8s  %(message)s"
    formatter = logging.Formatter(format_string)
    handler.setFormatter(formatter)
    return handler


def config_logger(level):
    logging.basicConfig(handlers=[console(level)], level=level)


def build_parser() -> argparse.ArgumentParser:
    description = "Helper to add icons to folders defined in a external JSON file."
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "--library",
        "-l",
        action="store_true",
        help="Execute the options on icon library",
    )
    parser.add_argument(
        "--content",
        "-c",
        action="store_true",
        help="Execute the options on search contents",
    )
    # Options
    parser.add_argument(
        "--create",
        "-a",
        action="store_true",
        help="Creates the library configs or applies the icons to folders",
    )
    parser.add_argument(
        "--re-create",
        "-r",
        action="store_true",
        help="Re apply the icons to the folder. The icons get lost over OneDrive synchronization",
    )
    parser.add_argument(
        "--update",
        "-u",
        action="store_true",
        help="Updates library configs with the content of the template",
    )
    parser.add_argument(
        "--delete",
        "-d",
        action="store_true",
        help="Deletes the library configs or applied icons",
    )
    parser.add_argument(
        "--archive",
        "-v",
        action="store_true",
        help='Moves the library configs without rules into subfolder "archive"',
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Reports every problem in the configuration files and the icon library, then exits",
    )
    return parser


def get_namespace_from_args(argv: list[str] | None = None) -> argparse.Namespace:
    return build_parser().parse_args(argv)


def get_app_config(config_file: ConfigFile) -> AppConfig:
    exclude_factory = ExcludeManagerFactory(JsonSource())
    factory = AppConfigFactory(JsonSource(), exclude_factory)
    config = factory.create(config_file)
    config.validate()
    return config


def get_service() -> IconsAppService:
    app_config = AppConfigFactory.app_config_file()
    if not app_config.exists():
        app_template = ConfigFile(app_config_template_path())
        app_template.copy_to(app_config)
    app_config = get_app_config(app_config)
    service = IconsAppService(app_config)
    return service


def config_folder_of(app_config: ConfigFile) -> Path | None:
    """The folder holding the user configs, read straight from the app config.

    Deliberately not through AppConfigFactory: that one asks the user for a
    path on stdin when something is missing, which is the wrong thing to do
    while reporting problems.
    """
    content, _ = read_json(Path(app_config.path))
    folder = (content or {}).get(AppConfigs.USER_CONFIGS.value)
    return Path(folder) if isinstance(folder, str) and folder else None


def run_check() -> int:
    """Report what is wrong with the configuration, and change nothing.

    Returns the exit code: non-zero when something would stop a real run.
    """
    app_config = AppConfigFactory.app_config_file()
    if not app_config.exists():
        print(f"No application configuration at {app_config.path}")
        return 1

    folder = config_folder_of(app_config)
    if folder is None:
        print(f'{app_config.path}: "{AppConfigs.USER_CONFIGS.value}" is missing or empty')
        return 1

    problems = list(validate_config_folder(folder, AppConfigFactory.EXCLUDE_NAME, AppConfigFactory.APP_CONFIG_NAME))
    for library in libraries_of(folder, AppConfigFactory.EXCLUDE_NAME, AppConfigFactory.APP_CONFIG_NAME):
        problems.extend(validate_library(Path(get_converted_env_path(str(library)))))

    if not problems:
        print(f"No problems found in {folder}")
        return 0
    print(problem_report(problems))
    errors = sum(1 for problem in problems if problem.severity is Severity.ERROR)
    warnings = len(problems) - errors
    print(f"\n{errors} error(s), {warnings} warning(s)")
    return 1 if errors else 0


def run_library_options(service: IconsAppService, args: argparse.Namespace) -> None:
    """Operations on the icon library itself.

    Run in this order so a single invocation stays meaningful: new icons get
    a config, existing configs are refreshed against the template, icons
    without rules are archived, and only then are configs deleted.
    """
    if args.create:
        service.create_library_configs()
    if args.update:
        service.update_library_configs()
    if args.archive:
        service.archive_icons_and_configs()
    if args.delete:
        service.delete_library_configs()


def run_content_options(service: IconsAppService, args: argparse.Namespace) -> None:
    """Operations on the searched folders.

    Deleting and re-applying both work from what is already on disk, so they
    need find_existing_content first; applying matches crawls on its own.
    """
    service.setup_and_merge_user_service()
    if args.delete or args.re_create:
        service.find_existing_content()
    if args.delete:
        service.delete_icon_settings()
    if args.re_create:
        service.re_apply_matched_icons()
    if args.create:
        service.find_and_apply_matches()


def run(service: IconsAppService, args: argparse.Namespace) -> None:
    """Read the icon library, then apply the requested options."""
    service.setup()
    service.create_settings()
    if args.library:
        run_library_options(service, args)
    elif args.content:
        run_content_options(service, args)
    else:
        log.warning("Nothing to do: pass --library or --content (see --help)")


def main(argv: list[str] | None = None) -> int:
    config_logger(logging.INFO)
    args = get_namespace_from_args(argv)
    if args.check:
        # before get_service(), which would create templates and ask for paths
        return run_check()
    start_time = datetime.now()
    run(get_service(), args)
    log.info(log_time("Execution-Time".upper(), start_time))
    return 0


if __name__ == "__main__":
    sys.exit(main())
