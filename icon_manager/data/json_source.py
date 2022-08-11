import json
from typing import Any, Dict

from icon_manager.models.path import JsonFile


class JsonSource:

    def read_file(self, config: JsonFile) -> Dict[str, Any]:
        with open(config.path, encoding='utf-8') as config_file:
            content = json.load(config_file)
            config_file.close()
            return content

    def write_file(self, config: JsonFile, content: Dict[str, Any]):
        with open(config.path, encoding='utf-8', mode='w') as config_file:
            json.dump(fp=config_file, obj=content)
            config_file.close()
