import json
import re
import subprocess
from collections.abc import Mapping
from xml.etree import ElementTree

# The API key of Bazarr in its config.yaml: the apikey of the auth block, not the one of jellyfin, plex or radarr.
BAZARR_KEY = re.compile(r"^auth:\n(?:  .*\n)*?  apikey: '?(\w+)", re.MULTILINE)


# The API key of each service by container name: the one given in the environment, or else the one the service
# generated on its first start, read from its config inside the container with docker exec.
class KeyService:
    def __init__(self, keys: Mapping[str, str | None], docker: str) -> None:
        self._keys = keys
        self._docker = docker

    def key(self, container: str) -> str:
        if given := self._keys.get(container):
            return given
        if container == "seerr":
            return json.loads(self._read(container, "/app/config/settings.json"))["main"]["apiKey"]
        if container == "bazarr":
            match = BAZARR_KEY.search(self._read(container, "/config/config/config.yaml"))
            if match is None:
                raise OSError("no apikey in the config of bazarr")
            return match[1]
        key = ElementTree.fromstring(self._read(container, "/config/config.xml")).findtext("ApiKey")
        if key is None:
            raise OSError(f"no ApiKey in the config of {container}")
        return key

    def _read(self, container: str, path: str) -> str:
        command = [self._docker, "exec", container, "cat", path]
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode:
            raise OSError(f"docker exec {container}: {result.stderr.strip()}")
        return result.stdout
