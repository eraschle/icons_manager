import json
from typing import Any, Dict

from dir_man.models.path import JsonFile


class JsonReader:

    def read_file(self, config: JsonFile) -> Dict[str, Any]:
        with open(config.path, encoding='utf-8') as config_file:
            content = json.load(config_file)
            return content
