from collections.abc import Callable

from tide.infrastructure.http.api_client import ApiClient
from tide.infrastructure.http.schema import find, with_values

PROWLARR = "http://prowlarr:9696"
# The media managers Prowlarr pushes its indexers to, by container name, at their address on the network tide.
APPS = {"radarr": "http://radarr:7878", "sonarr": "http://sonarr:8989"}


# Prowlarr: adds Radarr or Sonarr as an app with Full Sync, so every indexer added in Prowlarr reaches it.
# Prowlarr holds their API keys, key_of(container), not the other way round.
class ProwlarrService:
    def __init__(self, client: ApiClient, key_of: Callable[[str], str]) -> None:
        self._client = client
        self._key_of = key_of

    def sync(self, app: str) -> None:
        schema = find(self._client.get("/applications/schema"), "implementation", app.capitalize())
        values = {"prowlarrUrl": PROWLARR, "baseUrl": APPS[app], "apiKey": self._key_of(app)}
        application = {
            **schema,
            "name": schema["implementation"],
            "syncLevel": "fullSync",
            "fields": with_values(schema["fields"], values),
        }
        self._client.upsert("/applications", application)
