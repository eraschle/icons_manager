import logging
import os
from typing import List

from icon_manager.controller.base import FileBaseController
from icon_manager.models.path import JsonFile
from icon_manager.source.json_source import JsonSource
from icon_manager.utils.resources import folder_config_template

log = logging.getLogger(__name__)


class AppConfigController(FileBaseController[JsonFile]):

    def __init__(self, full_path: str) -> None:
        super().__init__(full_path, JsonFile)

    def export_app_config(self) -> None:
        source = JsonSource()
        config_file = folder_config_template()
        config = 'config'
        template_config = source.read(config_file)
        for section, values in template_config.get(config, {}).items():
            if isinstance(values, List):
                template_config[config][section] = []
            elif isinstance(values, str):
                template_config[config][section] = ''
            elif isinstance(values, bool):
                template_config[config][section] = False
        file_path = os.path.join(self.full_path, config_file.name)
        export_file = JsonFile(file_path)
        source.write(export_file, template_config)
