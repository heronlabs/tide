from collections.abc import Callable
from urllib.parse import urlencode

from tide.infrastructure.http.api_client import ApiClient
from tide.infrastructure.http.schema import find

# The plugin repository of JellyBridge, by the name Jellyfin lists it under.
REPOSITORY = {
    "Name": "Jelly Bridge",
    "Url": "https://raw.githubusercontent.com/kinggeorges12/JellyBridge/refs/heads/main/manifest.json",
    "Enabled": True,
}
# The library of JellyBridge's placeholders, ~/Media/Discover on the host.
DISCOVER = "Discover"
DISCOVER_PATH = "/media/Discover"


# Jellyfin: adds the plugin repository of JellyBridge and points the installed plugin at Seerr, by container name and
# with Seerr's API key, key_of(container), so it fills the library Discover with Seerr's catalog. Jellyfin replaces
# its repositories and a plugin's settings whole, so each step sends what Jellyfin has with tide's changed.
class JellyfinService:
    def __init__(self, client: ApiClient, key_of: Callable[[str], str]) -> None:
        self._client = client
        self._key_of = key_of

    def add_repository(self) -> None:
        others = [item for item in self._client.get("/Repositories") if item["Name"] != REPOSITORY["Name"]]
        self._client.post("/Repositories", [*others, REPOSITORY])

    # Installing the plugin needs a restart of Jellyfin, so it is left to a person; what it shows too.
    # UserPermissionRequest4k off: on, a favorite of a user who may request 4K (every admin) is a 4K request, and Seerr
    # has no 4K Radarr or Sonarr to send it to. EnableStartupSync on: the sync task's 24-hour interval restarts with
    # Jellyfin, and the host is shut down every day, so without a sync on startup the placeholders never change.
    def bridge_seerr(self) -> None:
        plugin = find(self._client.get("/Plugins"), "Name", "JellyBridge")
        path = f"/Plugins/{plugin['Id']}/Configuration"
        settings = {
            "JellyseerrUrl": "http://seerr:5055",
            "ApiKey": self._key_of("seerr"),
            "LibraryDirectory": DISCOVER_PATH,
            "IsEnabled": True,
            "UserPermissionRequest4k": False,
            "EnableStartupSync": True,
        }
        self._client.post(path, {**self._client.get(path), **settings})

    def add_discover(self) -> None:
        if any(folder["Name"] == DISCOVER for folder in self._client.get("/Library/VirtualFolders")):
            return
        query = {"name": DISCOVER, "collectionType": "mixed", "paths": DISCOVER_PATH, "refreshLibrary": "true"}
        self._client.post(f"/Library/VirtualFolders?{urlencode(query)}", {})
