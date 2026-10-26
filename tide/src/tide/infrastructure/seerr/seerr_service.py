from collections.abc import Callable
from typing import Any

from tide.infrastructure.http.api_client import ApiClient
from tide.infrastructure.http.schema import find


# Seerr: adds Radarr and Sonarr as the default servers of the requests, with the quality profile, the root folder
# and a link to their web UI on the LAN. Seerr reaches them by container name and holds their API keys, key_of.
# It scans every library of Jellyfin but Discover, whose placeholders it would take as available.
class SeerrService:
    def __init__(self, client: ApiClient, key_of: Callable[[str], str], quality_profile: str, lan_host: str) -> None:
        self._client = client
        self._key_of = key_of
        self._quality_profile = quality_profile
        self._lan_host = lan_host

    def send_to_radarr(self) -> None:
        server = self._server("radarr", 7878, "/data/movies")
        self._client.upsert("/settings/radarr", {**server, "minimumAvailability": "released"})

    # Anime goes through the same profile and folder: Sonarr only names its episodes another way.
    def send_to_sonarr(self) -> None:
        server = self._server("sonarr", 8989, "/data/shows")
        anime = {
            "activeAnimeProfileId": server["activeProfileId"],
            "activeAnimeProfileName": server["activeProfileName"],
            "activeAnimeDirectory": server["activeDirectory"],
            "animeTags": [],
            "enableSeasonFolders": True,
            "seriesType": "standard",
            "animeSeriesType": "anime",
        }
        self._client.upsert("/settings/sonarr", {**server, **anime})

    # The sync lists the libraries Jellyfin has now, Discover too once it exists, with the ids Seerr wants.
    def skip_discover(self) -> None:
        for library in self._client.post("/settings/jellyfin/library/sync", {}):
            self._client.put(f"/settings/jellyfin/library/{library['id']}", {"enabled": library["name"] != "Discover"})

    # Seerr's test of the connection lists the quality profiles, with the ids it wants.
    def _server(self, app: str, port: int, root_folder: str) -> dict[str, Any]:
        connection = {"hostname": app, "port": port, "apiKey": self._key_of(app), "useSsl": False, "baseUrl": ""}
        test = self._client.post(f"/settings/{app}/test", connection)
        profile = find(test["profiles"], "name", self._quality_profile)
        return {
            **connection,
            "name": app.capitalize(),
            "activeProfileId": profile["id"],
            "activeProfileName": profile["name"],
            "activeDirectory": root_folder,
            "is4k": False,
            "isDefault": True,
            "externalUrl": f"http://{self._lan_host}:{port}",
            "syncEnabled": True,
            "preventSearch": False,
            "tags": [],
            "tagRequests": False,
        }
