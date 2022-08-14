import json
from typing import Any, Dict


class JsonSource:

    def read(self, path: str) -> Dict[str, Any]:
        with open(path, encoding='utf-8') as config_file:
            content = json.load(config_file)
            config_file.close()
            return content

    def write(self, path: str, content: Dict[str, Any]):
        with open(path, encoding='utf-8', mode='w') as config_file:
            json.dump(fp=config_file, obj=content, indent=4)
            config_file.close()
