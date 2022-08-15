import json
from typing import Any, Dict

from icon_manager.source.base import Source
from icon_manager.models.path import JsonFile


class JsonSource(Source[JsonFile, Dict[str, Any]]):

    def read(self, source: JsonFile) -> Dict[str, Any]:
        with open(source.path, encoding='utf-8') as config_file:
            content = json.load(config_file)
            config_file.close()
            return content

    def write(self, source: JsonFile, content: Dict[str, Any]):
        with open(source.path, encoding='utf-8', mode='w') as config_file:
            json.dump(fp=config_file, obj=content, indent=4)
            config_file.close()
